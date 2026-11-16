# Unicaja 2026-27 -> sustituye al Unicaja de 1996 (equipo 1, 12 jugadores)
TI = 1
DATOS = 'unicaja'                    # carpeta en datos/ (creada con descargar.py)
OLD_SHORT = 'Unicaja'
SCOREBOARD = '  UNICAJA   '          # 12 caracteres exactos (igual que el original)

D = {
 # apellido (acb.com)   r1  r2  r3  r4  peso valor skin hair beard
 'Perry':         (92, 80, 78, 85,  79, 120, 1, 3, 1),
 'Hunt':          (89, 84, 80, 85,  86, 130, 1, 1, 3),
 'Brazdeikis':    (71, 62, 71, 72, 100, 100, 0, 1, 3),
 'Noua':          (80, 79, 84, 85, 102, 130, 2, 1, 3),
 'Kravish':       (68, 66, 74, 74, 109,  90, 0, 1, 3),
 'Pantzar':       (86, 77, 81, 84,  82, 130, 2, 3, 1),
 'Kalinoski':     (78, 67, 72, 75,  88,  70, 0, 1, 1),
 'Hernangómez':   (72, 78, 84, 83, 115, 110, 0, 1, 3),
 'Pérez':         (78, 78, 87, 86, 108, 100, 2, 1, 1),
 'Knox':          (65, 62, 68, 68,  98, 120, 2, 1, 1),
 'Barreiro':      (68, 61, 71, 72, 100,  50, 0, 3, 1),
 'Díaz':          (83, 67, 73, 78,  85,  70, 0, 3, 0),
}
# Titulares por partidos de inicio en la Liga 2026-27
ORDER = ['Perry', 'Hunt', 'Brazdeikis', 'Noua', 'Kravish',
         'Pantzar', 'Kalinoski', 'Hernangómez', 'Pérez', 'Knox', 'Barreiro', 'Díaz']
SURNAME = {'Pérez': 'Pérez, T.', 'Díaz': 'Díaz, A.'}

TEAM = dict(
    short_name='Unicaja',
    long_name='Unicaja',
    club_name='Club Baloncesto Málaga S.A.D.',
    arena='Palacio de Deportes José María Martín Carpena',
    address='C/ Miguel Mérida Nicolich, 2',
    capacity=10699,
    president='-',
    sponsor='Unicaja',
)
HISTORY = ("∙ El Club Baloncesto Málaga, que compite como Unicaja, disputa la Liga Endesa "
           "2026-27. Juega sus partidos en el Palacio de Deportes José María Martín Carpena, "
           "con capacidad para 10.699 espectadores. Su cuerpo técnico lo forman Jesús "
           "Vidorreta como primer entrenador y Andrija Gavrilovic, Gonzalo Hermoso y Federico "
           "Van Lacke como ayudantes.")
COACH = ('Jesús VIDORRETA', 'Jesús VIDORRETA',
         "∙ Jesús Vidorreta, entrenador español de 60 años, dirige al Unicaja en la "
         "temporada 2026-27.")
LOGO_CROP = (0.0, 0.0, 1.0, 0.43)   # el símbolo verde y la parte alta del escudo, sin el texto
