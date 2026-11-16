# Formato de BASKET96.DBC (PC Basket 4.5)

Esta es la base de datos única del juego: equipos, entrenadores y jugadores de la ACB, de Europa y de las "Estrellas NBA".
La usan tanto la base de datos (`BASKET4.DAT`) como el mánager y el simulador (`MANAGER.DAT`).
Pesa 1.425.593 bytes y contiene 51 equipos y 574 jugadores.

`BASKET96.DGF` solo guarda imágenes de 16 colores (fotos, escudos). El DBC apunta a ellas con offsets u32.

## Convenciones

| Tipo | Codificación |
|---|---|
| `pstr` | 1 byte de longitud (sin cifrar) + texto con **XOR 0x61** byte a byte |
| `lines` | `u16` nº de líneas + N × `pstr` (biografías e historias, ~72 caracteres por línea) |
| `u8/u16/u32` | little-endian, sin cifrar |
| Juego de caracteres | Nombres en Latin-1 (ñ=F1, ú=FA). Textos largos en CP437 (ó=A2, ñ=A4, viñeta ∙=F9) |

**No hay índice de offsets.** Todo se lee de forma secuencial, así que las cadenas pueden cambiar de longitud.
Ningún ejecutable ni archivo de datos contiene una tabla de offsets del DBC.

## Estructura general

```
0x00  "PC BASKET v4.5 Copyright (c)1996 Dinamic Multimedia\n"  (0x34 bytes)
0x34  u16 = 15   (sin identificar; se conserva)
0x36  Equipo × 51   (18 ACB, 32 Europa, 1 All-Star; ese orden)
fin   32 bytes = 8 × u32 punteros a DGF (sin identificar; se conservan)
```

No hay contador de equipos. El tipo de equipo cambia el número de punteros gráficos y la presencia de estadísticas:

| Sección | Punteros gfx | Estadísticas de equipo |
|---|---|---|
| ACB (Barcelona … Gran Canaria) | 12 | sí (15 × u16) |
| Europa (Olympiakos … Estrella Roja) | 9 | no |
| All-Star ("ESTRELLAS NBA", 21 jugadores) | 2 | no |

En el All-Star, los **jugadores 1-12 forman la Selección USA y los 13-21 la Selección Europea** (partido USA - Europa). Cada grupo numera su propio orden de plantilla (byte 10) desde 1. Europa solo tiene 9 jugadores: el juego la completa hasta 12 con 3 jugadores de los equipos europeos. Los números de orden de 1996 para Europa son 1-6, 8, 10 y 12.

**Las fichas del All-Star tienen que ser mínimas, como en 1996:** biografía de una línea («∙»), lugar y fecha de nacimiento «-» y procedencia «-». Si se rellenan, el mánager (`BASKET4.DAT`) desborda la memoria y el nombre del 7.º europeo de la pantalla All Stars sale con basura («OT», «ERS»). Está comprobado en el juego. Nombres, posiciones, valoraciones, estadísticas, equipo NBA y caras no dan problemas.

## Equipo

| Campo | Tipo | Ejemplo |
|---|---|---|
| nombre corto (menús) | pstr | `Barcelona` |
| nombre largo | pstr | `Unicaja Málaga` |
| punteros gráficos | 12/9/2 × u32 | offsets en DGF |
| nombre oficial | pstr | `Fútbol Club Barcelona` |
| dirección | pstr | `Avda. Arístides Maillol s/n` |
| pabellón | pstr | `Palau Blaugrana` |
| aforo | u16 | 8000 |
| presidente | pstr | |
| patrocinador | pstr | `BANCA CATALANA` |
| presupuesto | u32 | 1.551.000.000 (pesetas) |
| historia | lines | |
| nombre (repetido) | pstr | |
| palmarés | 26 bytes | byte 1 = ligas (Madrid 27, Barça 9, Joventut 4); el resto sin decodificar |
| estadísticas | 15 × u16 | solo ACB; mismo orden que las del jugador |
| entrenador | pstr nombre, pstr nombre corto, 2 × u32 gfx, lines bio | |
| nº de jugadores | u8 | 9–12 (21 en el All-Star) |
| jugadores | Jugador × N | |

