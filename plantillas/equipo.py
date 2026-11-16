"""
Aplica una plantilla de acb.com a un equipo ACB del juego.

Uso (desde la carpeta EDITOR\\plantillas):
    python equipo.py cfg_zaragoza.py                  equipo completo (datos, retratos, escudo, marcador)
    python equipo.py cfg_zaragoza.py --solo-retratos  solo rehace los retratos
    python equipo.py cfg_zaragoza.py --solo-escudo    solo rehace el escudo
    python equipo.py cfg_zaragoza.py --prueba CARPETA escribe en CARPETA (copia de los archivos del juego)

Cada cfg_*.py define: TI (nº de equipo 0-17), OLD_SHORT (nombre en 1996), DATOS (carpeta en datos/),
D (valoraciones, peso, valor y aspecto por jugador), ORDER (orden en la plantilla, 1-5 titulares),
SURNAME, TEAM, HISTORY, COACH, LOGO_CROP y opcionalmente LIGHT, DARK, FIXES, SCOREBOARD.

Los datos de cada equipo (players.json, roster.json, fotos y escudo) se descargan con descargar.py.
"""
import argparse, colorsys, importlib.util, json, os, re, shutil, sys, textwrap, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageEnhance  # noqa: E402
from dbc import Database, Player  # noqa: E402
from caras import Faces  # noqa: E402

GAME_DEFAULT = os.path.normpath(os.path.join(HERE, '..', '..')) + os.sep
POS = {'Base': 0, 'Escolta': 1, 'Alero': 2, 'Ala-pívot': 3, 'Pívot': 4}
POS_TXT = ['base', 'escolta', 'alero', 'ala-pívot', 'pívot']
BG = 180   # fondo negro de los retratos


# ---------------------------------------------------------------- utilidades
def load_cfg(path):
    spec = importlib.util.spec_from_file_location('cfg', path)
    cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg)
    return cfg


def upper_name(s):
    out = ''
    for ch in s.upper():
        out += ch if ch == 'Ñ' else ''.join(
            c for c in unicodedata.normalize('NFD', ch) if unicodedata.category(c) != 'Mn')
    return out


def place_fmt(place, country):
    # "Joliet (Illinois)" + "EE.UU." -> "Joliet, Illinois (EE.UU.)"
    town = re.sub(r' *[(](.*?)[)]', r', \1', place)
    return f"{town} ({country})"


def fmt(x, n=1):
    return f"{x:.{n}f}".replace('.', ',')


def bio_for(p, pos):
    s, car = p['totals'][0], p['totals'][2]
    g = max(s['numGames'], 1)
    d, m, y = p['birthDate'].split('-')
    txt = (f"∙ {p['first']} {p['last']}, {POS_TXT[pos]} de {fmt(p['height'] / 100, 2)} m, nació en "
           f"{place_fmt(p['birthPlace'], p['birthCountry'])} el {int(d)}/{int(m)}/{y}. Juega con "
           f"licencia {p['lic']} y su nacionalidad deportiva es {p['nationality']}. ")
    if s['numGames']:
        txt += (f"En la temporada 2026-27 de la Liga Endesa promedia {fmt(s['points'] / g)} puntos, "
                f"{fmt(s['rebounds'] / g)} rebotes y {fmt(s['assists'] / g)} asistencias en "
                f"{fmt(s['timePlayed'] / 60 / g)} minutos ({s['numGames']} partidos). ")
    else:
        txt += "Todavía no ha debutado en la temporada 2026-27 de la Liga Endesa. "
    if car['numGames'] > s['numGames']:
        cg = car['numGames']
        txt += (f"En su carrera en la ACB suma {cg} partidos, con {fmt(car['points'] / cg)} puntos "
                f"y {fmt(car['rating'] / cg)} de valoración de media.")
    return [l + ' ' for l in textwrap.wrap(txt, 72)]


