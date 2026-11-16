# FIATC Girona 2026-27 -> sustituye a VALVI Girona (equipo 16, 9 jugadores)
TI = 16
DATOS = 'girona'                    # carpeta en datos/ (creada con descargar.py)
OLD_SHORT = 'VALVI'
SCOREBOARD = '   GIRONA   '          # 12 caracteres exactos

D = {
 # apellido (como en acb.com)  r1  r2  r3  r4  peso valor skin hair beard
 'Mc Clung':      (72, 63, 67, 71,  84, 130, 0, 3, 0),
 'Perez':         (86, 85, 83, 89,  88, 140, 1, 3, 1),
 'Martínez':      (72, 64, 76, 77,  98,  80, 0, 3, 1),
 "N'Guessan":     (69, 66, 72, 75, 100, 110, 1, 1, 1),
 'Geben':         (79, 80, 85, 83, 113, 100, 0, 3, 3),
 'Pluta':         (71, 59, 65, 69,  80,  70, 0, 3, 1),
 'Whittaker Jr':  (73, 60, 65, 69,  82,  80, 1, 1, 3),
 'Maric':         (64, 67, 75, 73, 104,  60, 0, 3, 3),
 'Busquets':      (72, 67, 75, 76,  95,  60, 0, 3, 0),
}
# Titulares por partidos de inicio en la Liga 2026-27
ORDER = ['Mc Clung', 'Perez', 'Martínez', "N'Guessan", 'Geben',
         'Pluta', 'Whittaker Jr', 'Maric', 'Busquets']
SURNAME = {'Martínez': 'Martínez, S.', 'Perez': 'Pérez, J.', 'Whittaker Jr': 'Whittaker',
           'Mc Clung': 'McClung'}

TEAM = dict(
    short_name='Girona',
    long_name='FIATC Girona',
    club_name='Bàsquet Girona S.A.D.',
    arena='Palau Girona-Fontajau',
    address='Avda. Josep Tarradellas, 22-24',
    capacity=5750,
    president='-',
    sponsor='FIATC',
)
HISTORY = ("∙ Bàsquet Girona, que compite como FIATC Girona, disputa la Liga Endesa 2026-27. "
           "Juega sus partidos en el Palau Girona-Fontajau, con capacidad para 5.750 "
           "espectadores. Su cuerpo técnico lo forman Ramón Fernández como primer entrenador "
           "y Miquel Fuentes y Albert Sàbat como ayudantes.")
COACH = ('Ramón FERNANDEZ', 'Ramón FERNANDEZ',
         "∙ Ramón Fernández, entrenador español de 57 años, dirige al FIATC Girona en la "
         "temporada 2026-27.")
LOGO_CROP = (0.0, 0.2, 1.0, 1.0)   # quita el texto "FIATC" de encima del escudo
