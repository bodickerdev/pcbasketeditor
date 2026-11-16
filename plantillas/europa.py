"""
Pasa al juego los 32 equipos europeos de la temporada 2026-27 (datos de la API oficial de la
Euroliga, descargados con descargar_europa.py).

Uso (desde la carpeta EDITOR\\plantillas):
    python europa.py                    aplica los 32 equipos al juego
    python europa.py --prueba CARPETA   escribe en CARPETA (copia de los archivos del juego)

Qué hace con cada equipo europeo del juego (huecos 18-49):
  · datos del club, entrenador, historia y nombre del marcador (MANAGER.DAT)
  · jugadores: los N con más minutos (N = jugadores que tenía el equipo en 1996), con
    estadísticas reales, biografía, valoraciones calculadas a partir de las estadísticas,
    color de piel deducido de la foto y cara pequeña de la pantalla previa al partido
  · escudo: partido (ESCUDOS.BIN y CARAS.BIN) y menús (BASKET96.DGF)
  · colores de la equipación (partido y figuras del menú)
Se mantiene el número de jugadores de cada equipo para no mover nada en el archivo.
"""
import argparse, json, math, os, shutil, sys, textwrap, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image  # noqa: E402
from dbc import Database, Player  # noqa: E402
from caras import Faces, small_from_image, SMALL_PALETTE, LOGO_BASE, BG_INDEX  # noqa: E402
from dgf import DGF  # noqa: E402
import equipaciones as eq  # noqa: E402

DATA = os.path.join(HERE, 'datos', 'europa')
GAME_DEFAULT = os.path.normpath(os.path.join(HERE, '..', '..')) + os.sep
POS_TXT = ['base', 'escolta', 'alero', 'ala-pívot', 'pívot']

# ----------------------------------------------------------------------------------------
# Hueco del juego (equipo de 1996) -> club 2026-27
#   código API, nombre en menús (máx. 14), marcador (12), camiseta, detalles, pantalón
# Los colores son los de la equipación de casa (aproximados; se cambian en el editor).
# ----------------------------------------------------------------------------------------
SLOTS = {
    18: ('OLY', 'Olympiacos',     ' OLYMPIACOS ', 'Rojo', 'Blanco', 'Rojo'),
    19: ('PAN', 'Panathinaikos',  'PANATHINAIK.', 'Verde', 'Blanco', 'Verde'),
    20: ('HTA', 'Hapoel T. Aviv', 'HAPOEL T.AV.', 'Rojo', 'Blanco', 'Rojo'),
    21: ('VIR', 'Virtus Bolonia', '   VIRTUS   ', 'Negro', 'Blanco', 'Negro'),
    22: ('TRT', 'Tortona',        '  TORTONA   ', 'Azul', 'Blanco', 'Azul'),
    23: ('MIL', 'Olimpia Milán',  '   MILANO   ', 'Blanco', 'Rojo', 'Blanco'),
    24: ('LEM', 'Le Mans',        '  LE MANS   ', 'Verde', 'Blanco', 'Verde'),
    25: ('NAP', 'Napoli',         '   NAPOLI   ', 'Azul celeste', 'Blanco', 'Azul celeste'),
    26: ('ASV', 'ASVEL',          '   ASVEL    ', 'Verde', 'Blanco', 'Verde'),
    27: ('BUD', 'Buducnost',      ' BUDUCNOST  ', 'Azul', 'Blanco', 'Azul'),
    28: ('ZAL', 'Zalgiris',       '  ZALGIRIS  ', 'Verde', 'Blanco', 'Verde'),
    29: ('DUB', 'Dubai',          '   DUBAI    ', 'Azul marino', 'Dorado', 'Azul marino'),
    30: ('BES', 'Besiktas',       '  BESIKTAS  ', 'Negro', 'Blanco', 'Negro'),
    31: ('MUN', 'Bayern Múnich',  '   BAYERN   ', 'Rojo', 'Blanco', 'Rojo'),
    32: ('ULM', 'Ulm',            '    ULM     ', 'Naranja', 'Blanco', 'Naranja'),
    33: ('TEL', 'Maccabi',        '  MACCABI   ', 'Amarillo', 'Azul', 'Amarillo'),
    34: ('PAR', 'Partizan',       '  PARTIZAN  ', 'Negro', 'Blanco', 'Negro'),
    35: ('ULK', 'Fenerbahçe',     ' FENERBAHCE ', 'Azul marino', 'Amarillo', 'Azul marino'),
    36: ('IST', 'Anadolu Efes',   '    EFES    ', 'Azul', 'Blanco', 'Azul'),
    37: ('JER', 'H. Jerusalén',   ' JERUSALEM  ', 'Rojo', 'Negro', 'Rojo'),
    38: ('NIN', 'Chemnitz',       '  CHEMNITZ  ', 'Azul celeste', 'Blanco', 'Azul celeste'),
    39: ('PAO', 'PAOK',           '    PAOK    ', 'Negro', 'Blanco', 'Negro'),
    40: ('BAH', 'Bahçesehir',     ' BAHCESEHIR ', 'Azul', 'Naranja', 'Azul'),
    41: ('ARI', 'Aris',           '    ARIS    ', 'Amarillo', 'Negro', 'Amarillo'),
    42: ('VNC', 'Reyer Venecia',  '  VENEZIA   ', 'Granate', 'Dorado', 'Granate'),
    43: ('MRO', 'Maxima Roma',    'MAXIMA ROMA ', 'Granate', 'Amarillo', 'Granate'),
    44: ('BCR', 'Roma Basket',    '    ROMA    ', 'Amarillo', 'Rojo', 'Amarillo'),
    45: ('TTK', 'Türk Telekom',   'TURK TELEKOM', 'Azul celeste', 'Blanco', 'Azul celeste'),
    46: ('PRS', 'Paris',          '   PARIS    ', 'Negro', 'Blanco', 'Negro'),
    47: ('BUR', 'Tofas',          '   TOFAS    ', 'Azul', 'Blanco', 'Azul'),
    48: ('LLI', 'London Lions',   'LONDON LIONS', 'Negro', 'Dorado', 'Negro'),
    49: ('RED', 'Estrella Roja',  'CRVENA ZVEZ.', 'Rojo', 'Blanco', 'Rojo'),
}

