# Kosner Baskonia 2026-27 -> sustituye a Taugrés (equipo 4, 11 jugadores)
TI = 4
DATOS = 'baskonia'                    # carpeta en datos/ (creada con descargar.py)
FIXES = {30005346: {'first': 'Dwayne', 'last': 'Stewart Jr'},   # acb.com: 'Devvajne Stevvart Jr'
         30005375: {'birthPlace': 'Toronto'}}                      # acb.com: 'Toronto (Canada)'
OLD_SHORT = 'Taugrés'
SCOREBOARD = '  BASKONIA  '          # 12 caracteres exactos

D = {
 # apellido (acb.com)  r1  r2  r3  r4  peso valor skin hair beard
 'Baugh':        (73, 61, 68, 74,  88, 110, 1, 1, 1),
 'Simmons':      (84, 79, 77, 80,  88, 150, 1, 1, 1),
 'Stewart Jr':   (73, 67, 71, 75,  93, 140, 1, 1, 3),
 'Lawson':       (76, 68, 72, 74,  90, 140, 2, 3, 3),
 'Faried':       (72, 73, 82, 82, 104, 130, 1, 3, 3),
 'Spagnolo':     (80, 71, 75, 78,  88, 130, 0, 3, 1),
 'Theoret':      (87, 81, 79, 83,  90, 130, 2, 3, 3),
 'Joksimovic':   (66, 56, 65, 69,  88, 160, 0, 3, 0),
 'Frisch':       (76, 70, 76, 78, 100,  80, 0, 3, 1),
 'Kurucs':       (76, 71, 79, 80, 100, 110, 0, 3, 1),
 'Sedekerskis':  (81, 78, 84, 83, 103, 120, 0, 1, 1),
}
# Titulares por partidos de inicio (y minutos) en la Liga 2026-27
ORDER = ['Baugh', 'Simmons', 'Stewart Jr', 'Lawson', 'Faried',
         'Spagnolo', 'Theoret', 'Joksimovic', 'Frisch', 'Kurucs', 'Sedekerskis']
SURNAME = {'Stewart Jr': 'Stewart'}

TEAM = dict(
    short_name='Baskonia',
    long_name='Kosner Baskonia',
    club_name='Saski Baskonia S.A.D.',
    arena='Fernando Buesa Arena',
    address='Ctra. Zurbano, s/n, Vitoria',
    capacity=15504,
    president='-',
    sponsor='Kosner',
)
HISTORY = ("∙ Saski Baskonia, que compite como Kosner Baskonia, disputa la Liga Endesa "
           "2026-27. Juega sus partidos en el Fernando Buesa Arena de Vitoria, con capacidad "
           "para 15.504 espectadores. Su cuerpo técnico lo forman Velimir Perasovic como primer "
           "entrenador y Juan Pin, Xabier Aspe y Miguel Hoyo como ayudantes.")
COACH = ('Velimir PERASOVIC', 'Velimir PERASOVIC',
         "∙ Velimir Perasovic, entrenador croata de 61 años, dirige al Kosner Baskonia en la "
         "temporada 2026-27. Ya formó parte del club como jugador a mediados de los años 90.")
LOGO_CROP = (0.0, 0.17, 1.0, 1.0)   # quita el texto "kosner" de encima del escudo
