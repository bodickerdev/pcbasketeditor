"""
Descarga de acb.com la plantilla de un equipo: datos, estadísticas, fotos de cara y escudo.

Uso (desde la carpeta EDITOR\\plantillas):
    python descargar.py <dirección del equipo en acb.com> <nombre de carpeta>
Ejemplo:
    python descargar.py https://acb.com/es/liga/equipos/unicaja-14 unicaja

Crea datos\\<nombre>\\ con players.json, roster.json, img\\<id>.webp y logo.png
y muestra un resumen para elegir jugadores y valoraciones en la config.
"""
import html, json, os, re, sys, urllib.request

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0'}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def page(url):
    return get(url).decode('utf-8').replace('\\"', '"')


def obj_at(u, i):
    """Devuelve el objeto JSON que empieza en u[i] == '{'."""
    d = 0
    for k in range(i, len(u)):
        if u[k] == '{':
            d += 1
        elif u[k] == '}':
            d -= 1
            if d == 0:
                return json.loads(u[i:k + 1].replace('"$undefined"', 'null'))


def latin1(s):
    # la base de datos solo admite Latin-1: ć -> c, š -> s, ž -> z...
    out = ''
    for ch in s:
        try:
            ch.encode('latin-1'); out += ch
        except UnicodeEncodeError:
            import unicodedata
            out += unicodedata.normalize('NFD', ch)[0]
    return out


def main():
    url, name = sys.argv[1].rstrip('/'), sys.argv[2]
    slug = url.split('/equipos/')[1].split('/')[0]
    out = os.path.join(HERE, 'datos', name)
    os.makedirs(os.path.join(out, 'img'), exist_ok=True)

    u = page(f'https://acb.com/es/liga/equipos/{slug}/plantilla')
    i = u.find('"currentRoster":{"players":[') + len('"currentRoster":')
    roster = obj_at(u, i)
    json.dump(roster, open(os.path.join(out, 'roster.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    logo = re.findall(r'teamLogoUrl":"([^"]*)"', u)[0]
    open(os.path.join(out, 'logo.png'), 'wb').write(get(logo))

    t = page(f'https://acb.com/es/liga/equipos/{slug}')
    print('== Club')
    for k in ['stadiumName', 'stadiumAddress', 'stadiumCapacity']:
        m = re.findall('"' + k + '":("[^"]*"|[0-9]+)', t)
        print(f"  {k}: {html.unescape(m[0]) if m else '?'}")
    for s in roster['staff']:
        c = s.get('coach') or {}
        print(f"  {c.get('gameRole')}: {c.get('firstName')} {c.get('lastName')} "
              f"({s.get('age')} años, {s.get('nationalityCountry')})")

    links = sorted(set(re.findall(r'href="(/es/liga/jugadores/[^"]*)"', u)))
    players = []
    for rp in roster['players']:
        q = rp['player']
        link = next((l for l in links if l.endswith(f"-{q['id']}")), None)
        pu = page('https://acb.com' + link)
        j = pu.find('"birthDate"')
        info = {}
        for k in ['birthDate', 'birthPlace', 'birthCountry', 'nationality']:
            m = re.search(rf'"{k}":"([^"]*)"', pu[j:j + 400])
            info[k] = latin1(m.group(1)) if m else ''
        tots = [obj_at(pu, m.start() + len('"totals":'))
                for m in re.finditer(r'"totals":\{"numGames"', pu)]
        p = dict(id=q['id'], first=latin1(q['firstName'].strip()), last=latin1(q['lastName'].strip()),
                 nick=q['nickname'], num=q['shirtNumber'], role=q['gameRole'], height=rp['height'],
                 age=rp['age'], lic=rp['licensing'], natc=rp['nationalityCountry'],
                 img=q['headshotImageNoBackgroundUrl'], img2=q['headshotImageUrl'], **info, totals=tots)
        players.append(p)
        url_img = p['img'] or p['img2']
        if url_img:
            ext = 'webp' if p['img'] else 'jpg'
            open(os.path.join(out, 'img', f"{p['id']}.{ext}"), 'wb').write(get(url_img))
    json.dump(players, open(os.path.join(out, 'players.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print('\n== Jugadores (temporada actual | carrera ACB)')
    for p in players:
        t = p['totals']; s = t[0] if t else {}; c = t[2] if len(t) > 2 else {}
        pg = lambda x, k: x.get(k, 0) / max(x.get('numGames', 1), 1)
        print(f"{p['num']:>3} {p['first'] + ' ' + p['last']:26s} {p['role']:10s} {p['height']} "
              f"{p['lic']:6s} | {s.get('numGames', 0):2d} pj {s.get('timePlayed', 0) / 60:4.0f} min "
              f"tit={s.get('starter', 0)} | ACB {c.get('numGames', 0):3d} pj {pg(c, 'points'):4.1f} p "
              f"val {pg(c, 'rating'):4.1f}" + ('' if p['img'] else '  (sin foto sin fondo)'))
    print(f"\nGuardado en {out}")


if __name__ == '__main__':
    main()
