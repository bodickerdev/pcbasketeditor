# Leyma Coruña 2026-27 -> sustituye a Baloncesto León (equipo 8, 10 jugadores)
TI = 8
DATOS = 'coruna'                    # carpeta en datos/ (creada con descargar.py)
OLD_SHORT = 'León'
SCOREBOARD = '   CORUNA   '          # 12 caracteres; sin Ñ por la fuente del marcador

D = {
 # apellido (acb.com)  r1  r2  r3  r4  peso valor skin hair beard
 'Verge Jr':     (79, 70, 73, 78,  86, 150, 1, 3, 1),
 'Jorgensen':    (74, 64, 68, 72,  84,  80, 0, 1, 1),
 'Uleckas':      (75, 70, 77, 79,  98, 110, 0, 3, 1),
 'Silins':       (60, 59, 65, 67, 110,  80, 0, 3, 0),
 'Conditt IV':   (72, 77, 81, 83, 104, 110, 2, 3, 3),
 'De Souza':     (73, 62, 65, 70,  85,  60, 0, 3, 0),
 'Radoncic':     (68, 64, 74, 76, 102,  60, 0, 1, 1),
 'Dimsa':        (68, 58, 64, 68,  92,  50, 0, 1, 0),
 'Skapintsev':   (60, 59, 70, 70, 118,  60, 0, 1, 0),
 'Díaz':         (65, 58, 66, 69, 100,  40, 0, 3, 1),
}
# Titulares por partidos de inicio en la Liga 2026-27
ORDER = ['Verge Jr', 'Jorgensen', 'Uleckas', 'Silins', 'Conditt IV',
         'De Souza', 'Radoncic', 'Dimsa', 'Skapintsev', 'Díaz']
SURNAME = {'Verge Jr': 'Verge', 'Conditt IV': 'Conditt', 'Díaz': 'Díaz, J.'}

TEAM = dict(
    short_name='Coruña',
    long_name='Leyma Coruña',
    club_name='Básquet Coruña',
    arena='Coliseum',
    address='C/ Francisco Pérez Carballo, 2',
    capacity=9300,
    president='-',
    sponsor='Leyma',
)
HISTORY = ("∙ Básquet Coruña, que compite como Leyma Coruña, disputa la Liga Endesa 2026-27. "
           "Juega sus partidos en el Coliseum de A Coruña, con capacidad para 9.300 "
           "espectadores. Su cuerpo técnico lo forman Carles Marco como primer entrenador y "
           "Román Gómez y Carlos Penedo como ayudantes.")
COACH = ('Carles MARCO', 'Carles MARCO',
         "∙ Carles Marco, entrenador español de 52 años, dirige al Leyma Coruña en la "
         "temporada 2026-27.")
LOGO_CROP = None

# Camisetas naranjas: tiñen la cara, menos saturación
LIGHT = (0.75, 1.3, 1.35)
DARK = (0.85, 1.1, 1.2)
