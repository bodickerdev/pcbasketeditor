"""
Equipo «ESTRELLAS NBA» (hueco 50) con 21 estrellas actuales de la NBA.

Uso (desde la carpeta EDITOR\\plantillas):
    python nba.py                    descarga los datos y los aplica al juego
    python nba.py --sin-descargar    usa lo ya descargado en datos\\nba\\
    python nba.py --prueba CARPETA   escribe en CARPETA (copia de los archivos del juego)

Datos: API pública de ESPN (site.api.espn.com). La de nba.com no admite descargas
automáticas. Plantillas (equipo, dorsal, altura, peso, nacimiento), estadísticas y fotos.
Jugadores 1-12 = Selección USA y 13-21 = Selección Europea (así los reparte el juego).
Para las valoraciones se usan las estadísticas de 2026-27 si el jugador lleva al menos 5
partidos; si no (lesionados), las de 2025-26.
"""
import argparse, io, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image  # noqa: E402
from dbc import Database, Player  # noqa: E402
from formato100 import per100  # noqa: E402
from dgf import DGF  # noqa: E402
from caras import small_from_image, SMALL_PALETTE  # noqa: E402
from europa import (ratings, latin1, wrap, title, upper_name, fmt, backup, country,  # noqa: E402
                    POS_TXT, GAME_DEFAULT)

DATA = os.path.join(HERE, 'datos', 'nba')
TI = 50
ESPN = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba'
ESPN_STATS = 'https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{}/stats'

