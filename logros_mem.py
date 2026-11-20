"""
Lectura en directo de la liga del mánager desde la memoria de RetroArch
(núcleo DOSBox Pure), para que los logros salten sin tener que guardar.

Solo LEE la memoria del proceso (como un visor de memoria); no cambia nada.

En la memoria del juego, la parte central de LIGAS*.DAT (0x284-0x1078C:
jornada, bloques de equipo...) está entera y en el mismo orden. Empieza por
el año 2000 (D0 07) y la jornada. El calendario y los resultados están en
otro sitio, a una distancia fija:

    ancla           = archivo 0x284   (D0 07, jornada en +2)
    ancla - 0xE704  = resultados (archivo 0x119E2)
    ancla - 0xE3E8  = calendario y títulos (archivo 0x20-0x283)

El cuadro de playoffs y el final de la Copa de Europa están en otra zona,
unos 900 KB antes del ancla. El cuadro va justo detrás de la serie 01..31,
así que se busca por esa firma; el final de la Copa de Europa está 0xAE0
bytes después del cuadro y acaba en 0x28.

Se localiza el ancla buscando la serie de bloques de equipo («Ordenador»
cada 0x52C bytes). La posición cambia en cada arranque, así que se busca de
nuevo cuando deja de cuadrar.

Partido jugado (simulador arcade, amistoso o de liga). Solo existe en
memoria mientras se juega; los partidos simulados por el mánager no pasan
por aquí. Lo precede el texto «ESTO solo ES... DE PRUEBA»:

    P = fin de «DE PRUEBA\0\0\0»
    P+0     2 x u8   los dos equipos (índices del DBC); OJO: no siempre en el
                     mismo orden que las fichas y el marcador
    P+0x16  2 x u16  marcador, en el orden de las fichas
    P+0x18C8         fichas del 1.er equipo en pista (5), 199 bytes cada una
    P+0x18C8+1001    fichas del 2.º equipo en pista
    En cada ficha, respecto al nombre (16 caracteres): -5 T2 anotados,
    -4 T3 anotados, +29 T2 intentados, +30 T3 intentados.

Al hacer un cambio, la ficha del que entra sustituye a la del que sale, y
las cifras del que se sienta desaparecen de la ficha. Por eso los triples
se van sumando en directo, cada vez que sube el contador de una ficha.
En algunas pantallas (cambios, menús) la zona se tapa con otros datos y
el texto de la firma no está: esas lecturas se descartan.
"""
from __future__ import annotations

import ctypes
import sys
import time
from typing import Optional

import logros

PROCESS_NAMES = ("retroarch.exe",)
CPU_MARK = b" Ordenador "
MID_START, MID_END = 0x284, logros.TEAMS_OFS + logros.N_TEAMS * logros.TEAM_SIZE
ANCHOR_TO_TEAM0_NAME = logros.TEAMS_OFS - MID_START + logros.MANAGER_OFS
SCORES_FROM_ANCHOR = -0xE704
CALENDAR_FROM_ANCHOR = -0xE3E8
ANCHOR_MAGIC = b"\xd0\x07"
SAVE_SIZE = logros.SCORES_OFS + logros.N_ROUNDS * logros.N_ACB
MIN_CPU_TEAMS = 30
MAX_REGION = 1 << 30
RESCAN_SECONDS = 10
PLAYOFFS_SIGNATURE = bytes(range(1, 0x32))
PLAYOFFS_SEARCH = 0x200000      # se busca en ±2 MB alrededor del ancla
EURO_FROM_PLAYOFFS = 0xAE0     # sin liga cargada, no buscar en toda la memoria a cada momento
MATCH_SIGNATURE = b"DE PRUEBA\0\0\0"
MATCH_SCORE = 0x16
MATCH_SLOTS = 0x18C8
SLOT_SIZE = 199
SIDE_SIZE = 5 * SLOT_SIZE + 6
SLOT_NAME_LEN = 16
SLOT_T3_MADE = -4
MATCH_READ = MATCH_SLOTS + 2 * SIDE_SIZE


