"""
Colores de las equipaciones de PC Basket 4.5.

PARTIDO (MANAGER.DAT)
    Los sprites de los jugadores (*.EMP, imágenes de 8 bits sin comprimir) usan los
    índices 1..48 para la ropa y 49..55 para la piel. Al empezar el partido el juego
    copia 48 bytes del equipo en la tabla de traducción de colores de cada jugador:
        índice del sprite k+1  ->  color de paleta  tabla[equipo][k]
    Tabla (objeto 2 + 0x1AC44 = archivo 0x53444): 48 bytes por registro.
        registros 0..52   equipación principal (orden del marcador: 18 ACB, 32 Europa,
                          Sel. Europea, Equipo USA, Equipo ACB)
        registros 53..105 equipación alternativa del equipo n (53 + n)
    Matriz de choques (objeto 2 + 0x1CAE4 = archivo 0x552E4): 64 x 64 bytes.
        choque[local * 64 + visitante] != 0  ->  el visitante usa la alternativa.
    Hay una 2.ª tabla (objeto 2 + 0x1C054) que solo se usa en un modo especial del juego
    ([0x5498] == 4); no se toca.

MENÚS (BASKET96.DGF)
    Cada equipo ACB tiene la camiseta (gfx 7) y 4 figuras con la equipación (gfx 8-11),
    en 16 colores. Se recolorean a partir de las imágenes ORIGINALES (DGF.BAK), así que
    se pueden aplicar tantas veces como se quiera sin perder calidad.
"""
from __future__ import annotations

import os
import shutil
import struct
from collections import Counter

# ---------------------------------------------------------------------------
# Posiciones en MANAGER.DAT (comprobadas con el código que las usa)
# ---------------------------------------------------------------------------
OBJ2 = 0x38800                  # el objeto de datos empieza aquí en el archivo
KITS = OBJ2 + 0x1AC44           # 0x53444
CLASH = OBJ2 + 0x1CAE4          # 0x552E4
SKINS = OBJ2 + 0x1A4CC          # punteros a las 4 tablas de piel (7 bytes)
KIT_LEN = 48
N_TEAMS = 53                    # equipos con equipación (los del marcador)
ALT_BASE = 53
# firma del código:  mul edx / lea esi,[eax+1AC44h]
CODE_SIG = (0x26395, bytes.fromhex("8db044ac0100"))

# ---------------------------------------------------------------------------
# Zonas de la ropa (posiciones dentro de los 48 bytes)
# ---------------------------------------------------------------------------
# tipo "ramp": bloques de 5 tonos (claro -> oscuro); "one": un solo color
ZONES = [
    ("cam1", "Camiseta (mitad 1)", "ramp", [0, 1, 2, 3, 4]),
    ("cam2", "Camiseta (mitad 2)", "ramp", [15, 16, 17, 18, 19]),
    ("pecho1", "Número y dibujos del pecho 1", "ramp", [5, 6, 7, 8, 9, 36, 37, 38, 39, 40]),
    ("pecho2", "Número y dibujos del pecho 2", "ramp", [10, 11, 12, 13, 14, 41, 42, 43, 44, 45]),
    ("cuello", "Cuello", "one", [20]),
    ("sisas", "Sisas y bajo de la camiseta", "one", [21]),
    ("costados", "Costados de la camiseta", "one", [46, 47]),
    ("pantalon", "Pantalón", "ramp", [22, 23, 24, 25, 26]),
    ("franja", "Franja del pantalón", "one", [27]),
    ("bajo", "Bajo del pantalón", "one", [28]),
]
ZONE_BY_KEY = {z[0]: z for z in ZONES}
ONE_SHADE = 1                   # tono de la gama que se usa en las zonas de un color

