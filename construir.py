"""
Genera el paquete para publicar en GitHub Releases:

    python construir.py              rehace el parche desde la carpeta del juego, crea el .exe y el zip
    python construir.py --sin-parche usa el parche que ya está en parche/

Resultado: dist/EditorPCBasket_2026-27.zip  (EditorPCBasket.exe + LEEME.txt)
Necesita:  pip install pyinstaller pillow bsdiff4
"""
import os
import shutil
import subprocess
import sys
import zipfile

import parche

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.normpath(os.path.join(HERE, ".."))
PATCH = os.path.join(HERE, "parche", parche.PATCH_NAME)
ZIP = os.path.join(HERE, "dist", "EditorPCBasket_2026-27.zip")

LEEME = """EDITOR PC BASKET 4.5 - ACTUALIZACIÓN TEMPORADA 2026-27
=====================================================

INSTALAR
1. Descomprime este zip donde quieras.
2. Abre EditorPCBasket.exe.
   (Si Windows avisa de "aplicación desconocida": "Más información" > "Ejecutar de todas formas".)
3. Pulsa "Instalar actualización 2026-27" y elige la carpeta de tu PC Basket 4.5
   (la que tiene BASKET45.EXE).
4. Empieza una liga NUEVA en el juego.

Antes de cambiar nada se guarda una copia de cada archivo original (.BAK).
El botón "Restaurar copia de seguridad" deja el juego como estaba.

Necesitas tu propia copia de PC Basket 4.5: este paquete NO incluye el juego,
solo el editor y las diferencias (parche) respecto a los archivos originales.

AVISO LEGAL
{disclaimer}
"""


def main():
    os.chdir(HERE)
    if "--sin-parche" not in sys.argv:
        m = parche.create(GAME, PATCH)
        print(f"Parche: {len(m['files'])} archivos, {os.path.getsize(PATCH) // 1024} KB")
    if not os.path.exists(PATCH):
        sys.exit(f"Falta {PATCH}")

    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                    "--onefile", "--windowed", "--name", "EditorPCBasket",
                    "--add-data", f"{PATCH}{os.pathsep}.",
                    "--exclude-module", "numpy",
                    "editor.py"], check=True)

    import editor  # para copiar el mismo aviso legal
    os.makedirs(os.path.dirname(ZIP), exist_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join("dist", "EditorPCBasket.exe"), "EditorPCBasket.exe")
        z.writestr("LEEME.txt", LEEME.format(disclaimer=editor.DISCLAIMER)
                   .replace("\n", "\r\n").encode("utf-8-sig"))
    shutil.rmtree("build", ignore_errors=True)
    for f in ("EditorPCBasket.spec",):
        if os.path.exists(f):
            os.remove(f)
    print(f"\nListo: {ZIP} ({os.path.getsize(ZIP) // 1024 // 1024} MB)")


if __name__ == "__main__":
    main()