if sys.platform == "win32":
    import ctypes.wintypes as wt

    _k = ctypes.WinDLL("kernel32", use_last_error=True)

    class _MBI(ctypes.Structure):
        _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                    ("AllocationProtect", wt.DWORD), ("PartitionId", wt.WORD),
                    ("RegionSize", ctypes.c_size_t), ("State", wt.DWORD),
                    ("Protect", wt.DWORD), ("Type", wt.DWORD)]

    class _PE32(ctypes.Structure):
        _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ProcessID", wt.DWORD),
                    ("th32DefaultHeapID", ctypes.c_void_p), ("th32ModuleID", wt.DWORD),
                    ("cntThreads", wt.DWORD), ("th32ParentProcessID", wt.DWORD),
                    ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                    ("szExeFile", ctypes.c_wchar * 260)]

    _k.OpenProcess.restype = wt.HANDLE
    _k.CreateToolhelp32Snapshot.restype = wt.HANDLE
    _k.VirtualQueryEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.POINTER(_MBI), ctypes.c_size_t]
    _k.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                     ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    _k.CloseHandle.argtypes = [wt.HANDLE]
    _k.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
    _READABLE = (0x02, 0x04, 0x08, 0x20, 0x40, 0x80)
    _STILL_ACTIVE = 259


def _find_pid() -> Optional[int]:
    snap = _k.CreateToolhelp32Snapshot(0x2, 0)
    if snap in (None, wt.HANDLE(-1).value):
        return None
    try:
        e = _PE32()
        e.dwSize = ctypes.sizeof(e)
        ok = _k.Process32FirstW(snap, ctypes.byref(e))
        while ok:
            if e.szExeFile.lower() in PROCESS_NAMES:
                return e.th32ProcessID
            ok = _k.Process32NextW(snap, ctypes.byref(e))
    finally:
        _k.CloseHandle(snap)
    return None