## Jugador

| Campo | Tipo | Notas |
|---|---|---|
| nombre completo | pstr | `Rafael JOFRESA Prats` |
| nombre corto | pstr | `Rafa JOFRESA` |
| apellido / listado | pstr | `Jofresa, R.` |
| gráficos | 2 × u32 | foto 380×182 y **cara pequeña 24×24** de la pantalla previa al partido, en DGF (1 = ninguna) |
| biografía | lines | los extranjeros tienen 1 línea vacía |
| **dorsal** | u8 | |
| **posición** | u8 | 0 base, 1 escolta, 2 alero, 3 ala-pívot, 4 pívot |
| **altura** | u8 | **cm − 100** (Muresan 131 → 2,31 m) |
| **peso** | u8 | kg |
| lugar de nacimiento | pstr | `-` si se desconoce |
| fecha de nacimiento | pstr | `dd-mm-aa` o `-` |
| valor | u16 | millones de pesetas (Arlauckas 220) |
| procedencia | pstr | `Joventut (96)` |
| atributos | 21 bytes | ver abajo |
| equipo actual | pstr | |
| temporada actual | 30 × u16 | |
| historial | N × (`u8` año, `pstr` equipo, 30 × u16) | año 95 = 95-96 |
| fin | `0xF0` | |

### Los 21 bytes de atributos

| Byte | Significado | Seguridad |
|---|---|---|
| 0 | extranjero (0/1) | alta |
| 1 | **color de piel** (0 blanco, 1 negro, 2 = 3 casos) | alta |
| 2 | pelo (0 calvo: Jordan, Barkley, Shaq; 1 corto; 3 normal) | media |
| 3 | 0/1/2 (¿color de pelo?) | baja |
| 4 | 0/1 (desconocido) | — |
| 5 | barba/bigote (Olajuwon = 3) | media |
| 6 | valoración 1 (0-100): manejo/pase (Stockton 95, Laso 92) | media |
| 7 | valoración 2: tiro/ataque (Jordan 99, Mike Smith 95) | media |
| 8 | valoración 3: rebote/interior (Shaq 98, Sabonis 94) | media |
| 9 | valoración 4: defensa/físico (Ismael Santos 93) | media |
| 10 | orden en la plantilla; 1-5 = quinteto titular | alta |
| 11-18 | 8 parámetros del simulador (escala 1-7); el 12 sigue a la posición/altura | baja |
| 19 | flag 0/1 (27 jugadores) | — |
| 20 | siempre 0 | — |

Las etiquetas de las valoraciones se han deducido correlacionando los valores con las estadísticas reales.
Hay que confirmarlas en la ficha del mánager.

### Las 30 estadísticas de una temporada

> **El simulador del mánager las usa (deducido, sin confirmar en el juego).** En 1996, los jugadores europeos y los de la NBA no tenían estadísticas reales de la ACB. Aun así, los programadores les inventaron unas con el formato «100 intentos y 100 partidos»: por ejemplo, Stockton tiene 77/100 en T2, 72/100 en T3 y 95/100 en TL. Por tanto, los porcentajes y las medias de la temporada actual deben de servir para decidir cuánto tira y acierta cada jugador.
> Un jugador con todo a cero apenas anota. `equipo.py` y `europa.py` ya no dejan a nadie a cero: si el jugador aún no ha jugado, ponen sus medias de carrera o las típicas de su posición.

Son 15 de Liga Regular seguidas de 15 de Play-off, en este orden:
T2 conseguidos, T2 intentados, T3 conseguidos, T3 intentados, TL conseguidos, TL intentados,
rebotes defensivos, rebotes ofensivos, asistencias, tapones, balones robados, balones perdidos,
minutos, partidos, faltas personales.

## CARAS.BIN: retratos del partido

Son 252 imágenes seguidas. Cada una es `u16 ancho, u16 alto` + ancho×alto bytes, con 1 byte por píxel (índice de paleta).
Todas miden 24×24 y el archivo no tiene cabecera.