# Gamas de 5 tonos que ya usa el juego (índices de la paleta del partido)
PRESETS = [
    ("Blanco", (0x68, 0x6A, 0x6B, 0x6D, 0x6E)),
    ("Gris", (0x6D, 0x6F, 0x70, 0x72, 0x73)),
    ("Negro", (0x75, 0xB3, 0xB3, 0xB3, 0xB3)),
    ("Rojo", (0x8F, 0x90, 0x92, 0x92, 0x93)),
    ("Granate", (0x91, 0x92, 0x93, 0x93, 0x93)),
    ("Naranja", (0x80, 0x81, 0x82, 0x83, 0x84)),
    ("Amarillo", (0x76, 0xAA, 0xC4, 0xC6, 0x79)),
    ("Dorado", (0xB5, 0xB9, 0xBC, 0xBF, 0xC0)),
    ("Verde", (0x94, 0x95, 0x96, 0x97, 0x98)),
    ("Verde oscuro", (0x85, 0x86, 0x87, 0x88, 0x89)),
    ("Azul celeste", (0x99, 0x9A, 0x9B, 0x9C, 0x9D)),
    ("Azul", (0x7B, 0x7C, 0x7D, 0x7E, 0x7F)),
    ("Azul marino", (0x7D, 0x7E, 0x7F, 0x7F, 0x7F)),
    ("Morado", (0x8A, 0x8B, 0x8C, 0x8D, 0x8E)),
]


def _dist(a, b):
    """Distancia de color aproximada a la percepción ("redmean")."""
    rm = (a[0] + b[0]) / 2
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return ((2 + rm / 256) * dr * dr + 4 * dg * dg + (2 + (255 - rm) / 256) * db * db) ** 0.5


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def read_palette(campo_path):
    pcx = open(campo_path, "rb").read()
    if pcx[-769] != 0x0C:
        raise ValueError("No encuentro la paleta en " + os.path.basename(campo_path))
    p = pcx[-768:]
    return [tuple(p[i * 3:i * 3 + 3]) for i in range(256)]


