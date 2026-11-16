"""
Completa las estadísticas de los jugadores con muy pocos datos esta temporada.

El simulador del mánager usa las estadísticas de la temporada (porcentajes de tiro, rebotes,
asistencias...). Con 1 o 2 partidos, o con 0 de 0 en tiros libres, salen porcentajes extremos
(0 % o 100 %) y el jugador rinde mal o de forma extraña.

A cada jugador con pocos datos se le suman, a sus datos reales, sus medias habituales durante
los partidos que le faltan hasta 10:
    ACB       medias de su carrera en la ACB (datos de acb.com en datos\\<equipo>\\)
    Europa    medias de un suplente de su posición en su competición (Euroliga o Eurocup)
    NBA       medias de la temporada 2025-26 (datos\\nba\\)
Si no hay medias propias, se usan las típicas de su posición.

Uso (desde la carpeta EDITOR\\plantillas):
    python completar_estadisticas.py                 lista y corrige
    python completar_estadisticas.py --solo-listar
    python completar_estadisticas.py --prueba CARPETA
"""
import argparse, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.stdout.reconfigure(encoding='utf-8')
from dbc import Database  # noqa: E402
from europa import SLOTS, typical_stats, position, upper_name, backup, GAME_DEFAULT  # noqa: E402

TARGET_GAMES = 10
MIN_EXTRA = 3          # a los jugadores marcados se les suman al menos 3 partidos de medias
MIN_PRIOR_GAMES = 5    # una carrera de menos partidos no sirve como referencia
# orden de las 15 estadísticas del juego
KEYS = ('twoPointersMade', 'twoPointersAttempted', 'threePointersMade', 'threePointersAttempted',
        'freeThrowsMade', 'freeThrowsAttempted', 'defensiveRebounds', 'offensiveRebounds',
        'assists', 'blocks', 'steals', 'turnovers', 'minutesPlayed', 'gamesPlayed', 'foulsCommited')
ACB_KEYS = ('twoPointersMade', 'twoPointersAttempted', 'threePointersMade',
            'threePointersAttempted', 'freeThrowsMade', 'freeThrowsAttempted',
            'defensiveRebounds', 'offensiveRebounds', 'assists', 'blocks', 'steals', 'turnovers',
            'timePlayed', 'numGames', 'personalFouls')


def problems(c):
    """Motivos por los que las estadísticas de un jugador son poco fiables."""
    t2m, t2a, t3m, t3a, ftm, fta = c[0:6]
    mins, gp = c[12], c[13]
    out = []
    if gp < 3:
        out.append(f'{gp} partidos')
    if gp and mins / gp < 8:
        out.append(f'{mins / gp:.1f} min/p')
    if t2a + t3a < 10:
        out.append(f'{t2a + t3a} tiros')
    if t2a and t2a < 6 and t2m / t2a in (0, 1):
        out.append(f'T2 {t2m}/{t2a}')
    if fta < 3:
        out.append(f'TL {ftm}/{fta}')
    return out


def per_game(vals15):
    """Lista de 15 valores (orden del juego) -> medias por partido (o None)."""
    gp = vals15[13]
    return [v / gp for v in vals15] if gp else None


def acb_priors():
    """Medias de carrera ACB por (equipo, APELLIDO) desde datos\\<equipo>\\players.json."""
    folders = {}
    for f in glob.glob(os.path.join(HERE, 'cfg_*.py')):
        src = open(f, encoding='utf-8').read()
        ti = int(re.search(r'^TI\s*=\s*(\d+)', src, re.M).group(1))
        folders[ti] = re.search(r"^DATOS\s*=\s*'([^']+)'", src, re.M).group(1)
    folders.setdefault(13, 'joventut')       # el Joventut (editado a mano) no tiene cfg
    out = {}
    for ti, name in folders.items():
        path = os.path.join(HERE, 'datos', name, 'players.json')
        if not os.path.exists(path):
            continue
        for p in json.load(open(path, encoding='utf-8')):
            car = p['totals'][2] if len(p['totals']) > 2 else {}
            if car.get('numGames', 0) >= MIN_PRIOR_GAMES:
                vals = [car.get(k, 0) for k in ACB_KEYS]
                vals[12] = vals[12] / 60          # segundos -> minutos
                out[(ti, upper_name(p['last']))] = per_game(vals)
    return out


def euro_context():
    d = os.path.join(HERE, 'datos', 'europa')
    if not os.path.exists(os.path.join(d, 'clubs.json')):
        return None
    clubs = json.load(open(os.path.join(d, 'clubs.json'), encoding='utf-8'))
    comp_of = {x['code']: c for c in 'EU' for x in clubs[c]}
    stats, pos_of = {}, {}
    for c in 'EU':
        for s in json.load(open(os.path.join(d, f'stats_{c}.json'), encoding='utf-8')):
            stats[(c, s['player']['team']['code'], s['player']['code'])] = s
    for code in [v[0] for v in SLOTS.values()]:
        for p in json.load(open(os.path.join(d, code, 'people.json'), encoding='utf-8')):
            if p['type'] == 'J':
                pos_of[p['person']['code']] = position(p['position'], p['person']['height'] or 198)
    return comp_of, stats, pos_of


