"""
Ajuste fino de las 4 valoraciones de todos los jugadores (ACB, Europa y All-Star NBA).

Cómo se calcula
---------------
1. Se reúnen las temporadas de cada jugador:
   - ACB: todas sus temporadas de Liga Endesa (datos\\<equipo>\\historial.json).
   - Euroliga y Eurocup 2023-24 a 2026-27 (datos\\europa\\historial\\), también para los de
     equipos ACB que juegan en Europa.
   - NBA: 2023-24 a 2026-27 (datos\\nba\\jugadores.json, de ESPN).
2. Cada temporada pesa según sus minutos y lo reciente que es: la actual y la pasada mandan;
   las anteriores son el historial y pesan poco. Pocos minutos en total = el jugador se acerca
   a un nivel de suplente.
3. Edad: las temporadas antiguas se corrigen con una curva de edad (un joven de 21 años ha
   mejorado desde hace dos temporadas; uno de 35 ha bajado).
4. Nivel de la liga: Euroliga 1,00; ACB 0,95; Eurocup 0,85; NBA 1,05 (sobre la PIR por minuto).
5. Calidad general = PIR por 40 minutos (corregida) + peso en el equipo (minutos por partido).
   Se pasa a la escala de 1996: la ACB queda con media 74 y desviación ~5,5, como en el juego
   original; los equipos europeos y las estrellas NBA quedan donde les lleven sus números.
6. Cada valoración = calidad general + su especialidad, con el reparto que tenían en 1996:
   - r1 manejo/pase: asistencias, pérdidas, volumen y acierto de triple, tiros libres, altura.
     Es la que más cambia con la posición (los bases ~+6, los pívots ~−5).
   - r2 tiro/ataque: puntos por minuto y eficiencia de tiro (TS%). En 1996 era ~5 más baja.
   - r3 rebote/interior y r4 defensa/físico: en 1996 dependían casi solo de la calidad general,
     así que aquí se les suma una especialidad pequeña (rebotes; robos, tapones y altura).

Uso (desde EDITOR\\plantillas; antes, python descargar_historial.py):
    python valoraciones.py --solo-listar        muestra antes -> después sin tocar nada
    python valoraciones.py                      aplica al juego y actualiza los cfg_*.py
    python valoraciones.py --incluir-joventut   también el Joventut (por defecto no se toca)
    python valoraciones.py --prueba CARPETA     aplica sobre una copia del juego
Deja un informe en valoraciones_informe.txt.
"""
import argparse, glob, importlib.util, json, math, os, re, shutil, sys, unicodedata
from statistics import mean, pstdev

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from dbc import Database  # noqa: E402
import europa  # noqa: E402
import nba  # noqa: E402

NOW = 2026                       # temporada 2026-27
DATOS = os.path.join(HERE, 'datos')
GAME_DEFAULT = os.path.normpath(os.path.join(HERE, '..', '..')) + os.sep
JOVENTUT = 13

LEAGUE = {'EL': 1.00, 'ACB': 0.95, 'EC': 0.90, 'NBA': 0.70}
RECENCY = {0: 1.0, 1: 0.8, 2: 0.45, 3: 0.25}          # más antiguas: 0.12
PRIOR_PIR40, PRIOR_MIN = 9.0, 250                      # nivel de suplente y su peso (minutos)
TARGET_MEAN, TARGET_SD = 74.0, 5.5                     # escala de 1996 (media ACB)
OFFSET = (1.0, -5.0, 0.0, 2.5)                         # r1..r4 respecto a la calidad (1996)
POS_PIR_CORR = 0.75                                    # corrección de la PIR por posición
MPG_WEIGHT = 0.35                                      # peso de los minutos por partido


