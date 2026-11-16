# Recoletas Salud San Pablo Burgos 2026-27 -> sustituye a Estudiantes (equipo 6, 11 jugadores)
TI = 6
DATOS = 'burgos'                    # carpeta en datos/ (creada con descargar.py)
OLD_SHORT = 'Estudiantes'
SCOREBOARD = '   BURGOS   '          # 12 caracteres exactos

D = {
 # apellido (acb.com)    r1  r2  r3  r4  peso valor skin hair beard
 'Steward':        (83, 78, 77, 81,  79, 140, 1, 3, 0),
 'Lobaco':         (72, 63, 68, 71,  85,  70, 0, 3, 0),
 'Radosavljevic':  (64, 55, 69, 72,  98,  70, 0, 1, 0),
 'Sengfelder':     (75, 73, 78, 79, 105, 110, 0, 1, 1),
 'Koprivica':      (66, 68, 77, 78, 116, 100, 0, 1, 1),
 'Doumbouya':      (75, 73, 80, 80, 104, 110, 1, 3, 0),
 'Audige':         (75, 68, 70, 75,  91,  70, 1, 1, 1),
 'Samar':          (74, 63, 71, 73,  92,  70, 0, 3, 0),
 'Díez':           (73, 66, 75, 75, 100,  40, 0, 3, 3),
 'Cancar':         (68, 61, 68, 71, 107, 110, 0, 3, 1),
 'Taboada':        (67, 57, 65, 68,  85,  40, 0, 3, 0),
}
# Titulares por partidos de inicio en la Liga 2026-27
ORDER = ['Steward', 'Lobaco', 'Radosavljevic', 'Sengfelder', 'Koprivica',
         'Doumbouya', 'Audige', 'Samar', 'Díez', 'Cancar', 'Taboada']
SURNAME = {'Díez': 'Díez, D.', 'Radosavljevic': 'Radosavljevic'}

TEAM = dict(
    short_name='Burgos',
    long_name='Recoletas Salud San Pablo Burgos',
    club_name='C.B. San Pablo Burgos',
    arena='Coliseum Burgos',
    address='C/ La Chopera, s/n',
    capacity=9604,
    president='-',
    sponsor='Recoletas Salud',
)
HISTORY = ("∙ El Club Baloncesto San Pablo Burgos, que compite como Recoletas Salud San Pablo "
           "Burgos, disputa la Liga Endesa 2026-27. Juega sus partidos en el Coliseum Burgos, "
           "con capacidad para 9.604 espectadores. Su cuerpo técnico lo forman Porfirio Fisac "
           "como primer entrenador y Fernando Merchante y Juan Nieto como ayudantes.")
COACH = ('Porfirio FISAC', 'Porfirio FISAC',
         "∙ Porfirio Fisac, entrenador español de 61 años, dirige al San Pablo Burgos en la "
         "temporada 2026-27.")
LOGO_CROP = None
