# Barça 2026-27 -> sustituye al Barcelona de 1996 (equipo 0, 12 jugadores)
TI = 0
DATOS = 'barca'                       # carpeta en datos/ (creada con descargar.py)
OLD_SHORT = 'Barcelona'
SCOREBOARD = None                     # el marcador ya pone " BARCELONA "

D = {
 # apellido (acb.com)  r1  r2  r3  r4  peso valor skin hair beard
 'Punter':        (89, 85, 80, 85,  88, 240, 1, 3, 3),
 'Robinson':      (95, 86, 81, 85,  82, 150, 1, 3, 1),
 'Martin':        (77, 69, 77, 78,  98, 200, 1, 1, 3),
 'Parra':         (80, 76, 82, 83,  98, 130, 0, 3, 3),
 'Balcerowski':   (70, 77, 79, 80, 115, 170, 0, 3, 3),
 'Brizuela':      (83, 76, 74, 78,  85, 140, 0, 3, 3),
 'Nkamhoua':      (72, 70, 74, 75, 107, 190, 1, 3, 3),
 'Nebo':          (75, 79, 85, 84, 111, 160, 1, 1, 3),
 'Gibson':        (86, 78, 75, 80,  84, 120, 1, 1, 0),
 'Evbuomwan':     (62, 57, 69, 70, 100, 170, 1, 3, 3),
 'Umude':         (70, 63, 70, 73,  95, 110, 1, 3, 3),
 'Núñez':         (78, 66, 75, 78,  86, 210, 0, 3, 0),
}
# Quinteto titular según partidos de titular en la Liga 2026-27
ORDER = ['Robinson', 'Punter', 'Martin', 'Parra', 'Balcerowski',
         'Brizuela', 'Nkamhoua', 'Nebo', 'Gibson', 'Umude', 'Núñez', 'Evbuomwan']
SURNAME = {}

TEAM = dict(
    short_name='Barcelona',          # el del marcador del partido es fijo (" BARCELONA ")
    long_name='Barça',
    club_name='Futbol Club Barcelona',
    arena='Palau Blaugrana',
    address='C/ Arístides Maillol, s/n',
    capacity=7786,
    president='-',
    sponsor='-',
)
HISTORY = ("∙ La sección de baloncesto del Futbol Club Barcelona disputa la Liga Endesa 2026-27. "
           "Juega sus partidos en el Palau Blaugrana, con capacidad para 7.786 espectadores. Su "
           "cuerpo técnico lo forman Aleksander Sekulic como primer entrenador y Jurica Zuza y "
           "Jernej Valentincic como ayudantes.")
COACH = ('Aleksander SEKULIC', 'Aleksander SEKULIC',
         "∙ Aleksander Sekulic, entrenador esloveno de 48 años, dirige al Barça en la temporada "
         "2026-27 con Jurica Zuza y Jernej Valentincic como ayudantes.")
LOGO_CROP = None
# Nota: en 2026 la foto de Brizuela se procesó a mano (brillo 0,75, saturación 1,8); con los
# ajustes por defecto de ahora queda bien sin tratamiento especial.
