"""
Descarga el historial de estadísticas que usa valoraciones.py:

- ACB: la página «temporada» de acb.com de cada jugador descargado en datos\\<equipo>\\
  (sus estadísticas de Liga Endesa temporada a temporada) -> datos\\<equipo>\\historial.json
- Euroliga y Eurocup: estadísticas de todos los jugadores de las temporadas 2023-24 a 2026-27
  -> datos\\europa\\historial\\<E|U><año>.json
- NBA: no hace falta; datos\\nba\\jugadores.json (de nba.py) ya trae todas las temporadas.

Uso (desde EDITOR\\plantillas):
    python descargar_historial.py              (todo)
    python descargar_historial.py --solo-europa
    python descargar_historial.py --solo-acb
"""
import json, os, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(HERE, 'datos')
UA = {'User-Agent': 'Mozilla/5.0'}
API = 'https://api-live.euroleague.net'
EURO_SEASONS = (2023, 2024, 2025, 2026)


def get(url, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(2)


def obj_at(u, i):
    d = 0
    for k in range(i, len(u)):
        if u[k] == '{':
            d += 1
        elif u[k] == '}':
            d -= 1
            if d == 0:
                return json.loads(u[i:k + 1].replace('"$undefined"', 'null'))


def acb_seasons(pid):
    """[{season: '2025-2026', totals: {...}}] de la Liga Endesa (una fila por temporada)."""
    u = get(f'https://acb.com/es/liga/jugadores/x-{pid}/temporada').decode('utf-8', 'replace')
    u = u.replace('\\"', '"')
    out = []
    for m in re.finditer(r'"editionYear":"(\d{4}-\d{4})","totals":', u):
        t = obj_at(u, m.end())
        if t and t.get('numGames'):
            out.append(dict(season=m.group(1), totals=t))
    # una misma temporada puede salir repetida (p. ej. en dos tablas de la página)
    seen, uniq = set(), []
    for r in out:
        key = (r['season'], r['totals']['numGames'], r['totals']['timePlayed'])
        if key not in seen:
            seen.add(key); uniq.append(r)
    return uniq


def acb():
    teams = [d for d in sorted(os.listdir(DATOS))
             if os.path.exists(os.path.join(DATOS, d, 'players.json'))]
    for team in teams:
        players = json.load(open(os.path.join(DATOS, team, 'players.json'), encoding='utf-8'))
        with ThreadPoolExecutor(4) as ex:
            res = list(ex.map(lambda p: acb_seasons(p['id']), players))
        hist = {str(p['id']): r for p, r in zip(players, res)}
        json.dump(hist, open(os.path.join(DATOS, team, 'historial.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print(f"  {team:12s} {len(players):2d} jugadores, "
              f"{sum(len(r) for r in res):3d} temporadas ACB")


def europa():
    out = os.path.join(DATOS, 'europa', 'historial')
    os.makedirs(out, exist_ok=True)
    for c in 'EU':
        for y in EURO_SEASONS:
            s = json.loads(get(f'{API}/v3/competitions/{c}/statistics/players/traditional'
                               f'?SeasonMode=Single&SeasonCode={c}{y}&statisticMode=Accumulated'
                               f'&limit=2000').decode('utf-8'))['players']
            json.dump(s, open(os.path.join(out, f'{c}{y}.json'), 'w', encoding='utf-8'),
                      ensure_ascii=False)
            print(f"  {'Euroliga' if c == 'E' else 'Eurocup'} {y}-{(y + 1) % 100:02d}: {len(s)} jugadores")


if __name__ == '__main__':
    if '--solo-acb' not in sys.argv:
        print('== Euroliga / Eurocup'); europa()
    if '--solo-europa' not in sys.argv:
        print('== ACB'); acb()
