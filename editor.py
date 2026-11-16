"""
Editor gráfico de PC Basket 4.5  (BASKET96.DBC)

Ejecutar:  python editor.py   (o doble clic en Editor.bat)
"""
from __future__ import annotations

import os
import sys
import textwrap
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dbc import Database, Player, Team  # noqa: E402

try:
    from PIL import Image, ImageTk
    from caras import Faces
    PIL_ERROR = None
except ImportError as _e:  # sin Pillow: el editor funciona, pero sin retratos
    Faces = None
    PIL_ERROR = str(_e)

import equipaciones as eq  # noqa: E402

try:
    import parche
except ImportError:  # sin bsdiff4: el editor funciona, pero sin instalar parches
    parche = None

# Carpeta del programa: la del .exe si está empaquetado, la del .py si no.
HERE = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.abspath(__file__)))

APP_TITLE = "Editor PC Basket 4.5"
DISCLAIMER = (
    "Aviso legal: PC Basket 4.5 es propiedad de sus actuales titulares de la licencia. "
    "Este editor es un proyecto de aficionados, gratuito y sin ánimo de lucro, que no tiene "
    "ninguna relación ni acuerdo con la Liga Endesa (ACB), la NBA, la Euroliga (EuroLeague "
    "Basketball), la EuroCup, sus clubes ni sus jugadores. Los nombres, escudos, imágenes y "
    "fotografías pertenecen a sus respectivos dueños y se usan solo con fines informativos "
    "y de entretenimiento. En ningún caso se distribuye el juego completo: únicamente "
    "este editor y sus archivos asociados."
)
POS_LABELS = ["Base", "Escolta", "Alero", "Ala-pívot", "Pívot"]
SKIN_LABELS = [(0, "Blanca"), (1, "Negra"), (2, "Mulata")]
HAIR_LABELS = [(0, "Calvo"), (1, "Corto / rapado"), (2, "Variante 2"), (3, "Normal")]
BEARD_LABELS = [(0, "Nada"), (1, "Bigote"), (2, "Perilla"), (3, "Barba")]
HAIR_COLOR_LABELS = [(0, "Negro"), (1, "Rubio"), (2, "Castaño")]
SECTION_LABELS = {"ACB": "Liga ACB", "EUROPA": "Europa", "ALLSTAR": "All-Star"}
STAT_COLS = ["T2 anot.", "T2 int.", "T3 anot.", "T3 int.", "TL anot.", "TL int.",
             "Reb. def.", "Reb. of.", "Asist.", "Tapones", "Robos", "Pérdidas",
             "Minutos", "Partidos", "Faltas"]
RATINGS = [("rating1", "Manejo / pase"), ("rating2", "Tiro / ataque"),
           ("rating3", "Rebote / juego interior"), ("rating4", "Defensa / físico")]
BIO_WIDTH = 72

PAD = {"padx": 6, "pady": 4}


# ==========================================================================
# Utilidades de formulario
# ==========================================================================
class Form:
    """Construye filas etiqueta + control enlazadas a un objeto del modelo.

    Cada cambio válido se escribe al momento en el objeto y avisa a la app.
    Los valores no válidos se marcan en rojo y no se aplican.
    """

    def __init__(self, app: "App", parent: ttk.Frame):
        self.app = app
        self.parent = parent
        self.obj = None
        self.row = 0
        self.bindings = []      # (var, getter, setter, widget)
        self.loading = False

    # --- creación de filas -------------------------------------------------
    def _label(self, text):
        ttk.Label(self.parent, text=text).grid(row=self.row, column=0, sticky="w", **PAD)

    def _hint(self, text, style="Hint.TLabel"):
        lbl = ttk.Label(self.parent, text=text, style=style)
        lbl.grid(row=self.row, column=2, sticky="w", **PAD)
        return lbl

    def text(self, label, attr, width=40, hint="", maxlen=255, on_change=None):
        self._label(label)
        var = tk.StringVar()
        ent = ttk.Entry(self.parent, textvariable=var, width=width)
        ent.grid(row=self.row, column=1, sticky="we", **PAD)
        hint_lbl = self._hint(hint) if hint else None

        def setter(v):
            try:
                v.encode("latin-1")
            except UnicodeEncodeError:
                raise ValueError
            if len(v) > maxlen:
                if hint_lbl:
                    hint_lbl.configure(style="Warn.TLabel")
            elif hint_lbl:
                hint_lbl.configure(style="Hint.TLabel")
            setattr(self.obj, attr, v)
            if on_change:
                on_change(v)

        self._bind(var, lambda: getattr(self.obj, attr), setter, ent)
        self.row += 1
        return var

    def number(self, label, attr, lo, hi, width=8, hint="", fmt=None):
        self._label(label)
        var = tk.StringVar()
        sp = ttk.Spinbox(self.parent, textvariable=var, from_=lo, to=hi, width=width)
        sp.grid(row=self.row, column=1, sticky="w", **PAD)
        extra = self._hint(hint) if (hint or fmt) else None

        def setter(v):
            n = int(v)
            if not lo <= n <= hi:
                raise ValueError
            setattr(self.obj, attr, n)
            if fmt and extra:
                extra.configure(text=fmt(n))

        def getter():
            n = getattr(self.obj, attr)
            if fmt and extra:
                extra.configure(text=fmt(n))
            return n

        self._bind(var, getter, setter, sp)
        self.row += 1
        return var

    def choice(self, label, attr, options, hint=""):
        """options: lista de (valor, texto). Valores desconocidos se muestran tal cual."""
        self._label(label)
        var = tk.StringVar()
        cb = ttk.Combobox(self.parent, textvariable=var, state="readonly", width=22)
        cb.grid(row=self.row, column=1, sticky="w", **PAD)
        if hint:
            self._hint(hint)
        to_text = {v: t for v, t in options}

        def getter():
            v = getattr(self.obj, attr)
            vals = [t for _, t in options]
            if v not in to_text:
                vals.append(f"Valor {v}")
            cb.configure(values=vals)
            return to_text.get(v, f"Valor {v}")

        def setter(text):
            for v, t in options:
                if t == text:
                    setattr(self.obj, attr, v)
                    return
            if text.startswith("Valor "):
                return
            raise ValueError

        self._bind(var, getter, setter, cb)
        self.row += 1
        return var

    def check(self, label, attr, hint=""):
        self._label(label)
        var = tk.IntVar()
        ch = ttk.Checkbutton(self.parent, variable=var)
        ch.grid(row=self.row, column=1, sticky="w", **PAD)
        if hint:
            self._hint(hint)
        self._bind(var, lambda: 1 if getattr(self.obj, attr) else 0,
                   lambda v: setattr(self.obj, attr, 1 if int(v) else 0), ch)
        self.row += 1

    def section(self, title):
        ttk.Label(self.parent, text=title, style="Section.TLabel").grid(
            row=self.row, column=0, columnspan=3, sticky="w", padx=6, pady=(14, 2))
        self.row += 1

    # --- enlace -----------------------------------------------------------
    def _bind(self, var, getter, setter, widget):
        def on_write(*_):
            if self.loading or self.obj is None:
                return
            try:
                setter(var.get())
                self._mark(widget, ok=True)
                self.app.mark_dirty()
            except (ValueError, tk.TclError):
                self._mark(widget, ok=False)

        var.trace_add("write", on_write)
        self.bindings.append((var, getter, setter, widget))

    @staticmethod
    def _mark(widget, ok):
        if isinstance(widget, ttk.Spinbox):
            widget.configure(style="TSpinbox" if ok else "Error.TSpinbox")
        elif isinstance(widget, ttk.Entry):
            widget.configure(style="TEntry" if ok else "Error.TEntry")

    def load(self, obj):
        self.obj = obj
        self.loading = True
        try:
            for var, getter, _, widget in self.bindings:
                var.set(getter())
                self._mark(widget, ok=True)
        finally:
            self.loading = False


class TextTab:
    """Pestaña de texto largo (biografía / historia) guardado como lista de líneas."""

    def __init__(self, app, parent, attr_get, attr_set, help_text):
        self.app = app
        self.get, self.set = attr_get, attr_set
        self.obj = None
        self.loading = False
        top = ttk.Frame(parent)
        top.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(top, text=help_text, style="Hint.TLabel").pack(side="left")
        ttk.Button(top, text="Reajustar líneas", command=self.rewrap).pack(side="right")
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.txt = tk.Text(frame, wrap="none", font=("Consolas", 10), undo=True,
                           relief="solid", borderwidth=1)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt.pack(side="left", fill="both", expand=True)
        self.txt.bind("<<Modified>>", self._modified)

    def load(self, obj):
        self.obj = obj
        self.loading = True
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", "\n".join(l.rstrip() for l in self.get(obj)))
        self.txt.edit_reset()
        self.txt.edit_modified(False)
        self.loading = False

    def _modified(self, _=None):
        if self.loading or not self.txt.edit_modified():
            return
        self.txt.edit_modified(False)
        self.commit()

    def commit(self):
        if self.obj is None:
            return
        content = self.txt.get("1.0", "end-1c")
        lines = content.split("\n") if content else []
        # Sólo guarda si realmente cambió algo (evita perder espacios originales)
        if [l.rstrip() for l in self.get(self.obj)] != lines:
            try:
                for l in lines:
                    l.encode("cp437")
            except UnicodeEncodeError:
                return
            self.set(self.obj, [l + " " for l in lines])
            self.app.mark_dirty()

    def rewrap(self):
        content = self.txt.get("1.0", "end-1c")
        paras, cur = [], []
        for line in content.split("\n"):
            if line.strip().startswith("∙") and cur:
                paras.append(" ".join(cur)); cur = []
            if line.strip():
                cur.append(line.strip())
        if cur:
            paras.append(" ".join(cur))
        out = []
        for p in paras:
            out += textwrap.wrap(p, BIO_WIDTH) or [""]
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", "\n".join(out))
        self.commit()


