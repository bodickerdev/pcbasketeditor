# Valencia Basket 2026-27 -> sustituye a Pamesa Valencia (equipo 7, 10 jugadores)
TI = 7
DATOS = 'valencia'                    # carpeta en datos/ (creada con descargar.py)
OLD_SHORT = 'Pamesa'
SCOREBOARD = '  VALENCIA  '          # 12 caracteres exactos (igual que el original)

D = {
 # apellido (acb.com)    r1  r2  r3  r4  peso valor skin hair beard
 'Shorts':         (99, 88, 85, 89,  75, 200, 1, 1, 1),
 'Saint-Supery':   (74, 66, 71, 75,  84, 180, 0, 3, 0),
 'Taylor':         (88, 84, 86, 90,  95, 130, 1, 3, 1),
 'Osetkowski':     (80, 74, 79, 81, 113, 130, 0, 3, 3),
 'Sako':           (69, 72, 84, 80, 105, 110, 2, 1, 1),
 'Mirotic':        (87, 90, 89, 90, 107, 180, 0, 1, 3),
 'Brooks':         (91, 85, 83, 86,  88, 140, 1, 3, 3),
 'Rivero':         (73, 75, 80, 81, 107, 100, 1, 1, 0),
 'Corbalán':       (83, 77, 78, 84,  85, 140, 0, 3, 0),
 'Puerto':         (76, 70, 74, 75,  93,  70, 0, 3, 1),
}
ORDER = ['Shorts', 'Saint-Supery', 'Taylor', 'Osetkowski', 'Sako',
         'Mirotic', 'Brooks', 'Rivero', 'Corbalán', 'Puerto']
SURNAME = {}

TEAM = dict(
    short_name='Valencia',
    long_name='Valencia Basket',
    club_name='Valencia Basket Club S.A.D.',
    arena='Roig Arena',
    address='C/ Ángel Villena, 16',
    capacity=15600,
    president='-',
    sponsor='-',
)
HISTORY = ("∙ Valencia Basket disputa la Liga Endesa 2026-27, temporada en la que celebra su "
           "40 aniversario. Juega sus partidos en el Roig Arena, con capacidad para 15.600 "
           "espectadores. Su cuerpo técnico lo forman Xavier Albert como primer entrenador e "
           "Israel González, Juan Maroto y Vicent Revert como ayudantes.")
COACH = ('Xavier ALBERT', 'Xavier ALBERT',
         "∙ Xavier Albert, entrenador español de 39 años, dirige al Valencia Basket en la "
         "temporada 2026-27.")
LOGO_CROP = (0.0, 0.0, 1.0, 0.63)   # escudo sin el "40 anys" de debajo