COUNTRY_ES = {
    'United States of America': 'EE.UU.', 'Greece': 'Grecia', 'Serbia': 'Serbia',
    'Turkiye': 'Turquía', 'Turkey': 'Turquía', 'Italy': 'Italia', 'France': 'Francia',
    'Germany': 'Alemania', 'Spain': 'España', 'Lithuania': 'Lituania', 'Israel': 'Israel',
    'Montenegro': 'Montenegro', 'Croatia': 'Croacia', 'Slovenia': 'Eslovenia',
    'Bosnia and Herzegovina': 'Bosnia', 'Latvia': 'Letonia', 'Poland': 'Polonia',
    'Czech Republic': 'Chequia', 'Czechia': 'Chequia', 'United Kingdom': 'Reino Unido',
    'Great Britain': 'Reino Unido', 'Canada': 'Canadá', 'Australia': 'Australia',
    'Nigeria': 'Nigeria', 'Senegal': 'Senegal', 'Cameroon': 'Camerún', 'Mali': 'Malí',
    'Dominican Republic': 'Rep. Dominicana', 'Puerto Rico': 'Puerto Rico',
    'Argentina': 'Argentina', 'Brazil': 'Brasil', 'Uruguay': 'Uruguay', 'Mexico': 'México',
    'Bulgaria': 'Bulgaria', 'Georgia': 'Georgia', 'Ukraine': 'Ucrania', 'Russia': 'Rusia',
    'Belgium': 'Bélgica', 'Netherlands': 'Países Bajos', 'Finland': 'Finlandia',
    'Sweden': 'Suecia', 'Denmark': 'Dinamarca', 'Norway': 'Noruega', 'Estonia': 'Estonia',
    'Austria': 'Austria', 'Switzerland': 'Suiza', 'Portugal': 'Portugal',
    'Hungary': 'Hungría', 'Romania': 'Rumanía', 'North Macedonia': 'Macedonia del Norte',
    'Slovakia': 'Eslovaquia', 'Cyprus': 'Chipre', 'Albania': 'Albania', 'Kosovo': 'Kosovo',
    'Belarus': 'Bielorrusia', 'Iceland': 'Islandia', 'Ireland': 'Irlanda',
    'United Arab Emirates': 'Emiratos Árabes', 'Jamaica': 'Jamaica', 'Bahamas': 'Bahamas',
    'Congo': 'Congo', 'DR Congo': 'R.D. del Congo', 'Democratic Republic of the Congo':
    'R.D. del Congo', 'Angola': 'Angola', 'Egypt': 'Egipto', "Cote d'Ivoire": 'Costa de Marfil',
    'Ivory Coast': 'Costa de Marfil', 'Ghana': 'Ghana', 'South Sudan': 'Sudán del Sur',
    'Sudan': 'Sudán', 'Guinea': 'Guinea', 'Cape Verde': 'Cabo Verde', 'Japan': 'Japón',
    'China': 'China', 'Philippines': 'Filipinas', 'New Zealand': 'Nueva Zelanda',
    'Venezuela': 'Venezuela', 'Colombia': 'Colombia', 'Panama': 'Panamá', 'Haiti': 'Haití',
    'Lebanon': 'Líbano', 'Jordan': 'Jordania', 'Iran': 'Irán', 'Armenia': 'Armenia',
    'Azerbaijan': 'Azerbaiyán', 'Kazakhstan': 'Kazajistán', 'Luxembourg': 'Luxemburgo',
    'Gabon': 'Gabón', 'Central African Republic': 'Rep. Centroafricana', 'Benin': 'Benín',
    'Tunisia': 'Túnez', 'Morocco': 'Marruecos', 'Algeria': 'Argelia', 'Chad': 'Chad',
    'Burkina Faso': 'Burkina Faso', 'Togo': 'Togo', 'Rwanda': 'Ruanda', 'Uganda': 'Uganda',
    'Kenya': 'Kenia', 'South Africa': 'Sudáfrica', 'Mozambique': 'Mozambique',
    'Moldova': 'Moldavia', 'Montserrat': 'Montserrat', 'Qatar': 'Catar',
}
COMP_TXT = {'E': 'la Euroliga', 'U': 'la Eurocup'}


