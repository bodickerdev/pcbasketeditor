# Casademont Zaragoza 2026-27 -> sustituye a Cáceres C.B. (equipo 12, 11 jugadores)
TI = 12
DATOS = 'zaragoza'                    # carpeta en datos/ (creada con descargar.py)
OLD_SHORT = 'Cáceres'
SCOREBOARD = '  ZARAGOZA  '          # 12 caracteres exactos

D = {
 # apellido (acb.com)  r1  r2  r3  r4  peso valor skin hair beard
 'Bell-Haynes':     (88, 80, 79, 83,  85, 150, 1, 1, 0),
 'Jaworski':        (77, 71, 70, 74,  86, 120, 0, 3, 0),
 'González':        (71, 62, 72, 74,  96,  90, 0, 3, 3),
 'Blumbergs':       (73, 67, 73, 75, 100, 110, 0, 3, 1),
 'Olaseni':         (62, 63, 70, 70, 108,  80, 1, 1, 3),
 'Brussino':        (83, 77, 80, 83,  98, 120, 0, 3, 1),
 'Birutis':         (69, 75, 80, 80, 120, 150, 0, 3, 3),
 'Vives':           (77, 65, 69, 73,  89,  90, 0, 3, 3),
 'Homesley':        (79, 73, 74, 77,  95, 120, 1, 1, 1),
 'Fernández':       (65, 61, 70, 71, 103,  60, 0, 3, 3),
 'García':          (76, 64, 69, 75,  90,  80, 0, 3, 3),
}
# Titulares por partidos de inicio en la Liga 2026-27
ORDER = ['Bell-Haynes', 'Jaworski', 'González', 'Blumbergs', 'Olaseni',
         'Brussino', 'Birutis', 'Vives', 'Homesley', 'Fernández', 'García']
SURNAME = {'García': 'García, S.', 'Fernández': 'Fernández, J.', 'González': 'González, M.'}

TEAM = dict(
    short_name='Zaragoza',
    long_name='Casademont Zaragoza',
    club_name='Basket Zaragoza 2002 S.A.D.',
    arena='Pabellón Príncipe Felipe',
    address='Avda. Cesáreo Alierta, 120',
    capacity=10744,
    president='-',
    sponsor='Casademont',
)
HISTORY = ("∙ Basket Zaragoza 2002, que compite como Casademont Zaragoza, disputa la Liga Endesa "
           "2026-27. Juega sus partidos en el Pabellón Príncipe Felipe, con capacidad para 10.744 "
           "espectadores. Su cuerpo técnico lo forman Gonzalo García como primer entrenador y "
           "Rodrigo San Miguel y Jorge Serna como ayudantes.")
COACH = ('Gonzalo GARCIA', 'Gonzalo GARCIA',
         "∙ Gonzalo García, entrenador español de 55 años, dirige al Casademont Zaragoza en la "
         "temporada 2026-27.")
LOGO_CROP = None
