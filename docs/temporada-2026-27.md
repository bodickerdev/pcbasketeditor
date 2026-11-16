# Temporada 2026-27

[← Volver al inicio](../README.md)

Esta página describe lo que cambia la actualización. Los datos son de **noviembre de 2026**.

## Liga Endesa (18 equipos)

Barcelona, Unicaja, Real Madrid, Manresa, Baskonia, Andorra, Burgos, Valencia, Coruña, Tenerife, Obradoiro, Murcia, Zaragoza, Joventut, Lleida, Breogán, Girona y Bilbao.

Cada equipo incluye:
- La plantilla real de acb.com, con dorsales, posiciones, altura, peso, fecha y lugar de nacimiento, y procedencia.
- Las estadísticas de la temporada en curso y la trayectoria anterior.
- Valoraciones calculadas a partir del historial real (ver más abajo).
- Retratos del marcador hechos con las fotos oficiales.
- Escudo, nombre en el marcador, colores de la equipación, entrenador, pabellón y datos del club.

## Europa (32 equipos)

Ocupan los huecos de los equipos europeos de 1996. Los datos vienen de la web oficial de la Euroliga.

**Euroliga (16 clubes no españoles):** Panathinaikos, Olympiacos, Estrella Roja, Fenerbahçe, Zalgiris, Dubai, Hapoel Tel Aviv, Partizan, Anadolu Efes, Besiktas, Paris, ASVEL, Virtus Bolonia, Maccabi, Bayern Múnich y Olimpia Milán.

**EuroCup (16 clubes no españoles):** Hapoel Jerusalén, Napoli, Bahçesehir, Aris, Tofas, PAOK, London Lions, Buducnost, Maxima Roma, Le Mans, Chemnitz, Reyer Venecia, Ulm, Türk Telekom, Tortona y Roma Basket.

Cada equipo conserva el mismo número de jugadores que tenía en 1996, que es lo que exige el juego. Por eso algunas plantillas no incluyen a todos sus jugadores.

## Euroliga del modo mánager

En el juego original los participantes de la Euroliga eran una **lista fija** de 24 equipos, que no dependía de la clasificación. Con las plantillas nuevas eso hacía que, por ejemplo, Burgos o Tenerife jugaran la Euroliga. La actualización cambia esa lista por la real de 2026-27:

| Grupo A | Grupo B | Grupo C | Grupo D |
|---|---|---|---|
| Baskonia | Barcelona | Valencia | Real Madrid |
| Dubai | Hapoel Tel Aviv | Fenerbahçe | Olimpia Milán |
| Zalgiris | Maccabi | Olympiacos | Estrella Roja |
| Paris | Anadolu Efes | Panathinaikos | Bahçesehir |
| Hapoel Jerusalén | ASVEL | Bayern Múnich | Besiktas |
| Aris | Partizan | Virtus Bolonia | Napoli |

- **España:** Valencia, Barça, Real Madrid y Baskonia, uno en cada grupo.
- **Resto:** los 16 clubes de la Euroliga y los 4 mejores de la EuroCup, repartidos por nivel para que los grupos queden equilibrados.

## All-Star: Selección USA contra Selección Europea

**USA:** Stephen Curry, Anthony Edwards, Jayson Tatum, Anthony Davis, Joel Embiid, Jalen Brunson, Donovan Mitchell, Devin Booker, Kevin Durant, LeBron James, Kawhi Leonard y Paolo Banchero.

**Europa:** Luka Doncic, Bogdan Bogdanovic, Franz Wagner, Giannis Antetokounmpo, Nikola Jokic, Dennis Schröder, Deni Avdija, Victor Wembanyama y Alperen Sengun. El propio juego completa la Selección Europea hasta 12 con jugadores de clubes europeos.

## Cómo se calcularon las valoraciones

Las valoraciones del juego no son públicas, así que se reconstruyeron así:

1. **Calibración con 1996.** Se compararon las valoraciones originales del juego con las estadísticas reales de aquella temporada para saber qué mide cada una.
2. **Historial.** Se reunieron las temporadas de cada jugador: toda su trayectoria en la Liga Endesa, más la Euroliga, la EuroCup y la NBA desde 2023-24.
3. **Peso de cada temporada.** Cuentan los minutos jugados y lo reciente que es la temporada; la actual y la anterior son las que más pesan. Las temporadas antiguas se corrigen con una curva de edad.
4. **Nivel de cada liga.** La PIR por minuto se ajusta con un coeficiente: Euroliga 1,00, ACB 0,95, EuroCup 0,85 y NBA 1,05.
5. **Misma escala que el juego.** La calidad general sale de la PIR por 40 minutos y de los minutos por partido. Después se ajusta para que la ACB tenga media 74 y una dispersión parecida a la del juego de 1996.
6. **Especialidad.** Cada valoración suma una parte propia:
   - *Manejo / pase:* asistencias, triples y posición.
   - *Tiro / ataque:* puntos y acierto en el tiro.
   - *Rebote / juego interior:* rebotes.
   - *Defensa / físico:* robos, tapones y altura.

Los jugadores sin estadísticas recientes (lesionados o recién llegados) reciben valores típicos de su posición y competición. Así ningún jugador queda a cero en el simulador del mánager.

El proceso completo está en [`plantillas/valoraciones.py`](../plantillas/valoraciones.py), y el informe de resultados en [`plantillas/valoraciones_informe.txt`](../plantillas/valoraciones_informe.txt).

## Fuentes

- **Liga Endesa:** acb.com (plantillas, estadísticas, fotos y escudos).
- **Euroliga y EuroCup:** la API pública de la web oficial de la Euroliga.
- **NBA:** estadísticas públicas de ESPN.

Todas las marcas, nombres e imágenes pertenecen a sus respectivos dueños. Consulta el [aviso legal](../README.md#aviso-legal).