def growth(age):
    """Cambio de la PIR/40 entre los `age` y los `age`+1 años."""
    table = {20: 2.0, 21: 1.6, 22: 1.2, 23: 0.8, 24: 0.5, 25: 0.25, 26: 0, 27: 0, 28: 0, 29: 0,
             30: -0.3, 31: -0.6, 32: -0.9, 33: -1.2, 34: -1.6}
    return table.get(age, 2.0 if age < 20 else -2.0)


def norm(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', str(s).upper())
                if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^A-Z ]', ' ', s.replace('-', ' ')).split()


# ------------------------------------------------------------------ muestras (temporadas)
def from_acb(t, year):
    return dict(year=year, lg='ACB', gp=t['numGames'], min=t['timePlayed'] / 60, pts=t['points'],
                p2m=t['twoPointersMade'], p2a=t['twoPointersAttempted'],
                p3m=t['threePointersMade'], p3a=t['threePointersAttempted'],
                ftm=t['freeThrowsMade'], fta=t['freeThrowsAttempted'],
                orb=t['offensiveRebounds'], drb=t['defensiveRebounds'], ast=t['assists'],
                stl=t['steals'], blk=t['blocks'], tov=t['turnovers'], pf=t['personalFouls'])


def from_api(s, year, lg):
    return dict(year=year, lg=lg, gp=s.get('gamesPlayed', 0), min=s.get('minutesPlayed', 0),
                pts=s.get('pointsScored', 0), p2m=s.get('twoPointersMade', 0),
                p2a=s.get('twoPointersAttempted', 0), p3m=s.get('threePointersMade', 0),
                p3a=s.get('threePointersAttempted', 0), ftm=s.get('freeThrowsMade', 0),
                fta=s.get('freeThrowsAttempted', 0), orb=s.get('offensiveRebounds', 0),
                drb=s.get('defensiveRebounds', 0), ast=s.get('assists', 0), stl=s.get('steals', 0),
                blk=s.get('blocks', 0), tov=s.get('turnovers', 0), pf=s.get('foulsCommited', 0))


def pir(s):
    return (s['pts'] + s['orb'] + s['drb'] + s['ast'] + s['stl'] + s['blk'] - s['tov']
            - (s['p2a'] - s['p2m']) - (s['p3a'] - s['p3m']) - (s['fta'] - s['ftm']))


class EuroIndex:
    """Estadísticas de Euroliga/Eurocup por código de jugador y por nombre."""

    def __init__(self):
        self.by_code, self.by_name = {}, {}
        for f in glob.glob(os.path.join(DATOS, 'europa', 'historial', '*.json')):
            tag = os.path.basename(f)[:-5]
            lg, year = ('EL' if tag[0] == 'E' else 'EC'), int(tag[1:])
            for s in json.load(open(f, encoding='utf-8')):
                if not s.get('gamesPlayed'):
                    continue
                pl = s['player']
                smp = from_api(s, year, lg)
                smp['age'] = pl.get('age')
                self.by_code.setdefault(pl['code'], []).append(smp)
                if ',' in pl['name']:
                    last, first = pl['name'].split(',', 1)
                    key = (' '.join(norm(last)), ' '.join(norm(first)))
                    self.by_name.setdefault(key, {}).setdefault(pl['code'], []).append(smp)

    def find(self, first, last, age_now):
        """Muestras de un jugador ACB en Europa (por nombre; la edad confirma)."""
        L, F = ' '.join(norm(last)), ' '.join(norm(first))
        cands = [(k, v) for k, v in self.by_name.items()
                 if k[0] == L and (k[1] == F or k[1][:1] == F[:1] and len(k[1]) > 0)]
        out = []
        for _, codes in cands:
            for code, smps in codes.items():
                ok = [s for s in smps if s['age'] is None or age_now is None
                      or abs(s['age'] + (NOW - s['year']) - age_now) <= 1]
                if ok and len(ok) == len(smps):
                    out += self.by_code[code]
        return out


