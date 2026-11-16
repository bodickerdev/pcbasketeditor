# Desarrollo

[← Volver al inicio](../README.md)

## Ejecutar desde el código fuente

Necesitas Python 3.10 o superior.

```
git clone https://github.com/bodickerdev/pcbasketeditor.git
cd pcbasketeditor
pip install -r requirements.txt
python editor.py ruta\al\juego\BASKET96.DBC
```

Sin argumentos, el editor busca `BASKET96.DBC` en su propia carpeta y en la carpeta superior. Por eso lo más cómodo es clonar el repositorio **dentro** de la carpeta del juego y abrirlo con doble clic en `Editor.bat`.

## Estructura

| Archivo | Para qué sirve |
|---|---|
| `editor.py` | Interfaz gráfica (Tkinter) |
| `dbc.py` | Lee y escribe `BASKET96.DBC` (equipos y jugadores). La escritura es idéntica byte a byte |
| `caras.py` | Retratos de `CARAS.BIN`, la paleta de `CAMPO800.BIN` y las caras de la pantalla previa al partido |
| `dgf.py` | Gráficos de `BASKET96.DGF` (figuras de los menús y caras pequeñas) |
| `equipaciones.py` | Colores de las equipaciones y choques de color en `MANAGER.DAT` |
| `parche.py` | Crea y aplica los parches de actualización |
| `construir.py` | Genera el `.exe` y el zip para publicar |
| `FORMATO_DBC.md` | Documentación técnica de los formatos |
| `plantillas/` | Scripts que descargan y aplican las plantillas reales ([LEEME](../plantillas/LEEME.md)) |

## Formato del parche (`.pcbp`)

Es un ZIP con estos archivos:

- `manifest.json`: título, fecha y, para cada archivo, el SHA-256 y el tamaño del original y del resultado.
- `<ARCHIVO>.bsdiff`: la diferencia binaria, calculada con [bsdiff4](https://pypi.org/project/bsdiff4/), entre el original de 1996 y el archivo actualizado.

```
python parche.py crear   [CARPETA_JUEGO] [SALIDA.pcbp]   # compara cada archivo con su .BAK
python parche.py estado  CARPETA_JUEGO   [PARCHE.pcbp]
python parche.py aplicar CARPETA_JUEGO   [PARCHE.pcbp]
```

Para crear el parche, los `.BAK` de la carpeta del juego tienen que ser los **originales de 1996**. Por cada archivo, `estado` devuelve uno de estos valores:

| Estado | Significado |
|---|---|
| `original` | Listo para aplicar el parche |
| `aplicado` | Ya está actualizado |
| `modificado` | Se cambió a mano, pero el `.BAK` es el original |
| `desconocido` | Es de otra versión del juego |
| `falta` | No está en la carpeta |

La aplicación no escribe nada hasta comprobar que todos los archivos encajan y que el resultado coincide con el hash esperado.

## Publicar una versión nueva

1. Actualiza las plantillas con los scripts de `plantillas/` y pruébalas en el juego.
2. Genera el paquete:
   ```
   pip install pyinstaller
   python construir.py
   ```
   El script rehace el parche a partir de los archivos del juego (la carpeta superior), crea `dist/EditorPCBasket.exe` con el parche dentro, y prepara `dist/EditorPCBasket_2026-27.zip` con el `.exe` y un `LEEME.txt`.
3. En GitHub, ve a **Releases → Draft a new release**, crea una etiqueta (por ejemplo `v1.1`) y sube el zip.

Si cambia la temporada, actualiza `PATCH_NAME` en `parche.py`, el nombre del zip en `construir.py` y el texto del botón en `editor.py`.

## Qué no se sube al repositorio

El `.gitignore` excluye:
- Los archivos del juego, originales o modificados.
- El parche, que solo va en las releases.
- Las fotos y escudos descargados.

Los datos en JSON de `plantillas/datos/` sí se suben, para que los scripts se puedan volver a ejecutar. Las imágenes se vuelven a descargar con los scripts `descargar*.py`.