# ===========================================================================
# Equipaciones del partido
# ===========================================================================
class Kits:
    def __init__(self, manager_path, campo_path):
        self.path = manager_path
        self.d = bytearray(open(manager_path, "rb").read())
        s, sig = CODE_SIG
        if self.d[s:s + len(sig)] != sig:
            raise ValueError("MANAGER.DAT no es la versión esperada (no encuentro la tabla "
                             "de equipaciones).")
        self.palette = read_palette(campo_path)
        bak = manager_path + ".BAK"
        src = open(bak, "rb").read() if os.path.exists(bak) else bytes(self.d)
        self.original = bytes(src[KITS:KITS + 2 * N_TEAMS * KIT_LEN])
        self.original_clash = bytes(src[CLASH:CLASH + 64 * 64])
        # colores seguros: los que ya usa la tabla original (no dependen del pabellón)
        used = set(self.original) - {0, 47, 98, 102, 208}
        self.safe = sorted(used)
        ptr = struct.unpack_from("<I", self.d, SKINS)[0]
        self.skin = bytes(self.d[OBJ2 + ptr:OBJ2 + ptr + 7])
        self.dirty = False

    # ---- registros ---------------------------------------------------------
    @staticmethod
    def record(team, alt=False):
        return team + (ALT_BASE if alt else 0)

    def get(self, team, alt=False) -> bytearray:
        o = KITS + self.record(team, alt) * KIT_LEN
        return bytearray(self.d[o:o + KIT_LEN])

    def put(self, team, alt, data):
        assert len(data) == KIT_LEN
        o = KITS + self.record(team, alt) * KIT_LEN
        if self.d[o:o + KIT_LEN] != data:
            self.d[o:o + KIT_LEN] = data
            self.dirty = True

    def original_kit(self, team, alt=False):
        o = self.record(team, alt) * KIT_LEN
        return bytearray(self.original[o:o + KIT_LEN])

    # ---- zonas -------------------------------------------------------------
    def zone_ramp(self, kit, key):
        """Los 5 tonos de una zona (o el tono único repetido)."""
        _, _, kind, pos = ZONE_BY_KEY[key]
        if kind == "ramp":
            return tuple(kit[p] for p in pos[:5])
        return (kit[pos[0]],) * 5

    def zone_rgb(self, kit, key):
        _, _, kind, pos = ZONE_BY_KEY[key]
        return self.palette[kit[pos[0]] if kind == "one" else kit[pos[1]]]

    @staticmethod
    def set_zone(kit, key, ramp):
        _, _, kind, pos = ZONE_BY_KEY[key]
        if kind == "ramp":
            for i, p in enumerate(pos):
                kit[p] = ramp[i % 5]
        else:
            for p in pos:
                kit[p] = ramp[ONE_SHADE]

    def ramp_from_rgb(self, rgb):
        """Gama de 5 tonos (de claro a oscuro) con los colores seguros de la paleta."""
        out = []
        for f in (1.0, 0.88, 0.76, 0.66, 0.56):
            t = tuple(min(255, int(c * f)) for c in rgb)
            out.append(min(self.safe, key=lambda i: _dist(self.palette[i], t)))
        return tuple(out)

    # ---- choques de color --------------------------------------------------
    def clash(self, home, away):
        return bool(self.d[CLASH + home * 64 + away])

    def set_clash(self, home, away, value):
        o = CLASH + home * 64 + away
        v = 1 if value else 0
        if self.d[o] != v:
            self.d[o] = v
            self.dirty = True

    def shirt_colors(self, team, alt=False):
        k = self.get(team, alt)
        return [self.palette[k[1]], self.palette[k[16]]]

    def similar(self, a, b, alt_b=False):
        for x in self.shirt_colors(a):
            for y in self.shirt_colors(b, alt_b):
                if _dist(x, y) < 160 or (_lum(x) > 185 and _lum(y) > 185) or \
                        (_lum(x) < 45 and _lum(y) < 45):
                    return True
        return False

    def recompute_clash(self, team):
        """Recalcula los choques de un equipo con todos los demás (en los dos sentidos)."""
        for u in range(N_TEAMS):
            if u != team:
                v = self.similar(team, u)
                self.set_clash(team, u, v)
                self.set_clash(u, team, v)

    def rivals_with_alt(self, team):
        """Equipos locales contra los que este equipo, de visitante, usa la alternativa."""
        return [u for u in range(N_TEAMS) if u != team and self.clash(u, team)]

    # ---- archivo -----------------------------------------------------------
    def save(self, path=None):
        path = path or self.path
        if os.path.exists(path) and not os.path.exists(path + ".BAK"):
            shutil.copy2(path, path + ".BAK")
        # se parte del archivo actual para no pisar otros cambios (p. ej. nombres del marcador)
        cur = bytearray(open(path, "rb").read()) if os.path.exists(path) else bytearray(self.d)
        n = 2 * N_TEAMS * KIT_LEN
        cur[KITS:KITS + n] = self.d[KITS:KITS + n]
        cur[CLASH:CLASH + 64 * 64] = self.d[CLASH:CLASH + 64 * 64]
        if os.path.exists(path):
            os.chmod(path, 0o666)
        open(path, "wb").write(cur)
        self.dirty = False


# ===========================================================================
# Vista previa con los sprites del partido
# ===========================================================================
def load_frames(path, limit=None):
    """Fotogramas de un .EMP: bloques  u16 ancho, u16 alto, u32 tamaño, píxeles."""
    d = open(path, "rb").read()
    out, i = [], 0
    while i < len(d) - 8:
        w, h, s = struct.unpack_from("<HHI", d, i)
        if 4 <= w <= 200 and 4 <= h <= 200 and s == w * h and i + 8 + s <= len(d):
            out.append((w, h, d[i + 8:i + 8 + s]))
            i += 8 + s
            if limit and len(out) >= limit:
                break
        else:
            i += 1
    return out


