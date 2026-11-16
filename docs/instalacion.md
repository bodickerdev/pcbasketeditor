# Instalación

[← Volver al inicio](../README.md)

## Qué necesitas

- **Una copia de PC Basket 4.5**, la versión de 1996 que se ejecuta con `BASKET45.EXE`. Este proyecto no incluye el juego.
- **Windows 10 u 11** para el editor. No hace falta instalar Python ni nada más.
- **DOSBox** (o DOSBox Staging, o DOSBox-X) para jugar, porque el juego es de MS-DOS.

## Instalar la actualización 2026-27

1. Entra en [Releases](https://github.com/bodickerdev/pcbasketeditor/releases/latest) y descarga `EditorPCBasket_2026-27.zip`.
2. Descomprímelo en cualquier carpeta. Puede ser la del juego u otra distinta.
3. Abre `EditorPCBasket.exe`.
4. El editor detecta que el juego no está actualizado y te ofrece instalar la actualización: acepta. Si no te lo ofrece, pulsa **⬇ Instalar actualización 2026-27**, el primer botón arriba a la izquierda.
5. Elige la carpeta del juego, la que contiene `BASKET45.EXE` y `BASKET96.DBC`.
6. Confirma. En unos segundos verás «Actualización instalada», y el editor abrirá la base de datos ya actualizada.
7. Abre el juego y empieza una **liga nueva**. Las partidas guardadas antes de la actualización conservan los equipos antiguos.

### Qué hace el instalador

1. **Comprueba** que cada archivo es el original de 1996 (por su huella SHA-256). Si alguno no coincide, se detiene sin tocar nada.
2. **Guarda una copia** de cada original con la extensión `.BAK`, por ejemplo `BASKET96.DBC.BAK`, si no existe ya.
3. **Aplica el parche** y verifica que el resultado es exactamente el esperado.

Estos son los archivos que cambian:

| Archivo | Contenido |
|---|---|
| `BASKET96.DBC` | Equipos, jugadores, entrenadores, valoraciones, estadísticas y biografías |
| `BASKET96.DGF` | Caras de la pantalla previa al partido y colores de las figuras de los menús |
| `CARAS.BIN` | Retratos del marcador y escudos de los equipos europeos |
| `ESCUDOS.BIN` | Escudos grandes de los menús |
| `MANAGER.DAT` | Nombres en el marcador, equipaciones del partido y choques de colores |
| `BASKET4.DAT` | Participantes de la Euroliga en el modo mánager |

## Volver al juego original

En el editor, pulsa **↺ Restaurar copia de seguridad**. Los 6 archivos vuelven a ser los de 1996.

También puedes hacerlo a mano: borra cada archivo de la tabla anterior y cambia el nombre de su `.BAK` para quitarle esa extensión.

## Desinstalar el editor

Borra la carpeta donde descomprimiste el zip. El editor no escribe en el registro de Windows ni deja archivos en otros sitios.

## Jugar con DOSBox

Este es un ejemplo mínimo. Cambia la ruta por la de tu juego.

```
mount c "C:\Juegos\pcbasket45"
c:
cd BASKET45
BASKET45
```

## Problemas frecuentes

**Windows dice «Windows protegió su PC».**
El programa no está firmado digitalmente, porque firmarlo cuesta dinero cada año. Pulsa *Más información* y después *Ejecutar de todas formas*.

**El antivirus bloquea `EditorPCBasket.exe`.**
Algunos antivirus desconfían de los programas hechos con PyInstaller. Si lo prefieres, puedes ejecutar el editor desde el código fuente; los pasos están en [Desarrollo](desarrollo.md).

**«Esta carpeta no parece una copia original de PC Basket 4.5».**
- Comprueba que eliges la carpeta que contiene `BASKET45.EXE`.
- Si ya habías modificado el juego con otro editor, el parche no puede aplicarse. Empieza desde una copia limpia del juego.
- Si tienes otra edición del juego, por ejemplo una reedición con archivos distintos, el parche no es compatible. Abre una *issue* en GitHub indicando qué archivos fallan.

**«Has modificado estos archivos y se perderán tus cambios».**
Ya habías guardado cambios con el editor, pero los `.BAK` siguen siendo los originales. El instalador puede partir de ellos, aunque los cambios que hiciste se pierden.

**En el juego siguen saliendo los equipos de 1996.**
Estás continuando una liga antigua. Cada liga guarda su propia copia de los datos, así que empieza una liga nueva.

**El botón «Instalar actualización» no aparece.**
El parche viaja dentro del `.exe`. Si ejecutas el editor desde el código fuente, crea antes el parche (consulta [Desarrollo](desarrollo.md)) o copia `actualizacion_2026-27.pcbp` junto a `editor.py`.