def stats30(t):
    v = [t['twoPointersMade'], t['twoPointersAttempted'], t['threePointersMade'],
         t['threePointersAttempted'], t['freeThrowsMade'], t['freeThrowsAttempted'],
         t['defensiveRebounds'], t['offensiveRebounds'], t['assists'], t['blocks'],
         t['steals'], t['turnovers'], round(t['timePlayed'] / 60), t['numGames'], t['personalFouls']]
    return [min(int(x), 65535) for x in v] + [0] * 15


def season_or_career(p, games=10):
    """Estadísticas de la temporada; si aún no ha jugado, sus medias de carrera ACB como si
    llevara `games` partidos. El simulador del juego usa estas cifras (porcentajes de tiro,
    rebotes, asistencias...): un jugador con todo a cero apenas anota."""
    cur = p['totals'][0]
    car = p['totals'][2] if len(p['totals']) > 2 else {}
    if cur.get('numGames') or not car.get('numGames'):
        return cur
    k = games / car['numGames']
    return {key: (round(v * k) if isinstance(v, (int, float)) else v) for key, v in car.items()} |         {'numGames': games}


def backup(path):
    if os.path.exists(path) and not os.path.exists(path + '.BAK'):
        shutil.copy2(path, path + '.BAK')
    if os.path.exists(path):
        os.chmod(path, 0o666)


def load_players(cfg):
    """players.json + roster.json del equipo, con las correcciones FIXES de la config."""
    d = os.path.join(HERE, 'datos', cfg.DATOS)
    players = json.load(open(os.path.join(d, 'players.json'), encoding='utf-8'))
    roster = json.load(open(os.path.join(d, 'roster.json'), encoding='utf-8'))
    nick = {r['player']['id']: r['player']['nicknameFirstName'] for r in roster['players']}
    fixes = getattr(cfg, 'FIXES', {})
    out = {}
    for p in players:
        p['first'], p['last'] = p['first'].strip(), p['last'].strip()
        p['nick'] = (nick.get(p['id']) or p['first']).strip()
        for k, v in fixes.get(p['id'], {}).items():
            p[k] = v
        out[p['last']] = p
    return d, out


# ---------------------------------------------------------------- retratos
def face_colors(faces, game, cfg):
    def hsv(c):
        r, g, b = faces.palette[c]
        return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

    def is_red(c):
        h, s, v = hsv(c)
        return (h < 0.04 or h > 0.93) and s > 0.6 and v > 0.35

    def is_grey(c):
        h, s, v = hsv(c)
        return s < 0.22 and v > 0.4

    # SIEMPRE desde las caras originales (si se usa el archivo editado, la paleta mengua)
    orig = game + 'CARAS.BIN.BAK'
    safe = Faces(orig, game + 'CAMPO800.BIN').safe if os.path.exists(orig) else faces.safe
    base = [c for c in safe if not is_red(c)]          # sin rojos puros (puntos en los labios)
    # Pieles claras: sin grises claros (con la paleta completa salían manchas grises/azuladas).
    # Pieles oscuras: paleta completa (sin grises, la luz de contorno se volvía motas verdes).
    return {'light': [c for c in base if not is_grey(c)], 'dark': base}


def make_portrait(faces, colors, cfg, img_path, skin, slot):
    im = Image.open(img_path).convert('RGBA')
    w, h = im.size
    im = im.crop((0, 0, w, w))
    bg = Image.new('RGBA', im.size, faces.palette[BG] + (255,))
    bg.alpha_composite(im)
    im = bg.convert('RGB')
    # (brillo, saturación, contraste); LIGHT/DARK en la config para fotos especiales
    b, s, c = (getattr(cfg, 'LIGHT', (0.75, 1.5, 1.35)) if skin == 0
               else getattr(cfg, 'DARK', (0.85, 1.05, 1.2)))
    im = ImageEnhance.Contrast(ImageEnhance.Color(ImageEnhance.Brightness(im)
                               .enhance(b)).enhance(s)).enhance(c)
    return faces.convert(im, *faces.size(slot), colors['light' if skin == 0 else 'dark'])