# ------------------------------------------------------------------ utilidades
PUNCT = {'’': "'", '‘': "'", '“': '"', '”': '"', '–': '-', '—': '-', '…': '...', 'ı': 'i',
         'ł': 'l', 'Ł': 'L', 'đ': 'd', 'Đ': 'D', 'ß': 'ss', '∙': '\xf9'}


def latin1(s):
    """Solo caracteres Latin-1 (la viñeta ∙ se guarda como F9, igual que en el juego)."""
    out = ''
    for ch in s:
        if ch == '∙':
            out += ch           # dbc.py la convierte al guardar los textos largos
            continue
        try:
            ch.encode('latin-1'); out += ch
            continue
        except UnicodeEncodeError:
            pass
        if ch in PUNCT:
            out += PUNCT[ch]
            continue
        base = unicodedata.normalize('NFD', ch)[0]
        try:
            base.encode('latin-1'); out += base
        except UnicodeEncodeError:
            out += '?'
    return out


def upper_name(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s.upper())
                   if unicodedata.category(c) != 'Mn')


def title(s):
    """'MILLER-MCINTYRE' -> 'Miller-Mcintyre', 'JEAN CHARLES' -> 'Jean Charles'."""
    def word(w):
        return w.upper() if w.upper() in ('II', 'III', 'IV', 'V') else w.capitalize()
    return '-'.join(' '.join(word(w) for w in part.split()) for part in s.split('-'))


def country(c):
    return latin1(COUNTRY_ES.get(c, c))


def fmt(x, n=1):
    return f"{x:.{n}f}".replace('.', ',')


def cp437(s):
    """Los textos largos (biografías, historias) se guardan en CP437."""
    out = ''
    for ch in s:
        ch = PUNCT.get(ch, ch) if ch != '∙' else ch
        try:
            ch.encode('cp437'); out += ch
        except UnicodeEncodeError:
            base = unicodedata.normalize('NFD', ch)[0]
            try:
                base.encode('cp437'); out += base
            except UnicodeEncodeError:
                out += '?'
    return out


