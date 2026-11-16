"""
Imágenes de BASKET96.DGF (gráficos de la base de datos y del mánager).

Formato de cada imagen (apuntada desde el DBC con un u32):
    u16  0x0010            nº de colores
    48   paleta RGB (16 colores; en la práctica es la paleta global del juego)
    u8   0x01, u8 ancho     (ancho < 256)
    u16  alto  (big-endian)
    u16  planos (4, big-endian)
    2    bytes sin identificar (cabecera total: 58 bytes; tras los datos queda 1 byte)
    alto x 4 planos x ceil(ancho/8) bytes, entrelazado por líneas (fila: plano0, plano1, plano2, plano3)

Cada equipo ACB tiene 12 imágenes (Team.gfx):
    0/1 escudo grande + máscara, 2/3 escudo mediano + máscara (pantalla de elegir equipo),
    4/5 escudo pequeño + máscara (clasificación y calendario; la máscara mide 2 px más: contorno),
    6 pabellón, 7 camiseta, 8-11 figuras con las equipaciones.
Máscara: 15 = parte visible, 0 = transparente.
"""
from PIL import Image

# Colores fijos de la paleta global (los índices 1 y 2 cambian según la pantalla: no se usan)
FIXED = [0] + list(range(3, 16))
HDR = 58   # cabecera: 2 + 48 paleta + 1 + 1 ancho + 2 alto + 2 planos + 2 (comprobado con las máscaras)


class DGF:
    def __init__(self, path):
        self.path = path
        self.d = bytearray(open(path, 'rb').read())
        p = self.d[2:50]
        self.palette = [tuple(p[i:i + 3]) for i in range(0, 48, 3)]

    def header(self, o):
        return self.d[o + 51], int.from_bytes(self.d[o + 52:o + 54], 'big'), \
            int.from_bytes(self.d[o + 54:o + 56], 'big')

    def decode(self, o):
        w, h, pl = self.header(o)
        rb = (w + 7) // 8
        px = bytearray(w * h)
        for y in range(h):
            for p in range(pl):
                base = o + HDR + (y * pl + p) * rb
                row = self.d[base:base + rb]
                for x in range(w):
                    if row[x >> 3] >> (7 - (x & 7)) & 1:
                        px[y * w + x] |= 1 << p
        return w, h, px

    def encode(self, o, px):
        w, h, pl = self.header(o)
        assert pl == 4 and len(px) == w * h
        rb = (w + 7) // 8
        for y in range(h):
            for p in range(pl):
                row = bytearray(rb)
                for x in range(w):
                    if px[y * w + x] >> p & 1:
                        row[x >> 3] |= 0x80 >> (x & 7)
                base = o + HDR + (y * pl + p) * rb
                self.d[base:base + rb] = row

    def to_image(self, o, scale=1):
        w, h, px = self.decode(o)
        im = Image.frombytes('P', (w, h), bytes(px))
        im.putpalette([c for rgb in self.palette for c in rgb] + [0] * (768 - 48))
        im = im.convert('RGB')
        return im.resize((w * scale, h * scale), Image.NEAREST) if scale != 1 else im

    def _nearest(self, rgb):
        r, g, b = rgb
        return min(FIXED, key=lambda c: 3 * (self.palette[c][0] - r) ** 2 +
                   4 * (self.palette[c][1] - g) ** 2 + 2 * (self.palette[c][2] - b) ** 2)

    def put_logo(self, o_img, o_mask, logo, border=False):
        """Coloca un logo RGBA en la imagen o_img y genera su máscara en o_mask."""
        w, h, _ = self.header(o_img)
        mw, mh, _ = self.header(o_mask)
        lg = logo.copy()
        lg.thumbnail((w, h), Image.LANCZOS)
        canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        canvas.alpha_composite(lg, ((w - lg.width) // 2, (h - lg.height) // 2))
        px = bytearray(w * h)
        shape = [False] * (w * h)
        cache = {}
        for i, (r, g, b, a) in enumerate(canvas.getdata()):
            if a >= 128:
                shape[i] = True
                key = (r, g, b)
                if key not in cache:
                    cache[key] = self._nearest(key)
                px[i] = cache[key]
        self.encode(o_img, px)
        # máscara: mismo tamaño, o 2 px mayor con contorno de 1 px (escudo pequeño)
        dx, dy = (mw - w) // 2, (mh - h) // 2
        m = bytearray(mw * mh)
        for y in range(h):
            for x in range(w):
                if shape[y * w + x]:
                    for yy in range(y + dy - (1 if border else 0), y + dy + (2 if border else 1)):
                        for xx in range(x + dx - (1 if border else 0), x + dx + (2 if border else 1)):
                            if 0 <= xx < mw and 0 <= yy < mh:
                                m[yy * mw + xx] = 15
        self.encode(o_mask, m)

    def save(self, path=None):
        import os, shutil
        path = path or self.path
        if os.path.exists(path) and not os.path.exists(path + '.BAK'):
            shutil.copy2(path, path + '.BAK')
        if os.path.exists(path):
            os.chmod(path, 0o666)
        open(path, 'wb').write(self.d)


def put_team_shields(dgf, team_gfx, logo):
    """Escudos grande, mediano y pequeño de un equipo ACB (12 punteros gfx)."""
    g = team_gfx
    dgf.put_logo(g[0], g[1], logo)
    dgf.put_logo(g[2], g[3], logo)
    w4, h4, _ = dgf.header(g[4]); w5, h5, _ = dgf.header(g[5])
    dgf.put_logo(g[4], g[5], logo, border=(w5 > w4))