def render_sprite(frame, kit, skin, palette, scale=4, bg=(46, 52, 60)):
    from PIL import Image
    w, h, px = frame
    lut = []
    for v in range(256):
        if v == 0:
            lut.append(bg)
        elif v <= KIT_LEN:
            lut.append(palette[kit[v - 1]])
        elif v <= KIT_LEN + 7:
            lut.append(palette[skin[v - KIT_LEN - 1]])
        else:
            lut.append(palette[v])
    im = Image.new("RGB", (w, h))
    im.putdata([lut[v] for v in px])
    return im.resize((w * scale, h * scale), Image.NEAREST)


# ===========================================================================
# Figuras y camiseta de los menús (BASKET96.DGF)
# ===========================================================================
MENU_GFX = (7, 8, 9, 10, 11)                # "clase" de imagen: 7 camiseta, 8-11 figuras


def menu_gfx(g):
    """[(puntero, clase)] de la camiseta y las figuras de un equipo:
    ACB (12 punteros) en 7-11; Europa (9 punteros) en 4-8."""
    if len(g) >= 12:
        return [(g[k], k) for k in MENU_GFX]
    if len(g) == 9:
        return [(g[k - 3], k) for k in MENU_GFX]
    return []
MENU_COLORS = [0] + list(range(3, 16))      # el 1 y el 2 cambian según la pantalla
# tonos más oscuros de cada color de la paleta de 16 colores
MENU_SHADES = {15: [14, 13], 14: [13, 12], 13: [12, 0], 12: [0], 0: [12, 13],
               9: [3, 0, 12], 3: [0, 12], 4: [8, 11], 8: [11, 3, 12], 11: [3, 0, 12],
               10: [5, 0, 12], 5: [0, 12], 7: [6, 0, 12], 6: [0, 12]}
SKIN_MENU = {3, 8, 11}                      # colores de la piel en las figuras