def wrap(txt):
    return [l + ' ' for l in textwrap.wrap(cp437(txt), 72)]


def split_name(api_name):
    """'PAPANIKOLAOU, KOSTAS' -> ('Kostas', 'PAPANIKOLAOU')."""
    if ',' in api_name:
        last, first = [x.strip() for x in api_name.split(',', 1)]
    else:
        first, last = '', api_name.strip()
    return latin1(title(first)), latin1(upper_name(last))


def position(api_pos, h):
    """API: 1 base/escolta, 2 alero/ala-pívot, 3 pívot (y la altura decide el detalle)."""
    if api_pos == 1:
        return 0 if h < 192 else 1
    if api_pos == 2:
        return 2 if h < 204 else 3
    if api_pos == 3:
        return 4 if h >= 205 else 3
    return 2 if h < 200 else 4


def backup(path):
    if os.path.exists(path) and not os.path.exists(path + '.BAK'):
        shutil.copy2(path, path + '.BAK')
    if os.path.exists(path):
        os.chmod(path, 0o666)


# ------------------------------------------------------------------ jugadores
def per(s, k, mins):
    return s.get(k, 0) * 36 / mins if mins else 0


def ratings(s, pos, h, comp):
    """4 valoraciones (0-100) a partir de las estadísticas acumuladas de la temporada."""
    gp = s.get('gamesPlayed', 0)
    mins = s.get('minutesPlayed', 0)
    lvl_bonus = 4 if comp == 'E' else -2
    if gp < 1 or mins < 25:     # casi sin minutos: valores medios según la posición
        base = [[70, 62, 45, 60], [64, 66, 48, 60], [58, 64, 56, 62], [52, 60, 64, 62],
                [45, 56, 70, 64]][pos]
        return [max(35, min(97, v + lvl_bonus - 6)) for v in base]
    pir = s.get('pir', 0) / gp
    mpg = mins / gp
    level = 50 + 32 * math.tanh(max(pir, -5) / 13) + min(mpg, 30) * 0.35 + lvl_bonus
    ast, tov = per(s, 'assists', mins), per(s, 'turnovers', mins)
    pts, reb = per(s, 'pointsScored', mins), per(s, 'totalRebounds', mins)
    stl, blk = per(s, 'steals', mins), per(s, 'blocks', mins)
    fta, ftm = s.get('freeThrowsAttempted', 0), s.get('freeThrowsMade', 0)
    tpa, tpm = s.get('threePointersAttempted', 0), s.get('threePointersMade', 0)
    ft = ftm / fta if fta >= 5 else 0.72
    tp = tpm / tpa if tpa >= 8 else 0.33
    r1 = 38 + 6.5 * ast - 2.0 * tov + [16, 9, 2, -5, -10][pos]
    r2 = 30 + 2.0 * pts + 20 * (ft - 0.72) + 25 * (tp - 0.33)
    r3 = 28 + 3.0 * reb + (h - 196) * 0.9
    r4 = 42 + 5.5 * (stl + blk) + (h - 196) * 0.35 + min(mpg, 30) * 0.4
    return [int(max(35, min(97, round(0.5 * r + 0.5 * level)))) for r in (r1, r2, r3, r4)]


def skin_from_photo(path):
    """0 blanca, 1 negra, 2 mulata, según el brillo de la cara en la foto (aproximado)."""
    if not path:
        return 0
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    reg = im.crop((int(w * .38), int(h * .18), int(w * .62), int(h * .38)))
    px = [(r, g, b) for r, g, b, a in reg.getdata() if a > 200]
    if not px:
        return 0
    lum = sum(0.3 * r + 0.59 * g + 0.11 * b for r, g, b in px) / len(px)
    return 1 if lum < 90 else (2 if lum < 112 else 0)


