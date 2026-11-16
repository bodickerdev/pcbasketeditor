"""
Deja al jugador más flojo del banquillo como 12.º de la plantilla.

En el modo mánager, el juego empieza la liga con 11 jugadores por equipo
(el hueco libre es para fichar): el 12.º de la lista, que también es el de
orden 12, se queda fuera de la liga. Este script coloca en ese hueco al
suplente con la valoración media más baja, en vez de a quien hubiera
quedado último por minutos jugados.

En los equipos ACB también mueve los retratos de CARAS.BIN, que van por
posición en la lista. Las caras pequeñas y las fotos van con el jugador.

Uso (desde EDITOR\\plantillas):
    python orden12.py              aplica a todos los equipos de 12 jugadores
    python orden12.py --prueba     solo muestra los cambios
"""
import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.stdout.reconfigure(encoding='utf-8')
from dbc import Database  # noqa: E402
from caras import Faces  # noqa: E402

GAME = os.path.normpath(os.path.join(HERE, '..', '..')) + os.sep
MAX_IN_LEAGUE = 11
N_LEAGUE_TEAMS = 50      # ACB + Europa (el All-Star no juega la liga)
BACKUP_SUFFIX = '.antes_orden12'


def overall(p) -> float:
    return (p.rating1 + p.rating2 + p.rating3 + p.rating4) / 4


def weakest_last(players: list) -> int | None:
    """Mueve al suplente más flojo al final y renumera el orden 6..N.
    Devuelve su posición anterior (None si no había que mover a nadie)."""
    if len(players) <= MAX_IN_LEAGUE:
        return None
    bench = [i for i, p in enumerate(players) if not 1 <= p.roster_order <= 5]
    k = min(bench, key=lambda i: (overall(players[i]), players[i].value, -i))
    players.append(players.pop(k))
    starters = [p for p in players if 1 <= p.roster_order <= 5]
    rest = [p for p in players if not 1 <= p.roster_order <= 5]
    rest.sort(key=lambda p: (p is players[-1], p.roster_order))
    for n, p in enumerate(rest, start=6):
        p.roster_order = n
    return None if k == len(players) - 1 else k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prueba', action='store_true')
    a = ap.parse_args()

    db = Database.load(GAME + 'BASKET96.DBC')
    faces = Faces(GAME + 'CARAS.BIN', GAME + 'CAMPO800.BIN')
    changed = False
    for ti, team in enumerate(db.teams[:N_LEAGUE_TEAMS]):
        before = list(team.players)
        out = before[-1] if len(before) > MAX_IN_LEAGUE else None
        k = weakest_last(team.players)
        if k is None:
            continue
        changed = True
        new = team.players[-1]
        print(f"{ti:2d} {team.short_name:15s} fuera de la liga: {new.surname} "
              f"({overall(new):.0f}) en vez de {out.surname} ({overall(out):.0f})")
        # retratos ACB: van por posición, así que se mueven igual que los jugadores
        if faces.player_slot(ti, 0) is not None:
            px = [bytes(faces.faces[faces.player_slot(ti, i)][2]) for i in range(len(before))]
            px.append(px.pop(k))
            for i, data in enumerate(px):
                faces.set_pixels(faces.player_slot(ti, i), data)

    if not changed:
        print('Nada que cambiar.')
        return
    if a.prueba:
        print('(prueba: no se ha guardado nada)')
        return
    for f in ('BASKET96.DBC', 'CARAS.BIN'):
        if not os.path.exists(GAME + f + BACKUP_SUFFIX):
            shutil.copy2(GAME + f, GAME + f + BACKUP_SUFFIX)
    Database.parse(db.serialize())   # comprobación
    db.save(GAME + 'BASKET96.DBC', backup=False)
    faces.save(GAME + 'CARAS.BIN')
    print('Guardado.')


if __name__ == '__main__':
    main()