- La paleta del partido está al final de `CAMPO800.BIN`, que es un PCX de 800×480: byte `0x0C` + 768 bytes RGB.
- **0–215:** retratos de jugadores ACB. Imagen = `índice_equipo × 12 + posición del jugador en el equipo dentro del DBC`.
  Se ha comprobado con el Unicaja y el Real Madrid. Los retratos del Joventut son de una plantilla anterior y no coinciden.
- **216–248:** escudos que salen al anotar un equipo no ACB. Imagen = `216 + (índice_equipo − 18)`; Panathinaikos es la 217 y la 248 es "All Stars".
- **249–251:** sin uso.
- Retrato entero del color 180 (casi negro) = sin foto. Entero del color 105 (blanco) = hueco sin jugador.
- Si se mueve, añade o quita un jugador de un equipo ACB, su retrato no le sigue: el retrato va ligado a la posición.

## ESCUDOS.BIN: escudos de los equipos

Son 54 imágenes seguidas. Cada una es `u16 ancho (44), u16 alto (46), u32 tamaño (2024)` + píxeles, con la misma paleta que CARAS.BIN y fondo de color 0.
El orden es el de los equipos del DBC (0-50); después van Selección Europea, USA y ACB.

## Nombres de equipo en el marcador (MANAGER.DAT)

Están fijos en el ejecutable, no en el DBC: 53 nombres de **12 caracteres** centrados con espacios, seguidos, a partir de `" BARCELONA  "`.
El orden es el del DBC. Se pueden cambiar sin riesgo si se sustituye por un texto de exactamente 12 caracteres.

## Otros archivos

- `DATAFA.TMP` lo genera el juego al empezar un partido (nombre de 16 caracteres + 183 bytes por jugador). No hay que editarlo.
- Las partidas de `SAVE*/LIGAS*.DAT` no contienen copias legibles de los jugadores (parecen comprimidas). Lo más seguro es probar las ediciones en una liga nueva.
- Los archivos vienen del CD como solo lectura. `dbc.py` quita ese atributo al guardar y crea `BASKET96.DBC.BAK`.

## BASKET96.DGF: gráficos de la base de datos y de los menús

Imágenes de 16 colores apuntadas desde el DBC con offsets u32 (`Team.gfx`, `Player.gfx`, `Coach.gfx`). Cada imagen tiene:
- **Cabecera de 58 bytes:** `u16 0x0010` (nº de colores), 48 bytes de paleta, `u8 0x01`, `u8 ancho`, `u16 alto` (big-endian), `u16 planos = 4` (big-endian) y 2 bytes sin identificar.
- **Datos:** alto × 4 planos × ⌈ancho/8⌉ bytes, entrelazados por línea, seguidos de 1 byte.
- **Paleta:** es la global del juego. Los colores 0 y 3-15 son fijos; el 1 y el 2 cambian según la pantalla.

Gráficos de cada equipo ACB (12 punteros):

| k | Contenido |
|---|---|
| 0 / 1 | Escudo grande y su máscara (15 = visible, 0 = transparente) |
| 2 / 3 | Escudo mediano y su máscara (pantalla de elegir equipo) |
| 4 / 5 | Escudo pequeño y su máscara, que mide 2 px más para el contorno (clasificación y calendario) |
| 6 | Foto del pabellón (188×140) |
| 7 | Camiseta |
| 8-11 | Figuras con las equipaciones |

Hay que mantener el ancho y el alto de cada imagen, porque el DBC apunta a posiciones fijas. Está implementado en `EDITOR/dgf.py`.

## Equipaciones

### En el partido (MANAGER.DAT)

Los sprites de los jugadores (`*.EMP`) son imágenes de 8 bits sin comprimir: bloques `u16 ancho, u16 alto, u32 tamaño` + píxeles.
Usan los índices **1-48 para la ropa** y **49-55 para la piel**. Al empezar el partido, el juego copia 48 bytes del equipo en la tabla de traducción de colores de cada jugador. Después añade 7 bytes de piel, que salen de unos punteros en `0x1A4CC` del objeto de datos.