def head_crop(path):
    """Cuadrado de la cabeza de la foto oficial (750x1000, fondo transparente) sobre negro."""
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    a = im.split()[3]
    bb = a.getbbox() or (0, 0, w, h)
    top = bb[1]
    side = int(h * 0.29)                     # cabeza y un poco de cuello
    # centro horizontal de la cabeza (filas por encima de los hombros)
    xs = []
    for y in range(top + int(side * 0.2), top + int(side * 0.7), 8):
        row = [x for x in range(0, w, 4) if a.getpixel((x, y)) > 128]
        if row:
            xs.append((row[0] + row[-1]) / 2)
    cx = sorted(xs)[len(xs) // 2] if xs else w / 2
    box = (int(cx - side / 2), max(0, top - int(side * 0.06)))
    im = im.crop((box[0], box[1], box[0] + side, box[1] + side))
    bg = Image.new('RGBA', im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    return bg.convert('RGB')


def stats30(s):
    v = [s.get(k, 0) for k in ('twoPointersMade', 'twoPointersAttempted', 'threePointersMade',
                               'threePointersAttempted', 'freeThrowsMade', 'freeThrowsAttempted',
                               'defensiveRebounds', 'offensiveRebounds', 'assists', 'blocks',
                               'steals', 'turnovers', 'minutesPlayed', 'gamesPlayed',
                               'foulsCommited')]
    return [min(int(round(x)), 65535) for x in v] + [0] * 15


STAT_KEYS = ('gamesPlayed', 'minutesPlayed', 'pointsScored', 'twoPointersMade',
             'twoPointersAttempted', 'threePointersMade', 'threePointersAttempted',
             'freeThrowsMade', 'freeThrowsAttempted', 'offensiveRebounds', 'defensiveRebounds',
             'totalRebounds', 'assists', 'steals', 'turnovers', 'blocks', 'foulsCommited', 'pir')


def typical_stats(stats, comp, pos_of, pos, games=8):
    """Medias de los jugadores de suplente (10-20 min) de esa posición en la competición,
    como si llevara `games` partidos. Para jugadores que aún no han jugado: el simulador del
    juego usa estas cifras y con todo a cero el jugador apenas anota."""
    rows = [s for (c, _t, code), s in stats.items() if c == comp and pos_of.get(code) == pos
            and s.get('gamesPlayed', 0) >= 3 and 10 <= s['minutesPlayed'] / s['gamesPlayed'] <= 20]
    if not rows:
        return {}
    out = {}
    for k in STAT_KEYS[1:]:
        vals = sorted(s.get(k, 0) / s['gamesPlayed'] for s in rows)
        out[k] = vals[len(vals) // 2] * games
    out['gamesPlayed'] = games
    return out


def bio(first, last, pos, h, birth, ctry, comp, s):
    d = f"{int(birth[8:10])}/{int(birth[5:7])}/{birth[:4]}" if birth else '?'
    txt = (f"∙ {first} {title(last)}, {POS_TXT[pos]} de {fmt(h / 100, 2)} m, nació en {ctry} el {d}. ")
    gp = int(s.get('gamesPlayed', 0))
    if gp:
        txt += (f"En {COMP_TXT[comp]} 2026-27 promedia {fmt(s['pointsScored'] / gp)} puntos, "
                f"{fmt(s['totalRebounds'] / gp)} rebotes y {fmt(s['assists'] / gp)} asistencias "
                f"en {fmt(s['minutesPlayed'] / gp)} minutos ({gp} partidos).")
    else:
        txt += f"Todavía no ha jugado en {COMP_TXT[comp]} 2026-27."
    return wrap(latin1(txt))


# ------------------------------------------------------------------ escudos
def crest_image(path):
    im = Image.open(path).convert('RGBA')
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def write_shields(game, slot_ti, crest, faces, dg, esc, esc_offs, esc_used):
    # menús: escudo grande (0/1) y pequeño (2/3) con sus máscaras
    g = TEAMS_GFX[slot_ti]
    dg.put_logo(g[0], g[1], crest)
    w2, h2, _ = dg.header(g[2]); w3, h3, _ = dg.header(g[3])
    dg.put_logo(g[2], g[3], crest, border=(w3 > w2))
    # partido: ESCUDOS.BIN (marcador) ...
    start, w, h = esc_offs[slot_ti]
    lg = crest.copy(); lg.thumbnail((w - 2, h - 2), Image.LANCZOS)
    canvas = Image.new('RGBA', (w, h), faces.palette[0] + (255,))
    canvas.alpha_composite(lg, ((w - lg.width) // 2, (h - lg.height) // 2))
    esc[start:start + w * h] = faces.convert(canvas, w, h, esc_used)
    # ... y CARAS.BIN (sale al anotar un equipo sin retratos)
    slot = faces.logo_slot(slot_ti)
    fw, fh = faces.size(slot)
    lg = crest.copy(); lg.thumbnail((fw - 2, fh - 2), Image.LANCZOS)
    canvas = Image.new('RGBA', (fw, fh), faces.palette[BG_INDEX] + (255,))
    canvas.alpha_composite(lg, ((fw - lg.width) // 2, (fh - lg.height) // 2))
    faces.set_pixels(slot, faces.convert(canvas, fw, fh, faces.colors_for(slot)))


TEAMS_GFX = {}
POS_OF = {}


# ------------------------------------------------------------------ principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prueba', help='carpeta con una COPIA de los archivos del juego')
    a = ap.parse_args()
    game = (os.path.abspath(a.prueba) + os.sep) if a.prueba else GAME_DEFAULT

    clubs = json.load(open(os.path.join(DATA, 'clubs.json'), encoding='utf-8'))
    club_by = {x['code']: (c, x) for c in 'EU' for x in clubs[c]}
    standings = json.load(open(os.path.join(DATA, 'standings.json'), encoding='utf-8'))
    stats = {}
    for c in 'EU':
        for s in json.load(open(os.path.join(DATA, f'stats_{c}.json'), encoding='utf-8')):
            stats[(c, s['player']['team']['code'], s['player']['code'])] = s

    global POS_OF
    POS_OF = {}
    for code in [v[0] for v in SLOTS.values()]:
        for p in json.load(open(os.path.join(DATA, code, 'people.json'), encoding='utf-8')):
            if p['type'] == 'J':
                POS_OF[p['person']['code']] = position(p['position'], p['person']['height'] or 198)

    db = Database.load(game + 'BASKET96.DBC')
    orig_db = Database.load(game + 'BASKET96.DBC.BAK') if os.path.exists(game + 'BASKET96.DBC.BAK') else db
    faces = Faces(game + 'CARAS.BIN', game + 'CAMPO800.BIN')
    dg = DGF(game + 'BASKET96.DGF')
    dg_orig = DGF(game + 'BASKET96.DGF.BAK') if os.path.exists(game + 'BASKET96.DGF.BAK') else dg
    kits = eq.Kits(game + 'MANAGER.DAT', game + 'CAMPO800.BIN')
    menu = eq.MenuKits(dg, dg_orig, [t.gfx for t in orig_db.teams if eq.menu_gfx(t.gfx)])
    presets = dict(eq.PRESETS)

    esc = bytearray(open(game + 'ESCUDOS.BIN', 'rb').read())
    esc_orig = open(game + 'ESCUDOS.BIN.BAK', 'rb').read() if os.path.exists(game + 'ESCUDOS.BIN.BAK') else bytes(esc)
    esc_offs, esc_used, o = [], set(), 0
    for n in range(54):
        w = int.from_bytes(esc[o:o + 2], 'little'); h = int.from_bytes(esc[o + 2:o + 4], 'little')
        sz = int.from_bytes(esc[o + 4:o + 8], 'little')
        esc_offs.append((o + 8, w, h))
        if n < 51:
            esc_used.update(esc_orig[o + 8:o + 8 + sz])
        o += 8 + sz
    esc_used = sorted(esc_used)

    # parámetros del simulador: copiados de jugadores de 1996 de la misma posición
    tmpl = {}
    for t in orig_db.teams:
        for p in t.players:
            tmpl.setdefault(p.position, bytes(p.attrs[11:19]))

    for ti, (code, short, board, c_main, c_det, c_pan) in SLOTS.items():
        team = db.teams[ti]
        TEAMS_GFX[ti] = team.gfx
        comp, club = club_by[code]
        d = os.path.join(DATA, code)
        people = json.load(open(os.path.join(d, 'people.json'), encoding='utf-8'))
        n = len(orig_db.teams[ti].players)
        assert len(team.players) == n, f"El equipo {ti} ya no tiene {n} jugadores"
        ctry_club = club['country']['code']

        cand = []
        for p in people:
            if p['type'] != 'J' or not p['active']:
                continue
            s = stats.get((comp, code, p['person']['code']), {})
            cand.append((p, s))
        # los N con más minutos; titulares = los 5 con más partidos de titular
        cand.sort(key=lambda x: (-x[1].get('minutesPlayed', 0), -x[1].get('gamesPlayed', 0)))
        cand = cand[:n]
        starters = sorted(cand, key=lambda x: (-x[1].get('gamesStarted', 0),
                                               -x[1].get('minutesPlayed', 0)))[:5]
        rest = [x for x in cand if x not in starters]
        ordered = starters + rest

        new, surnames = [], {}
        for p, s in ordered:
            last_up = split_name(p['person']['name'])[1]
            surnames[last_up] = surnames.get(last_up, 0) + 1
        for i, (p, s) in enumerate(ordered):
            pr = p['person']
            first, last = split_name(pr['name'])
            h = pr['height'] or 198
            pos = position(p['position'], h)
            kg = pr['weight'] or int(h - 100 + (5 if pos >= 3 else -5))
            photo = next((f for f in (os.path.join(d, 'img', pr['code'] + ext)
                                      for ext in ('.webp', '.png')) if os.path.exists(f)), None)
            skin = skin_from_photo(photo)
            r = ratings(s, pos, h, comp)
            gp = s.get('gamesPlayed', 0)
            pir = s.get('pir', 0) / gp if gp else 0
            at = bytearray(21)
            at[0] = 1 if pr['country']['code'] != ctry_club else 0
            at[1] = skin
            at[2] = 3 if skin == 0 else 1          # pelo normal / corto
            at[3] = 2 if skin == 0 else 0          # castaño / negro
            at[5] = 0                              # sin barba (se cambia en el editor)
            at[6:10] = bytes(r)
            at[10] = i + 1
            at[11:19] = tmpl[pos]
            surname = title(last)
            if surnames[last] > 1:
                surname = f"{surname}, {first[:1]}."
            birth = (pr.get('birthDate') or '')[:10]
            ctry = country(pr.get('birthCountry', pr['country'])['name']) if pr.get('birthCountry') else country(pr['country']['name'])
            old = team.players[i]
            dorsal = int(p['dorsal']) if str(p.get('dorsal', '')).isdigit() else 0
            new.append(Player(
                full_name=f"{first} {last}".strip(), short_name=f"{first} {last}".strip()[:24],
                surname=latin1(surname)[:15], gfx=[1, old.gfx[1]],
                bio=bio(first, last, pos, h, birth, ctry, comp, s),
                dorsal=dorsal % 256, position=pos, height_raw=max(0, min(255, h - 100)),
                weight=max(60, min(160, kg)), birthplace=ctry,
                birthdate=f"{birth[8:10]}-{birth[5:7]}-{birth[2:4]}" if birth else '-',
                value=int(max(10, min(400, 20 + pir * 9 + (25 if comp == 'E' else 0)))),
                prev_club=latin1(title(p.get('lastTeam') or '-'))[:30] or '-',
                attrs=at, team=short,
                current=stats30(s if s.get('gamesPlayed') else typical_stats(stats, comp, POS_OF, pos)),
                seasons=[]))
            # cara pequeña de la pantalla previa al partido
            g = old.gfx[1]
            if g > 1 and dg.header(g)[:3] == (24, 24, 4):
                px = small_from_image(head_crop(photo), 1.15, 1.15) if photo else bytes(576)
                dg.encode(g, px)
                dg.d[g + 2:g + 50] = bytes(v for rgb in SMALL_PALETTE for v in rgb)

        team.players = new
        name = latin1(club['name'])
        arena = ''
        af = os.path.join(d, 'arena.json')
        if os.path.exists(af):
            arena = latin1(title(json.load(open(af, encoding='utf-8')).get('name') or ''))
        coach = next((p['person'] for p in people if p['type'] == 'E'), None)
        w, l, _ = standings[comp].get(code, (0, 0, 0))
        team.short_name = latin1(short)
        team.long_name = name
        team.club_name = latin1(club.get('clubPermanentName') or name)
        team.address = latin1(club.get('address') or '-')[:120]
        team.arena = arena or '-'
        team.capacity = 0
        team.president = latin1(club.get('president') or '-')
        team.sponsor = latin1(club.get('sponsor') or name)
        team.tag = team.short_name
        hist = (f"∙ {name} ({title(club.get('city') or '').strip()}, {country(club['country']['name'])}) "
                f"juega {COMP_TXT[comp]} 2026-27" + (f" en el {arena}" if arena else '') + ". ")
        if coach:
            cf, cl = split_name(coach['name'])
            hist += f"Su entrenador es {cf} {title(cl)}. "
        hist += f"Tras {w + l} jornadas suma {w} victorias y {l} derrotas."
        team.history = wrap(latin1(hist))
        if coach:
            cf, cl = split_name(coach['name'])
            team.coach.full_name = team.coach.short_name = f"{cf} {cl}"
            age = ''
            if coach.get('birthDate'):
                age = f", de {2026 - int(coach['birthDate'][:4])} años"
            team.coach.bio = wrap(latin1(f"∙ {cf} {title(cl)} ({country(coach['country']['name'])}{age}) "
                                         f"entrena a {name} en la temporada 2026-27."))

        # marcador
        nb = board.encode('latin-1')
        assert len(nb) == 12, board
        i = kits.d.find(b' BARCELONA  ')
        i = i if i >= 0 else 0x5C07C
        kits.d[i + 12 * ti:i + 12 * ti + 12] = nb

        # escudos
        cp = os.path.join(d, 'crest.png')
        if os.path.exists(cp):
            write_shields(game, ti, crest_image(cp), faces, dg, esc, esc_offs, esc_used)

        # equipación: principal y alternativa (blanca, o del color de los detalles si la
        # principal ya es blanca)
        kit = kits.get(ti)
        for z in ('cam1', 'cam2'):
            kits.set_zone(kit, z, presets[c_main])
        for z in ('pecho1', 'pecho2', 'cuello', 'sisas', 'costados', 'franja', 'bajo'):
            kits.set_zone(kit, z, presets[c_det])
        kits.set_zone(kit, 'pantalon', presets[c_pan])
        kits.put(ti, False, kit)
        alt_main, alt_det = ('Blanco', c_main) if c_main != 'Blanco' else (c_det, 'Blanco')
        alt = kits.get(ti, True)
        for z in ('cam1', 'cam2', 'pantalon'):
            kits.set_zone(alt, z, presets[alt_main])
        for z in ('pecho1', 'pecho2', 'cuello', 'sisas', 'costados', 'franja', 'bajo'):
            kits.set_zone(alt, z, presets[alt_det])
        kits.put(ti, True, alt)
        menu.recolor(team.gfx, eq.menu_colors_from_kit(kits, kit))

        print(f"{ti} {code} {team.short_name:15s} {len(new):2d} jug. | " +
              ', '.join(f"{p.dorsal} {p.surname}" for p in new[:5]))

    for ti in SLOTS:
        kits.recompute_clash(ti)

    Database.parse(db.serialize())   # comprobación
    for f in ('BASKET96.DBC', 'CARAS.BIN', 'BASKET96.DGF', 'ESCUDOS.BIN', 'MANAGER.DAT'):
        backup(game + f)
    db.save(game + 'BASKET96.DBC')
    faces.save(game + 'CARAS.BIN')
    dg.save(game + 'BASKET96.DGF')
    open(game + 'ESCUDOS.BIN', 'wb').write(esc)
    # MANAGER.DAT: nombres del marcador + equipaciones (kits.save solo copia las tablas)
    man = bytearray(open(game + 'MANAGER.DAT', 'rb').read())
    i = man.find(b' BARCELONA  ')
    i = i if i >= 0 else 0x5C07C
    for ti in SLOTS:
        man[i + 12 * ti:i + 12 * ti + 12] = kits.d[i + 12 * ti:i + 12 * ti + 12]
    open(game + 'MANAGER.DAT', 'wb').write(man)
    kits.save(game + 'MANAGER.DAT')
    print("\nHecho.")
    print('Recuerda: ejecuta  python valoraciones.py  para recalcular las valoraciones con el '
          'historial (este script usa una fórmula más simple).')


if __name__ == '__main__':
    main()
