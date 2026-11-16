# UCAM Murcia 2026-27 -> sustituye a Baloncesto Murcia 1996 (equipo 11, 10 jugadores)
TI = 11
DATOS = 'murcia'                    # carpeta en datos/ (creada con descargar.py)
OLD_SHORT = 'Murcia'
SCOREBOARD = '   MURCIA   '          # 12 caracteres exactos

D = {
 # apellido (acb.com)  r1  r2  r3  r4  peso valor skin hair beard
 'Boum':        (74, 62, 66, 70,  84, 100, 1, 1, 1),
 'Howell':      (84, 76, 77, 82,  88, 100, 1, 1, 1),
 'Nakic':       (76, 70, 73, 77,  98,  80, 0, 1, 0),
 'Bray-Gates':  (72, 65, 71, 73, 100,  90, 2, 3, 3),
 'Cate':        (73, 73, 81, 81, 110,  80, 0, 1, 1),
 'Forrest':     (79, 72, 69, 73,  77,  90, 1, 3, 1),
 'Pansa':       (64, 64, 72, 73, 108,  80, 1, 1, 0),
 'Sant-roos':   (77, 69, 76, 80,  98,  60, 1, 1, 3),
 'Radebaugh':   (79, 68, 73, 78,  88,  60, 2, 1, 1),
 'Marcos':      (77, 63, 69, 73,  84,  70, 0, 3, 0),
}
ORDER = ['Boum', 'Howell', 'Nakic', 'Bray-Gates', 'Cate',
         'Forrest', 'Pansa', 'Sant-roos', 'Radebaugh', 'Marcos']
SURNAME = {'Sant-roos': 'Sant-Roos'}

TEAM = dict(
    short_name='Murcia',
    long_name='UCAM Murcia',
    club_name='UCAM Murcia C.B.',
    arena='Palacio de Deportes de Murcia',
    address='Avda. del Rocío, 7',
    capacity=7454,
    president='-',
    sponsor='UCAM',
)
HISTORY = ("∙ El UCAM Murcia disputa la Liga Endesa 2026-27. Juega sus partidos en el Palacio "
           "de Deportes de Murcia, con capacidad para 7.454 espectadores. Su cuerpo técnico lo "
           "forman Alfonso Alonso como primer entrenador y Lucas Pérez y Dimitrios Tsesmetzis "
           "como ayudantes.")
COACH = ('Alfonso ALONSO', 'Alfonso ALONSO',
         "∙ Alfonso Alonso, entrenador español de 50 años, dirige al UCAM Murcia en la "
         "temporada 2026-27.")
LOGO_CROP = (0.0, 0.0, 1.0, 0.43)   # solo el escudo, sin "UCAM UNIVERSIDAD"