- **Tabla de equipaciones:** archivo `0x53444` (objeto 2 + `0x1AC44`). Tiene 48 bytes por registro con índices de la paleta del partido.
  - Registros 0-52: equipación principal, en el orden del marcador (18 ACB, 32 Europa, Sel. Europea, Equipo USA y Equipo ACB).
  - Registros 53-105: equipación alternativa del equipo *n*, que es el registro 53 + *n*. La tabla `0x552A4` (alt[*n*] = *n*) da ese número.
- **Matriz de choques:** archivo `0x552E4`, de 64 × 64 bytes. Si `choque[local × 64 + visitante] ≠ 0`, el visitante se pone la alternativa. Está hecha a mano. El editor solo recalcula la fila y la columna del equipo que se cambia.
- Hay una 2.ª tabla en objeto 2 + `0x1C054` que solo se usa cuando `[0x5498] == 4`. Es un modo especial que no está identificado y no se toca.

Qué pinta cada uno de los 48 bytes (comprobado coloreando los sprites):

| Bytes | Zona |
|---|---|
| 0-4 | Camiseta, mitad 1 (gama de 5 tonos, de claro a oscuro) |
| 15-19 | Camiseta, mitad 2 |
| 5-9 y 36-40 | Número y dibujos del pecho 1 |
| 10-14 y 41-45 | Número y dibujos del pecho 2 |
| 20 | Cuello |
| 21 | Sisas y bajo de la camiseta |
| 46-47 | Costados de la camiseta |
| 22-26 | Pantalón |
| 27 / 28 | Franja / bajo del pantalón |
| 29-35 | Calcetines y zapatillas (el editor no los cambia) |

Solo se usan colores que ya aparecen en la tabla original, porque otras zonas de la paleta pueden cambiar según el pabellón.

### En los menús (BASKET96.DGF)

Cada equipo ACB tiene la camiseta (gfx 7) y 4 figuras con la equipación (gfx 8-11), en 16 colores.
La paleta de 16 colores no tiene morado ni azul celeste. Los colores 1 y 2 cambian según la pantalla.
El editor recolorea a partir de las imágenes de `BASKET96.DGF.BAK`:
- Camiseta: filas hasta el 44,5 % de la altura. Pantalón: hasta el 58,8 %.
- Solo cambia los píxeles que varían de un equipo a otro.

## Caras de la pantalla previa al partido (BASKET96.DGF)

Cada jugador ACB tiene una cara de 24×24 en 16 colores, a la que apunta su 2.º puntero gráfico. Es distinta del retrato de `CARAS.BIN`.
En esa pantalla, los colores 1 y 2 son tonos de piel: (252,208,156) y (212,120,96). El resto de colores son la paleta fija. Las caras originales usan solo los colores 0, 1, 2, 3, 4, 8, 11 y 12-15. Una cara toda negra significa que el jugador no tiene foto.
Al guardar, el editor convierte a estas caras los retratos de `CARAS.BIN` que ya no son los de 1996 (`caras.sync_small_faces`).

## Partidas guardadas del mánager (SAVE*/LIGAS*.DAT)

El juego escribe el archivo solo cuando el usuario pulsa «Guardar». Mide unos 74 KB. Lo que se conoce hasta ahora:

| Offset | Tamaño | Contenido |
|---|---|---|
| `0x0000` | u32 | Año de la temporada (2026) |
| `0x000C` | texto | Nombre de la liga |
| `0x0020` | 612 | Calendario: 34 jornadas × 9 partidos, como pares de equipos 0-17 |
| `0x0280` | 4 | Títulos de la temporada anterior: `+1` campeón de liga, `+3` subcampeón (comprobado: Breogán campeón y Real Madrid subcampeón; `+0` y `+2`, sin identificar, quizá la Copa del Rey). Al empezar una liga valen `03 01 0C 00`, los de 1995-96 |
| `0x0286` | u8 | Jornada que toca jugar: 1 al empezar, así que las jugadas son este valor menos 1 |
| `0x051C` | 50 × `0x52C` | Un bloque por equipo, en el mismo orden que el DBC |
| `0x11452` | 122 | Cuadro de playoffs (ver abajo) |
| `0x119E2` | 612 | Resultados de la liga regular: 34 jornadas × 9 partidos × 2 bytes. Cada par es el tanteo del 1.º y del 2.º equipo, en el mismo orden que el calendario. 0-0 = sin jugar |
| final − 4 | 4 | Copa de Europa: campeón, subcampeón, ?, `0x28`. `FF` = sin decidir. Antes van la Final Four (semis, 3.er puesto y final: 2 equipos + 2 × u16 cada una) y el resto de la competición, de longitud variable |

