"""
Estadísticas de los equipos no ACB en el formato «por 100» de 1996.

En el DBC original, los 358 jugadores europeos y los de la NBA no tienen
totales reales. Tienen las cifras «por 100»:
    T2, T3 y TL     anotados = porcentaje, intentados = 100
    partidos        100
    el resto        media por partido x 100 (rebotes, asistencias, minutos...)

El simulador del mánager las lee así en los equipos no ACB: divide entre 100
sin mirar los intentos. Con totales reales (p. ej. 15 de 29 en T2) un jugador
tira al 15 % y los equipos europeos meten 20-35 puntos por partido. Comprobado
con la partida del usuario: los 20 europeos de la Euroliga promediaban 24-34
puntos, y los 4 españoles, 80-90.

Uso (desde la carpeta EDITOR\\plantillas):
    python formato100.py            convierte los equipos 18-50 del DBC del juego
    python formato100.py --prueba   solo muestra lo que cambiaría
Es idempotente: los jugadores que ya están en este formato no se tocan.
"""
import argparse, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from dbc import Database  # noqa: E402

FIRST_NON_ACB = 18
GAME_DBC = os.path.join(HERE, '..', '..', 'BASKET96.DBC')
BACKUP_SUFFIX = '.antes_formato100'

MIN_ATTEMPTS = 10          # con menos intentos se usa el porcentaje típico
# (por defecto, mínimo, máximo) de T2, T3 y TL. Los valores de 1996 van de
# 10 (pívots que no tiran triples) a 95 (TL de Stockton).
PCT_RULES = {0: (50, 35, 75), 2: (33, 10, 60), 4: (72, 40, 97)}
BIG_MEN_3P = 10            # pívots y ala-pívots sin apenas triples, como en 1996
PER_GAME = (6, 7, 8, 9, 10, 11, 12, 14)   # rebotes, asist., tapones, robos, pérdidas, minutos, faltas


def is_per100(c) -> bool:
    return c[13] == 100 and all(c[k] in (0, 100) for k in (1, 3, 5))


def per100(c, position: int):
    """15 + 15 estadísticas reales -> formato «por 100» (los playoffs, a cero)."""
    c = list(c)
    if is_per100(c):
        return c
    out = [0] * 30
    for made, (default, lo, hi) in PCT_RULES.items():
        att = c[made + 1]
        if att >= MIN_ATTEMPTS:
            pct = round(100 * c[made] / att)
        elif made == 2 and position >= 3:
            pct = BIG_MEN_3P
        else:
            pct = default
        out[made] = max(lo, min(hi, pct))
        out[made + 1] = 100
    games = c[13]
    for k in PER_GAME:
        out[k] = min(65535, round(100 * c[k] / games)) if games else 0
    out[13] = 100
    return out


def convert(db: Database):
    changed = []
    for t in db.teams[FIRST_NON_ACB:]:
        for p in t.players:
            new = per100(p.current, p.position)
            if new != list(p.current):
                changed.append((t.short_name, p.short_name, p.current[:15], new[:15]))
                p.current = new
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--prueba', action='store_true', help='no guarda nada')
    ap.add_argument('--dbc', default=GAME_DBC)
    a = ap.parse_args()
    db = Database.load(a.dbc)
    changed = convert(db)
    for team, name, old, new in changed[:12]:
        print(f'{team:16} {name:24} {old}\n{"":41} -> {new}')
    print(f'{len(changed)} jugadores convertidos')
    if changed and not a.prueba:
        if not os.path.exists(a.dbc + BACKUP_SUFFIX):
            shutil.copy2(a.dbc, a.dbc + BACKUP_SUFFIX)
        os.chmod(a.dbc, 0o666)
        with open(a.dbc, 'wb') as f:
            f.write(db.serialize())
        print('Guardado. Copia de seguridad:', a.dbc + BACKUP_SUFFIX)


if __name__ == '__main__':
    main()