# ==========================================================================
# Retratos
# ==========================================================================
class CropDialog(tk.Toplevel):
    """Ventana para elegir qué parte de la foto se usa como retrato."""

    VIEW = 460

    def __init__(self, app: "App", img: "Image.Image", slot, small=False):
        """slot: imagen de CARAS.BIN. small=True: cara pequeña de la pantalla previa
        al partido (24x24, 16 colores, en BASKET96.DGF)."""
        super().__init__(app)
        self.title("Recortar retrato")
        self.transient(app)
        self.resizable(False, False)
        self.app, self.faces, self.slot, self.small = app, app.faces, slot, small
        self.result = None
        fw, fh = (24, 24) if small else self.faces.size(slot)
        self.aspect = fw / fh
        self.src = img.convert("RGBA")
        W, H = self.src.size
        self.k = min(self.VIEW / W, self.VIEW / H, 4)
        self.disp = self.src.resize((max(1, int(W * self.k)), max(1, int(H * self.k))))
        # Selección inicial: cuadrado centrado arriba (donde suele estar la cara)
        side = min(W, H / self.aspect) * 0.75
        self.sel = [(W - side) / 2, max(0, H * 0.04), side]   # x, y, ancho (imagen original)
        self._clamp()

        body = ttk.Frame(self, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Arrastra el recuadro hasta la cara.  Rueda del ratón = tamaño.",
                  style="Hint.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        self.canvas = tk.Canvas(body, width=self.disp.width, height=self.disp.height,
                                highlightthickness=1, highlightbackground="#999",
                                cursor="fleur")
        self.canvas.grid(row=1, column=0, rowspan=4, pady=8)
        self._tk_disp = ImageTk.PhotoImage(self.disp)
        self.canvas.create_image(0, 0, anchor="nw", image=self._tk_disp)
        self.rect = self.canvas.create_rectangle(0, 0, 1, 1, outline="#ffcc00", width=2)
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<MouseWheel>", self._wheel)

        side_panel = ttk.Frame(body)
        side_panel.grid(row=1, column=1, sticky="n", padx=(14, 0), pady=8)
        ttk.Label(side_panel, text="Resultado en el juego", style="Section.TLabel").pack(anchor="w")
        self.prev_big = ttk.Label(side_panel)
        self.prev_big.pack(anchor="w", pady=6)
        ttk.Label(side_panel, text="Tamaño real (x1 y x2):", style="Hint.TLabel").pack(anchor="w")
        row = ttk.Frame(side_panel)
        row.pack(anchor="w", pady=4)
        self.prev_1 = ttk.Label(row)
        self.prev_1.pack(side="left", padx=(0, 8))
        self.prev_2 = ttk.Label(row)
        self.prev_2.pack(side="left")
        ttk.Label(side_panel, text="Tamaño del recuadro").pack(anchor="w", pady=(14, 0))
        maxside = min(W, H / self.aspect)
        self.size_var = tk.DoubleVar(value=self.sel[2])
        ttk.Scale(side_panel, from_=8, to=maxside, variable=self.size_var, length=200,
                  command=lambda v: self._resize(float(v))).pack(anchor="w")
        ttk.Label(side_panel, text="Consejo: encuadra de la barbilla\na la frente, como las "
                  "caras\noriginales del juego.", style="Hint.TLabel").pack(anchor="w", pady=10)

        btns = ttk.Frame(body)
        btns.grid(row=5, column=0, columnspan=2, sticky="e")
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(btns, text="✔  Usar este retrato", command=self._ok).pack(side="right", padx=8)
        self.bind("<Escape>", lambda _: self.destroy())
        self.bind("<Return>", lambda _: self._ok())
        self._update()
        self.grab_set()
        self.focus_set()

    def _clamp(self):
        W, H = self.src.size
        x, y, s = self.sel
        s = max(8, min(s, W, H * self.aspect))
        x = max(0, min(x, W - s))
        y = max(0, min(y, H - s / self.aspect))
        self.sel = [x, y, s]

    def _press(self, e):
        self._last = (e.x, e.y)

    def _drag(self, e):
        dx, dy = (e.x - self._last[0]) / self.k, (e.y - self._last[1]) / self.k
        self._last = (e.x, e.y)
        self.sel[0] += dx
        self.sel[1] += dy
        self._clamp()
        self._update()

    def _wheel(self, e):
        self._resize(self.sel[2] * (0.93 if e.delta > 0 else 1.07))

    def _resize(self, new):
        x, y, s = self.sel
        cx, cy = x + s / 2, y + s / self.aspect / 2
        self.sel = [cx - new / 2, cy - new / self.aspect / 2, new]
        self._clamp()
        if abs(self.size_var.get() - self.sel[2]) > 0.5:
            self.size_var.set(self.sel[2])
        self._update()

    def _crop(self):
        x, y, s = self.sel
        return self.src.crop((int(x), int(y), int(x + s), int(y + s / self.aspect)))

    def _update(self):
        x, y, s = self.sel
        k = self.k
        self.canvas.coords(self.rect, x * k, y * k, (x + s) * k, (y + s / self.aspect) * k)
        if self.small:
            from caras import small_from_image, SMALL_PALETTE
            fw = fh = 24
            crop = self._crop()
            bg = Image.new("RGBA", crop.size, (0, 0, 0, 255))
            bg.alpha_composite(crop)
            self.pixels = small_from_image(bg.convert("RGB"), 1.15, 1.15)
            im = Image.new("RGB", (fw, fh))
            im.putdata([SMALL_PALETTE[v] for v in self.pixels])
        else:
            fw, fh = self.faces.size(self.slot)
            self.pixels = self.faces.convert(self._crop(), fw, fh, self.faces.colors_for(self.slot))
            im = Image.frombytes("P", (fw, fh), self.pixels)
            im.putpalette(self.faces.flat_palette)
            im = im.convert("RGB")
        self._p = [ImageTk.PhotoImage(im.resize((fw * 7, fh * 7), Image.NEAREST)),
                   ImageTk.PhotoImage(im),
                   ImageTk.PhotoImage(im.resize((fw * 2, fh * 2), Image.NEAREST))]
        self.prev_big.configure(image=self._p[0])
        self.prev_1.configure(image=self._p[1])
        self.prev_2.configure(image=self._p[2])

    def _ok(self):
        self.result = self.pixels
        self.destroy()