def img_file(d, p):
    for ext in ('webp', 'jpg', 'png'):
        f = os.path.join(d, 'img', f"{p['id']}.{ext}")
        if os.path.exists(f):
            return f
    raise FileNotFoundError(f"No hay foto de {p['first']} {p['last']} en {d}\\img")


# ---------------------------------------------------------------- escudo
def load_logo(cfg, d):
    logo = Image.open(os.path.join(d, 'logo.png')).convert('RGBA')
    if getattr(cfg, 'LOGO_CROP', None):
        lw, lh = logo.size
        logo = logo.crop(tuple(int(c * s) for c, s in zip(cfg.LOGO_CROP, (lw, lh, lw, lh))))
    return logo


def write_logo(game, faces, cfg, d, team):
    """Escudo del partido (ESCUDOS.BIN) y escudos de los menús (BASKET96.DGF:
    grande, mediano para elegir equipo y pequeño para clasificación/calendario)."""
    from dgf import DGF, put_team_shields
    dg = DGF(game + 'BASKET96.DGF')
    put_team_shields(dg, team.gfx, load_logo(cfg, d))
    dg.save(game + 'BASKET96.DGF')

    esc = bytearray(open(game + 'ESCUDOS.BIN', 'rb').read())
    orig = open(game + 'ESCUDOS.BIN.BAK', 'rb').read() if os.path.exists(game + 'ESCUDOS.BIN.BAK') else bytes(esc)
    offs, used, o = [], set(), 0
    for n in range(54):
        w = int.from_bytes(esc[o:o + 2], 'little'); h = int.from_bytes(esc[o + 2:o + 4], 'little')
        sz = int.from_bytes(esc[o + 4:o + 8], 'little')
        offs.append((o + 8, w, h))
        if n < 51:
            used.update(orig[o + 8:o + 8 + sz])
        o += 8 + sz
    start, w, h = offs[cfg.TI]
    logo = load_logo(cfg, d)
    logo.thumbnail((w - 2, h - 2), Image.LANCZOS)
    canvas = Image.new('RGBA', (w, h), faces.palette[0] + (255,))
    canvas.alpha_composite(logo, ((w - logo.width) // 2, (h - logo.height) // 2))
    esc[start:start + w * h] = faces.convert(canvas, w, h, sorted(used))
    backup(game + 'ESCUDOS.BIN')
    open(game + 'ESCUDOS.BIN', 'wb').write(esc)


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cfg')
    ap.add_argument('--solo-retratos', action='store_true')
    ap.add_argument('--solo-escudo', action='store_true')
    ap.add_argument('--prueba', help='carpeta con una COPIA de los archivos del juego')
    a = ap.parse_args()
    cfg = load_cfg(a.cfg)
    game = (os.path.abspath(a.prueba) + os.sep) if a.prueba else GAME_DEFAULT
    d, P = load_players(cfg)

    db = Database.load(game + 'BASKET96.DBC')
    team = db.teams[cfg.TI]
    faces = Faces(game + 'CARAS.BIN', game + 'CAMPO800.BIN')
    colors = face_colors(faces, game, cfg)
    if team.short_name not in (cfg.OLD_SHORT, cfg.TEAM['short_name']):
        sys.exit(f"El equipo {cfg.TI} es '{team.short_name}', no '{cfg.OLD_SHORT}'. ¿Config equivocada?")
    if len(team.players) != len(cfg.ORDER):
        sys.exit(f"El equipo tiene {len(team.players)} jugadores y la config {len(cfg.ORDER)}.")

    if a.solo_escudo:
        write_logo(game, faces, cfg, d, team)
        print(f"Escudo de {cfg.TEAM['long_name']} actualizado.")
        return

    if a.solo_retratos:
        if team.short_name != cfg.TEAM['short_name']:
            sys.exit("Primero hay que aplicar el equipo completo.")
        for i, last in enumerate(cfg.ORDER):
            p = P[last]
            gp = team.players[i]
            if upper_name(p['last']) not in gp.full_name:
                sys.exit(f"El hueco {i} es {gp.full_name}, no {p['last']}: no toco los retratos.")
            slot = faces.player_slot(cfg.TI, i)
            faces.set_pixels(slot, make_portrait(faces, colors, cfg, img_file(d, p), cfg.D[last][6], slot))
        faces.save(game + 'CARAS.BIN')
        print(f"Retratos de {cfg.TEAM['long_name']} rehechos ({len(cfg.ORDER)}).")
        return

    # ---- equipo completo ----
    tmpl = {}   # parámetros del simulador: copiados de jugadores de 1996 de la misma posición
    orig_db = Database.load(game + 'BASKET96.DBC.BAK') if os.path.exists(game + 'BASKET96.DBC.BAK') else db
    for t in orig_db.teams:
        for p in t.players:
            tmpl.setdefault(p.position, bytes(p.attrs[11:19]))

    new = []
    for i, last in enumerate(cfg.ORDER):
        p = P[last]
        r1, r2, r3, r4, kg, val, skin, hair, beard = cfg.D[last]
        pos = POS[p['role']]
        old = team.players[i]
        d_, m_, y_ = p['birthDate'].split('-')
        at = bytearray(21)
        at[0] = 1 if p['lic'] == 'EXT' else 0
        at[1], at[2], at[5] = skin, hair, beard
        at[6:10] = bytes([r1, r2, r3, r4])
        at[10] = i + 1
        at[11:19] = tmpl[pos]
        new.append(Player(
            full_name=f"{p['first']} {upper_name(p['last'])}",
            short_name=f"{p['nick']} {upper_name(p['last'])}",
            surname=cfg.SURNAME.get(last, p['last']), gfx=[1, old.gfx[1]], bio=bio_for(p, pos),
            dorsal=int(p['num']), position=pos, height_raw=p['height'] - 100, weight=kg,
            birthplace=place_fmt(p['birthPlace'], p['birthCountry']), birthdate=f"{d_}-{m_}-{y_[2:]}",
            value=val, prev_club='-', attrs=at, team=cfg.TEAM['short_name'],
            current=stats30(season_or_career(p)), seasons=[]))
        slot = faces.player_slot(cfg.TI, i)
        faces.set_pixels(slot, make_portrait(faces, colors, cfg, img_file(d, p), skin, slot))

    team.players = new
    for k, v in cfg.TEAM.items():
        setattr(team, k, v)
    team.tag = cfg.TEAM['short_name']
    team.history = [l + ' ' for l in textwrap.wrap(cfg.HISTORY, 72)]
    team.coach.full_name, team.coach.short_name = cfg.COACH[0], cfg.COACH[1]
    team.coach.gfx = [1, team.coach.gfx[1]]
    team.coach.bio = [l + ' ' for l in textwrap.wrap(cfg.COACH[2], 72)]

    Database.parse(db.serialize())   # comprobación
    db.save(game + 'BASKET96.DBC')
    faces.save(game + 'CARAS.BIN')
    write_logo(game, faces, cfg, d, team)

    man = bytearray(open(game + 'MANAGER.DAT', 'rb').read())
    name = getattr(cfg, 'SCOREBOARD', None)
    if name:
        nb = name.encode('latin-1')
        assert len(nb) == 12, 'SCOREBOARD debe tener exactamente 12 caracteres'
        pos = man.find(b' BARCELONA  ') + 12 * cfg.TI
        if man[pos:pos + 12] != nb:
            man[pos:pos + 12] = nb
            backup(game + 'MANAGER.DAT')
            open(game + 'MANAGER.DAT', 'wb').write(man)

    for p in new:
        print(f"{p.dorsal:>2} {p.short_name:22s} {POS_TXT[p.position]:9s} {p.height_cm} cm "
              f"ext={p.foreign} val={list(p.attrs[6:10])} orden={p.roster_order}")


if __name__ == '__main__':
    main()