class MemoryReader:
    """Devuelve la liga que está en la memoria de RetroArch (o None)."""

    def __init__(self):
        self.available = sys.platform == "win32"
        self.pid: Optional[int] = None
        self.handle = None
        self.anchor: Optional[int] = None
        self.playoffs_addr: Optional[int] = None
        self._next_scan = 0.0
        self.match_addr: Optional[int] = None
        self.match_region: Optional[tuple] = None   # (base, tamaño) donde se encontró
        self._next_match_scan = 0.0

    # ---- proceso ---------------------------------------------------------
    def _alive(self) -> bool:
        if not self.handle:
            return False
        code = wt.DWORD()
        return bool(_k.GetExitCodeProcess(self.handle, ctypes.byref(code))) and \
            code.value == _STILL_ACTIVE

    def _attach(self) -> bool:
        if self._alive():
            return True
        self.close()
        pid = _find_pid()
        if not pid:
            return False
        h = _k.OpenProcess(0x0400 | 0x0010, False, pid)  # QUERY_INFORMATION | VM_READ
        if not h:
            return False
        self.pid, self.handle = pid, h
        return True

    def exe_path(self) -> Optional[str]:
        """Ruta de retroarch.exe (para encontrar su retroarch.cfg)."""
        if not self.available or not self._attach():
            return None
        buf = ctypes.create_unicode_buffer(1024)
        n = wt.DWORD(len(buf))
        if _k.QueryFullProcessImageNameW(self.handle, 0, buf, ctypes.byref(n)):
            return buf.value
        return None

    def running(self) -> bool:
        return self.available and self._attach()

    def close(self):
        if self.handle:
            _k.CloseHandle(self.handle)
        self.pid = self.handle = self.anchor = self.playoffs_addr = self.match_addr = self.match_region = None

    def _read(self, addr: int, size: int) -> Optional[bytes]:
        buf = ctypes.create_string_buffer(size)
        n = ctypes.c_size_t()
        if not _k.ReadProcessMemory(self.handle, ctypes.c_void_p(addr), buf, size, ctypes.byref(n)):
            return None
        return buf.raw[:n.value] if n.value == size else None

    # ---- localizar la liga -------------------------------------------------
    def _valid_anchor(self, a: int) -> bool:
        head = self._read(a, 4)
        if not head or head[:2] != ANCHOR_MAGIC or not 1 <= head[2] <= logros.N_ROUNDS + 1:
            return False
        cpu = 0
        for t in range(logros.N_TEAMS):
            name = self._read(a + ANCHOR_TO_TEAM0_NAME + t * logros.TEAM_SIZE, len(CPU_MARK))
            if name is None:
                return False
            cpu += name == CPU_MARK
        return cpu >= MIN_CPU_TEAMS

    def _regions(self):
        """(base, contenido) de cada zona de memoria legible del proceso."""
        m = _MBI()
        addr = 0
        while _k.VirtualQueryEx(self.handle, ctypes.c_void_p(addr), ctypes.byref(m), ctypes.sizeof(m)):
            base, size = m.BaseAddress or 0, m.RegionSize
            if m.State == 0x1000 and m.Protect in _READABLE and size < MAX_REGION:
                data = self._read(base, size)
                if data:
                    yield base, data
            addr = base + size
            if addr >= 1 << 47:
                break

    def _scan(self) -> Optional[int]:
        m = _MBI()
        addr = 0
        while _k.VirtualQueryEx(self.handle, ctypes.c_void_p(addr), ctypes.byref(m), ctypes.sizeof(m)):
            base, size = m.BaseAddress or 0, m.RegionSize
            if m.State == 0x1000 and m.Protect in _READABLE and size < MAX_REGION:
                data = self._read(base, size)
                if data:
                    i = data.find(CPU_MARK)
                    while i != -1:
                        # el equipo t es de la CPU: probar como si fuera cada uno de los 50
                        for t in range(logros.N_TEAMS):
                            a = base + i - ANCHOR_TO_TEAM0_NAME - t * logros.TEAM_SIZE
                            if 0 <= a - base < size and data[a - base:a - base + 2] == ANCHOR_MAGIC \
                                    and self._valid_anchor(a):
                                return a
                        i = data.find(CPU_MARK, i + 1)
            addr = base + size
            if addr >= 1 << 47:
                break
        return None

    # ---- lectura -----------------------------------------------------------
    def read(self) -> Optional[logros.LeagueSave]:
        if not self.available or not self._attach():
            return None
        if self.anchor is None or not self._valid_anchor(self.anchor):
            self.anchor = None
            if time.monotonic() < self._next_scan:
                return None
            self.anchor = self._scan()
            self.playoffs_addr = self._find_playoffs() if self.anchor else None
            if self.anchor is None:
                self._next_scan = time.monotonic() + RESCAN_SECONDS
                return None
        a = self.anchor
        mid = self._read(a, MID_END - MID_START)
        if mid is None:
            self.anchor = None
            return None
        d = bytearray(SAVE_SIZE)
        d[MID_START:MID_END] = mid
        cal = self._read(a + CALENDAR_FROM_ANCHOR, MID_START - logros.CALENDAR_OFS)
        scores = self._read(a + SCORES_FROM_ANCHOR, logros.N_ROUNDS * logros.N_ACB)
        if cal and scores and _plausible(cal, scores):
            d[logros.CALENDAR_OFS:MID_START] = cal
            d[logros.SCORES_OFS:] = scores
        save = logros.LeagueSave.parse(bytes(d), "memoria")
        save.playoffs, save.euro_champion = [], None
        if self.playoffs_addr is not None:
            raw = self._read(self.playoffs_addr, logros.PLAYOFFS_SIZE)
            if raw:
                save.playoffs = logros.parse_playoffs(raw)
            save.euro_champion = logros.parse_euro_end(
                self._read(self.playoffs_addr + EURO_FROM_PLAYOFFS, 4) or b"")
        return save

    def _find_playoffs(self) -> Optional[int]:
        """Dirección del cuadro de playoffs (la serie 01..31 lo precede)."""
        lo = max(self.anchor - PLAYOFFS_SEARCH, 0)
        step = 0x10000
        tail = b""
        for base in range(lo, self.anchor + PLAYOFFS_SEARCH, step):
            chunk = self._read(base, step)
            if chunk is None:
                tail = b""
                continue
            buf = tail + chunk
            i = buf.find(PLAYOFFS_SIGNATURE)
            if i != -1:
                addr = base - len(tail) + i + len(PLAYOFFS_SIGNATURE)
                end = self._read(addr + EURO_FROM_PLAYOFFS + 3, 1)
                if end == bytes([logros.EURO_END_MARK]):
                    return addr
            tail = chunk[-len(PLAYOFFS_SIGNATURE):]
        return None


    # ---- partido jugado (simulador) -----------------------------------------
    def read_match(self) -> Optional[logros.LiveMatch]:
        """El partido que se está jugando en la cancha, o None (no hay partido,
        o la pantalla actual tapa los datos)."""
        if not self.available or not self._attach():
            return None
        m = self._parse_match(self.match_addr) if self.match_addr is not None else None
        if m is None and time.monotonic() >= self._next_match_scan:
            self._next_match_scan = time.monotonic() + RESCAN_SECONDS
            # la RAM del DOS es siempre la misma zona: se busca ahí primero
            # y solo se recorre toda la memoria si aún no se conoce
            if self.match_region:
                base, size = self.match_region
                data = self._read(base, size)
                regions = [(base, data)] if data else []
            else:
                regions = self._regions()
            for base, data in regions:
                i = data.find(MATCH_SIGNATURE)
                while i != -1:
                    m = self._parse_match(base + i + len(MATCH_SIGNATURE))
                    if m is not None:
                        self.match_addr = base + i + len(MATCH_SIGNATURE)
                        self.match_region = (base, len(data))
                        return m
                    i = data.find(MATCH_SIGNATURE, i + 1)
        return m

    def _parse_match(self, p: int) -> Optional[logros.LiveMatch]:
        head = self._read(p - len(MATCH_SIGNATURE), len(MATCH_SIGNATURE))
        d = self._read(p, MATCH_READ)
        if head != MATCH_SIGNATURE or d is None:
            return None
        return parse_match(d)


