"""
Interfaz de los logros: aviso emergente («SUPERADO») y ventana de consulta.
"""
from __future__ import annotations

import datetime
import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk

import logros
import logros_mem
import retroarch_cmd

TOAST_MS = 5000          # tiempo en pantalla de cada aviso
TOPMOST_REFRESH_MS = 250 # el juego a pantalla completa puede taparlo: se vuelve a subir
TOAST_MARGIN = 16        # separación de la esquina superior izquierda
POLL_MS = 2000           # cada cuánto se revisan las partidas guardadas
RA_CHECK_MS = 60000      # cada cuánto se mira si hay que preparar retroarch.cfg
RA_EXE_KEY = "retroarch_exe"          # en LOGROS.JSON
RA_ASKED_KEY = "retroarch_avisos"     # "si" / "no": respuesta a activar los avisos

BG = "#1b1f27"
FG = "#ffffff"
GOLD = "#f2b632"
MUTED = "#8a94a6"
ORANGE = "#e8792b"


def draw_ball(cv: tk.Canvas, x: int, y: int, size: int, active: bool = True):
    """Pelota de baloncesto dibujada con formas (sin imágenes externas)."""
    fill = ORANGE if active else "#b9bec7"
    line = "#3a1d08" if active else "#7d828b"
    w = max(1, size // 20)
    cv.create_oval(x, y, x + size, y + size, fill=fill, outline=line, width=w)
    cx, cy = x + size / 2, y + size / 2
    cv.create_line(cx, y, cx, y + size, fill=line, width=w)
    cv.create_line(x, cy, x + size, cy, fill=line, width=w)
    k = size * 0.32
    cv.create_arc(x - k, y, x + k, y + size, start=-60, extent=120,
                  style="arc", outline=line, width=w)
    cv.create_arc(x + size - k, y, x + size + k, y + size, start=120, extent=120,
                  style="arc", outline=line, width=w)


def _hwnd(win: tk.Toplevel) -> int:
    import ctypes
    return ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()


def _no_activate(win: tk.Toplevel):
    """Que el aviso no robe el foco al juego (Windows)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        u = ctypes.windll.user32
        hwnd = _hwnd(win)
        GWL_EXSTYLE, WS_EX_NOACTIVATE, WS_EX_TOOLWINDOW, WS_EX_TOPMOST = -20, 0x08000000, 0x80, 0x8
        style = u.GetWindowLongW(hwnd, GWL_EXSTYLE)
        u.SetWindowLongW(hwnd, GWL_EXSTYLE,
                         style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST)
    except Exception:  # noqa: BLE001
        pass


def _bring_to_top(win: tk.Toplevel):
    """Pone el aviso encima de todo, también de un juego a pantalla completa,
    sin quitarle el foco."""
    if sys.platform != "win32":
        win.lift()
        return
    try:
        import ctypes
        HWND_TOPMOST = -1
        SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE, SWP_SHOWWINDOW = 0x1, 0x2, 0x10, 0x40
        ctypes.windll.user32.SetWindowPos(
            _hwnd(win), HWND_TOPMOST, 0, 0, 0, 0,
            SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
    except Exception:  # noqa: BLE001
        pass


class Toasts:
    """Cola de avisos: se muestran de uno en uno en la esquina superior izquierda."""

    def __init__(self, root: tk.Misc):
        self.root = root
        self.queue: list[str] = []
        self.current: tk.Toplevel | None = None
        self.busy = False           # hay un aviso en pantalla o a punto de salir

    def push(self, name: str):
        self.queue.append(name)
        if not self.busy:
            self._next()

    def _next(self):
        if not self.queue:
            self.current, self.busy = None, False
            return
        self.busy = True
        name = self.queue.pop(0)
        w = tk.Toplevel(self.root, bg=BG)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        try:
            w.attributes("-alpha", 0.95)
        except tk.TclError:
            pass
        frame = tk.Frame(w, bg=BG, highlightbackground=GOLD, highlightthickness=2)
        frame.pack()
        cv = tk.Canvas(frame, width=64, height=64, bg=BG, highlightthickness=0)
        cv.pack(side="left", padx=(12, 8), pady=12)
        draw_ball(cv, 4, 4, 56)
        txt = tk.Frame(frame, bg=BG)
        txt.pack(side="left", padx=(0, 20), pady=10)
        tk.Label(txt, text="LOGRO", bg=BG, fg=MUTED,
                 font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(txt, text=name, bg=BG, fg=FG,
                 font=("Segoe UI Semibold", 13)).pack(anchor="w")
        tk.Label(txt, text="SUPERADO", bg=BG, fg=GOLD,
                 font=("Segoe UI Black", 11)).pack(anchor="w")
        w.geometry(f"+{TOAST_MARGIN}+{TOAST_MARGIN}")
        w.update_idletasks()
        _no_activate(w)
        self.current = w
        self._keep_on_top(w)
        w.after(TOAST_MS, lambda: self._close(w))

    def _keep_on_top(self, w):
        if self.current is not w:
            return
        try:
            _bring_to_top(w)
            w.after(TOPMOST_REFRESH_MS, lambda: self._keep_on_top(w))
        except tk.TclError:
            pass

    def _close(self, w):
        self.current = None
        try:
            w.destroy()
        except tk.TclError:
            pass
        self.root.after(250, self._next)


class AchievementTracker:
    """Vigila las partidas guardadas de una carpeta del juego y avisa."""

    def __init__(self, root: tk.Misc, on_change=None):
        self.root = root
        self.toasts = Toasts(root)
        self.watcher: logros.Watcher | None = None
        self.memory = logros_mem.MemoryReader()
        self.live = False           # True si se está leyendo la liga en directo
        self.on_change = on_change
        self._job = None
        self._next_ra_check = 0.0

    def set_game_dir(self, game_dir: str | None):
        if self.watcher and game_dir and self.watcher.game_dir == game_dir:
            return
        self.watcher = None
        if game_dir:
            try:
                self.watcher = logros.Watcher(game_dir)
            except OSError:
                self.watcher = None
        if self._job is None:
            self._job = self.root.after(500, self._tick)

    def _tick(self):
        self._job = self.root.after(POLL_MS, self._tick)
        if not self.watcher:
            return
        try:
            new = self.watcher.poll()
        except OSError:
            new = []
        try:
            league = self.memory.read()
        except Exception:  # noqa: BLE001 - la lectura en directo es un extra
            league = None
        was_live, self.live = self.live, league is not None
        new += [i for i in self.watcher.poll_live(league) if i not in new]
        try:
            match = self.memory.read_match()
        except Exception:  # noqa: BLE001
            match = None
        new += [i for i in self.watcher.poll_match(match, league) if i not in new]
        if was_live != self.live and self.on_change:
            self.on_change()
        self._check_retroarch()
        for i in new:
            self.toasts.push(logros.BY_ID[i].name)
            self._show_in_retroarch(logros.BY_ID[i].name)
        if new and self.on_change:
            self.on_change()

    # ---- avisos dentro de RetroArch ------------------------------------------
    def _retroarch_cfg(self) -> str | None:
        extra = self.watcher.progress.extra
        return retroarch_cmd.find_config(extra.get(RA_EXE_KEY))

    def _show_in_retroarch(self, name: str):
        """El aviso del editor puede quedar tapado por RetroArch a pantalla
        completa; RetroArch lo pinta encima del juego (SHOW_MSG)."""
        try:
            if self.memory.running():
                port = retroarch_cmd.command_port(self._retroarch_cfg())
                if port:
                    retroarch_cmd.show_message(port, f"Logro superado: {name}")
        except Exception:  # noqa: BLE001 - es un extra
            pass

    def _check_retroarch(self):
        """Recuerda dónde está RetroArch y, con RetroArch cerrado, ofrece una vez
        activar su interfaz de comandos para que los logros se vean en el juego."""
        now = time.monotonic()
        if now < self._next_ra_check:
            return
        self._next_ra_check = now + RA_CHECK_MS / 1000
        extra = self.watcher.progress.extra
        try:
            if self.memory.running():
                exe = self.memory.exe_path()
                if exe and extra.get(RA_EXE_KEY) != exe:
                    extra[RA_EXE_KEY] = exe
                    self.watcher.progress.save()
                return
            if extra.get(RA_ASKED_KEY) == "no" or RA_EXE_KEY not in extra:
                return
            cfg = self._retroarch_cfg()
            port = retroarch_cmd.needed_change(cfg) if cfg else None
        except Exception:  # noqa: BLE001
            return
        if port is None:
            return
        ok = messagebox.askyesno("Logros en RetroArch", (
            "Si juegas en RetroArch a pantalla completa, los avisos de logros del editor "
            "pueden quedar ocultos detrás del juego.\n\n"
            "El editor puede hacer que sea RetroArch quien los muestre dentro del juego. "
            "Para eso hay que activar sus «comandos de red» en retroarch.cfg "
            f"(puerto {port}). Se guarda una copia como retroarch.cfg.antes_logros.\n\n"
            "¿Activarlo ahora? (RetroArch está cerrado, que es cuando se puede cambiar.)"),
            parent=self.root)
        extra[RA_ASKED_KEY] = "si" if ok else "no"
        if ok:
            try:
                retroarch_cmd.enable(cfg, port)
            except OSError as e:
                messagebox.showerror("Logros en RetroArch",
                                     f"No se pudo cambiar retroarch.cfg:\n{e}", parent=self.root)
        self.watcher.progress.save()


def _fmt_date(iso: str) -> str:
    try:
        return datetime.datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso


class AchievementsWindow(tk.Toplevel):
    def __init__(self, master, tracker: AchievementTracker, title: str):
        super().__init__(master)
        self.tracker = tracker
        self.title(f"Logros — {title}")
        self.geometry("620x640")
        self.minsize(480, 400)
        self.transient(master)

        top = ttk.Frame(self, padding=(16, 12, 16, 4))
        top.pack(fill="x")
        ttk.Label(top, text="🏆  Logros", style="Title.TLabel").pack(side="left")
        ttk.Button(top, text="Reiniciar logros", command=self.reset).pack(side="right")
        self.count = ttk.Label(self, padding=(16, 0, 16, 8), style="Hint.TLabel")
        self.count.pack(fill="x")
        ttk.Separator(self).pack(fill="x")

        # lista desplazable
        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(outer, highlightthickness=0, bg="#ffffff")
        sb = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg="#ffffff")
        win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(win, width=e.width))
        self.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(-e.delta // 120, "units"))

        self.note = ttk.Label(self, padding=(16, 8), style="Hint.TLabel", wraplength=580)
        self.note.pack(fill="x", side="bottom")
        ttk.Separator(self).pack(fill="x", side="bottom")
        self.refresh()

    def refresh(self):
        for w in self.inner.winfo_children():
            w.destroy()
        watcher = self.tracker.watcher
        unlocked = watcher.progress.unlocked if watcher else {}
        done = [a for a in logros.ACHIEVEMENTS if a.id in unlocked]
        pending = [a for a in logros.ACHIEVEMENTS if a.id not in unlocked]
        self.count.configure(text=f"{len(done)} de {len(logros.ACHIEVEMENTS)} superados")
        self.note.configure(text=(
            "● En directo: el editor está leyendo tu liga en RetroArch y los logros "
            "saltan al momento." if self.tracker.live else
            "Los logros se comprueban al pulsar «Guardar» en el juego. Si juegas con "
            "RetroArch (DOSBox Pure), saltan al momento en cuanto cargues una liga.")
            + " El editor tiene que estar abierto (puede estar minimizado).")
        if not watcher:
            tk.Label(self.inner, bg="#ffffff", fg="#a00000", padx=16, pady=12,
                     text="Abre la base de datos del juego para ver tus logros.").pack(anchor="w")
            return
        for header, items in (("Superados", done), ("Pendientes", pending)):
            if not items:
                continue
            tk.Label(self.inner, text=header, bg="#ffffff", fg="#1f4e8c", anchor="w",
                     font=("Segoe UI Semibold", 11), padx=16, pady=(8)).pack(fill="x")
            for a in items:
                self._row(a, unlocked.get(a.id))

    def _row(self, a: logros.Achievement, when: str | None):
        row = tk.Frame(self.inner, bg="#ffffff", padx=16, pady=6)
        row.pack(fill="x")
        cv = tk.Canvas(row, width=40, height=40, bg="#ffffff", highlightthickness=0)
        cv.pack(side="left", padx=(0, 12))
        draw_ball(cv, 2, 2, 36, active=bool(when))
        txt = tk.Frame(row, bg="#ffffff")
        txt.pack(side="left", fill="x", expand=True)
        tk.Label(txt, text=a.name, bg="#ffffff", anchor="w",
                 fg="#1b1f27" if when else "#6b6b6b",
                 font=("Segoe UI Semibold", 11)).pack(fill="x")
        tk.Label(txt, text=a.description, bg="#ffffff", fg="#6b6b6b",
                 anchor="w").pack(fill="x")
        if when:
            status, color = f"SUPERADO\n{_fmt_date(when)}", "#b07d00"
        elif a.check is None and not a.live_match:
            status, color = "Pendiente\n(aún en preparación)", "#9a9a9a"
        else:
            status, color = "Pendiente", "#6b6b6b"
        tk.Label(row, text=status, bg="#ffffff", fg=color, justify="right",
                 font=("Segoe UI Semibold", 9)).pack(side="right")
        tk.Frame(self.inner, bg="#ececec", height=1).pack(fill="x", padx=16)

    def reset(self):
        w = self.tracker.watcher
        if not w:
            return
        if not messagebox.askyesno("Reiniciar logros", (
                "¿Borrar todos los logros conseguidos?\n\n"
                "Solo contarán las partidas que guardes a partir de ahora."), parent=self):
            return
        w.progress.reset()
        self.refresh()