Dentro de cada bloque de equipo:

| Offset | Contenido |
|---|---|
| `+0x0C` | Nombre del mánager. `" Ordenador "` indica un equipo de la CPU |
| `+0x38` | 12 jugadores de `0x68` bytes cada uno. Si el primer byte es `0xFF`, la lista termina ahí |

Cada jugador empieza así: `+0` índice del jugador en su equipo **original** del DBC, `+1` equipo original, `+2` dorsal. Con eso se ven los traspasos: un jugador cuyo equipo original no coincide con el bloque en el que está ha sido fichado.

Estadísticas del jugador: tres bloques de 24 bytes, `+0x20` liga regular, `+0x38` playoffs y `+0x50` Europa. Cada uno tiene 10 × u16 (robos, TL anotados, T2 anotados, T3 anotados, TL intentados, T2 intentados, T3 intentados, rebotes, tapones, asistencias) y un u32 con el tiempo jugado en centésimas de segundo. Puntos = TL + 2·T2 + 3·T3. La suma por equipo da un 85 % de los puntos de los marcadores; el reparto entre jugadores sirve igual para los líderes. Al pasar de temporada se ponen a cero.

Cuadro de playoffs (`0x11452`): 4 cuartos (2 equipos + 3 partidos, al mejor de 3), 2 semifinales y la final (2 equipos + 5 partidos, al mejor de 5). Cada partido son 2 × u16 con el tanteo de cada equipo; `FFFF` = sin jugar. El cuadro solo vale cuando ha terminado la liga regular: antes tiene restos, y al empezar la temporada siguiente se rellena con `00 07 03 04 01 06 02 05`. En ese momento el campeón queda en `0x0281` y el subcampeón en `0x0283`.

Al empezar una liga, el juego carga como máximo **11 jugadores** por equipo: el 12.º del DBC no aparece en la liga.

Con el calendario y los resultados se calcula el balance de cada equipo. Se ha comprobado con 9 partidas: no hay empates ni jornadas a medias.

Los logros (`logros.py`) usan este formato. El progreso se guarda en `LOGROS.JSON`, en la carpeta del juego.

### La liga en memoria (RetroArch + DOSBox Pure)

Mientras se juega, la liga está en la memoria del juego con casi el mismo formato que el archivo, así que los logros saltan sin guardar (`logros_mem.py`, solo lectura). Las posiciones son relativas al «ancla», que corresponde al offset `0x284` del archivo:

| En memoria | Equivale en el archivo | Contenido |
|---|---|---|
| ancla | `0x0284`-`0x1078C` | Bloque entero y en el mismo orden: `D0 07`, jornada y los 50 bloques de equipo |
| ancla − `0xE3E8` | `0x0020`-`0x0283` | Calendario y títulos de la temporada anterior |
| detrás de la serie `01`..`31` (≈ ancla − `0xDD116`) | `0x11452` | Cuadro de playoffs |
| cuadro + `0xAE0` | final − 4 | Campeón y subcampeón de la Copa de Europa, `0x28` |
| ancla − `0xE704` | `0x119E2` | Resultados |

El ancla se localiza buscando la serie de bloques de equipo («Ordenador» cada `0x52C` bytes). Las direcciones absolutas cambian en cada arranque de RetroArch. El resultado de una jornada aparece en memoria cuando se termina de simular la jornada entera, no al acabar tu partido.