def nba_priors():
    path = os.path.join(HERE, 'datos', 'nba', 'jugadores.json')
    if not os.path.exists(path):
        return {}
    from nba import season_stats
    out = {}
    for x in json.load(open(path, encoding='utf-8')):
        s = season_stats(x['stats'], '2025-26')
        if s.get('gamesPlayed', 0) >= MIN_PRIOR_GAMES:
            out[upper_name(x['athlete'].get('lastName', ''))] = per_game([s.get(k, 0) for k in KEYS])
    return out


def league_typical(db, teams, pos):
    """Medias de los suplentes (10-20 min) de esa posición en esos equipos del juego."""
    rows = [p.current for ti in teams for p in db.teams[ti].players
            if p.position == pos and p.current[13] >= 3 and 10 <= p.current[12] / p.current[13] <= 20]
    if not rows:
        return None
    pg = [per_game(r) for r in rows]
    return [sorted(v[k] for v in pg)[len(pg) // 2] for k in range(15)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--solo-listar', action='store_true')
    ap.add_argument('--prueba', help='carpeta con una COPIA de los archivos del juego')
    a = ap.parse_args()
    game = (os.path.abspath(a.prueba) + os.sep) if a.prueba else GAME_DEFAULT
    db = Database.load(game + 'BASKET96.DBC')
    acb, nba, eu = acb_priors(), nba_priors(), euro_context()
    euro_typ = {}

    n = 0
    for ti, t in enumerate(db.teams):
        for p in t.players:
            why = problems(p.current)
            if not why:
                continue
            last = p.full_name.split(' ', 1)[-1] if ' ' in p.full_name else p.full_name
            prior, src = None, ''
            if t.kind == 'ACB':
                prior = acb.get((ti, last)) or next((v for (tt, ln), v in acb.items()
                                                     if tt == ti and ln in p.full_name), None)
                src = 'carrera ACB'
                if not prior:
                    prior, src = league_typical(db, range(18), p.position), 'típicas ACB'
            elif t.kind == 'ALLSTAR':
                prior = next((v for ln, v in nba.items() if ln and ln in p.full_name), None)
                src = 'NBA 2025-26'
            elif eu and ti in SLOTS:
                comp = eu[0][SLOTS[ti][0]]
                key = (comp, p.position)
                if key not in euro_typ:
                    typ = typical_stats(eu[1], comp, eu[2], p.position, 1)
                    euro_typ[key] = [typ.get(k, 0) for k in KEYS] if typ else None
                prior, src = euro_typ[key], ('típicas Euroliga' if comp == 'E' else 'típicas Eurocup')
            if not prior:
                prior, src = league_typical(db, range(len(db.teams)), p.position), 'típicas del juego'
            gp = p.current[13]
            missing = max(MIN_EXTRA, TARGET_GAMES - gp)
            if not prior:
                print(f"  (sin cambios) {t.short_name:15s} {p.full_name:28s} {', '.join(why)}")
                continue
            new = [p.current[k] + prior[k] * missing for k in range(15)]
            # tiros que siguen casi sin intentos (p. ej. nunca ha tirado libres en su carrera):
            # se completan con los típicos de su posición
            typ = league_typical(db, range(18) if t.kind == 'ACB' else range(len(db.teams)),
                                 p.position)
            if typ:
                for m, att in ((0, 1), (2, 3), (4, 5)):
                    if att != 3 and new[att] < 3:      # los triples pueden ser 0 (pívots)
                        new[m] += typ[m] * TARGET_GAMES
                        new[att] += typ[att] * TARGET_GAMES
            new = [int(round(v)) for v in new]
            new[13] = gp + missing
            n += 1
            print(f"{t.short_name:15s} {p.full_name:28s} {', '.join(why):32s} +{missing} partidos "
                  f"({src}) -> T2 {new[0]}/{new[1]} T3 {new[2]}/{new[3]} TL {new[4]}/{new[5]}")
            if not a.solo_listar:
                p.current = [min(v, 65535) for v in new] + list(p.current[15:])
    if a.solo_listar or not n:
        print(f"\n{n} jugadores por completar.")
        return
    Database.parse(db.serialize())
    backup(game + 'BASKET96.DBC')
    db.save(game + 'BASKET96.DBC')
    print(f"\n{n} jugadores completados.")


if __name__ == '__main__':
    main()
