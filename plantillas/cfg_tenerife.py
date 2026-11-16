# La Laguna Tenerife 2026-27 -> sustituye a Caja San Fernando (equipo 9, 11 jugadores)
TI = 9
DATOS = 'tenerife'                    # carpeta en datos/ (creada con descargar.py)
FIXES = {20201760: {'first': 'Marcelinho', 'last': 'Huertas', 'nick': 'Marcelinho'},  # acb.com: 'Marcelo Tieppo'
         30001954: {'first': 'Ethan', 'last': 'Happ', 'nick': 'Ethan'}}                # acb.com: 'Itan Hap'
OLD_SHORT = 'Caja S.F.'
SCOREBOARD = '  TENERIFE  '          # 12 caracteres exactos

D = {
 # apellido             r1  r2  r3  r4  peso valor skin hair beard
 'Fitipaldo':        (80, 67, 67, 71,  80,  90, 0, 3, 3),
 'Guy':              (86, 78, 76, 80,  79, 140, 0, 1, 0),
 'Doornekamp':       (71, 63, 68, 71, 100,  40, 0, 3, 3),
 'Abromaitis':       (72, 68, 73, 74, 107,  60, 0, 3, 0),
 'Happ':             (78, 80, 87, 90, 107, 150, 0, 3, 0),
 'Huertas':          (79, 70, 67, 71,  85, 110, 0, 1, 0),
 'Shermadini':       (74, 88, 85, 84, 125, 120, 0, 1, 0),
 'Fernández':        (84, 74, 75, 80,  83,  70, 0, 3, 0),
 'Van Beck':         (81, 78, 74, 76,  88,  70, 0, 3, 1),
 'Hunter':           (67, 68, 73, 76, 106,  80, 1, 0, 3),
 'López-Arostegui':  (78, 74, 80, 81,  95, 110, 0, 3, 0),
}
# Titulares por partidos de inicio en la Liga 2026-27
ORDER = ['Fitipaldo', 'Guy', 'Doornekamp', 'Abromaitis', 'Happ',
         'Huertas', 'Shermadini', 'Fernández', 'Van Beck', 'Hunter', 'López-Arostegui']
SURNAME = {'Fernández': 'Fernández, J.'}

TEAM = dict(
    short_name='Tenerife',
    long_name='La Laguna Tenerife',
    club_name='Club Baloncesto Canarias S.A.D.',
    arena='Pabellón Santiago Martín',
    address='C/ Mercedes, s/n, Los Majuelos',
    capacity=5100,
    president='-',
    sponsor='-',
)
HISTORY = ("∙ El Club Baloncesto Canarias, que compite como La Laguna Tenerife, disputa la "
           "Liga Endesa 2026-27. Juega sus partidos en el Pabellón Santiago Martín de La "
           "Laguna, con capacidad para 5.100 espectadores. Su cuerpo técnico lo forman Jaka "
           "Lakovic como primer entrenador y Alberto Oliver, Juan Gatti y Ronald Comez como "
           "ayudantes.")
COACH = ('Jaka LAKOVIC', 'Jaka LAKOVIC',
         "∙ Jaka Lakovic, entrenador esloveno de 48 años, dirige al La Laguna Tenerife en la "
         "temporada 2026-27.")
LOGO_CROP = (0.0, 0.0, 1.0, 0.74)   # quita el texto "La Laguna Tenerife" de debajo del escudo
