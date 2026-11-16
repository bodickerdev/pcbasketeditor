# Real Madrid 2026-27 -> sustituye al Real Madrid de 1996 (equipo 2, 12 jugadores)
TI = 2
DATOS = 'realmadrid'                    # carpeta en datos/ (creada con descargar.py)
OLD_SHORT = 'Real Madrid'
SCOREBOARD = 'REAL MADRID '          # 12 caracteres exactos (igual que el original)

D = {
 # apellido (acb.com)  r1  r2  r3  r4  peso valor skin hair beard
 'Feliz':      (87, 78, 81, 83,  88, 150, 1, 3, 1),
 'Maledon':    (94, 90, 86, 89,  91, 200, 2, 1, 1),
 'Abalde':     (79, 71, 75, 77,  95, 110, 0, 1, 0),
 'Pradilla':   (83, 80, 88, 87, 103, 120, 0, 3, 0),
 'Tavares':    (77, 87, 93, 93, 120, 230, 2, 1, 1),
 'Campazzo':   (94, 80, 78, 84,  88, 200, 0, 3, 3),
 'Llull':      (75, 62, 64, 68,  87, 150, 0, 3, 3),
 'Luwawu':     (90, 89, 85, 87,  98, 180, 2, 1, 3),
 'Deck':       (77, 73, 78, 78, 105, 150, 0, 1, 0),
 'Okeke':      (78, 70, 78, 81, 104, 100, 2, 1, 1),
 'Jantunen':   (76, 71, 77, 77, 105, 120, 0, 3, 1),
 'Sarr':       (63, 63, 69, 70, 109, 110, 2, 3, 3),
}
# Titulares por partidos de inicio en la Liga 2026-27
ORDER = ['Feliz', 'Maledon', 'Abalde', 'Pradilla', 'Tavares',
         'Campazzo', 'Llull', 'Luwawu', 'Deck', 'Okeke', 'Jantunen', 'Sarr']
SURNAME = {}

TEAM = dict(
    short_name='Real Madrid',
    long_name='Real Madrid',
    club_name='Real Madrid Club de Fútbol',
    arena='Movistar Arena',
    address='Av. Felipe II, s/n',
    capacity=13109,
    president='-',
    sponsor='-',
)
HISTORY = ("∙ La sección de baloncesto del Real Madrid disputa la Liga Endesa 2026-27. Juega "
           "sus partidos en el Movistar Arena de Madrid, con capacidad para 13.109 "
           "espectadores. Su cuerpo técnico lo forman Pedro Martínez como primer entrenador y "
           "Francisco Redondo, Salvador Camps e Isidoro Calín como ayudantes.")
COACH = ('Pedro MARTINEZ', 'Pedro MARTINEZ',
         "∙ Pedro Martínez, entrenador español de 65 años, dirige al Real Madrid en la "
         "temporada 2026-27.")
LOGO_CROP = None