# ------------------------------------------------------------------ modelo
def rating_inputs(samples, age_now, h, pos):
    """Calidad bruta y estadísticas por 40 minutos ponderadas de un jugador."""
    acc = dict(w=0.0, pir=0.0, wg=0.0, mpg=0.0)
    keys = ('pts', 'p2m', 'p2a', 'p3m', 'p3a', 'ftm', 'fta', 'orb', 'drb', 'ast', 'stl', 'blk',
            'tov', 'pf')
    tot = dict.fromkeys(keys, 0.0)
    for s in samples:
        if s['min'] < 1 or s['gp'] < 1:
            continue
        ago = NOW - s['year']
        rec = RECENCY.get(ago, 0.12)
        w = s['min'] * rec
        p40 = pir(s) * 40 / s['min'] * LEAGUE[s['lg']]
        if age_now:
            p40 += sum(growth(a) for a in range(age_now - ago, age_now))
        acc['w'] += w
        acc['pir'] += w * p40
        # el papel en el equipo: la temporada actual cuenta el doble
        wg = s['gp'] * rec * (2 if ago == 0 else 1)
        acc['wg'] += wg
        acc['mpg'] += wg * min(s['min'] / s['gp'], 34)
        for k in keys:
            tot[k] += s[k] * rec
    wmin = acc['w']
    pir40 = (acc['pir'] + PRIOR_PIR40 * PRIOR_MIN) / (wmin + PRIOR_MIN)
    mpg = (acc['mpg'] + 10 * 5) / (acc['wg'] + 5)
    raw = None                      # se calcula en compute() (corrige la PIR por posición)
    m40 = sum(s['min'] * RECENCY.get(NOW - s['year'], 0.12) for s in samples if s['min'] >= 1)
    k = 40 / (m40 + 200)            # por 40 min, con 200 min "medios" de colchón
    fga = tot['p2a'] + tot['p3a']
    x = dict(raw=raw, pir40=pir40, mpg=mpg, wmin=wmin, h=h, pos=pos,
             ast=tot['ast'] * k, tov=tot['tov'] * k, p3a=tot['p3a'] * k, pts=tot['pts'] * k,
             reb=(tot['orb'] + tot['drb']) * k, orb=tot['orb'] * k, stl=tot['stl'] * k,
             blk=tot['blk'] * k, pf=tot['pf'] * k,
             p3=(tot['p3m'] + 0.34 * 15) / (tot['p3a'] + 15),
             ft=(tot['ftm'] + 0.74 * 20) / (tot['fta'] + 20),
             ts=(tot['pts'] + 0.55 * 2 * 60) / (2 * (fga + 0.44 * tot['fta']) + 2 * 60))
    # a los que casi no tienen datos, las tasas de su posición
    for key, by_pos in POS_TYPICAL.items():
        share = min(m40 / 300, 1)
        x[key] = share * x[key] + (1 - share) * by_pos[pos]
    return x


# tasas típicas por 40 minutos según la posición (base ... pívot), para quien no tiene datos
POS_TYPICAL = dict(ast=[6.5, 3.8, 2.6, 2.0, 1.6], tov=[3.0, 2.3, 2.0, 2.0, 2.2],
                   p3a=[6.0, 6.5, 5.5, 4.0, 1.2], pts=[14, 16, 15, 15, 15],
                   reb=[4.0, 5.0, 6.5, 8.5, 10.0], orb=[0.6, 0.9, 1.4, 2.3, 3.2],
                   stl=[1.6, 1.4, 1.3, 1.1, 1.0], blk=[0.1, 0.2, 0.4, 0.7, 1.3],
                   pf=[3.6, 3.6, 3.8, 4.2, 4.8])


