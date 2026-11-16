"""
Parches de actualización para PC Basket 4.5.

Un parche (.pcbp) es un ZIP con solo las DIFERENCIAS (bsdiff) entre los archivos
originales de 1996 y los actualizados. No contiene el juego: sin una copia
original del juego no sirve para nada.

    python parche.py crear  [CARPETA_JUEGO] [SALIDA.pcbp]    (usa los .BAK como originales)
    python parche.py estado CARPETA_JUEGO [PARCHE.pcbp]
    python parche.py aplicar CARPETA_JUEGO [PARCHE.pcbp]
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
import sys
import zipfile

import bsdiff4

FILES = ["BASKET96.DBC", "BASKET96.DGF", "CARAS.BIN", "ESCUDOS.BIN",
         "MANAGER.DAT", "BASKET4.DAT"]
PATCH_NAME = "actualizacion_2026-27.pcbp"
FORMAT = 1

# Estados de cada archivo frente al parche
ORIGINAL = "original"          # listo para parchear
APPLIED = "aplicado"           # ya actualizado
FROM_BAK = "modificado"        # cambiado a mano, pero el .BAK es el original
MISSING = "falta"
UNKNOWN = "desconocido"        # otra versión del juego


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_file(folder: str, name: str) -> str | None:
    """Busca NAME en FOLDER sin distinguir mayúsculas (copias desde CD/DOSBox)."""
    p = os.path.join(folder, name)
    if os.path.exists(p):
        return p
    try:
        for f in os.listdir(folder):
            if f.upper() == name.upper():
                return os.path.join(folder, f)
    except OSError:
        pass
    return None


def default_patch() -> str | None:
    """Parche junto al .exe/.py; si no, el que va empaquetado dentro del .exe."""
    here = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
            else os.path.dirname(os.path.abspath(__file__)))
    candidates = [os.path.join(here, PATCH_NAME), os.path.join(here, "parche", PATCH_NAME)]
    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, PATCH_NAME))
    return next((c for c in candidates if os.path.exists(c)), None)


# --------------------------------------------------------------------------
def create(game: str, out: str, title: str = "Temporada 2026-27") -> dict:
    manifest = {"format": FORMAT, "title": title,
                "created": datetime.date.today().isoformat(), "files": []}
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            cur, bak = os.path.join(game, name), os.path.join(game, name + ".BAK")
            if not os.path.exists(bak):
                raise FileNotFoundError(f"Falta {bak} (el original de 1996)")
            old, new = open(bak, "rb").read(), open(cur, "rb").read()
            if old == new:
                continue
            z.writestr(name + ".bsdiff", bsdiff4.diff(old, new))
            manifest["files"].append({
                "name": name,
                "orig_sha256": hashlib.sha256(old).hexdigest(), "orig_size": len(old),
                "new_sha256": hashlib.sha256(new).hexdigest(), "new_size": len(new)})
        z.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest


def read_manifest(patch: str) -> dict:
    with zipfile.ZipFile(patch) as z:
        m = json.loads(z.read("manifest.json"))
    if m.get("format") != FORMAT:
        raise ValueError("Este parche es de una versión más nueva del editor.")
    return m


def status(game: str, patch: str) -> list[tuple[dict, str]]:
    out = []
    for e in read_manifest(patch)["files"]:
        p = find_file(game, e["name"])
        if not p:
            out.append((e, MISSING))
            continue
        h = sha256(p)
        if h == e["new_sha256"]:
            st = APPLIED
        elif h == e["orig_sha256"]:
            st = ORIGINAL
        else:
            bak = find_file(game, e["name"] + ".BAK")
            st = FROM_BAK if bak and sha256(bak) == e["orig_sha256"] else UNKNOWN
        out.append((e, st))
    return out


def apply(game: str, patch: str) -> list[str]:
    """Aplica el parche. Antes guarda cada original como .BAK (si no existe ya).
    Devuelve los archivos actualizados. No toca nada si algún archivo no encaja."""
    sts = status(game, patch)
    bad = [e["name"] for e, st in sts if st in (MISSING, UNKNOWN)]
    if bad:
        raise ValueError("Estos archivos no son los originales de PC Basket 4.5 (o faltan): "
                         + ", ".join(bad))
    # 1) calcular todo en memoria y verificar
    results = []
    with zipfile.ZipFile(patch) as z:
        for e, st in sts:
            if st == APPLIED:
                continue
            target = find_file(game, e["name"])
            src = target if st == ORIGINAL else find_file(game, e["name"] + ".BAK")
            old = open(src, "rb").read()
            new = bsdiff4.patch(old, z.read(e["name"] + ".bsdiff"))
            if hashlib.sha256(new).hexdigest() != e["new_sha256"]:
                raise ValueError(f"El parche de {e['name']} está dañado.")
            results.append((target, old, new))
    # 2) copias de seguridad y escritura
    done = []
    for target, old, new in results:
        bak = target + ".BAK"
        if not find_file(game, os.path.basename(bak)):
            with open(bak, "wb") as f:
                f.write(old)
        os.chmod(target, 0o666)       # los archivos copiados del CD son de solo lectura
        tmp = target + ".tmp"
        with open(tmp, "wb") as f:
            f.write(new)
        os.replace(tmp, target)
        done.append(os.path.basename(target))
    return done


# --------------------------------------------------------------------------
def _main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    if len(argv) < 2 or argv[1] not in ("crear", "estado", "aplicar"):
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd == "crear":
        game = argv[2] if len(argv) > 2 else os.path.join(here, "..")
        out = argv[3] if len(argv) > 3 else os.path.join(here, "parche", PATCH_NAME)
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        m = create(os.path.normpath(game), out)
        print(f"Creado {out} ({os.path.getsize(out) // 1024} KB)")
        for e in m["files"]:
            print(f"  {e['name']}")
        return 0
    game = argv[2]
    patch = argv[3] if len(argv) > 3 else default_patch()
    if cmd == "estado":
        for e, st in status(game, patch):
            print(f"  {e['name']:14} {st}")
    else:
        print("Actualizados:", ", ".join(apply(game, patch)) or "nada (ya estaba al día)")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
