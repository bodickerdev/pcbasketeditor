# Plantillas de la ACB 2026-27

Con estos scripts se pasan las plantillas de acb.com al juego: datos, estadísticas, retratos, escudo y nombre en el marcador.
Hay que ejecutarlos desde esta carpeta, en una terminal (por ejemplo, la de VS Code).

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `descargar.py` | Descarga de acb.com un equipo (plantilla, estadísticas, fotos y escudo) a `datos\<nombre>\` |
| `equipo.py` | Aplica la configuración de un equipo al juego |
| `cfg_<equipo>.py` | Configuración de cada equipo: qué jugadores entran, valoraciones, aspecto y datos del club |
| `datos\` | Copia de lo descargado en noviembre de 2026 (con las erratas de acb.com ya corregidas) |

## Usos habituales

**Cambiar valoraciones, el quinteto o el aspecto de un equipo**
1. Abre su `cfg_<equipo>.py`.
2. Cambia los números de `D` (valoraciones, peso, valor, piel, pelo, barba) o el orden de `ORDER` (los 5 primeros son los titulares).
3. Ejecuta `python equipo.py cfg_<equipo>.py`.

**Rehacer solo los retratos o solo el escudo**
```
python equipo.py cfg_<equipo>.py --solo-retratos
python equipo.py cfg_<equipo>.py --solo-escudo
```

**Actualizar un equipo con la plantilla nueva de acb.com**
```
python descargar.py https://acb.com/es/liga/equipos/unicaja-14 unicaja
```
Revisa el resumen que muestra y ajusta la configuración: si hay jugadores nuevos, añádelos a `D` y a `ORDER` en lugar de otros, porque el número de jugadores debe ser el mismo. Después ejecuta `equipo.py`.

**Probar sin tocar el juego**: copia `BASKET96.DBC`, `CARAS.BIN`, `ESCUDOS.BIN`, `MANAGER.DAT` y `CAMPO800.BIN`, con sus `.BAK`, a otra carpeta y añade `--prueba CARPETA`.

## Reglas que hay que respetar

- **Mismo número de jugadores.** Cada equipo debe tener los mismos jugadores que tenía en 1996 (entre 9 y 12). Si cambia, se desplazan los jugadores de todos los equipos siguientes del archivo.
- **Nombre del marcador (`SCOREBOARD`).** Tiene que tener exactamente 12 caracteres y conviene no usar tildes ni Ñ.
- **Letras admitidas.** Solo letras del alfabeto latino básico (Latin-1). `descargar.py` convierte las demás: ć pasa a c, š a s.
- **Extranjeros.** `equipo.py` marca como extranjeros a los de licencia EXT (extracomunitarios). Conviene que no haya más de 2 por equipo.

## Ajustes de los retratos

- **Pieles claras:** brillo 0,75, saturación 1,5, contraste 1,35 y sin grises en la paleta.
- **Pieles oscuras:** brillo 0,85, saturación 1,05, contraste 1,2, con la paleta completa.
- **Fotos especiales:** se pueden cambiar en la configuración con `LIGHT = (brillo, saturación, contraste)` y `DARK = (...)`. Por ejemplo, el Coruña y el Obradoiro tienen camisetas naranjas o luz cálida y usan menos saturación.

## Equipos

| cfg | Equipo 2026-27 | Hueco en el juego (equipo de 1996) |
|---|---|---|
| barca | Barça | 0 Barcelona |
| unicaja | Unicaja | 1 Unicaja |
| realmadrid | Real Madrid | 2 Real Madrid |
| manresa | Kids&Us Manresa | 3 TDK Manresa |
| baskonia | Kosner Baskonia | 4 Taugrés |
| andorra | MoraBanc Andorra | 5 Fuenlabrada |
| burgos | Recoletas Salud San Pablo Burgos | 6 Estudiantes |
| valencia | Valencia Basket | 7 Pamesa |
| coruna | Leyma Coruña | 8 León |
| tenerife | La Laguna Tenerife | 9 Caja San Fernando |
| obradoiro | Monbus Obradoiro | 10 Forum |
| murcia | UCAM Murcia | 11 Murcia |
| zaragoza | Casademont Zaragoza | 12 Cáceres |
| (a mano) | Asisa Joventut | 13 Joventut |
| lleida | iLERNA Lleida | 14 Xacobeo 99 |
| breogan | Río Breogán | 15 Granada |
| girona | FIATC Girona | 16 VALVI |
| bilbao | Surne Bilbao | 17 Gran Canaria |

El Joventut no tiene configuración porque lo editaste tú a mano. Sus datos descargados están en `datos\joventut\` por si quieres crearla.

# Equipos europeos 2026-27

Los 32 equipos europeos del juego (huecos 18-49) se rellenan con datos de la **API oficial de la Euroliga** (`api-live.euroleague.net`).

| Archivo | Para qué sirve |
|---|---|
| `descargar_europa.py` | Descarga clubes, clasificaciones, plantillas, estadísticas, escudos y fotos en `datos\europa\` |
| `europa.py` | Lo aplica al juego. `SLOTS`, al principio del archivo, dice qué club va en cada hueco y con qué colores |

```
python descargar_europa.py      (vuelve a descargar todo con los datos del día)
python europa.py                (o  --prueba CARPETA  para probar en una copia)
```

**Qué equipos entran.** Los 16 de la Euroliga que no son españoles (los españoles ya están en la sección ACB) y los 16 primeros de la Eurocup en la clasificación del día de la descarga.

**Qué hace con cada equipo:**
- **Jugadores.** Mete los N con más minutos, donde N es el número de jugadores que tenía el equipo en 1996, para no mover nada en el archivo. Los 5 con más partidos de titular forman el quinteto.
- **Fichas.** Dorsal, posición (deducida de la posición de la API y la altura), altura, peso, país y fecha de nacimiento, procedencia, estadísticas reales de la temporada y una biografía corta.
- **Valoraciones.** Se calculan con las estadísticas: PIR, minutos, asistencias, puntos, porcentajes, rebotes, robos, tapones y altura. Los de la Euroliga tienen +4 y los de la Eurocup −2.
- **Aspecto.** El color de piel se deduce del brillo de la cara en la foto y puede fallar. El pelo queda normal y castaño si la piel es blanca, y corto y negro si es negra o mulata. No se pone barba. Todo esto se corrige en el editor.
- **Caras pequeñas.** La de la pantalla previa al partido sale de la foto oficial.
- **Club.** Nombre, dirección, pabellón, presidente, entrenador, historia y nombre del marcador. La API no da el aforo, así que queda a 0.
- **Escudos.** Se ponen en el marcador (`ESCUDOS.BIN`), en `CARAS.BIN` (sale al anotar) y en los menús (`BASKET96.DGF`).
- **Equipaciones.** Los colores de casa de `SLOTS` son aproximados. La alternativa es blanca, o del color de los detalles si la principal ya es blanca. También se repintan las figuras del menú y se recalculan los choques de color.

# Estrellas NBA 2026-27

`nba.py` cambia los 21 jugadores del equipo «ESTRELLAS NBA» (hueco 50) por estrellas actuales. La lista y su aspecto (piel, pelo y barba) están en `PLAYERS`, al principio del archivo.

```
python nba.py                   (descarga de ESPN y aplica)
python nba.py --sin-descargar   (usa lo ya descargado en datos\nba\)
```

- **Fuente de datos.** La API pública de ESPN. La de nba.com no admite descargas automáticas.
- **Datos que se toman.** Equipo, dorsal, altura, peso, lugar y fecha de nacimiento, estadísticas y foto.
- **Valoraciones.** Usan la fórmula de `europa.py`. Se calculan con la temporada 2026-27 si el jugador lleva al menos 5 partidos; si no, con la 2025-26.
- **Selecciones.** El juego forma el partido Selección USA - Selección Europea **por el lugar en la lista**: jugadores 1-12 = USA y 13-21 = Europa. Cada grupo tiene su propio orden de plantilla y sus 5 primeros son los titulares.

# Jugadores con pocos datos

El simulador del juego usa las estadísticas de la temporada. Con 1 o 2 partidos, o con 0 de 0 en tiros libres, el jugador rinde mal o de forma extraña.
`python completar_estadisticas.py` suma, a los datos reales de esos jugadores, sus medias habituales hasta llegar a 10 partidos (y al menos 3):
- **ACB:** medias de su carrera en la ACB.
- **Europa:** medias típicas de su posición.
- **NBA:** medias de su temporada 2025-26.

Conviene ejecutarlo después de cargar plantillas nuevas. Con `--solo-listar` muestra a quién afectaría sin cambiar nada.

# Valoraciones (ajuste fino)

`valoraciones.py` recalcula las 4 valoraciones de todos los jugadores (ACB, Europa y All-Star NBA) con la escala del juego de 1996.
No toca el Joventut, porque lo editaste a mano. Para incluirlo, añade `--incluir-joventut`.

```
python descargar_historial.py          (historial ACB de acb.com y Euroliga/Eurocup de 2023-24 a 2026-27)
python valoraciones.py --solo-listar   (muestra antes -> después sin cambiar nada)
python valoraciones.py                 (aplica al juego y actualiza los cfg_*.py)
```

**Hay que ejecutarlo al final**, después de `equipo.py`, `europa.py` o `nba.py`. Los dos últimos ponen sus propias valoraciones, que son más simples.

**Qué tiene en cuenta:**
- **Temporadas.** La actual y la pasada pesan más; las anteriores (el historial) pesan poco. Cada temporada cuenta según sus minutos jugados.
- **Competiciones.** ACB, Euroliga, Eurocup y NBA, cada una con un factor de nivel: Euroliga 1,00, ACB 0,95, Eurocup 0,90 y NBA 0,70. El de la NBA es bajo porque allí se juega más rápido y la PIR sale inflada.
- **Edad.** Las temporadas antiguas se corrigen con una curva de edad: los jóvenes han mejorado desde entonces y los veteranos han bajado.
- **Calidad general.** Es la PIR por 40 minutos, corregida por posición (si no, los pívots saldrían inflados por los rebotes), más los minutos por partido, que reflejan la confianza del entrenador.
- **Pocos datos.** Un jugador casi sin minutos se acerca a nivel de suplente.
- **Reparto entre las 4.** Imita el de 1996. La r1 (manejo/pase) depende mucho de las asistencias, los triples y la posición; la r2 (tiro), de los puntos y la eficiencia. La r3 y la r4 son casi la calidad general, con un poco de rebote o de defensa.

El detalle por jugador (antes -> después, PIR/40, minutos y temporadas usadas) queda en `valoraciones_informe.txt`.
Las valoraciones anteriores están guardadas en `BASKET96.DBC.antes_valoraciones` y en `cfg_antes_valoraciones\`.

# Euroliga del mánager

Los 24 equipos de la Euroliga del mánager no salen de la clasificación: están fijos en `BASKET4.DAT` (posición 0xA5484, 4 grupos de 6).
`python euroliga.py` pone a Valencia, Barça, Real Madrid y Baskonia (uno por grupo), a los 16 clubes no españoles de la Euroliga y a los 4 primeros de la Eurocup. Los grupos se reparten por nivel.
Con `--solo-listar` muestra los grupos sin tocar nada. El original está en `BASKET4.DAT.BAK`. Solo vale para **ligas nuevas**, porque cada partida guarda su propia copia de la lista.

`clasificacion.py` pone en el palmarés la posición de cada equipo en la ACB 2025-26, pero el juego **no** la usa para la Euroliga.
