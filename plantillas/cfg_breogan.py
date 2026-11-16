# Río Breogán 2026-27 -> sustituye a Covirán Granada (equipo 15, 12 jugadores)
TI = 15
DATOS = 'breogan'                    # carpeta en datos/ (creada con descargar.py)
FIXES = {30002695: {'last': 'Andric'}}   # 'Andrić': la base de datos no admite la ć
OLD_SHORT = 'Granada'
SCOREBOARD = '  BREOGAN   '          # 12 caracteres; sin tilde por la fuente del marcador

D = {
 # apellido (acb.com)  r1  r2  r3  r4  peso valor skin hair beard
 'Bolton':      (83, 74, 74, 78,  84, 110, 2, 1, 1),
 'Peris':       (66, 56, 61, 65,  85,  50, 0, 3, 3),
 'Brown':       (81, 73, 76, 80,  93, 140, 2, 3, 3),
 'Andric':      (77, 72, 72, 75, 100,  60, 0, 3, 1),
 'Brankovic':   (77, 85, 87, 89, 120, 120, 0, 1, 1),
 'Mavra':       (86, 75, 77, 81,  92,  80, 0, 1, 3),
 'Alonso':      (86, 83, 78, 82,  86,  90, 0, 3, 3),
 'Aranitovic':  (76, 67, 76, 78,  92,  60, 0, 1, 0),
 'Mejia':       (68, 63, 72, 74, 100,  60, 2, 3, 1),
 'Ilic':        (59, 58, 67, 68, 108,  60, 0, 3, 0),
 'Martín':      (53, 50, 62, 62, 110,  30, 1, 1, 3),
 'Brimah':      (62, 67, 71, 75, 106,  50, 1, 1, 0),
}
# Titulares por partidos de inicio en la Liga 2026-27
ORDER = ['Bolton', 'Peris', 'Brown', 'Andric', 'Brankovic',
         'Mavra', 'Alonso', 'Aranitovic', 'Mejia', 'Ilic', 'Brimah', 'Martín']
SURNAME = {'Alonso': 'Alonso, F.', 'Martín': 'Martín, J.', 'Mejia': 'Mejía'}

TEAM = dict(
    short_name='Breogán',
    long_name='Río Breogán',
    club_name='C.B. Breogán S.A.D.',
    arena='Pazo dos Deportes de Lugo',
    address='Avda. Filarmónica Lucense, s/n',
    capacity=5310,
    president='-',
    sponsor='Río',
)
HISTORY = ("∙ El Club Baloncesto Breogán, que compite como Río Breogán, disputa la Liga Endesa "
           "2026-27. Juega sus partidos en el Pazo Provincial dos Deportes de Lugo, con "
           "capacidad para 5.310 espectadores. Su cuerpo técnico lo forman Luis Palomo como "
           "primer entrenador y Víctor Pérez y Fernán Varela como ayudantes.")
COACH = ('Luis PALOMO', 'Luis PALOMO',
         "∙ Luis Palomo, entrenador español de 66 años, dirige al Río Breogán en la "
         "temporada 2026-27.")
LOGO_CROP = None