class PortraitPanel(ttk.Frame):
    """Muestra y permite cambiar una imagen de CARAS.BIN (retrato o escudo)."""

    def __init__(self, app: "App", parent, kind="retrato"):
        super().__init__(parent, padding=12)
        self.app, self.kind = app, kind
        self.slot = None
        self.name = ""

        left = ttk.Frame(self)
        left.pack(side="left", anchor="n")
        self.big = tk.Label(left, bg="#202020", width=192, height=192,
                            relief="solid", borderwidth=1)
        self.big.pack()
        ttk.Label(left, text="Tamaño real en el juego:", style="Hint.TLabel").pack(anchor="w", pady=(10, 2))
        row = ttk.Frame(left)
        row.pack(anchor="w")
        self.small1 = ttk.Label(row)
        self.small1.pack(side="left", padx=(0, 10))
        self.small2 = ttk.Label(row)
        self.small2.pack(side="left")

        right = ttk.Frame(self)
        right.pack(side="left", anchor="n", padx=24, fill="x", expand=True)
        self.title = ttk.Label(right, text="", style="Section.TLabel")
        self.title.pack(anchor="w")
        self.info = ttk.Label(right, text="", style="Hint.TLabel", justify="left")
        self.info.pack(anchor="w", pady=(2, 14))
        self.buttons = []
        is_logo = kind == "escudo"
        for text, cmd in [("📷  Importar imagen…", self.import_image),
                          ("💾  Exportar como PNG…", self.export),
                          ("✖  Dejar en negro" if is_logo else "✖  Quitar foto (dejar en negro)",
                           self.clear),
                          ("↺  Deshacer cambios en esta imagen", self.restore)]:
            b = ttk.Button(right, text=text, command=cmd, width=34)
            b.pack(anchor="w", pady=3)
            self.buttons.append(b)
        if is_logo:
            tip = ("Admite PNG, JPG, BMP o GIF. Usa el escudo sobre fondo liso.\n"
                   "Al importar podrás elegir el recorte. Se reduce a 24×24 píxeles\n"
                   "con los colores de la paleta del juego.")
        else:
            tip = ("Admite PNG, JPG, BMP o GIF. Lo mejor es una foto de la cara de frente,\n"
                   "a ser posible con fondo oscuro (las caras originales tienen fondo negro).\n"
                   "Al importar podrás elegir el recorte. La imagen se reduce a 24×24\n"
                   "píxeles con los colores de la paleta del juego.\n"
                   "El retrato aparece en el marcador cuando el jugador anota.")
        self.help = ttk.Label(right, style="Hint.TLabel", justify="left", text=tip)
        self._tip = tip
        self.help.pack(anchor="w", pady=(16, 0))
        self.msg = ttk.Label(self, text="", style="Hint.TLabel", wraplength=520, justify="left")

    # ---- cara pequeña de la pantalla previa (jugadores sin retrato en CARAS.BIN) ----
    def _small_image(self, scale):
        from caras import SMALL_PALETTE
        w, h, px = self.app.dgf.decode(self.small_ptr)
        im = Image.new("RGB", (w, h))
        im.putdata([SMALL_PALETTE[v] for v in px])
        return im.resize((w * scale, h * scale), Image.NEAREST) if scale != 1 else im

    def _load_small(self, name, note):
        for b in self.buttons:
            b.state(["!disabled"])
        self.title.configure(text=f"Cara de {name}")
        cur = bytes(self.app.dgf.decode(self.small_ptr)[2])
        opened = self.app.small_opened.setdefault(self.small_ptr, cur)
        estado = "SIN FOTO (sale en negro)" if not any(cur) else "tiene imagen"
        cambiado = "  ·  modificada" if cur != opened else ""
        self.info.configure(text="Cara de la pantalla previa al partido (24×24, 16 colores)  ·  "
                                 f"{estado}{cambiado}" + (f"\n{note}" if note else ""))
        self.help.configure(text="Admite PNG, JPG, BMP o GIF. Al importar podrás elegir el "
                                 "recorte.\nSe reduce a 24×24 píxeles con los 16 colores de esa "
                                 "pantalla.")
        self._imgs = [ImageTk.PhotoImage(self._small_image(8)),
                      ImageTk.PhotoImage(self._small_image(1)),
                      ImageTk.PhotoImage(self._small_image(2))]
        self.big.configure(image=self._imgs[0], width=192, height=192)
        self.small1.configure(image=self._imgs[1])
        self.small2.configure(image=self._imgs[2])

    def _set_small(self, px):
        from caras import SMALL_PALETTE
        dg = self.app.dgf
        dg.encode(self.small_ptr, px)
        dg.d[self.small_ptr + 2:self.small_ptr + 50] = bytes(v for rgb in SMALL_PALETTE for v in rgb)
        self.app.menu_dirty = True      # hay que guardar BASKET96.DGF
        self.app.mark_dirty()
        self.load(None, self.name, self._note, self.small_ptr)

    def load(self, slot, name, note="", small_ptr=None):
        self.slot, self.name, self._note = slot, name, note
        self.small_ptr = None
        faces = self.app.faces
        dg = self.app.dgf
        if slot is None and small_ptr and small_ptr > 1 and dg is not None and faces is not None \
                and dg.header(small_ptr)[:3] == (24, 24, 4):
            self.small_ptr = small_ptr
            self._load_small(name, note)
            return
        self.help.configure(text=self._tip)
        if faces is None or slot is None:
            self.big.configure(image="", text="", width=24, height=12)
            self.small1.configure(image="")
            self.small2.configure(image="")
            for b in self.buttons:
                b.state(["disabled"])
            self.title.configure(text="Sin " + self.kind)
            self.info.configure(text=note or self.app.faces_error or "")
            return
        for b in self.buttons:
            b.state(["!disabled"])
        self.title.configure(text=f"{self.kind.capitalize()} de {name}")
        st = faces.state(slot)
        estado = {"foto": "tiene imagen", "sin foto": "SIN FOTO (sale en negro)",
                  "hueco libre": "hueco libre"}[st]
        cambiado = "  ·  modificado" if bytes(faces.faces[slot][2]) != faces.original[slot] else ""
        self.info.configure(text=f"Imagen nº {slot} de CARAS.BIN  ·  {estado}{cambiado}"
                                 + (f"\n{note}" if note else ""))
        self._imgs = [ImageTk.PhotoImage(faces.to_image(slot, 8)),
                      ImageTk.PhotoImage(faces.to_image(slot, 1)),
                      ImageTk.PhotoImage(faces.to_image(slot, 2))]
        self.big.configure(image=self._imgs[0], width=192, height=192)
        self.small1.configure(image=self._imgs[1])
        self.small2.configure(image=self._imgs[2])

    def _changed(self):
        self.app.mark_dirty()
        self.load(self.slot, self.name, "")
        self.app.on_faces_changed()

    def import_image(self):
        path = filedialog.askopenfilename(
            title="Elegir imagen",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Todos", "*.*")])
        if not path:
            return
        try:
            img = Image.open(path)
            img.load()
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(APP_TITLE, f"No se pudo abrir la imagen:\n{e}")
            return
        dlg = CropDialog(self.app, img, self.slot, small=self.small_ptr is not None)
        self.wait_window(dlg)
        if dlg.result:
            if self.small_ptr is not None:
                self._set_small(dlg.result)
                return
            self.app.faces.set_pixels(self.slot, dlg.result)
            self._changed()

    def export(self):
        path = filedialog.asksaveasfilename(
            title="Exportar imagen", defaultextension=".png",
            initialfile=f"{self.name}.png".replace("/", "-").replace('"', ""),
            filetypes=[("PNG", "*.png")])
        if path:
            scale = 4
            if self.small_ptr is not None:
                self._small_image(scale).save(path)
            else:
                self.app.faces.to_image(self.slot, scale).save(path)
            messagebox.showinfo(APP_TITLE, f"Guardada (ampliada x{scale}) en:\n{path}")

    def clear(self):
        if self.small_ptr is not None:
            self._set_small(bytes(24 * 24))
            return
        self.app.faces.clear(self.slot)
        self._changed()

    def restore(self):
        if self.small_ptr is not None:
            # «deshacer» = volver a como estaba al abrir el archivo
            px = self.app.small_opened.get(self.small_ptr)
            if px is not None:
                self._set_small(px)
            return
        self.app.faces.restore(self.slot)
        self._changed()


# ==========================================================================
# Editor de jugador
# ==========================================================================
class PlayerEditor(ttk.Frame):
    def __init__(self, app: "App", parent):
        super().__init__(parent)
        self.app = app
        self.player: Player | None = None

        head = ttk.Frame(self)
        head.pack(fill="x", padx=10, pady=(10, 4))
        self.title = ttk.Label(head, text="", style="Title.TLabel")
        self.title.pack(side="left")
        self.subtitle = ttk.Label(head, text="", style="Hint.TLabel")
        self.subtitle.pack(side="left", padx=12, pady=(6, 0))

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.nb = nb
        self.forms = []

        # ---- Datos --------------------------------------------------------
        t1 = self._scroll_tab(nb, "  Datos  ")
        f = Form(app, t1); self.forms.append(f)
        f.section("Nombres")
        f.text("Nombre completo", "full_name", hint="Ficha de la base de datos",
               on_change=lambda _: self._refresh_title())
        f.text("Nombre corto", "short_name", hint="Listas y plantilla",
               on_change=lambda _: self._refresh_title())
        f.text("Nombre en listados", "surname", width=20, maxlen=15,
               hint="Máx. 15 caracteres (se ve en el partido)")
        f.section("Equipo")
        f.number("Dorsal", "dorsal", 0, 99)
        f.choice("Posición", "position", list(enumerate(POS_LABELS)))
        f.number("Orden en plantilla", "roster_order", 0, 30,
                 hint="1-5 = quinteto titular")
        f.check("Extranjero", "foreign", hint="Cuenta para el cupo de extranjeros")
        f.number("Valor de mercado", "value", 0, 65535, hint="millones de pesetas")
        f.section("Biografía básica")
        f.text("Lugar de nacimiento", "birthplace")
        f.text("Fecha de nacimiento", "birthdate", width=12, hint="dd-mm-aa  (o «-»)")
        f.text("Procedencia", "prev_club", hint="p. ej. «Joventut (96)»")

        # ---- Físico y aspecto ---------------------------------------------
        t2 = self._scroll_tab(nb, "  Físico y aspecto  ")
        f = Form(app, t2); self.forms.append(f)
        f.section("Físico")
        f.number("Altura (cm)", "height_cm", 100, 355,
                 fmt=lambda n: f"{n / 100:.2f} m".replace(".", ","))
        f.number("Peso (kg)", "weight", 30, 255)
        f.section("Aspecto en el partido")
        f.choice("Color de piel", "skin", SKIN_LABELS)
        f.choice("Pelo", "hair", HAIR_LABELS)
        f.choice("Color de pelo", "hair_color", HAIR_COLOR_LABELS)
        f.choice("Barba / bigote", "beard", BEARD_LABELS)

        # ---- Valoraciones -------------------------------------------------
        t3 = self._scroll_tab(nb, "  Valoraciones  ")
        self._build_ratings(t3)

        # ---- Retrato -------------------------------------------------------
        tr = ttk.Frame(nb)
        nb.add(tr, text="  Retrato  ")
        self.portrait = PortraitPanel(app, tr)
        self.portrait.pack(fill="both", expand=True)

        # ---- Biografía ----------------------------------------------------
        t4 = ttk.Frame(nb)
        nb.add(t4, text="  Biografía  ")
        self.bio = TextTab(app, t4, lambda o: o.bio, lambda o, v: setattr(o, "bio", v),
                           "Texto de la ficha. Líneas de ~72 caracteres.")

        # ---- Estadísticas -------------------------------------------------
        t5 = ttk.Frame(nb)
        nb.add(t5, text="  Estadísticas  ")
        self._build_stats(t5)

    # ----------------------------------------------------------------------
    def _scroll_tab(self, nb, title):
        outer = ttk.Frame(nb)
        nb.add(outer, text=title)
        inner = ttk.Frame(outer)
        inner.pack(fill="both", expand=True, padx=12, pady=6)
        inner.columnconfigure(1, weight=0)
        return inner

    def _build_ratings(self, parent):
        f = Form(self.app, parent); self.forms.append(f)
        f.section("Valoraciones (0-100)")
        ttk.Label(parent, text="Nombres deducidos de las estadísticas reales; "
                  "confírmalos en la ficha del mánager.", style="Hint.TLabel").grid(
            row=f.row, column=0, columnspan=3, sticky="w", padx=6)
        f.row += 1
        for attr, label in RATINGS:
            f._label(label)
            var = tk.StringVar()
            box = ttk.Frame(parent)
            box.grid(row=f.row, column=1, columnspan=2, sticky="w", **PAD)
            scale = ttk.Scale(box, from_=0, to=100, length=260,
                              command=lambda v, var=var: var.set(str(round(float(v)))))
            scale.pack(side="left")
            sp = ttk.Spinbox(box, textvariable=var, from_=0, to=100, width=5)
            sp.pack(side="left", padx=8)
            bar = ttk.Label(box, text="", width=10)
            bar.pack(side="left")

            def setter(v, attr=attr, scale=scale, bar=bar):
                n = int(v)
                if not 0 <= n <= 100:
                    raise ValueError
                setattr(f.obj, attr, n)
                scale.set(n)
                bar.configure(text=self._grade(n))

            def getter(attr=attr, scale=scale, bar=bar):
                n = getattr(f.obj, attr)
                scale.set(n)
                bar.configure(text=self._grade(n))
                return n

            f._bind(var, getter, setter, sp)
            f.row += 1

    @staticmethod
    def _grade(n):
        return ("Excelente" if n >= 90 else "Muy bueno" if n >= 80 else
                "Bueno" if n >= 70 else "Normal" if n >= 60 else "Flojo")

    def _build_stats(self, parent):
        top = ttk.Frame(parent)
        top.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(top, text="Mostrar:").pack(side="left")
        self.stats_mode = tk.StringVar(value="Liga regular")
        cb = ttk.Combobox(top, textvariable=self.stats_mode, state="readonly", width=14,
                          values=["Liga regular", "Play-off"])
        cb.pack(side="left", padx=6)
        cb.bind("<<ComboboxSelected>>", lambda _: self._fill_stats())
        ttk.Label(top, text="Doble clic en una cifra para editarla.",
                  style="Hint.TLabel").pack(side="left", padx=12)

        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        cols = ["temp", "equipo", "pts"] + [f"s{i}" for i in range(15)]
        self.stats = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        heads = ["Temporada", "Equipo", "Puntos"] + STAT_COLS
        for c, h in zip(cols, heads):
            self.stats.heading(c, text=h)
            w = 80 if c == "temp" else 130 if c == "equipo" else 62
            self.stats.column(c, width=w, minwidth=40,
                              anchor="w" if c == "equipo" else "center", stretch=False)
        xs = ttk.Scrollbar(frame, orient="horizontal", command=self.stats.xview)
        ys = ttk.Scrollbar(frame, orient="vertical", command=self.stats.yview)
        self.stats.configure(xscrollcommand=xs.set, yscrollcommand=ys.set)
        self.stats.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.stats.bind("<Double-1>", self._edit_stat)

    def _stat_rows(self):
        p = self.player
        rows = [("Actual", p.team, p.current)]
        for s in p.seasons:
            rows.append((f"{s.year % 100:02d}-{(s.year + 1) % 100:02d}", s.team, s.stats))
        return rows

    def _fill_stats(self):
        self.stats.delete(*self.stats.get_children())
        if not self.player:
            return
        off = 0 if self.stats_mode.get() == "Liga regular" else 15
        for i, (temp, team, st) in enumerate(self._stat_rows()):
            v = st[off:off + 15]
            pts = 2 * v[0] + 3 * v[2] + v[4]
            self.stats.insert("", "end", iid=str(i), values=[temp, team, pts] + v)

    def _edit_stat(self, event):
        row = self.stats.identify_row(event.y)
        col = self.stats.identify_column(event.x)
        if not row or not col:
            return
        ci = int(col[1:]) - 1
        if ci < 3:
            return
        stat_idx = ci - 3 + (0 if self.stats_mode.get() == "Liga regular" else 15)
        target = self._stat_rows()[int(row)][2]
        x, y, w, h = self.stats.bbox(row, col)
        var = tk.StringVar(value=str(target[stat_idx]))
        ent = ttk.Entry(self.stats, textvariable=var, justify="center")
        ent.place(x=x, y=y, width=w, height=h)
        ent.focus_set()
        ent.select_range(0, "end")

        def done(commit=True):
            if commit:
                try:
                    n = int(var.get())
                    if 0 <= n <= 65535 and n != target[stat_idx]:
                        target[stat_idx] = n
                        self.app.mark_dirty()
                except ValueError:
                    pass
            ent.destroy()
            self._fill_stats()

        ent.bind("<Return>", lambda _: done())
        ent.bind("<FocusOut>", lambda _: done())
        ent.bind("<Escape>", lambda _: done(False))

    # ----------------------------------------------------------------------
    def _refresh_title(self):
        p = self.player
        self.title.configure(text=p.short_name)
        pos = POS_LABELS[p.position] if p.position < 5 else "?"
        self.subtitle.configure(
            text=f"{p.team}  ·  {pos}  ·  nº {p.dorsal}  ·  {p.height_cm / 100:.2f} m".replace(".", ","))
        self.app.refresh_current_label()

    def load(self, player: Player, ti: int, pi: int):
        self.player = player
        for f in self.forms:
            f.load(player)
        self.bio.load(player)
        self._fill_stats()
        self._refresh_title()
        slot, note = None, ""
        if self.app.faces:
            slot = self.app.faces.player_slot(ti, pi)
            if slot is None:
                note = ("Solo los equipos de la Liga ACB tienen retratos (12 por equipo).\n"
                        "Cuando anota este equipo, en el partido sale su escudo:\n"
                        "puedes cambiarlo en la ficha del equipo, pestaña «Escudo».")
        if slot is None:
            note = ("Este equipo no tiene retratos para el marcador del partido (solo los\n"
                    "tienen los equipos ACB). Aquí se cambia la cara de la pantalla previa.")
        self.portrait.load(slot, player.short_name, note,
                           small_ptr=player.gfx[1] if len(player.gfx) > 1 else None)


# ==========================================================================
# Editor de equipo
# ==========================================================================
class TeamEditor(ttk.Frame):
    def __init__(self, app: "App", parent):
        super().__init__(parent)
        self.app = app
        self.team: Team | None = None
        self._old_short = ""

        head = ttk.Frame(self)
        head.pack(fill="x", padx=10, pady=(10, 4))
        self.title = ttk.Label(head, text="", style="Title.TLabel")
        self.title.pack(side="left")
        self.subtitle = ttk.Label(head, text="", style="Hint.TLabel")
        self.subtitle.pack(side="left", padx=12, pady=(6, 0))

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        t1 = ttk.Frame(nb)
        nb.add(t1, text="  Club  ")
        inner = ttk.Frame(t1)
        inner.pack(fill="both", expand=True, padx=12, pady=6)
        f = self.form = Form(app, inner)
        f.section("Nombres")
        f.text("Nombre en menús", "short_name", width=24,
               hint="Nombre corto del equipo", on_change=self._short_changed)
        f.text("Nombre largo", "long_name", on_change=lambda _: self._refresh_title())
        f.text("Nombre oficial", "club_name")
        self.sync = tk.IntVar(value=1)
        ttk.Checkbutton(inner, variable=self.sync,
                        text="Al cambiar el nombre en menús, cambiarlo también en la "
                             "ficha de sus jugadores").grid(row=f.row, column=1,
                                                            columnspan=2, sticky="w", **PAD)
        f.row += 1
        f.section("Club")
        f.text("Pabellón", "arena")
        f.number("Aforo", "capacity", 0, 65535, width=10, hint="espectadores")
        f.text("Dirección", "address")
        f.text("Presidente", "president")
        f.text("Patrocinador", "sponsor")
        f.number("Presupuesto", "budget", 0, 4_294_967_295, width=16,
                 fmt=lambda n: f"{n:,} pts".replace(",", "."))

        self.coach_form = Form(app, inner)
        self.coach_form.row = f.row
        self.coach_form.section("Entrenador")
        self.coach_form.text("Nombre completo", "full_name")
        self.coach_form.text("Nombre corto", "short_name")

        t2 = ttk.Frame(nb)
        nb.add(t2, text="  Historia  ")
        self.hist = TextTab(app, t2, lambda o: o.history,
                            lambda o, v: setattr(o, "history", v),
                            "Historia del club que aparece en la base de datos.")
        t3 = ttk.Frame(nb)
        nb.add(t3, text="  Bio del entrenador  ")
        self.cbio = TextTab(app, t3, lambda o: o.bio, lambda o, v: setattr(o, "bio", v),
                            "Biografía del entrenador.")

        self.nb = nb
        self.tab_faces = ttk.Frame(nb)
        nb.add(self.tab_faces, text="  Retratos  ")
        self.grid_box = ttk.Frame(self.tab_faces, padding=12)
        self.logo_panel = PortraitPanel(app, self.tab_faces, kind="escudo")
        self.kit_panel = KitPanel(app, nb)
        nb.add(self.kit_panel, text="  Equipación  ")
        self.team_idx = 0

    def build_faces_tab(self):
        """Rejilla de retratos (ACB) o panel del escudo (resto de equipos)."""
        for w in self.grid_box.winfo_children():
            w.destroy()
        self.grid_box.pack_forget()
        self.logo_panel.pack_forget()
        faces, ti, t = self.app.faces, self.team_idx, self.team
        if faces is None:
            self.nb.tab(self.tab_faces, text="  Retratos  ")
            ttk.Label(self.grid_box, text=self.app.faces_error or "", style="Hint.TLabel").grid()
            self.grid_box.pack(fill="both", expand=True)
            return
        if faces.player_slot(ti, 0) is None:
            self.nb.tab(self.tab_faces, text="  Escudo  ")
            self.logo_panel.load(faces.logo_slot(ti), t.short_name,
                                 "Sale en el marcador del partido cuando anota\n"
                                 "cualquier jugador de este equipo.")
            self.logo_panel.pack(fill="both", expand=True)
            return
        self.nb.tab(self.tab_faces, text="  Retratos  ")
        ttk.Label(self.grid_box, text="Haz clic en un retrato para abrir la ficha del jugador "
                  "y cambiarlo.", style="Hint.TLabel").grid(row=0, column=0, columnspan=6,
                                                           sticky="w", pady=(0, 8))
        self._thumbs = []
        for s in range(12):
            slot = faces.player_slot(ti, s)
            cell = ttk.Frame(self.grid_box, padding=4)
            cell.grid(row=1 + s // 6, column=s % 6, padx=6, pady=6, sticky="n")
            img = ImageTk.PhotoImage(faces.to_image(slot, 4))
            self._thumbs.append(img)
            lbl = tk.Label(cell, image=img, relief="solid", borderwidth=1, cursor="hand2")
            lbl.pack()
            if s < len(t.players):
                p = t.players[s]
                st = faces.state(slot)
                ttk.Label(cell, text=p.short_name, wraplength=110, justify="center").pack()
                ttk.Label(cell, text="sin foto" if st != "foto" else f"nº {p.dorsal}",
                          style="Warn.TLabel" if st != "foto" else "Hint.TLabel").pack()
                lbl.bind("<Button-1>", lambda _e, s=s: self.app.select_player(ti, s, tab="Retrato"))
            else:
                ttk.Label(cell, text="(hueco libre)", style="Hint.TLabel").pack()
        self.grid_box.pack(fill="both", expand=True)

    def _short_changed(self, new):
        old = self._old_short
        if self.sync.get() and old and new != old:
            for p in self.team.players:
                if p.team == old:
                    p.team = new
            if self.team.tag == old:
                self.team.tag = new
        self._old_short = new
        self._refresh_title()

    def _refresh_title(self):
        t = self.team
        self.title.configure(text=t.short_name)
        self.subtitle.configure(text=f"{t.long_name}  ·  {SECTION_LABELS[t.kind]}  ·  "
                                     f"{len(t.players)} jugadores")
        self.app.refresh_current_label()

    def load(self, team: Team, ti: int):
        self.team = team
        self.team_idx = ti
        self._old_short = team.short_name
        self.form.load(team)
        self.coach_form.load(team.coach)
        self.hist.load(team)
        self.cbio.load(team.coach)
        self._refresh_title()
        self.build_faces_tab()
        self.kit_panel.load(team, ti)


# ==========================================================================
# Equipaciones (partido y menús)
# ==========================================================================
class KitPanel(ttk.Frame):
    """Colores de la equipación de un equipo: en el partido y en los menús."""

    PREVIEW = [("TLIBRE.EMP", 0, "De frente"), ("CORRER.EMP", 0, "De espaldas"),
               ("PASEPEC2.EMP", 6, "De lado")]

    def __init__(self, app: "App", parent):
        super().__init__(parent, padding=10)
        self.app = app
        self.ti = 0
        self.alt = tk.IntVar(value=0)
        self.auto_clash = tk.IntVar(value=1)
        self.auto_menu = tk.IntVar(value=1)
        self._imgs = []
        self._swatch_cache = {}
        self.body = ttk.Frame(self)
        self.msg = ttk.Label(self, text="", style="Hint.TLabel", justify="left")

    # ---- construcción ------------------------------------------------------
    def _build(self):
        for w in self.body.winfo_children():
            w.destroy()
        b = self.body
        top = ttk.Frame(b)
        top.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        ttk.Radiobutton(top, text="Equipación principal", variable=self.alt, value=0,
                        command=self.refresh).pack(side="left")
        ttk.Radiobutton(top, text="Equipación alternativa (de visitante, si choca de color)",
                        variable=self.alt, value=1, command=self.refresh).pack(side="left", padx=12)

        # izquierda: vistas previas
        left = ttk.Frame(b)
        left.grid(row=1, column=0, sticky="nw", padx=(0, 16))
        ttk.Label(left, text="En el partido", style="Section.TLabel").pack(anchor="w")
        self.match_box = ttk.Frame(left)
        self.match_box.pack(anchor="w", pady=(2, 10))
        self.menu_title = ttk.Label(left, text="En los menús", style="Section.TLabel")
        self.menu_title.pack(anchor="w")
        self.menu_box = ttk.Frame(left)
        self.menu_box.pack(anchor="w", pady=(2, 0))

        # derecha: zonas
        right = ttk.Frame(b)
        right.grid(row=1, column=1, sticky="nw")
        ttk.Label(right, text="Cambio rápido", style="Section.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w")
        quick = ttk.Frame(right)
        quick.grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 8))
        for text, keys in [("Camiseta…", ["cam1", "cam2"]),
                           ("Número y detalles…", ["pecho1", "pecho2", "cuello", "sisas",
                                                   "costados", "franja", "bajo"]),
                           ("Pantalón…", ["pantalon"])]:
            btn = ttk.Button(quick, text=text)
            btn.configure(command=lambda k=keys, w=btn: self._pick(k, w))
            btn.pack(side="left", padx=(0, 6))
        ttk.Label(right, text="Zona por zona (haz clic en el color)",
                  style="Section.TLabel").grid(row=2, column=0, columnspan=3, sticky="w")
        self.swatches = {}
        for i, (key, label, _kind, _pos) in enumerate(eq.ZONES):
            ttk.Label(right, text=label).grid(row=3 + i, column=0, sticky="w", padx=(0, 8), pady=2)
            c = tk.Canvas(right, width=110, height=20, highlightthickness=1,
                          highlightbackground="#888", cursor="hand2")
            c.grid(row=3 + i, column=1, sticky="w", pady=2)
            c.bind("<Button-1>", lambda _e, k=key, w=c: self._pick([k], w))
            self.swatches[key] = c
        r = 3 + len(eq.ZONES)
        ttk.Checkbutton(right, variable=self.auto_clash,
                        text="Recalcular los choques de color con los rivales").grid(
            row=r, column=0, columnspan=3, sticky="w", pady=(10, 0))
        self.menu_check = ttk.Checkbutton(right, variable=self.auto_menu,
                                          text="Pasar los colores también a las figuras del menú")
        self.menu_check.grid(row=r + 1, column=0, columnspan=3, sticky="w")
        btns = ttk.Frame(right)
        btns.grid(row=r + 2, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Button(btns, text="Copiar en la otra equipación",
                   command=self._copy_other).pack(side="left")
        ttk.Button(btns, text="↺  Colores originales",
                   command=self._restore).pack(side="left", padx=6)
        self.clash_lbl = ttk.Label(right, text="", style="Hint.TLabel", wraplength=420,
                                   justify="left")
        self.clash_lbl.grid(row=r + 3, column=0, columnspan=3, sticky="w", pady=(10, 0))
        ttk.Label(right, text="Las zonas del partido salen de los sprites del juego. "
                  "Los calcetines y las zapatillas no se cambian.\n"
                  "Pruébalo en el juego: la vista previa es aproximada.",
                  style="Hint.TLabel", justify="left", wraplength=420).grid(
            row=r + 4, column=0, columnspan=3, sticky="w", pady=(6, 0))
        self._built = True

    # ---- carga -------------------------------------------------------------
    def load(self, team, ti):
        self.ti = ti
        self.team = team
        kits = self.app.kits
        self.body.pack_forget()
        self.msg.pack_forget()
        problem = None
        if kits is None:
            problem = self.app.kits_error or "No se han podido leer las equipaciones."
        elif ti >= 50:
            problem = ("El equipo All-Star no tiene equipación propia en la tabla del juego.")
        elif Faces is None:
            problem = "Para ver las equipaciones hace falta Pillow:  pip install pillow"
        if problem:
            self.msg.configure(text=problem)
            self.msg.pack(anchor="w")
            return
        if not getattr(self, "_built", False):
            self._build()
        self.body.pack(fill="both", expand=True)
        self.refresh()

    def _kit(self):
        return self.app.kits.get(self.ti, bool(self.alt.get()))

    def _has_menu(self):
        return (self.app.menu is not None and not self.alt.get()
                and bool(eq.menu_gfx(self.team.gfx)))

    def refresh(self):
        kits = self.app.kits
        kit = self._kit()
        self._imgs = []
        # partido
        for w in self.match_box.winfo_children():
            w.destroy()
        for col, (f, n, label) in enumerate(self.PREVIEW):
            fr = self.app.sprite_frames.get((f, n))
            if not fr:
                continue
            im = ImageTk.PhotoImage(eq.render_sprite(fr, kit, kits.skin, kits.palette, 4))
            self._imgs.append(im)
            tk.Label(self.match_box, image=im, borderwidth=0).grid(row=0, column=col, padx=3,
                                                                   sticky="s")
            ttk.Label(self.match_box, text=label, style="Hint.TLabel").grid(row=1, column=col)
        # menús
        for w in self.menu_box.winfo_children():
            w.destroy()
        if self.app.menu is not None and eq.menu_gfx(self.team.gfx):
            g = self.team.gfx
            for col, pim in enumerate(self.app.menu.images(g, 2)):
                im = ImageTk.PhotoImage(pim)
                self._imgs.append(im)
                tk.Label(self.menu_box, image=im, borderwidth=0).grid(row=0, column=col, padx=2,
                                                                      sticky="s")
            note = "" if not self.alt.get() else "Los menús solo muestran la equipación principal."
            ttk.Label(self.menu_box, text=note, style="Hint.TLabel").grid(
                row=1, column=0, columnspan=5, sticky="w")
            self.menu_check.state(["!disabled"] if not self.alt.get() else ["disabled"])
        else:
            ttk.Label(self.menu_box, text="Este equipo no tiene figuras en los menús.",
                      style="Hint.TLabel").grid(row=0, column=0, sticky="w")
            self.menu_check.state(["disabled"])
        # zonas
        for key, c in self.swatches.items():
            c.delete("all")
            ramp = kits.zone_ramp(kit, key)
            for i, v in enumerate(ramp):
                c.create_rectangle(i * 22, 0, i * 22 + 22, 22, outline="",
                                   fill="#%02x%02x%02x" % kits.palette[v])
        # choques
        names = self.app.scoreboard_names
        if self.alt.get():
            rivals = kits.rivals_with_alt(self.ti)
            txt = ("Se pone esta equipación cuando juega fuera contra: " +
                   (", ".join(names[u] for u in rivals) if rivals else "ningún equipo") + ".")
        else:
            rivals = kits.rivals_with_alt(self.ti)
            txt = ("De visitante cambia a la alternativa contra: " +
                   (", ".join(names[u] for u in rivals) if rivals else "ningún equipo") + ".")
        self.clash_lbl.configure(text=txt)

    # ---- elegir color ------------------------------------------------------
    def _swatch(self, ramp):
        key = tuple(ramp)
        if key not in self._swatch_cache:
            pal = self.app.kits.palette
            im = Image.new("RGB", (60, 14))
            for i, v in enumerate(ramp):
                im.paste(pal[v], (i * 12, 0, i * 12 + 12, 14))
            self._swatch_cache[key] = ImageTk.PhotoImage(im)
        return self._swatch_cache[key]

    def _pick(self, keys, widget):
        menu = tk.Menu(self, tearoff=0)
        for name, ramp in eq.PRESETS:
            menu.add_command(label="  " + name, image=self._swatch(ramp), compound="left",
                             command=lambda r=ramp: self._apply(keys, r))
        menu.add_separator()
        menu.add_command(label="  Otro color…", command=lambda: self._custom(keys))
        x, y = widget.winfo_rootx(), widget.winfo_rooty() + widget.winfo_height()
        menu.tk_popup(x, y)

    def _custom(self, keys):
        from tkinter import colorchooser
        kits = self.app.kits
        start = "#%02x%02x%02x" % kits.zone_rgb(self._kit(), keys[0])
        rgb, _ = colorchooser.askcolor(color=start, title="Elige un color", parent=self)
        if rgb:
            self._apply(keys, kits.ramp_from_rgb(tuple(int(c) for c in rgb)))

    def _apply(self, keys, ramp):
        kits = self.app.kits
        kit = self._kit()
        for k in keys:
            kits.set_zone(kit, k, ramp)
        self._store(kit)

    def _store(self, kit):
        kits, alt = self.app.kits, bool(self.alt.get())
        kits.put(self.ti, alt, kit)
        if self.auto_clash.get() and not alt:
            kits.recompute_clash(self.ti)
        if self.auto_menu.get() and self._has_menu():
            self.app.menu.recolor(self.team.gfx, eq.menu_colors_from_kit(kits, kit))
            self.app.menu_dirty = True
        self.app.mark_dirty()
        self.refresh()

    def _copy_other(self):
        kits, alt = self.app.kits, bool(self.alt.get())
        other = "alternativa" if not alt else "principal"
        if not messagebox.askyesno(APP_TITLE, f"¿Copiar estos colores en la equipación {other}?"):
            return
        kits.put(self.ti, not alt, self._kit())
        self.app.mark_dirty()
        self.refresh()

    def _restore(self):
        kits, alt = self.app.kits, bool(self.alt.get())
        if not messagebox.askyesno(APP_TITLE, "¿Volver a los colores originales de 1996 de "
                                   "esta equipación?"):
            return
        kits.put(self.ti, alt, kits.original_kit(self.ti, alt))
        if not alt:
            for u in range(eq.N_TEAMS):
                kits.set_clash(self.ti, u, kits.original_clash[self.ti * 64 + u])
                kits.set_clash(u, self.ti, kits.original_clash[u * 64 + self.ti])
            if self._has_menu():
                self.app.menu.restore(self.team.gfx)
                self.app.menu_dirty = True
        self.app.mark_dirty()
        self.refresh()


# ==========================================================================
# Aplicación
# ==========================================================================
class App(tk.Tk):
    def __init__(self, path: str | None):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(960, 600)
        self.db: Database | None = None
        self.faces = None
        self.faces_error: str | None = None
        self.kits = None            # equipaciones del partido (MANAGER.DAT)
        self.kits_error: str | None = None
        self.menu = None            # figuras de los menús (BASKET96.DGF)
        self.menu_dirty = False
        self.dgf = None             # BASKET96.DGF (menús y caras pequeñas)
        self.small_opened = {}      # caras pequeñas tal como estaban al abrir
        self.sprite_frames = {}
        self.scoreboard_names = []
        self.path: str | None = None
        self.dirty = False
        self.current = None     # (iid, objeto)
        self._setup_style()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind_all("<Control-s>", lambda _: self.save())
        self.bind_all("<Control-f>", lambda _: self.search_entry.focus_set())
        if path and os.path.exists(path):
            self.open(path)
            if parche and parche.default_patch():
                self.after(300, lambda: self.offer_patch(os.path.dirname(path)))
        elif parche and parche.default_patch():
            self.after(300, self.offer_patch)
        else:
            self.after(100, self.ask_open)

    # ---- aspecto ---------------------------------------------------------
    def _setup_style(self):
        st = ttk.Style(self)
        if "vista" in st.theme_names():
            st.theme_use("vista")
        import tkinter.font as tkfont
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            tkfont.nametofont(name).configure(family="Segoe UI", size=10)
        st.configure("Title.TLabel", font=("Segoe UI Semibold", 16))
        st.configure("Section.TLabel", font=("Segoe UI Semibold", 11), foreground="#1f4e8c")
        st.configure("Hint.TLabel", foreground="#6b6b6b")
        st.configure("Warn.TLabel", foreground="#c0392b")
        st.configure("Error.TEntry", fieldbackground="#ffd6d6", foreground="#a00000")
        st.configure("Error.TSpinbox", fieldbackground="#ffd6d6", foreground="#a00000")
        st.configure("Treeview", rowheight=24)
        st.configure("Status.TLabel", padding=(8, 3))
        st.configure("Accent.TButton", font=("Segoe UI Semibold", 10))
        st.configure("Disclaimer.TLabel", padding=(12, 4), foreground="#6b6b6b",
                     font=("Segoe UI", 8))

    def _build(self):
        # Barra superior
        bar = ttk.Frame(self, padding=(8, 6))
        bar.pack(fill="x")
        if parche and parche.default_patch():
            ttk.Button(bar, text="⬇  Instalar actualización 2026-27", style="Accent.TButton",
                       command=self.install_patch).pack(side="left", padx=(0, 10))
        ttk.Button(bar, text="📂  Abrir…", command=self.ask_open).pack(side="left")
        ttk.Button(bar, text="💾  Guardar  (Ctrl+S)", command=self.save).pack(side="left", padx=6)
        ttk.Button(bar, text="Guardar como…", command=self.save_as).pack(side="left")
        ttk.Button(bar, text="↺  Restaurar copia de seguridad",
                   command=self.restore_backup).pack(side="left", padx=6)
        ttk.Button(bar, text="?  Ayuda", command=self.show_help).pack(side="right")
        ttk.Separator(self).pack(fill="x")

        # Aviso legal (abajo del todo). Se empaqueta antes que el panel central
        # para que siempre quede visible aunque la ventana sea pequeña.
        disclaimer = ttk.Label(self, text=DISCLAIMER, style="Disclaimer.TLabel",
                               justify="center", anchor="center")
        disclaimer.pack(side="bottom", fill="x")
        disclaimer.bind("<Configure>",
                        lambda e: disclaimer.configure(wraplength=max(200, e.width - 24)))
        ttk.Separator(self).pack(side="bottom", fill="x")
        # Barra de estado
        self.status = ttk.Label(self, text="", style="Status.TLabel")
        self.status.pack(side="bottom", fill="x")
        ttk.Separator(self).pack(side="bottom", fill="x")

        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Panel izquierdo
        left = ttk.Frame(paned, padding=(8, 8, 4, 8))
        paned.add(left, weight=0)
        sf = ttk.Frame(left)
        sf.pack(fill="x")
        ttk.Label(sf, text="🔎").pack(side="left")
        self.search = tk.StringVar()
        self.search_entry = ttk.Entry(sf, textvariable=self.search)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.search.trace_add("write", lambda *_: self.fill_tree())
        ttk.Label(left, text="Busca jugadores o equipos (Ctrl+F)",
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 6))
        tf = ttk.Frame(left)
        tf.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tf, show="tree", selectmode="browse")
        self.tree.column("#0", width=290)
        ys = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ys.set)
        ys.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.tag_configure("section", font=("Segoe UI Semibold", 10), foreground="#1f4e8c")
        self.tree.tag_configure("team", font=("Segoe UI Semibold", 10))
        self.tree.tag_configure("starter", foreground="#000000")
        self.tree.tag_configure("bench", foreground="#555555")

        # Panel derecho
        self.right = ttk.Frame(paned)
        paned.add(self.right, weight=1)
        self.empty = ttk.Label(self.right, text="Elige un equipo o un jugador en la lista "
                               "de la izquierda.", style="Hint.TLabel", anchor="center")
        self.empty.pack(fill="both", expand=True)
        self.player_ed = PlayerEditor(self, self.right)
        self.team_ed = TeamEditor(self, self.right)

    # ---- árbol -----------------------------------------------------------
    def fill_tree(self):
        if not self.db:
            return
        q = self.search.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        sections = {}
        for ti, t in enumerate(self.db.teams):
            team_hit = not q or q in t.short_name.lower() or q in t.long_name.lower()
            players = [(pi, p) for pi, p in enumerate(t.players)
                       if team_hit or q in p.full_name.lower() or q in p.short_name.lower()
                       or q in p.surname.lower()]
            if not team_hit and not players:
                continue
            if t.kind not in sections:
                sections[t.kind] = self.tree.insert(
                    "", "end", iid=f"s{t.kind}", text=SECTION_LABELS[t.kind],
                    open=True, tags=("section",))
            tid = self.tree.insert(sections[t.kind], "end", iid=f"t{ti}",
                                   text=self._team_label(t), open=bool(q), tags=("team",))
            for pi, p in sorted(players, key=lambda x: (x[1].roster_order or 99)):
                self.tree.insert(tid, "end", iid=f"p{ti}_{pi}", text=self._player_label(p),
                                 tags=("starter" if 1 <= p.roster_order <= 5 else "bench",))
        if self.current and self.tree.exists(self.current[0]):
            self.tree.selection_set(self.current[0])
            self.tree.see(self.current[0])

    @staticmethod
    def _team_label(t):
        return f"{t.short_name}"

    @staticmethod
    def _player_label(p):
        star = "★ " if 1 <= p.roster_order <= 5 else "   "
        return f"{star}{p.dorsal:>2}  {p.short_name}"

    def refresh_current_label(self):
        if not self.current:
            return
        iid, obj = self.current
        if self.tree.exists(iid):
            text = self._player_label(obj) if iid.startswith("p") else self._team_label(obj)
            self.tree.item(iid, text=text)

    def on_select(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        for w in (self.empty, self.player_ed, self.team_ed):
            w.pack_forget()
        if iid.startswith("p"):
            ti, pi = map(int, iid[1:].split("_"))
            obj = self.db.teams[ti].players[pi]
            self.current = (iid, obj)
            self.player_ed.load(obj, ti, pi)
            self.player_ed.pack(fill="both", expand=True)
        elif iid.startswith("t"):
            ti = int(iid[1:])
            obj = self.db.teams[ti]
            self.current = (iid, obj)
            self.team_ed.load(obj, ti)
            self.team_ed.pack(fill="both", expand=True)
        else:
            self.current = None
            self.empty.pack(fill="both", expand=True)

    def select_player(self, ti, pi, tab=None):
        iid = f"p{ti}_{pi}"
        if not self.tree.exists(iid):
            self.search.set("")
        self.tree.item(f"t{ti}", open=True)
        self.tree.selection_set(iid)
        self.tree.see(iid)
        self.on_select()
        if tab:
            for t in self.player_ed.nb.tabs():
                if self.player_ed.nb.tab(t, "text").strip() == tab:
                    self.player_ed.nb.select(t)

    def on_faces_changed(self):
        pass  # la rejilla del equipo se regenera cada vez que se abre

    def _load_faces(self, dbc_path):
        self.faces, self.faces_error = None, None
        if Faces is None:
            self.faces_error = ("Para ver y cambiar retratos hace falta Pillow:\n"
                                "abre una terminal y escribe  pip install pillow")
            return
        folder = os.path.dirname(dbc_path)
        caras, campo = os.path.join(folder, "CARAS.BIN"), os.path.join(folder, "CAMPO800.BIN")
        if not (os.path.exists(caras) and os.path.exists(campo)):
            self.faces_error = "No encuentro CARAS.BIN / CAMPO800.BIN junto a la base de datos."
            return
        try:
            self.faces = Faces(caras, campo)
        except Exception as e:  # noqa: BLE001
            self.faces_error = f"No se pudo leer CARAS.BIN: {e}"

    def _load_kits(self, dbc_path):
        """Equipaciones del partido (MANAGER.DAT) y figuras de los menús (BASKET96.DGF)."""
        self.kits, self.kits_error, self.menu, self.menu_dirty = None, None, None, False
        self.sprite_frames, self.scoreboard_names = {}, []
        folder = os.path.dirname(dbc_path)
        manager, campo = os.path.join(folder, "MANAGER.DAT"), os.path.join(folder, "CAMPO800.BIN")
        if not (os.path.exists(manager) and os.path.exists(campo)):
            self.kits_error = "No encuentro MANAGER.DAT / CAMPO800.BIN junto a la base de datos."
            return
        try:
            self.kits = eq.Kits(manager, campo)
            raw = self.kits.d
            i = raw.find(b" BARCELONA  ")
            if i < 0:   # el Barcelona puede haber cambiado de nombre: posición fija
                i = 0x5C07C
            self.scoreboard_names = [raw[i + 12 * n:i + 12 * n + 12].decode("latin-1").strip()
                                     for n in range(eq.N_TEAMS)]
        except Exception as e:  # noqa: BLE001
            self.kits, self.kits_error = None, f"No se pudieron leer las equipaciones: {e}"
            return
        if Faces is None:
            return
        for f, n, _ in KitPanel.PREVIEW:
            p = os.path.join(folder, f)
            if os.path.exists(p):
                fr = eq.load_frames(p, n + 1)
                if len(fr) > n:
                    self.sprite_frames[(f, n)] = fr[n]
        dgf_path = os.path.join(folder, "BASKET96.DGF")
        if self.dgf is not None:
            try:
                from dgf import DGF
                orig = DGF(dgf_path + ".BAK") if os.path.exists(dgf_path + ".BAK") else DGF(dgf_path)
                gfx = [t.gfx for t in self.db.teams if eq.menu_gfx(t.gfx)]
                self.menu = eq.MenuKits(self.dgf, orig, gfx)
            except Exception:  # noqa: BLE001  (sin figuras de menú, el resto funciona)
                self.menu = None

    def _load_dgf(self, dbc_path):
        """BASKET96.DGF: figuras de los menús y caras pequeñas de la pantalla previa."""
        self.dgf = None
        p = os.path.join(os.path.dirname(dbc_path), "BASKET96.DGF")
        if os.path.exists(p):
            try:
                from dgf import DGF
                self.dgf = DGF(p)
            except Exception:  # noqa: BLE001
                self.dgf = None

    def _sync_small_faces(self, folder) -> int:
        """Pasa los retratos actuales a las caras pequeñas de la pantalla previa al partido."""
        if not (self.faces and self.dgf):
            return 0
        from caras import sync_small_faces
        bak = os.path.join(folder, "CARAS.BIN.BAK")
        orig = open(bak, "rb").read() if os.path.exists(bak) else None
        return sync_small_faces(self.db, self.faces, self.dgf, orig)

    # ---- archivo ---------------------------------------------------------
    def _commit_text(self):
        """Asegura que el texto que se está escribiendo queda guardado en el modelo."""
        for tab in (self.player_ed.bio, self.team_ed.hist, self.team_ed.cbio):
            tab.commit()

    def mark_dirty(self):
        if self.current:  # refresca la cabecera (altura, dorsal, posición...)
            ed = self.player_ed if self.current[0].startswith("p") else self.team_ed
            ed._refresh_title()
        if not self.dirty:
            self.dirty = True
            self.update_status()

    def update_status(self):
        if not self.db:
            self.status.configure(text="Sin archivo abierto")
            return
        n = sum(len(t.players) for t in self.db.teams)
        state = "●  Cambios sin guardar" if self.dirty else "✓  Todo guardado"
        self.status.configure(text=f"{state}     ·     {self.path}     ·     "
                                   f"{len(self.db.teams)} equipos, {n} jugadores")
        self.title(f"{'* ' if self.dirty else ''}{APP_TITLE} — {os.path.basename(self.path)}")

    def confirm_discard(self) -> bool:
        if not self.dirty:
            return True
        r = messagebox.askyesnocancel(APP_TITLE, "Hay cambios sin guardar.\n\n¿Guardarlos ahora?")
        if r is None:
            return False
        if r:
            return self.save()
        return True

    def ask_open(self):
        if not self.confirm_discard():
            return
        start = os.path.dirname(self.path) if self.path else os.path.join(HERE, "..")
        path = filedialog.askopenfilename(
            title="Abrir base de datos de PC Basket", initialdir=start,
            filetypes=[("Base de datos PC Basket", "BASKET96.DBC *.DBC"), ("Todos", "*.*")])
        if path:
            self.open(path)

    def open(self, path):
        try:
            db = Database.load(path)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(APP_TITLE, f"No se pudo leer el archivo:\n{e}")
            return
        if not db.teams:
            messagebox.showerror(APP_TITLE, "El archivo no parece una base de datos de PC Basket 4.5.")
            return
        self.db, self.path, self.dirty, self.current = db, path, False, None
        self._load_faces(path)
        self._load_dgf(path)
        self.small_opened = {}
        self._load_kits(path)
        self.search.set("")
        self.fill_tree()
        for w in (self.player_ed, self.team_ed):
            w.pack_forget()
        self.empty.pack(fill="both", expand=True)
        self.update_status()

    def _write(self, path) -> bool:
        self._commit_text()
        try:
            data = self.db.serialize()
            Database.parse(data)  # comprobación: el resultado debe poder leerse
            self.db.save(path)
            if self.faces and (self.faces.dirty or path != self.path):
                self.faces.save(os.path.join(os.path.dirname(path), "CARAS.BIN"))
            folder = os.path.dirname(path)
            if self.kits and (self.kits.dirty or path != self.path):
                self.kits.save(os.path.join(folder, "MANAGER.DAT"))
            changed_faces = self._sync_small_faces(folder)
            if self.dgf and (changed_faces or self.menu_dirty or path != self.path):
                self.dgf.save(os.path.join(folder, "BASKET96.DGF"))
                self.menu_dirty = False
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(APP_TITLE, f"No se pudo guardar:\n{e}")
            return False
        self.path, self.dirty = path, False
        self.update_status()
        return True

    def save(self) -> bool:
        if not self.db:
            return False
        first_backup = not os.path.exists(self.path + ".BAK")
        ok = self._write(self.path)
        if ok and first_backup:
            messagebox.showinfo(APP_TITLE, "Guardado.\n\nSe ha creado una copia del archivo "
                                f"original en:\n{self.path}.BAK")
        return ok

    def save_as(self):
        if not self.db:
            return
        path = filedialog.asksaveasfilename(
            title="Guardar como", defaultextension=".DBC", initialfile="BASKET96.DBC",
            initialdir=os.path.dirname(self.path),
            filetypes=[("Base de datos PC Basket", "*.DBC")])
        if path:
            self._write(path)

    def restore_backup(self):
        if not self.path:
            return
        folder = os.path.dirname(self.path)
        pairs = [(p + ".BAK", p) for p in
                 [self.path] + [os.path.join(folder, f) for f in
                                ("CARAS.BIN", "ESCUDOS.BIN", "BASKET96.DGF", "MANAGER.DAT",
                                 "BASKET4.DAT")]]
        pairs = [(b, p) for b, p in pairs if os.path.exists(b)]
        if not pairs:
            messagebox.showinfo(APP_TITLE, "Aún no hay copia de seguridad: se crea la primera "
                                           "vez que guardas.")
            return
        if not messagebox.askyesno(APP_TITLE, "¿Volver a los archivos ORIGINALES de 1996 "
                                   "(base de datos, retratos, escudos, marcador y "
                                   "Euroliga)?\n\n"
                                   "Se perderán todos los cambios hechos con el editor."):
            return
        import shutil
        for bak, target in pairs:
            os.chmod(target, 0o666)
            shutil.copy2(bak, target)
        self.dirty = False
        self.open(self.path)
        messagebox.showinfo(APP_TITLE, "Base de datos original restaurada.")

    def offer_patch(self, game: str | None = None):
        """Al arrancar: si el juego aún no tiene la actualización, ofrece instalarla."""
        patch = parche.default_patch()
        if game is None:  # el .exe no está junto al juego: preguntar dónde está
            if messagebox.askyesno(APP_TITLE, (
                    "Este editor incluye la actualización de la temporada 2026-27.\n\n"
                    "¿Quieres instalarla ahora? A continuación elige la carpeta de "
                    "PC Basket 4.5 (la que contiene BASKET45.EXE).")):
                self.install_patch()
            elif not self.path:
                self.ask_open()
            return
        try:
            sts = parche.status(game, patch)
        except Exception:  # noqa: BLE001
            return
        if any(st in (parche.MISSING, parche.UNKNOWN) for _, st in sts):
            return  # no es una copia original: que el usuario use el botón si quiere
        if all(st == parche.APPLIED for _, st in sts):
            return
        self.install_patch(game, sts)

    def install_patch(self, game: str | None = None, sts=None):
        patch = parche.default_patch()
        if not self.confirm_discard():
            return
        if game is None:
            start = os.path.dirname(self.path) if self.path else os.path.join(HERE, "..")
            game = filedialog.askdirectory(
                title="Elige la carpeta de PC Basket 4.5 (donde está BASKET45.EXE)",
                initialdir=start, mustexist=True)
            if not game:
                return
            sts = None
        game = os.path.normpath(game)
        try:
            sts = sts or parche.status(game, patch)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(APP_TITLE, f"No se puede leer el parche:\n{e}")
            return
        bad = [e["name"] for e, st in sts if st in (parche.MISSING, parche.UNKNOWN)]
        if bad:
            messagebox.showerror(APP_TITLE, (
                "Esta carpeta no parece una copia original de PC Basket 4.5.\n\n"
                "Archivos que faltan o no coinciden:\n  " + "\n  ".join(bad) +
                "\n\nElige la carpeta donde está BASKET45.EXE. Si ya habías "
                "modificado el juego con otro editor, empieza desde una copia limpia."))
            return
        if all(st == parche.APPLIED for _, st in sts):
            messagebox.showinfo(APP_TITLE, "Este juego ya tiene la actualización instalada.")
        else:
            touched = [e["name"] for e, st in sts if st == parche.FROM_BAK]
            older = any(st == parche.OLDER for _, st in sts)
            msg = ("Hay una versión nueva de la actualización.\n\n" if older else
                   "El juego aún no tiene la actualización.\n\n")
            msg += ("Se instalarán las plantillas de la temporada 2026-27 (Liga Endesa, "
                   "Euroliga, EuroCup y All-Star) en:\n\n" + game +
                   "\n\nAntes se guarda una copia de cada archivo original (.BAK), y "
                   "«Restaurar copia de seguridad» la recupera.")
            if touched:
                msg += ("\n\n⚠ Has modificado estos archivos y se perderán tus cambios:\n  "
                        + "\n  ".join(touched))
            if not messagebox.askyesno(APP_TITLE, msg + "\n\n¿Continuar?"):
                return
            try:
                parche.apply(game, patch)
            except Exception as e:  # noqa: BLE001
                messagebox.showerror(APP_TITLE, f"No se ha podido instalar:\n{e}")
                return
            messagebox.showinfo(APP_TITLE, "Actualización instalada.\n\nEmpieza una liga "
                                "NUEVA en el juego para ver los equipos actualizados.")
        self.dirty = False
        self.open(parche.find_file(game, "BASKET96.DBC"))

    def on_close(self):
        if self.confirm_discard():
            self.destroy()

    def show_help(self):
        messagebox.showinfo(APP_TITLE, (
            "Cómo usar el editor\n\n"
            "1. Elige un equipo o jugador en la lista de la izquierda.\n"
            "   ★ marca el quinteto titular.\n"
            "2. Cambia los datos en las pestañas de la derecha. Los cambios se\n"
            "   aplican al momento; un campo en rojo tiene un valor no válido.\n"
            "3. Pulsa Guardar (Ctrl+S). La primera vez se crea BASKET96.DBC.BAK\n"
            "   con el original; «Restaurar copia» lo recupera.\n\n"
            "Consejos\n"
            "· Prueba los cambios empezando una liga NUEVA.\n"
            "· Equipo › Equipación: colores de la ropa en el partido y en las\n"
            "  figuras de los menús (se guardan en MANAGER.DAT y BASKET96.DGF).\n"
            "· «Nombre en listados» con 15 caracteres como máximo.\n"
            "· Los nombres de algunas valoraciones y el aspecto (pelo, barba)\n"
            "  están deducidos y conviene comprobarlos en el juego."))


def main():
    here = HERE
    try:  # texto nítido en pantallas con escalado
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:  # noqa: BLE001
        pass
    if len(sys.argv) > 1:
        default = sys.argv[1]
    else:  # el editor puede estar dentro de la carpeta del juego o en una subcarpeta
        default = next((p for p in (os.path.join(here, "BASKET96.DBC"),
                                    os.path.join(here, "..", "BASKET96.DBC"))
                        if os.path.exists(p)), os.path.join(here, "..", "BASKET96.DBC"))
    App(os.path.normpath(default)).mainloop()


if __name__ == "__main__":
    main()