def parse_match(d: bytes) -> Optional[logros.LiveMatch]:
    """Partido a partir de los bytes que siguen a la firma."""
    teams = (d[0], d[1])
    if max(teams) >= logros.N_TEAMS or teams[0] == teams[1]:
        return None
    score = (int.from_bytes(d[MATCH_SCORE:MATCH_SCORE + 2], "little"),
             int.from_bytes(d[MATCH_SCORE + 2:MATCH_SCORE + 4], "little"))
    if max(score) > 250:
        return None
    sides = []
    for side in range(2):
        slots = []
        for k in range(5):
            n = MATCH_SLOTS + side * SIDE_SIZE + k * SLOT_SIZE
            raw = d[n:n + SLOT_NAME_LEN]
            if not raw[:1].isalpha() or any(c < 0x20 for c in raw):
                return None
            slots.append((raw.decode("cp850").strip(), d[n + SLOT_T3_MADE]))
        sides.append(slots)
    return logros.LiveMatch(teams, score, sides)


def _plausible(cal: bytes, scores: bytes) -> bool:
    """Calendario: cada jornada, los 18 equipos una vez. Resultados: sin empates."""
    n = logros.N_ACB
    for r in range(logros.N_ROUNDS):
        if sorted(cal[r * n:(r + 1) * n]) != list(range(n)):
            return False
        for k in range(0, n, 2):
            x, y = scores[r * n + k], scores[r * n + k + 1]
            if x == y and x != 0:
                return False
    return True
