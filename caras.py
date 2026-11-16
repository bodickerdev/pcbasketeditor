"""
Retratos del partido de PC Basket 4.5 (CARAS.BIN).

CARAS.BIN = 252 imágenes seguidas, cada una:  u16 ancho, u16 alto, ancho*alto bytes
(1 byte por píxel, índice de la paleta VGA del partido, que está al final de
CAMPO800.BIN, un PCX de 800x480).

  0..215   retratos de jugadores ACB: equipo_acb * 12 + posición en la plantilla
  216..248 escudos que salen al anotar un equipo sin retratos (32 europeos + All-Star)
  249..251 sin uso

Un retrato completamente del color 180 (casi negro) = jugador sin foto.
Un retrato completamente del color 105 (blanco)    = hueco sin jugador.
"""
from __future__ import annotations

import os
import shutil
from typing import List, Optional, Tuple

from PIL import Image

ACB_TEAMS = 18
SLOTS_PER_TEAM = 12
LOGO_BASE = ACB_TEAMS * SLOTS_PER_TEAM   # 216
BG_INDEX = 180                           # fondo negro de los retratos
EMPTY_INDEX = 105                        # hueco libre (blanco)

# Caras pequeñas de la pantalla previa al partido: imagen de 24x24 y 16 colores en
# BASKET96.DGF, apuntada por el 2.º puntero gráfico de cada jugador ACB.
# En esa pantalla los colores 1 y 2 son tonos de piel; el resto, la paleta fija del juego.
SMALL_W = SMALL_H = 24
SMALL_PALETTE = [(0, 0, 0), (252, 208, 156), (212, 120, 96), (155, 43, 0), (255, 219, 27),
                 (11, 39, 163), (23, 107, 19), (47, 211, 47), (231, 167, 0), (255, 0, 0),
                 (39, 87, 255), (227, 107, 0), (99, 99, 99), (151, 151, 151), (203, 203, 203),
                 (255, 255, 255)]
SMALL_USE = [0, 1, 2, 3, 4, 8, 11, 12, 13, 14, 15]   # los que usan las caras originales


def small_from_image(im: "Image.Image", brightness=1.3, contrast=1.2) -> bytes:
    """Reduce una cara (RGB, ya recortada y cuadrada) a 24x24 con los colores de las caras
    pequeñas. Devuelve los índices (0-15)."""
    from PIL import ImageEnhance
    im = im.convert("RGB").resize((SMALL_W, SMALL_H), Image.LANCZOS)
    im = ImageEnhance.Contrast(ImageEnhance.Brightness(im).enhance(brightness)).enhance(contrast)
    pal = [SMALL_PALETTE[c] for c in SMALL_USE]
    pimg = Image.new("P", (1, 1))
    pimg.putpalette([v for rgb in pal for v in rgb] + [0] * (768 - 3 * len(pal)))
    q = im.quantize(palette=pimg, dither=Image.Dither.FLOYDSTEINBERG)
    src = list(im.getdata())
    out = bytearray()
    for k, v in enumerate(q.getdata()):
        r, g, b = src[k]
        # fondo y zonas muy oscuras en negro limpio (el tramado las llena de puntos)
        out.append(0 if 0.3 * r + 0.59 * g + 0.11 * b < 40 else SMALL_USE[v])
    return bytes(out)


def sync_small_faces(db, faces: "Faces", dgf, original_caras: Optional[bytes]) -> int:
    """Copia a BASKET96.DGF las caras de CARAS.BIN que ya no son las de 1996.
    original_caras: contenido de CARAS.BIN.BAK (None = actualizar todas)."""
    orig = None
    if original_caras:
        orig, o = [], 0
        while o + 4 <= len(original_caras):
            w = int.from_bytes(original_caras[o:o + 2], "little")
            h = int.from_bytes(original_caras[o + 2:o + 4], "little")
            orig.append(bytes(original_caras[o + 4:o + 4 + w * h]))
            o += 4 + w * h
    pal = bytes(v for rgb in SMALL_PALETTE for v in rgb)
    n = 0
    for ti, t in enumerate(db.teams[:ACB_TEAMS]):
        for pi, p in enumerate(t.players[:SLOTS_PER_TEAM]):
            g = p.gfx[1] if len(p.gfx) > 1 else 1
            if g <= 1 or dgf.header(g)[:3] != (SMALL_W, SMALL_H, 4):
                continue
            slot = ti * SLOTS_PER_TEAM + pi
            if orig is not None and bytes(faces.faces[slot][2]) == orig[slot]:
                continue        # sigue siendo el retrato original: se deja la cara de 1996
            px = faces.small_face(slot)
            if dgf.decode(g)[2] != px or dgf.d[g + 2:g + 50] != pal:
                dgf.encode(g, px)
                dgf.d[g + 2:g + 50] = pal
                n += 1
    return n


