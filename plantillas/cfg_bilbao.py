# Surne Bilbao 2026-27 -> sustituye a C.B. Gran Canaria (equipo 17, 11 jugadores)
TI = 17
DATOS = 'bilbao'                    # carpeta en datos/ (creada con descargar.py)
OLD_SHORT = 'Gran Canaria'
SCOREBOARD = '   BILBAO   '          # 12 caracteres exactos

D = {
 # apellido (acb.com)  r1  r2  r3  r4  peso valor skin hair beard
 'Frey':          (82, 71, 72, 76,  82,  80, 0, 3, 0),
 'Normantas':     (74, 65, 70, 75,  90,  70, 0, 1, 1),
 'Hilliard II':   (82, 75, 77, 80,  93,  90, 1, 1, 3),
 'Petrasek':      (70, 66, 72, 75, 104,  70, 0, 3, 1),
 'Vautier':       (63, 63, 71, 72, 115,  60, 0, 0, 3),
 'Hlinason':      (74, 80, 87, 87, 120,  70, 0, 1, 3),
 'Darling':       (70, 59, 67, 70,  90,  70, 0, 3, 3),
 'Krampelj':      (75, 74, 77, 78, 102,  60, 0, 3, 0),
 'Somogyi':       (71, 58, 65, 70,  88,  50, 0, 1, 0),
 'Font':          (67, 59, 64, 66,  85,  30, 0, 3, 1),
 'Ansorregi':     (61, 55, 62, 64,  92,  20, 0, 3, 0),
}
ORDER = ['Frey', 'Normantas', 'Hilliard II', 'Petrasek', 'Vautier',
         'Hlinason', 'Darling', 'Krampelj', 'Somogyi', 'Font', 'Ansorregi']
SURNAME = {'Hilliard II': 'Hilliard'}

TEAM = dict(
    short_name='Bilbao',
    long_name='Surne Bilbao',
    club_name='Bilbao Basket',
    arena='Bilbao Arena',
    address='Avenida Askatasuna, 13',
    capacity=10014,
    president='-',
    sponsor='Surne',
)
HISTORY = ("∙ Bilbao Basket, que compite como Surne Bilbao, disputa la Liga Endesa 2026-27. "
           "Juega sus partidos en el Bilbao Arena de Miribilla, con capacidad para 10.014 "
           "espectadores. Su cuerpo técnico lo forman Jaume Ponsarnau como primer entrenador, "
           "Javier Salgado como segundo y Mikel Odriozola e Ibon López de Letona como "
           "ayudantes.")
COACH = ('Jaume PONSARNAU', 'Jaume PONSARNAU',
         "∙ Jaume Ponsarnau, entrenador español de 55 años, dirige al Surne Bilbao en la "
         "temporada 2026-27.")
LOGO_CROP = (0.0, 0.0, 1.0, 0.8)   # sin la palabra "surne" de debajo del escudo
