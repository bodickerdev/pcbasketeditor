"""
Descarga de la API oficial de la Euroliga (api-live.euroleague.net) los equipos europeos
de la temporada 2026-27: clubes, clasificación, plantillas, estadísticas, escudos y fotos.

Uso (desde la carpeta EDITOR\\plantillas):
    python descargar_europa.py            descarga todo en datos\\europa\\
    python descargar_europa.py --sin-fotos

Elige los 32 equipos así: los de la Euroliga que no son españoles (los españoles ya están en
la sección ACB del juego) y, hasta completar 32, los mejores de la Eurocup en su clasificación.
"""
import json, os, re, sys, time, urllib.request
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'datos', 'europa')
API = 'https://api-live.euroleague.net'
SEASON = 2026
UA = {'User-Agent': 'Mozilla/5.0'}


def get(url, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(2)


def jget(path):
    return json.loads(get(API + path).decode('utf-8'))


def save_photo(data, path):
    """Las fotos oficiales son PNG de 750x1000 (~460 KB). Para el juego basta con la mitad:
    se guardan a 375x500 en WebP con transparencia (~26 KB)."""
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert('RGBA')
    im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    im.save(path, 'WEBP', quality=85)


def save(name, obj):
    json.dump(obj, open(os.path.join(OUT, name), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def standings(comp):
    """Clasificación (todas las fases de grupos juntas): código -> (victorias, derrotas, dif.)."""
    x = ET.fromstring(get(f'{API}/v1/standings?seasonCode={comp}{SEASON}'))
    out = {}
    for t in x.iter('team'):
        out[t.findtext('code')] = (int(t.findtext('wins')), int(t.findtext('losses')),
                                   int(t.findtext('difference')))
    return out


def main():
    fotos = '--sin-fotos' not in sys.argv
    os.makedirs(OUT, exist_ok=True)
    clubs = {c: jget(f'/v2/competitions/{c}/seasons/{c}{SEASON}/clubs')['data'] for c in 'EU'}
    st = {c: standings(c) for c in 'EU'}
    save('clubs.json', clubs)
    save('standings.json', st)

    def rank(c, x):
        w, l, d = st[c].get(x['code'], (0, 0, 0))
        return (-(w / max(w + l, 1)), -d)

    el = sorted([x for x in clubs['E'] if x['country']['code'] != 'ESP'], key=lambda x: rank('E', x))
    ec = sorted([x for x in clubs['U'] if x['country']['code'] != 'ESP'], key=lambda x: rank('U', x))
    chosen = [('E', x) for x in el] + [('U', x) for x in ec][:32 - len(el)]
    save('elegidos.json', [{'comp': c, 'code': x['code'], 'name': x['name']} for c, x in chosen])

    for c in 'EU':
        s = jget(f'/v3/competitions/{c}/statistics/players/traditional?SeasonMode=Single'
                 f'&SeasonCode={c}{SEASON}&statisticMode=Accumulated&limit=2000')
        save(f'stats_{c}.json', s['players'])

    for c, x in chosen:
        code = x['code']
        d = os.path.join(OUT, code)
        os.makedirs(os.path.join(d, 'img'), exist_ok=True)
        people = jget(f'/v2/competitions/{c}/seasons/{c}{SEASON}/clubs/{code}/people')
        save(os.path.join(code, 'people.json'), people)
        crest = (x.get('images') or {}).get('crest')
        if crest:
            open(os.path.join(d, 'crest.png'), 'wb').write(get(crest))
        # pabellón: está en el XML v1 del equipo
        try:
            t = ET.fromstring(get(f'{API}/v1/teams?seasonCode={c}{SEASON}&teamCode={code}'))
            club = next(cl for cl in t.iter('club') if cl.get('code') == code)
            ar = club.find('arena')
            save(os.path.join(code, 'arena.json'), {'name': ar.get('name') if ar is not None else ''})
        except Exception:  # noqa: BLE001
            pass
        players = [p for p in people if p['type'] == 'J' and p['active']]
        if fotos:
            for p in players:
                url = (p.get('images') or {}).get('headshot')
                f = os.path.join(d, 'img', p['person']['code'] + '.webp')
                if url and not os.path.exists(f):
                    save_photo(get(url), f)
        coach = [p['person']['name'] for p in people if p['type'] == 'E']
        w, l, _ = st[c].get(code, (0, 0, 0))
        print(f"{'Euroliga' if c == 'E' else 'Eurocup ':8s} {code}  {x['name']:40s} {w}-{l}  "
              f"{len(players):2d} jugadores  entrenador: {', '.join(coach) or '?'}")
    print(f"\nGuardado en {OUT}")


if __name__ == '__main__':
    main()