def compute(players):
    """players: lista de dicts con 'x' (rating_inputs). Añade 'new' = [r1, r2, r3, r4]."""
    # La PIR favorece a los pívots (rebotes, tapones): se resta el 75 % de la diferencia entre la
    # media de su posición y la media general (solo jugadores con minutos de verdad).
    real = [p['x'] for p in players if p['ti'] < 50 and p['x']['wmin'] > 300]
    allm = mean(x['pir40'] for x in real)
    posm = [mean(x['pir40'] for x in real if x['pos'] == k) for k in range(5)]
    for p in players:
        x = p['x']
        x['pir40_pos'] = x['pir40'] - POS_PIR_CORR * (posm[x['pos']] - allm)
        x['raw'] = x['pir40_pos'] + MPG_WEIGHT * x['mpg']
    acb = [p['x']['raw'] for p in players if p['ti'] < 18]
    mu, sd = mean(acb), pstdev(acb)
    feats = ('ast', 'tov', 'p3a', 'p3', 'ft', 'pts', 'ts', 'reb', 'orb', 'stl', 'blk', 'pf', 'h')
    base = [p['x'] for p in players if p['ti'] < 50]
    st = {f: (mean(x[f] for x in base), pstdev(x[f] for x in base) or 1) for f in feats}
    for p in players:
        x = p['x']
        z = {f: (x[f] - st[f][0]) / st[f][1] for f in feats}
        q = TARGET_MEAN + TARGET_SD * (x['raw'] - mu) / sd
        if q > 86:                                   # comprime la parte alta (estrellas NBA)
            q = 86 + 8 * math.tanh((q - 86) / 8)
        d1 = 2.6 * z['ast'] - 0.8 * z['tov'] + 1.3 * z['p3a'] + 0.8 * z['p3'] + 0.7 * z['ft'] - 1.4 * z['h']
        d2 = 2.2 * z['pts'] + 1.8 * z['ts'] + 0.5 * z['ft']
        d3 = 1.6 * z['reb'] + 0.5 * z['orb'] + 0.4 * z['h']
        d4 = 1.0 * z['stl'] + 1.0 * z['blk'] + 0.5 * z['h'] - 0.4 * z['pf']
        p['q'] = q
        p['new'] = [int(max(40, min(99, round(q + o + d)))) for o, d in zip(OFFSET, (d1, d2, d3, d4))]


