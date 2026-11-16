# MoraBanc Andorra 2026-27 -> sustituye a Fuenlabrada (equipo 5, 11 jugadores)
TI = 5
DATOS = 'andorra'                    # carpeta en datos/ (creada con descargar.py)
OLD_SHORT = 'Fuenlabrada'
SCOREBOARD = '  ANDORRA   '          # 12 caracteres exactos

D = {
 # apellido (acb.com)     r1  r2  r3  r4  peso valor skin hair beard
 'Akinjo':           (83, 69, 74, 79,  82, 140, 1, 1, 1),
 'Robertson':        (78, 71, 71, 74,  86, 100, 2, 1, 1),
 'Iwundu':           (74, 67, 72, 75,  88, 100, 1, 3, 1),
 'McGriff':          (66, 58, 68, 70, 100,  80, 1, 1, 1),
 'Radosevic':        (62, 60, 68, 68, 113,  50, 0, 3, 0),
 'Pustovyi':         (69, 82, 82, 83, 120,  90, 0, 3, 0),
 'Kuric':            (76, 71, 69, 73,  89,  50, 0, 1, 0),
 'Best':             (74, 65, 69, 71,  88,  50, 1, 3, 3),
 'Mutic':            (65, 57, 68, 69, 100,  30, 0, 0, 3),
 'Luz':              (78, 65, 71, 75,  82,  40, 0, 0, 0),
 'Andronikashvili':  (64, 51, 58, 62,  88,  30, 0, 1, 1),
}
# Titulares por partidos de inicio en la Liga 2026-27
ORDER = ['Akinjo', 'Robertson', 'Iwundu', 'McGriff', 'Radosevic',
         'Pustovyi', 'Kuric', 'Best', 'Mutic', 'Luz', 'Andronikashvili']
SURNAME = {}

TEAM = dict(
    short_name='Andorra',
    long_name='MoraBanc Andorra',
    club_name='Bàsquet Club Andorra',
    arena='Pavelló Toni Martí',
    address='C/ Baixada del Molí, 31-35',
    capacity=5001,
    president='-',
    sponsor='MoraBanc',
)
HISTORY = ("∙ El Bàsquet Club Andorra, que compite como MoraBanc Andorra, disputa la Liga "
           "Endesa 2026-27. Juega sus partidos en el Pavelló Toni Martí de Andorra la Vella, "
           "con capacidad para 5.001 espectadores. Su cuerpo técnico lo forman Zan Tabak como "
           "primer entrenador y Francisco Vázquez y Alejandro González como ayudantes.")
COACH = ('Zan TABAK', 'Zan TABAK',
         "∙ Zan Tabak, entrenador croata de 56 años, dirige al MoraBanc Andorra en la "
         "temporada 2026-27.")
LOGO_CROP = (0.0, 0.0, 1.0, 0.72)   # deja solo el yeti, sin el texto de debajo

# Menos saturación: con la de por defecto salían anaranjadas
LIGHT = (0.75, 1.2, 1.35)
DARK = (0.85, 1.05, 1.2)
