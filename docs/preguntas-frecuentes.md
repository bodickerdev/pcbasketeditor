# Preguntas frecuentes

[← Volver al inicio](../README.md)

### ¿Incluye el juego?
No. Necesitas tu propia copia de PC Basket 4.5. El parche solo contiene las diferencias respecto a los archivos originales y no sirve sin ellos.

### ¿Dónde consigo el juego?
Este proyecto no distribuye el juego ni enlaza a copias. Usa una copia original que tengas.

### ¿Funciona con mis partidas guardadas?
Las ligas que ya tenías siguen con los equipos de 1996, porque cada partida guarda su propia copia de los datos. Para jugar con las plantillas nuevas, empieza una liga nueva.

### ¿Puedo deshacer la instalación?
Sí. Pulsa **Restaurar copia de seguridad** en el editor, o recupera a mano los archivos `.BAK`. Los detalles están en [Instalación](instalacion.md#volver-al-juego-original).

### ¿Puedo seguir editando después de instalar la actualización?
Sí. El editor abre la base de datos actualizada y puedes cambiar lo que quieras. Ten en cuenta que **Restaurar** vuelve a los archivos de 1996, no a la actualización. Para recuperarla, restaura y vuelve a instalar.

### ¿Por qué no puedo añadir más jugadores a un equipo?
El juego espera exactamente el mismo número de jugadores por equipo que tenía en 1996. Si cambia, se descolocan todos los equipos que vienen detrás en el archivo. Para fichar a alguien, sustituye a otro jugador.

### ¿Por qué falta un jugador en la plantilla de un equipo europeo?
Por la misma razón: algunos equipos tenían 9 o 10 jugadores en 1996, así que de la plantilla actual entran solo los más importantes.

### Un nombre sale sin tildes o con letras raras
El juego solo admite el alfabeto latino básico (Latin-1). Los nombres con *ć*, *š* y letras parecidas se escriben sin el signo. El marcador tampoco muestra bien las tildes, así que allí se usan mayúsculas sin ellas.

### ¿Se actualizarán las plantillas durante la temporada?
Los scripts de la carpeta [`plantillas/`](../plantillas/LEEME.md) permiten volver a descargar los datos y generar un parche nuevo. Las nuevas versiones se publicarán en [Releases](https://github.com/bodickerdev/pcbasketeditor/releases).

### ¿Funciona en Mac o Linux?
El `.exe` es solo para Windows. El código fuente es Python y Tkinter, así que debería funcionar en Mac y Linux con `python editor.py`, pero no se ha probado.

### He encontrado un error
Abre una [issue](https://github.com/bodickerdev/pcbasketeditor/issues) e indica el equipo o jugador afectado y, si puedes, una captura de pantalla.