# ------------------------------------------------------------------ lectura de los equipos
def load_cfg(path):
    spec = importlib.util.spec_from_file_location('cfg', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def acb_players(db, euro):
    import equipo
    out = []
    cfgs = {load_cfg(f).TI: f for f in glob.glob(os.path.join(HERE, 'cfg_*.py'))}
    for ti in range(18):
        team = db.teams[ti]
        folder = load_cfg(cfgs[ti]).DATOS if ti in cfgs else 'joventut'
        d = os.path.join(DATOS, folder)
        js = {str(p['id']): p for p in json.load(open(os.path.join(d, 'players.json'), encoding='utf-8'))}
        hist = json.load(open(os.path.join(d, 'historial.json'), encoding='utf-8'))
        cfg = load_cfg(cfgs[ti]) if ti in cfgs else None
        P = equipo.load_players(cfg)[1] if cfg else {}
        for i, pl in enumerate(team.players):
            jp, key = None, None
            if cfg and i < len(cfg.ORDER):
                cand = P.get(cfg.ORDER[i])
                if cand and norm(pl.full_name)[-1:] == norm(cand['last'])[-1:]:
                    jp, key = cand, cfg.ORDER[i]
            if jp is None:                             # por nombre (Joventut o editados a mano)
                words = set(norm(pl.full_name))
                m = [q for q in js.values() if set(norm(q['last'])) <= words
                     and (set(norm(q['first'])) & words or set(norm(q.get('nick', ''))) & words)]
                jp = m[0] if len(m) == 1 else None
            samples = []
            age = None
            if jp:
                age = jp.get('age')
                for r in hist.get(str(jp['id']), []):
                    samples.append(from_acb(r['totals'], int(r['season'][:4])))
                samples += euro.find(jp['first'], jp['last'], age)
            out.append(dict(ti=ti, i=i, pl=pl, cfg=cfgs.get(ti), key=key, age=age,
                            found=jp is not None, samples=samples))
    return out


def euro_players(db, euro):
    out = []
    for ti, (code, *_rest) in europa.SLOTS.items():
        people = json.load(open(os.path.join(DATOS, 'europa', code, 'people.json'), encoding='utf-8'))
        by_name = {}
        for p in people:
            if p['type'] == 'J':
                first, last = europa.split_name(p['person']['name'])
                by_name[' '.join(norm(f"{first} {last}"))] = p['person']
        for i, pl in enumerate(db.teams[ti].players):
            pr = by_name.get(' '.join(norm(pl.full_name)))
            age = None
            if pr and pr.get('birthDate'):
                y, m = int(pr['birthDate'][:4]), int(pr['birthDate'][5:7])
                age = 2026 - y - (1 if m > 11 else 0)
            samples = list(euro.by_code.get(pr['code'], [])) if pr else []
            out.append(dict(ti=ti, i=i, pl=pl, cfg=None, key=None, age=age, found=pr is not None,
                            samples=samples))
    return out


def nba_players(db):
    data = json.load(open(os.path.join(DATOS, 'nba', 'jugadores.json'), encoding='utf-8'))
    by_name = {' '.join(norm(x['athlete']['fullName'])): x for x in data}
    out = []
    for i, pl in enumerate(db.teams[50].players):
        x = by_name.get(' '.join(norm(pl.full_name)))
        if x is None:
            out.append(dict(ti=50, i=i, pl=pl, cfg=None, key=None, age=None, found=False, samples=[]))
            continue
        samples = []
        for y in range(NOW - 3, NOW + 1):
            s = nba.season_stats(x['stats'], f"{y}-{(y + 1) % 100:02d}")
            if s.get('gamesPlayed'):
                samples.append(from_api(s, y, 'NBA'))
        out.append(dict(ti=50, i=i, pl=pl, cfg=None, key=None, age=x['athlete'].get('age'),
                        found=True, samples=samples))
    return out


# ------------------------------------------------------------------ escritura
def update_cfg(path, changes):
    """Cambia r1..r4 de las entradas de D: {apellido: [r1, r2, r3, r4]}."""
    txt = open(path, encoding='utf-8', newline='').read()     # conserva los finales de línea
    for key, r in changes.items():
        q = '"' if "'" in key else "'"                          # N'Guessan va entre comillas dobles
        pat = re.compile(r"(\n\s*" + q + re.escape(key) + q + r":\s*\()\s*\d+,\s*\d+,\s*\d+,\s*\d+,")
        new, n = pat.subn(lambda m: m.group(1) + ', '.join(f'{v:2d}' for v in r) + ',', txt, count=1)
        if n:
            txt = new
        else:
            print(f"  ! no encuentro '{key}' en {os.path.basename(path)}")
    open(path, 'w', encoding='utf-8', newline='').write(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--solo-listar', action='store_true')
    ap.add_argument('--incluir-joventut', action='store_true')
    ap.add_argument('--prueba')
    a = ap.parse_args()
    game = os.path.abspath(a.prueba) + os.sep if a.prueba else GAME_DEFAULT
    path = os.path.join(game, 'BASKET96.DBC')
    db = Database.load(path)

    if not os.path.isdir(os.path.join(DATOS, 'europa', 'historial')):
        sys.exit('Falta el historial: ejecuta antes  python descargar_historial.py')
    euro = EuroIndex()
    players = acb_players(db, euro) + euro_players(db, euro) + nba_players(db)
    for p in players:
        p['x'] = rating_inputs(p['samples'], p['age'], pl_h(p), p['pl'].position)
    compute(players)

    rep = []
    for ti in sorted({p['ti'] for p in players}):
        team = db.teams[ti]
        ps = [p for p in players if p['ti'] == ti]
        top = lambda key: mean(sum(key(p)) / 4 for p in sorted(ps, key=lambda p: p['pl'].roster_order)[:8])
        skip = ti == JOVENTUT and not a.incluir_joventut
        rep.append(f"\n== {ti:2d} {team.short_name}   media 8 primeros: "
                   f"{top(lambda p: list(p['pl'].attrs[6:10])):.1f} -> {top(lambda p: p['new']):.1f}"
                   + ('   (NO SE APLICA: Joventut editado a mano)' if skip else ''))
        for p in sorted(ps, key=lambda p: p['pl'].roster_order):
            x, pl = p['x'], p['pl']
            seas = ' '.join(sorted({f"{s['lg']}{s['year'] % 100:02d}" for s in p['samples']
                                    if NOW - s['year'] <= 2}, reverse=True))
            flag = '' if p['found'] else '  [sin datos: nivel de suplente]'
            rep.append(f"  {pl.roster_order:2d} {pl.short_name[:22]:22s} {['B','E','A','AP','P'][pl.position]:2s} "
                       f"{p['age'] or '?':>2} años  {list(pl.attrs[6:10])} -> {p['new']}  "
                       f"PIR/40 {x['pir40']:4.1f}  min {x['mpg']:4.1f}  [{seas}]{flag}")
    report = '\n'.join(rep)
    print(report)
    open(os.path.join(HERE, 'valoraciones_informe.txt'), 'w', encoding='utf-8').write(report.lstrip() + '\n')

    groups = [('ACB', range(18)), ('Euroliga', [t for t, s in europa.SLOTS.items() if comp_of(s[0]) == 'E']),
              ('Eurocup', [t for t, s in europa.SLOTS.items() if comp_of(s[0]) == 'U']), ('NBA', [50])]
    print('\n== Medias por grupo (r1 r2 r3 r4)')
    for name, rng in groups:
        q = [p for p in players if p['ti'] in rng]
        print(f"  {name:9s} antes {[round(mean(p['pl'].attrs[6 + k] for p in q), 1) for k in range(4)]}"
              f"  después {[round(mean(p['new'][k] for p in q), 1) for k in range(4)]}"
              f"  desviación {[round(pstdev(p['new'][k] for p in q), 1) for k in range(4)]}")
    print('  (1996: ACB [74.7, 68.1, 74.0, 76.2] desv. [9.2, 8.6, 5.8, 6.3]; '
          'Europa [75.6, 71.7, 76.5, 77.3]; NBA [88.9, 85.6, 89.1, 91.8])')
    if a.solo_listar:
        print('\n(--solo-listar: no se ha cambiado nada)')
        return

    cfg_changes = {}
    for p in players:
        if p['ti'] == JOVENTUT and not a.incluir_joventut:
            continue
        p['pl'].attrs[6:10] = bytes(p['new'])
        if p['cfg'] and p['key']:
            cfg_changes.setdefault(p['cfg'], {})[p['key']] = p['new']
    europa.backup(path)
    prev = path + '.antes_valoraciones'
    if not os.path.exists(prev):                 # para poder volver a las valoraciones de antes
        shutil.copy2(path, prev)
    db.save(path, backup=False)
    if not a.prueba:
        for f, ch in cfg_changes.items():
            update_cfg(f, ch)
    print(f"\nGuardado en {path}" + ('' if a.prueba else ' y actualizados los cfg_*.py')
          + '. Informe: valoraciones_informe.txt')


def pl_h(p):
    return p['pl'].height_cm


_COMP = None


def comp_of(code):
    global _COMP
    if _COMP is None:
        _COMP = {x['code']: x['comp'] for x in json.load(open(os.path.join(DATOS, 'europa', 'elegidos.json'),
                                                               encoding='utf-8'))}
    return _COMP.get(code)


if __name__ == '__main__':
    main()
