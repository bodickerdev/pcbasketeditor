"""
Avisos de logros dentro de RetroArch (mensaje en pantalla del propio RetroArch).

La ventanita del editor no se ve encima de RetroArch a pantalla completa con
algunos drivers de vídeo (glcore en tarjetas NVIDIA). RetroArch tiene una
«interfaz de comandos de red»: escucha en un puerto UDP de 127.0.0.1 y el
comando «SHOW_MSG texto» pinta el texto encima del juego, como sus avisos.

Hay que activarla en retroarch.cfg (network_cmd_enable, network_cmd_port).
El puerto por defecto, 55355, cae dentro del rango dinámico de Windows
(49152-65535), y Hyper-V, WSL o Docker suelen reservar trozos de ese rango.
Entonces RetroArch no puede abrirlo y en su registro aparece «[NetCMD] Error al
asignar el socket». Por eso, si el puerto configurado no se puede abrir, se
elige uno por debajo de 49152.

retroarch.cfg solo se cambia con RetroArch cerrado: al salir, RetroArch
guarda su configuración (config_save_on_exit) y borraría el cambio.
"""
from __future__ import annotations

import os
import re
import socket
from typing import Optional

DEFAULT_PORT = 55355
FALLBACK_PORTS = (45355, 43555, 41555, 39555, 37555)
ENABLE_KEY, PORT_KEY = "network_cmd_enable", "network_cmd_port"
COMMON_DIRS = (r"C:\RetroArch-Win64", r"C:\RetroArch", r"C:\Program Files\RetroArch",
               r"C:\Program Files (x86)\RetroArch")


def find_config(exe_path: Optional[str] = None) -> Optional[str]:
    """retroarch.cfg que usa RetroArch: junto al .exe (instalación normal o
    portátil) o en %APPDATA%\\RetroArch."""
    dirs = [os.path.dirname(exe_path)] if exe_path else []
    dirs += [os.path.join(os.environ.get("APPDATA", ""), "RetroArch")]
    dirs += list(COMMON_DIRS)
    for d in dirs:
        p = os.path.join(d, "retroarch.cfg")
        if d and os.path.isfile(p):
            return p
    return None


def read_settings(cfg: str) -> dict:
    out = {}
    with open(cfg, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.match(r'\s*(\w+)\s*=\s*"(.*)"', line)
            if m:
                out[m.group(1)] = m.group(2)
    return out


def command_port(cfg: Optional[str]) -> Optional[int]:
    """Puerto de comandos si la interfaz está activada en retroarch.cfg."""
    if not cfg:
        return None
    try:
        s = read_settings(cfg)
    except OSError:
        return None
    if s.get(ENABLE_KEY) != "true":
        return None
    try:
        return int(s.get(PORT_KEY, DEFAULT_PORT))
    except ValueError:
        return None


def port_usable(port: int) -> bool:
    """¿Se puede abrir este puerto UDP? (con RetroArch cerrado)"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def needed_change(cfg: str) -> Optional[int]:
    """Puerto que habría que configurar, o None si ya está bien.
    Solo tiene sentido con RetroArch cerrado (si no, el puerto lo tiene él)."""
    s = read_settings(cfg)
    try:
        port = int(s.get(PORT_KEY, DEFAULT_PORT))
    except ValueError:
        port = DEFAULT_PORT
    if s.get(ENABLE_KEY) == "true" and port_usable(port):
        return None
    if port_usable(port):
        return port
    return next((p for p in FALLBACK_PORTS if port_usable(p)), None)


def enable(cfg: str, port: int):
    """Activa la interfaz de comandos en retroarch.cfg (con RetroArch cerrado).
    Guarda una copia como retroarch.cfg.antes_logros la primera vez."""
    with open(cfg, "rb") as f:
        raw = f.read()
    bak = cfg + ".antes_logros"
    if not os.path.exists(bak):
        with open(bak, "wb") as f:
            f.write(raw)
    text = raw.decode("utf-8", errors="surrogateescape")
    nl = "\r\n" if "\r\n" in text else "\n"
    for key, value in ((ENABLE_KEY, "true"), (PORT_KEY, str(port))):
        line = f'{key} = "{value}"'
        text, n = re.subn(rf'(?m)^\s*{key}\s*=.*?(?=\r?$)', line, text)
        if not n:
            text = text.rstrip("\r\n") + nl + line + nl
    tmp = cfg + ".tmp"
    with open(tmp, "wb") as f:
        f.write(text.encode("utf-8", errors="surrogateescape"))
    os.replace(tmp, cfg)


def show_message(port: int, text: str) -> bool:
    """Pide a RetroArch que muestre el texto en pantalla."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.sendto(b"SHOW_MSG " + text.encode("utf-8"), ("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()
