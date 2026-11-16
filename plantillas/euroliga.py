"""
Cambia los 24 participantes de la Euroliga del mánager.

El juego no elige los equipos de la Euroliga por la clasificación: la lista está fija dentro de
BASKET4.DAT (el programa del mánager), en 0xA5484: 24 números de equipo del DBC, en 4 grupos de 6.
En 1996 eran Barcelona (0), Estudiantes (6) y Caja San Fernando (9) más 21 europeos (18-38).
Con las plantillas actuales eso metía al Burgos (6) y al Tenerife (9).

Cada liga nueva copia esta lista en su partida (SAVE*\\LIGAS*.DAT): el cambio solo vale para
ligas creadas después.

Participantes que pone este script (como la Euroliga real 2026-27):
- España: Valencia, Barça, Real Madrid y Baskonia (uno en cada grupo).
- Los 16 clubes no españoles de la Euroliga (europa.py los tiene en SLOTS).
- Los 4 primeros de la Eurocup, para llegar a 24.
Los grupos se hacen por nivel (media de valoraciones de los 8 primeros), en serpiente.

Uso (desde EDITOR\\plantillas):  python euroliga.py  [--solo-listar] [--prueba CARPETA]
"""
import argparse, json, os, shutil, sys
from statistics import mean

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from dbc import Database  # noqa: E402
import europa  # noqa: E402

GAME_DEFAULT = os.path.normpath(os.path.join(HERE, '..', '..')) + os.sep
OFFSET = 0xA5484
ORIGINAL = bytes([23, 24, 20, 29, 35, 33, 18, 22, 6, 27, 32, 38,
                  0, 19, 26, 31, 28, 37, 25, 9, 21, 36, 30, 34])
SPAIN = [7, 0, 2, 4]          # Valencia, Barça, Real Madrid, Baskonia
EUROCUP_PLACES = 4


def strength(team):
    ps = sorted(team.players, key=lambda p: p.roster_order)[:8]
    return mean(sum(p.attrs[6:10]) / 4 for p in ps)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--solo-listar', action='store_true')
    ap.add_argument('--prueba')
    a = ap.parse_args()
    game = os.path.abspath(a.prueba) + os.sep if a.prueba else GAME_DEFAULT
    db = Database.load(game + 'BASKET96.DBC')

    chosen = json.load(open(os.path.join(HERE, 'datos', 'europa', 'elegidos.json'), encoding='utf-8'))
    slot = {s[0]: ti for ti, s in europa.SLOTS.items()}
    el = [slot[x['code']] for x in chosen if x['comp'] == 'E']
    ec = [slot[x['code']] for x in chosen if x['comp'] == 'U'][:EUROCUP_PLACES]
    others = sorted(el + ec, key=lambda ti: -strength(db.teams[ti]))
    assert len(SPAIN) == 4 and len(others) == 20

    # el español más débil va al grupo del europeo más fuerte, para equilibrar
    groups = [[s] for s in sorted(SPAIN, key=lambda ti: strength(db.teams[ti]))]
    for k, ti in enumerate(others):            # serpiente: 0 1 2 3 3 2 1 0 ...
        rnd, i = divmod(k, 4)
        groups[i if rnd % 2 == 0 else 3 - i].append(ti)
    new =bytes(ti for g in groups for ti in g)
    assert len(new) == 24 and len(set(new)) == 24

    for n, g in enumerate(groups):
        print(f"Grupo {'ABCD'[n]}: " + ', '.join(f"{db.teams[ti].short_name} ({strength(db.teams[ti]):.1f})" for ti in g))
    if a.solo_listar:
        return

    path = game + 'BASKET4.DAT'
    data = bytearray(open(path, 'rb').read())
    cur = bytes(data[OFFSET:OFFSET + 24])
    if cur != ORIGINAL and (len(set(cur)) != 24 or max(cur) > 50):
        sys.exit(f"En {hex(OFFSET)} no está la lista esperada: no toco nada.")
    if not os.path.exists(path + '.BAK'):
        shutil.copy2(path, path + '.BAK')
    os.chmod(path, 0o666)
    data[OFFSET:OFFSET + 24] = new
    open(path, 'wb').write(data)
    print(f"\nGuardado en {path} (original en BASKET4.DAT.BAK). Vale para ligas nuevas.")


if __name__ == '__main__':
    main()
