# Monbus Obradoiro 2026-27 -> sustituye a Forum Valladolid (equipo 10, 10 jugadores)
TI = 10
DATOS = 'obradoiro'                    # carpeta en datos/ (creada con descargar.py)
OLD_SHORT = 'Forum'
SCOREBOARD = ' OBRADOIRO  '          # 12 caracteres exactos

D = {
 # apellido (acb.com)  r1  r2  r3  r4  peso valor skin hair beard
 'Childress':   (77, 64, 68, 73,  86, 100, 1, 1, 1),
 'Barcello':    (76, 67, 71, 74,  86,  90, 0, 3, 0),
 'Meindl':      (78, 71, 81, 82, 100,  90, 2, 3, 3),
 'Abogidi':     (60, 55, 65, 66, 102,  70, 1, 1, 0),
 'Soriano':     (69, 74, 79, 77, 116, 100, 2, 1, 3),
 'Barrueta':    (73, 63, 69, 72,  92,  70, 0, 1, 3),
 'Agada':       (75, 64, 73, 77,  90,  50, 1, 1, 1),
 'Galan':       (61, 56, 66, 68, 104,  30, 0, 0, 1),
 'Dos Anjos':   (59, 61, 72, 72, 120,  50, 2, 3, 0),
 'Quintela':    (70, 57, 65, 70,  82,  40, 0, 3, 1),
}
# Titulares por partidos de inicio en la Liga 2026-27
ORDER = ['Childress', 'Barcello', 'Meindl', 'Abogidi', 'Soriano',
         'Barrueta', 'Agada', 'Galan', 'Dos Anjos', 'Quintela']
SURNAME = {'Galan': 'Galán'}

TEAM = dict(
    short_name='Obradoiro',
    long_name='Monbus Obradoiro',
    club_name='Obradoiro C.A.B.',
    arena='Multiusos Fontes do Sar',
    address='Rúa Diego Bernal, s/n',
    capacity=6000,
    president='-',
    sponsor='Monbus',
)
HISTORY = ("∙ El Obradoiro Clube Amigos do Baloncesto, que compite como Monbus Obradoiro, "
           "disputa la Liga Endesa 2026-27. Juega sus partidos en el Multiusos Fontes do Sar "
           "de Santiago de Compostela, con capacidad para 6.000 espectadores. Su cuerpo "
           "técnico lo forman Diego Epifanio como primer entrenador y Francisco Hernández y "
           "Alberto Codeso como ayudantes.")
COACH = ('Diego EPIFANIO', 'Diego EPIFANIO',
         "∙ Diego Epifanio, entrenador español de 48 años, dirige al Monbus Obradoiro en la "
         "temporada 2026-27.")
LOGO_CROP = (0.0, 0.0, 1.0, 0.9)   # quita el logo de "Monbus" de debajo del escudo

# Fotos con luz cálida: menos saturación para que no salgan anaranjadas
LIGHT = (0.75, 1.2, 1.35)
DARK = (0.85, 1.05, 1.2)