class Faces:
    def __init__(self, path: str, palette_path: str):
        self.path = path
        data = open(path, "rb").read()
        self.faces: List[Tuple[int, int, bytearray]] = []
        o = 0
        while o + 4 <= len(data):
            w = int.from_bytes(data[o:o + 2], "little")
            h = int.from_bytes(data[o + 2:o + 4], "little")
            self.faces.append((w, h, bytearray(data[o + 4:o + 4 + w * h])))
            o += 4 + w * h
        if o != len(data) or len(self.faces) < LOGO_BASE:
            raise ValueError("CARAS.BIN no tiene el formato esperado")
        self.original = [bytes(f[2]) for f in self.faces]

        pcx = open(palette_path, "rb").read()
        if pcx[-769] != 0x0C:
            raise ValueError("No encuentro la paleta en " + os.path.basename(palette_path))
        p = pcx[-768:]
        self.palette = [tuple(p[i * 3:i * 3 + 3]) for i in range(256)]
        self.flat_palette = list(p)
        self.safe = self._safe_colors()
        logo_cols = set()
        for i in range(LOGO_BASE, len(self.faces)):
            logo_cols.update(self.faces[i][2])
        self.safe_logo = sorted(set(self.safe) | logo_cols - {EMPTY_INDEX})
        self.dirty = False

    def colors_for(self, i) -> List[int]:
        """Colores permitidos: los de las caras para retratos; más los de los escudos."""
        return self.safe if i < LOGO_BASE else self.safe_logo

    def _safe_colors(self) -> List[int]:
        """Colores que aparecen en retratos de al menos 3 equipos distintos:
        son colores fijos de la paleta (no los de las equipaciones)."""
        teams_using = {}
        for i in range(LOGO_BASE):
            px = self.faces[i][2]
            if len(set(px)) <= 2:
                continue
            for c in set(px):
                teams_using.setdefault(c, set()).add(i // SLOTS_PER_TEAM)
        safe = [c for c, t in teams_using.items() if len(t) >= 3 and c != EMPTY_INDEX]
        if BG_INDEX not in safe:
            safe.append(BG_INDEX)
        return sorted(safe)

    # ---- direcciones -----------------------------------------------------
    @staticmethod
    def player_slot(team_idx: int, player_idx: int) -> Optional[int]:
        if team_idx < ACB_TEAMS and player_idx < SLOTS_PER_TEAM:
            return team_idx * SLOTS_PER_TEAM + player_idx
        return None

    def logo_slot(self, team_idx: int) -> Optional[int]:
        i = LOGO_BASE + team_idx - ACB_TEAMS
        if team_idx >= ACB_TEAMS and i < len(self.faces):
            return i
        return None

    # ---- consulta --------------------------------------------------------
    def size(self, i) -> Tuple[int, int]:
        return self.faces[i][0], self.faces[i][1]

    def state(self, i) -> str:
        px = self.faces[i][2]
        if all(c == BG_INDEX for c in px):
            return "sin foto"
        if all(c == EMPTY_INDEX for c in px):
            return "hueco libre"
        return "foto"

    def to_image(self, i, scale: int = 1) -> Image.Image:
        w, h, px = self.faces[i]
        im = Image.frombytes("P", (w, h), bytes(px))
        im.putpalette(self.flat_palette)
        im = im.convert("RGB")
        if scale != 1:
            im = im.resize((w * scale, h * scale), Image.NEAREST)
        return im

    # ---- modificación ----------------------------------------------------
    def convert(self, img: Image.Image, w: int, h: int, colors: List[int] = None) -> bytes:
        """Reduce una imagen (ya recortada) a w x h con los colores seguros."""
        bg = self.palette[BG_INDEX]
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            base = Image.new("RGBA", img.size, bg + (255,))
            base.alpha_composite(img)
            img = base
        img = img.convert("RGB").resize((w, h), Image.LANCZOS)
        cols = [(c, self.palette[c]) for c in (colors or self.safe)]
        cache = {}
        out = bytearray()
        for (r, g, b) in img.getdata():
            key = (r, g, b)
            if key not in cache:
                # distancia ponderada (el ojo es más sensible al verde)
                cache[key] = min(cols, key=lambda kc: 3 * (kc[1][0] - r) ** 2 +
                                 4 * (kc[1][1] - g) ** 2 + 2 * (kc[1][2] - b) ** 2)[0]
            out.append(cache[key])
        return bytes(out)

    def small_face(self, i) -> bytes:
        """Cara de 24x24 en 16 colores para la pantalla previa al partido (BASKET96.DGF).
        Sin foto -> todo negro (como en las originales)."""
        if self.state(i) != "foto":
            return bytes(SMALL_W * SMALL_H)
        return small_from_image(self.to_image(i))

    def set_pixels(self, i, pixels: bytes):
        w, h, _ = self.faces[i]
        assert len(pixels) == w * h
        self.faces[i] = (w, h, bytearray(pixels))
        self.dirty = True

    def clear(self, i):
        w, h, _ = self.faces[i]
        self.set_pixels(i, bytes([BG_INDEX]) * (w * h))

    def restore(self, i):
        self.set_pixels(i, self.original[i])

    # ---- guardar ---------------------------------------------------------
    def serialize(self) -> bytes:
        out = bytearray()
        for w, h, px in self.faces:
            out += w.to_bytes(2, "little") + h.to_bytes(2, "little") + px
        return bytes(out)

    def save(self, path: Optional[str] = None):
        path = path or self.path
        if os.path.exists(path) and not os.path.exists(path + ".BAK"):
            shutil.copy2(path, path + ".BAK")
        if os.path.exists(path):
            os.chmod(path, 0o666)
        with open(path, "wb") as f:
            f.write(self.serialize())
        self.original = [bytes(f[2]) for f in self.faces]
        self.dirty = False


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    fc = Faces(os.path.join(here, "..", "CARAS.BIN"), os.path.join(here, "..", "CAMPO800.BIN"))
    raw = open(fc.path, "rb").read()
    print("Retratos:", len(fc.faces), " colores seguros:", len(fc.safe),
          " round-trip:", fc.serialize() == raw)