class MenuKits:
    """Recolorea la camiseta y las figuras del menú (equipos ACB y europeos)."""

    def __init__(self, dgf, dgf_original, teams_gfx):
        self.dgf = dgf
        self.orig = dgf_original                # DGF con las imágenes de 1996
        self.pal = dgf.palette
        self.masks = {}
        # Píxeles de ropa: los que cambian de un equipo a otro (mismo tamaño de imagen)
        groups = {}
        for g in teams_gfx:
            for ptr, k in menu_gfx(g):
                w, h, px = self.orig.decode(ptr)
                groups.setdefault((k, w, h), []).append(px)
        for (k, w, h), imgs in groups.items():
            if len(imgs) >= 4:
                self.masks[(k, w, h)] = [len({im[i] for im in imgs}) > 1 for i in range(w * h)]

    def nearest(self, rgb):
        """Color de los 16 del menú más parecido. Se compara el tono, no el brillo:
        los colores del partido son más oscuros que los del menú."""
        mx, mn = max(rgb), min(rgb)
        sat = (mx - mn) / mx if mx else 0
        if sat < 0.25:      # blanco, grises o negro: por luminosidad
            return min((0, 12, 13, 14, 15), key=lambda c: abs(_lum(self.pal[c]) - _lum(rgb)))

        def norm(c):
            m = max(c) or 1
            return tuple(v * 255 / m for v in c)
        t = norm(rgb)
        # las versiones oscuras (marrón, azul marino, verde oscuro) solo para colores oscuros
        dark_ok = {3: mx < 120, 5: mx < 170, 6: mx < 100}
        cands = [c for c in range(3, 12) if dark_ok.get(c, True)]
        return min(cands, key=lambda c: _dist(norm(self.pal[c]), t))

    @staticmethod
    def _shade(c, level):
        if level == 0:
            return c
        sh = MENU_SHADES.get(c, [0])
        return sh[min(level - 1, len(sh) - 1)]

    def _mask(self, k, w, h, px):
        m = self.masks.get((k, w, h))
        if m is not None:
            return m
        if k == 7:   # camiseta suelta: todo lo que no es el fondo gris
            return [v not in (13, 14) for v in px]
        return [v not in SKIN_MENU and v != 0 for v in px]

    @staticmethod
    def _region(k, w, h, x, y):
        """'cam' (camiseta), 'pan' (pantalón) o None (piernas, calcetines...)."""
        if k == 7:
            return "cam" if x * 71 / w < 45 - y * 0.25 else "pan"
        if y <= round(h * 0.445):
            return "cam"
        if y <= round(h * 0.588):
            return "pan"
        return None

    def recolor(self, g, colors):
        """g: punteros gfx del equipo.
        colors: dict con los RGB de 'cam1', 'cam2', 'pecho', 'pan', 'pan_det'."""
        new_main = {"cam": self.nearest(colors["cam1"]), "pan": self.nearest(colors["pan"])}
        new_alt = self.nearest(colors["cam2"])
        new_det = {"cam": self.nearest(colors["pecho"]), "pan": self.nearest(colors["pan_det"])}
        for ptr, k in menu_gfx(g):
            w, h, px = self.orig.decode(ptr)
            mask = self._mask(k, w, h, px)
            regions = {}
            for i in range(w * h):
                if mask[i]:
                    r = self._region(k, w, h, i % w, i // w)
                    if r:
                        regions.setdefault(r, []).append(i)
            out = bytearray(self.dgf.decode(ptr)[2])
            if len(out) != len(px):
                continue
            for r, idx in regions.items():
                cnt = Counter(px[i] for i in idx)
                total = sum(cnt.values())
                # colores de fondo de la prenda: un color con sus sombras ocupa >= 35 %
                # (el más abundante siempre); el resto son detalles (letras, números...)
                level = {}
                for c, _n in cnt.most_common():
                    if c in level:
                        continue
                    fam = [c] + [s for s in MENU_SHADES.get(c, []) if s not in level]
                    if level and sum(cnt[m] for m in fam) < 0.35 * total:
                        continue
                    level[c] = 0
                    for j, s in enumerate(MENU_SHADES.get(c, [])):
                        level.setdefault(s, j + 1)
                xs = [i % w for i in idx]
                mid = (min(xs) + max(xs)) / 2
                for i in idx:
                    c = px[i]
                    main = new_main[r]
                    if r == "cam" and k != 7 and i % w < mid:
                        main = new_alt
                    elif r == "cam" and k == 7 and (i % w) < 18:
                        main = new_alt
                    if c in level:
                        out[i] = self._shade(main, level[c])
                    elif c == 0:
                        out[i] = 0          # contornos negros
                    else:
                        out[i] = new_det[r]
            self.dgf.encode(ptr, out)

    def restore(self, g):
        for ptr, _k in menu_gfx(g):
            w, h, px = self.orig.decode(ptr)
            if self.dgf.header(ptr)[:2] == (w, h):
                self.dgf.encode(ptr, px)

    def images(self, g, scale=2):
        return [self.dgf.to_image(ptr, scale) for ptr, _k in menu_gfx(g)]


def menu_colors_from_kit(kits: Kits, kit):
    cam1 = kits.zone_rgb(kit, "cam1")
    pecho = kits.zone_rgb(kit, "pecho1")
    if _dist(pecho, cam1) < 60:          # número del mismo color: usar el del cuello
        pecho = kits.zone_rgb(kit, "cuello")
    pan = kits.zone_rgb(kit, "pantalon")
    pan_det = kits.zone_rgb(kit, "franja")
    if _dist(pan_det, pan) < 60:
        pan_det = kits.zone_rgb(kit, "bajo")
    return {"cam1": cam1, "cam2": kits.zone_rgb(kit, "cam2"), "pecho": pecho,
            "pan": pan, "pan_det": pan_det}
