"""
Pone en el palmarés de cada equipo ACB su posición en la temporada pasada (2025-26).

El palmarés del DBC (26 bytes) termina con las posiciones de las 11 últimas temporadas; la
última (byte 25) es la de la temporada anterior. Parece que el juego la usa para repartir las
plazas europeas: con los datos de 1996, el Burgos (hueco del Estudiantes, 3.º en 1995-96)
jugaba la Euroliga. 250 = estaba en una categoría inferior; 251 = no existía en la ACB.

Clasificación final 2025-26 (con el playoff): campeón Valencia, subcampeón Barça,
semifinalistas Joventut y Tenerife; luego cuartofinalistas y el resto según la liga regular.

Uso (desde EDITOR\\plantillas):  python clasificacion.py   [--prueba CARPETA]
"""
import argparse, os, shutil, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from dbc import Database  # noqa: E402

GAME_DEFAULT = os.path.normpath(os.path.join(HERE, '..', '..')) + os.sep
LAST = 25           # byte del palmarés con la posición de la temporada pasada

# hueco del juego: (equipo 2026-27, posición final en la ACB 2025-26)
POSITIONS = {
    7: ('Valencia', 1),      # campeón
    0: ('Barça', 2),         # subcampeón
    # Madrid y Baskonia se ponen por delante de los semifinalistas para que entren en la
    # Euroliga del juego, como en la Euroliga real 2026-27 (Madrid, Barça, Valencia, Baskonia).
    2: ('Real Madrid', 3),   # real: cuartos (1.º en liga regular)
    4: ('Baskonia', 4),      # real: cuartos (3.º)
    13: ('Joventut', 5),     # real: semifinal (6.º)
    9: ('Tenerife', 6),      # real: semifinal (8.º)
    11: ('Murcia', 7),       # cuartos (4.º)
    17: ('Bilbao', 8),       # cuartos (7.º)
    1: ('Unicaja', 9),
    3: ('Manresa', 10),
    15: ('Breogán', 11),
    16: ('Girona', 12),
    6: ('Burgos', 13),
    14: ('Lleida', 14),
    12: ('Zaragoza', 15),
    5: ('Andorra', 16),
    8: ('Coruña', 250),      # 2025-26 en Primera FEB (ascendido)
    10: ('Obradoiro', 250),  # 2025-26 en Primera FEB (ascendido)
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prueba')
    a = ap.parse_args()
    game = os.path.abspath(a.prueba) + os.sep if a.prueba else GAME_DEFAULT
    path = game + 'BASKET96.DBC'
    db = Database.load(path)
    prev = path + '.antes_clasificacion'
    if not os.path.exists(prev):
        shutil.copy2(path, prev)
    for ti, (name, pos) in sorted(POSITIONS.items(), key=lambda x: x[1][1]):
        t = db.teams[ti]
        pal = bytearray(t.palmares)
        old = pal[LAST]
        pal[LAST] = pos
        t.palmares = bytes(pal)
        print(f"  {ti:2d} {name:12s} temporada pasada: {old:3d} -> {pos}")
    os.chmod(path, 0o666)
    db.save(path, backup=False)
    print(f"\nGuardado en {path} (copia anterior: {os.path.basename(prev)})")


if __name__ == '__main__':
    main()