# nombre (ESPN), posición en el juego, piel, pelo, color de pelo, barba, apellido en listados
#   piel 0 blanca 1 negra 2 mulata · pelo 0 calvo 1 corto 3 normal · color 0 negro 1 rubio
#   2 castaño · barba 0 nada 1 bigote 2 perilla 3 barba
# El juego forma los equipos del partido Selección USA - Selección Europea por el LUGAR en la
# lista: jugadores 1-12 = USA, 13-21 = Europa (así estaba en 1996). Cada grupo tiene su propio
# orden de plantilla; los 5 primeros de cada grupo son los titulares.
USA = 12
EUROPE_ORDER = [1, 2, 3, 4, 5, 6, 8, 10, 12]
PLAYERS = [
    # ---- Selección USA (12) ----
    ('Stephen Curry',           0, 2, 1, 0, 2, 'Curry'),
    ('Anthony Edwards',         1, 1, 1, 0, 2, 'Edwards'),
    ('Jayson Tatum',            2, 1, 1, 0, 3, 'Tatum'),
    ('Anthony Davis',           3, 1, 1, 0, 3, 'Davis'),
    ('Joel Embiid',             4, 1, 1, 0, 3, 'Embiid'),
    ('Jalen Brunson',           0, 2, 1, 0, 3, 'Brunson'),
    ('Donovan Mitchell',        1, 1, 1, 0, 3, 'Mitchell'),
    ('Devin Booker',            1, 2, 1, 0, 3, 'Booker'),
    ('Kevin Durant',            2, 1, 1, 0, 3, 'Durant'),
    ('LeBron James',            2, 1, 1, 0, 3, 'James'),
    ('Kawhi Leonard',           2, 1, 1, 0, 3, 'Leonard'),
    ('Paolo Banchero',          3, 2, 1, 0, 2, 'Banchero'),
    # ---- Selección Europea (9) ----
    ('Luka Doncic',             0, 0, 3, 2, 3, 'Doncic'),
    ('Bogdan Bogdanovic',       1, 0, 1, 0, 3, 'Bogdanovic'),
    ('Franz Wagner',            2, 0, 3, 2, 0, 'Wagner'),
    ('Giannis Antetokounmpo',   3, 1, 1, 0, 3, 'Antetokounmpo'),
    ('Nikola Jokic',            4, 0, 1, 2, 3, 'Jokic'),
    ('Dennis Schroder',         0, 2, 1, 0, 3, 'Schroder'),
    ('Deni Avdija',             2, 0, 3, 2, 0, 'Avdija'),
    ('Victor Wembanyama',       4, 1, 1, 0, 0, 'Wembanyama'),
    ('Alperen Sengun',          4, 0, 1, 0, 3, 'Sengun'),
]


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def plain(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn').lower()


def download():
    os.makedirs(os.path.join(DATA, 'img'), exist_ok=True)
    teams = json.loads(get(ESPN + '/teams'))['sports'][0]['leagues'][0]['teams']
    found = {}
    for t in teams:
        t = t['team']
        r = json.loads(get(f"{ESPN}/teams/{t['id']}/roster"))
        for a in r['athletes']:
            found[plain(a['fullName'])] = dict(athlete=a, team=t['displayName'])
    out = []
    for name, *_ in PLAYERS:
        x = found.get(plain(name))
        if not x:
            sys.exit(f"No encuentro a {name} en ninguna plantilla de la NBA.")
        a = x['athlete']
        x['stats'] = json.loads(get(ESPN_STATS.format(a['id'])))
        href = (a.get('headshot') or {}).get('href')
        if href:
            open(os.path.join(DATA, 'img', a['id'] + '.png'), 'wb').write(get(href))
        out.append(x)
        print(f"  {name:26s} {x['team']}")
    json.dump(out, open(os.path.join(DATA, 'jugadores.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)


def season_stats(st, season):
    """Totales de una temporada (ESPN) con las claves de las estadísticas de la Euroliga."""
    cats = {c['name']: c for c in st['categories']}

    def row(cat):
        c = cats.get(cat)
        if not c:
            return None
        rows = [s for s in c['statistics'] if s['season']['displayName'] == season]
        if not rows:
            return None
        # si cambió de equipo a mitad de temporada hay varias filas: se suman
        vals = {}
        for r in rows:
            for k, v in zip(c['names'], r['stats']):
                vals.setdefault(k, []).append(v)
        return vals

    av, to = row('averages'), row('totals')
    if not av or not to:
        return {}

    def num(v):
        try:
            return float(str(v).replace(',', ''))
        except ValueError:
            return 0.0

    def pair(k):
        m = a = 0
        for v in to[k]:
            x, y = v.split('-')
            m += num(x); a += num(y)
        return m, a

    gp = sum(num(v) for v in av['gamesPlayed'])
    gs = sum(num(v) for v in av['gamesStarted'])
    mins = sum(num(g) * num(m) for g, m in zip(av['gamesPlayed'], av['avgMinutes']))
    fgm, fga = pair('fieldGoalsMade-fieldGoalsAttempted')
    tpm, tpa = pair('threePointFieldGoalsMade-threePointFieldGoalsAttempted')
    ftm, fta = pair('freeThrowsMade-freeThrowsAttempted')
    tot = {k: sum(num(v) for v in to[k]) for k in ('offensiveRebounds', 'defensiveRebounds',
                                                    'totalRebounds', 'assists', 'blocks',
                                                    'steals', 'fouls', 'turnovers', 'points')}
    s = dict(gamesPlayed=gp, gamesStarted=gs, minutesPlayed=mins, pointsScored=tot['points'],
             twoPointersMade=fgm - tpm, twoPointersAttempted=fga - tpa,
             threePointersMade=tpm, threePointersAttempted=tpa,
             freeThrowsMade=ftm, freeThrowsAttempted=fta,
             offensiveRebounds=tot['offensiveRebounds'], defensiveRebounds=tot['defensiveRebounds'],
             totalRebounds=tot['totalRebounds'], assists=tot['assists'], blocks=tot['blocks'],
             steals=tot['steals'], turnovers=tot['turnovers'], foulsCommited=tot['fouls'])
    # valoración tipo PIR
    s['pir'] = (s['pointsScored'] + s['totalRebounds'] + s['assists'] + s['steals'] + s['blocks']
                - (fga - fgm) - (fta - ftm) - s['turnovers'])
    return s


def stats30(s):
    v = [s.get(k, 0) for k in ('twoPointersMade', 'twoPointersAttempted', 'threePointersMade',
                               'threePointersAttempted', 'freeThrowsMade', 'freeThrowsAttempted',
                               'defensiveRebounds', 'offensiveRebounds', 'assists', 'blocks',
                               'steals', 'turnovers', 'minutesPlayed', 'gamesPlayed',
                               'foulsCommited')]
    return [min(int(round(x)), 65535) for x in v] + [0] * 15


def head_crop(path):
    """Fotos de ESPN (600x436, fondo transparente): cuadrado de la cabeza sobre negro."""
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    a = im.split()[3]
    top = (a.getbbox() or (0, 0, w, h))[1]
    side = int(h * 0.62)
    xs = []
    for y in range(top + int(side * 0.15), top + int(side * 0.6), 6):
        row = [x for x in range(0, w, 3) if a.getpixel((x, y)) > 128]
        if row:
            xs.append((row[0] + row[-1]) / 2)
    cx = sorted(xs)[len(xs) // 2] if xs else w / 2
    x0, y0 = int(cx - side / 2), max(0, top - int(side * 0.05))
    im = im.crop((x0, y0, x0 + side, y0 + side))
    bg = Image.new('RGBA', im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    return bg.convert('RGB')


def bio(first, last, pos, h, team, birth, place, s, season):
    d = f"{int(birth[8:10])}/{int(birth[5:7])}/{birth[:4]}" if birth else '?'
    txt = (f"∙ {first} {title(last)}, {POS_TXT[pos]} de {fmt(h / 100, 2)} m de los {team}, "
           f"nació en {place} el {d}. ")
    gp = int(s.get('gamesPlayed', 0))
    if gp:
        txt += (f"En la temporada {season} de la NBA promedió {fmt(s['pointsScored'] / gp)} "
                f"puntos, {fmt(s['totalRebounds'] / gp)} rebotes y {fmt(s['assists'] / gp)} "
                f"asistencias en {fmt(s['minutesPlayed'] / gp)} minutos ({gp} partidos).")
    return wrap(latin1(txt))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sin-descargar', action='store_true')
    ap.add_argument('--prueba', help='carpeta con una COPIA de los archivos del juego')
    a = ap.parse_args()
    game = (os.path.abspath(a.prueba) + os.sep) if a.prueba else GAME_DEFAULT
    if not a.sin_descargar:
        print('Descargando de ESPN...')
        download()
    data = json.load(open(os.path.join(DATA, 'jugadores.json'), encoding='utf-8'))

    db = Database.load(game + 'BASKET96.DBC')
    orig_db = Database.load(game + 'BASKET96.DBC.BAK') if os.path.exists(game + 'BASKET96.DBC.BAK') else db
    team = db.teams[TI]
    if team.kind != 'ALLSTAR' or len(team.players) != len(PLAYERS):
        sys.exit("El equipo 50 no es el All-Star de 21 jugadores.")
    dg = DGF(game + 'BASKET96.DGF')
    tmpl = {}
    for t in orig_db.teams:
        for p in t.players:
            tmpl.setdefault(p.position, bytes(p.attrs[11:19]))

    new = []
    for i, ((name, pos, skin, hair, hcol, beard, surname), x) in enumerate(zip(PLAYERS, data)):
        at_ = x['athlete']
        cur = season_stats(x['stats'], '2026-27')
        prev = season_stats(x['stats'], '2025-26')
        for_rating, season_txt = (cur, '2026-27') if cur.get('gamesPlayed', 0) >= 5 else (prev, '2025-26')
        h = round(float(at_.get('height') or 78) * 2.54)
        kg = round(float(at_.get('weight') or 220) * 0.4536)
        r = ratings(for_rating, pos, h, 'E')
        bp = at_.get('birthPlace') or {}
        ctry = country({'USA': 'United States of America'}.get(bp.get('country'), bp.get('country') or ''))
        place = f"{bp['city']} ({ctry})" if bp.get('city') else ctry
        birth = (at_.get('dateOfBirth') or '')[:10]
        first = latin1(at_.get('firstName') or name.split()[0])
        last = latin1(upper_name(at_.get('lastName') or name.split()[-1]))
        nba_team = latin1(x['team'])
        attrs = bytearray(21)
        attrs[0] = 0 if bp.get('country') in ('USA', None) else 1
        attrs[1], attrs[2], attrs[3], attrs[5] = skin, hair, hcol, beard
        attrs[6:10] = bytes(r)
        # orden dentro de cada selección. Europa usa los números de 1996 (1-6, 8, 10, 12):
        # el juego mete en los huecos 7, 9 y 11 a 3 jugadores de los equipos europeos.
        attrs[10] = (i + 1) if i < USA else EUROPE_ORDER[i - USA]
        attrs[11:19] = tmpl[pos]
        pir = for_rating.get('pir', 0) / max(for_rating.get('gamesPlayed', 1), 1)
        old = team.players[i]
        jersey = str(at_.get('jersey') or '0')
        new.append(Player(
            full_name=f"{first} {last}", short_name=f"{first} {last}"[:24], surname=surname[:15],
            gfx=[1, old.gfx[1]], bio=bio(first, last, pos, h, nba_team, birth, place, for_rating, season_txt),
            dorsal=int(jersey) if jersey.isdigit() else 0, position=pos, height_raw=h - 100,
            weight=kg, birthplace=latin1(place),
            birthdate=f"{birth[8:10]}-{birth[5:7]}-{birth[2:4]}" if birth else '-',
            value=int(min(900, 300 + pir * 12)), prev_club='-', attrs=attrs,
            team=upper_name(nba_team)[:30], current=per100(stats30(cur), pos), seasons=[]))
        photo = os.path.join(DATA, 'img', at_['id'] + '.png')
        g = old.gfx[1]
        if os.path.exists(photo) and g > 1 and dg.header(g)[:3] == (24, 24, 4):
            dg.encode(g, small_from_image(head_crop(photo), 1.15, 1.15))
            dg.d[g + 2:g + 50] = bytes(v for rgb in SMALL_PALETTE for v in rgb)
        print(f"{new[-1].dorsal:>3} {new[-1].full_name:28s} {POS_TXT[pos]:9s} {h} cm {kg} kg "
              f"{nba_team:24s} val={r} ({season_txt}, {int(for_rating.get('gamesPlayed', 0))} pj)")

    # El mánager (BASKET4.DAT) solo admite fichas mínimas en el equipo de estrellas, como en
    # 1996: con biografía, lugar o fecha de nacimiento se desborda la memoria y el nombre del
    # 7.º europeo sale con basura («OT», «ERS»). Comprobado en el juego.
    for p in new:
        p.bio, p.birthplace, p.birthdate, p.prev_club = ['  ∙'], '-', '-', '-'
    team.players = new
    team.club_name = 'Selección de estrellas de la NBA 2026-27'
    team.address = '-'
    team.arena = '-'
    team.capacity = 0
    team.president = 'Adam Silver (comisionado de la NBA)'
    team.sponsor = 'NBA'
    team.tag = 'ESTRELLAS NBA'
    team.history = ['  ∙']        # como en 1996 (ver arriba)

    Database.parse(db.serialize())   # comprobación
    for f in ('BASKET96.DBC', 'BASKET96.DGF'):
        backup(game + f)
    db.save(game + 'BASKET96.DBC')
    dg.save(game + 'BASKET96.DGF')
    print('\nHecho.')
    print('Recuerda: ejecuta  python valoraciones.py  para recalcular las valoraciones con el '
          'historial (este script usa una fórmula más simple).')


if __name__ == '__main__':
    main()
