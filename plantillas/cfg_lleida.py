# iLERNA Lleida 2026-27 -> sustituye a Xacobeo 99 Ourense (equipo 14, 11 jugadores)
TI = 14
DATOS = 'lleida'                    # carpeta en datos/ (creada con descargar.py)
OLD_SHORT = 'Xacobeo 99'
SCOREBOARD = '   LLEIDA   '          # 12 caracteres exactos

D = {
 # apellido (acb.com)  r1  r2  r3  r4  peso valor skin hair beard
 'Mc Ghee':   (81, 66, 70, 74,  75, 110, 1, 1, 1),
 'Batemon':   (89, 84, 80, 83,  84, 150, 1, 3, 3),
 'Hughes':    (79, 74, 75, 78,  95, 100, 2, 3, 1),
 'Ejim':      (74, 72, 76, 78, 100,  80, 1, 1, 1),
 'Perrin':    (73, 76, 84, 82, 105, 160, 2, 3, 0),
 'Paulí':     (76, 70, 76, 78,  98,  70, 0, 3, 3),
 'Kuath':     (69, 71, 79, 83, 100,  80, 1, 3, 0),
 'Shurna':    (70, 65, 70, 72, 102,  60, 0, 3, 3),
 'Sanz':      (72, 68, 72, 74,  95,  70, 0, 3, 0),
 'García':    (75, 58, 66, 69,  80,  60, 0, 3, 0),
 'Diagne':    (65, 73, 78, 78, 115,  80, 1, 1, 3),
}
# Titulares por partidos de inicio en la Liga 2026-27
ORDER = ['Mc Ghee', 'Batemon', 'Hughes', 'Ejim', 'Perrin',
         'Paulí', 'Kuath', 'Shurna', 'Sanz', 'García', 'Diagne']
SURNAME = {'Mc Ghee': 'McGhee', 'García': 'García, D.', 'Sanz': 'Sanz, M.'}

TEAM = dict(
    short_name='Lleida',
    long_name='iLERNA Lleida',
    club_name='Força Lleida C.E.',
    arena='Espai Fruita Barris Nord',
    address='Av. Prat de la Riba, 113-117',
    capacity=6100,
    president='-',
    sponsor='iLERNA',
)
HISTORY = ("∙ Força Lleida, que compite como iLERNA Lleida, disputa la Liga Endesa 2026-27. "
           "Juega sus partidos en el Espai Fruita Barris Nord, con capacidad para 6.100 "
           "espectadores. Su cuerpo técnico lo forman Gerard Encuentra como primer entrenador "
           "y Jorge Ribas y Mikel Garitaonandia como ayudantes.")
COACH = ('Gerard ENCUENTRA', 'Gerard ENCUENTRA',
         "∙ Gerard Encuentra, entrenador español de 36 años, dirige al iLERNA Lleida en la "
         "temporada 2026-27.")
LOGO_CROP = None
