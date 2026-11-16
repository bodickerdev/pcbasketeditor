"""
Lector/escritor de BASKET96.DBC (PC Basket 4.5, Dinamic Multimedia 1996).

Formato (ver FORMATO_DBC.md):
  - Cadenas: 1 byte de longitud (sin cifrar) + texto XOR 0x61.
  - Enteros little-endian.
  - El juego lee el archivo de forma secuencial (no hay índice de offsets),
    por lo que las cadenas pueden cambiar de longitud.

Uso:
    from dbc import Database
    db = Database.load("BASKET96.DBC")
    p = db.find_player("JOFRESA")[0]
    p.height_cm = 190
    db.save("BASKET96.DBC")
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

XOR = 0x61
NAME_ENC = "latin-1"   # nombres, equipos, lugares (ñ=0xF1, ú=0xFA ...)
TEXT_ENC = "cp437"     # biografías e historias (texto DOS: ó=0xA2, ñ=0xA4, ∙=0xF9)
SEASON_END = 0xF0      # marca fin de la lista de temporadas de un jugador

POSITIONS = ["base", "escolta", "alero", "ala-pivot", "pivot"]

# Orden de las 15 estadísticas de cada temporada (x2: liga regular + play-off)
STAT_NAMES = [
    "T2 conseguidos", "T2 intentados", "T3 conseguidos", "T3 intentados",
    "TL conseguidos", "TL intentados", "Rebotes def.", "Rebotes of.",
    "Asistencias", "Tapones", "Balones robados", "Balones perdidos",
    "Minutos", "Partidos", "Faltas personales",
]


# --------------------------------------------------------------------------
# Lectura / escritura de primitivas
# --------------------------------------------------------------------------
class Reader:
    def __init__(self, data: bytes, pos: int = 0):
        self.d = data
        self.pos = pos

    def u8(self) -> int:
        v = self.d[self.pos]
        self.pos += 1
        return v

    def u16(self) -> int:
        v = struct.unpack_from("<H", self.d, self.pos)[0]
        self.pos += 2
        return v

    def u32(self) -> int:
        v = struct.unpack_from("<I", self.d, self.pos)[0]
        self.pos += 4
        return v

    def raw(self, n: int) -> bytes:
        v = self.d[self.pos:self.pos + n]
        if len(v) != n:
            raise EOFError
        self.pos += n
        return v

    def pstr(self, enc: str = NAME_ENC) -> str:
        n = self.u8()
        return bytes(b ^ XOR for b in self.raw(n)).decode(enc)

    def lines(self) -> List[str]:
        return [self.pstr(TEXT_ENC) for _ in range(self.u16())]

    def peek(self) -> int:
        return self.d[self.pos]


class Writer:
    def __init__(self):
        self.b = bytearray()

    def u8(self, v: int):
        self.b += struct.pack("<B", v)

    def u16(self, v: int):
        self.b += struct.pack("<H", v)

    def u32(self, v: int):
        self.b += struct.pack("<I", v)

    def raw(self, v: bytes):
        self.b += v

    def pstr(self, s: str, enc: str = NAME_ENC):
        e = s.encode(enc)
        if len(e) > 255:
            raise ValueError(f"Cadena demasiado larga (max 255): {s[:40]}...")
        self.u8(len(e))
        self.b += bytes(c ^ XOR for c in e)

    def lines(self, ls: List[str]):
        self.u16(len(ls))
        for s in ls:
            self.pstr(s, TEXT_ENC)


# --------------------------------------------------------------------------
# Estructuras
# --------------------------------------------------------------------------
@dataclass
class Season:
    year: int                 # 95 = temporada 95-96
    team: str
    stats: List[int]          # 30 valores: 15 liga regular + 15 play-off


@dataclass
class Player:
    full_name: str            # "Rafael JOFRESA Prats"
    short_name: str           # "Rafa JOFRESA"
    surname: str              # "Jofresa, R."  (nombre para listados/partido)
    gfx: List[int]            # 2 punteros a BASKET96.DGF (foto, firma)
    bio: List[str]            # líneas de biografía (~72 caracteres)
    dorsal: int
    position: int             # 0 base, 1 escolta, 2 alero, 3 ala-pívot, 4 pívot
    height_raw: int           # altura - 100 (cm)
    weight: int               # kg
    birthplace: str
    birthdate: str            # "dd-mm-aa" o "-"
    value: int                # valor de mercado (millones de ptas)
    prev_club: str            # "Joventut (96)"
    attrs: bytearray          # 21 bytes (ver propiedades)
    team: str
    current: List[int]        # 30 estadísticas de la temporada actual
    seasons: List[Season] = field(default_factory=list)

    # ---- bloque de 21 bytes -------------------------------------------
    # [0] extranjero  [1] piel  [2] pelo  [3] ?(color pelo)  [4] ?  [5] barba
    # [6..9] valoraciones 0-100  [10] orden en plantilla (1-5 = titulares)
    # [11..18] 8 parámetros del simulador (1-7)  [19] flag  [20] ?
    def _get(i):
        return property(lambda s: s.attrs[i],
                        lambda s, v: s.attrs.__setitem__(i, int(v)))

    foreign = _get(0)
    skin = _get(1)            # 0 blanco, 1 negro, 2 (3 casos: ¿mulato?)
    hair = _get(2)            # 0 calvo, 1 rapado/corto, 3 normal, 2 ?
    hair_color = _get(3)      # hipótesis
    attr4 = _get(4)           # desconocido (0/1)
    beard = _get(5)           # 0 nada, 1-3 bigote/perilla/barba (hipótesis)
    rating1 = _get(6)         # manejo/pase  (hipótesis: corr. asistencias)
    rating2 = _get(7)         # tiro/ataque  (hipótesis: corr. puntos)
    rating3 = _get(8)         # rebote/interior (hipótesis)
    rating4 = _get(9)         # defensa/físico  (hipótesis)
    roster_order = _get(10)
    flag19 = _get(19)
    del _get

    @property
    def sim_params(self) -> List[int]:
        return list(self.attrs[11:19])

    @sim_params.setter
    def sim_params(self, vals: List[int]):
        assert len(vals) == 8
        self.attrs[11:19] = bytes(vals)

    @property
    def height_cm(self) -> int:
        return self.height_raw + 100

    @height_cm.setter
    def height_cm(self, v: int):
        if not 100 <= v <= 355:
            raise ValueError("altura fuera de rango (100-355 cm)")
        self.height_raw = v - 100

    @classmethod
    def read(cls, r: Reader) -> "Player":
        full, short, sur = r.pstr(), r.pstr(), r.pstr()
        gfx = [r.u32(), r.u32()]
        bio = r.lines()
        dorsal, pos, h, w = r.u8(), r.u8(), r.u8(), r.u8()
        place, date = r.pstr(), r.pstr()
        value = r.u16()
        prev = r.pstr()
        attrs = bytearray(r.raw(21))
        team = r.pstr()
        cur = [r.u16() for _ in range(30)]
        seasons = []
        while r.peek() != SEASON_END:
            year = r.u8()
            t = r.pstr()
            seasons.append(Season(year, t, [r.u16() for _ in range(30)]))
        r.u8()  # 0xF0
        return cls(full, short, sur, gfx, bio, dorsal, pos, h, w, place, date,
                   value, prev, attrs, team, cur, seasons)

    def write(self, w: Writer):
        w.pstr(self.full_name); w.pstr(self.short_name); w.pstr(self.surname)
        for g in self.gfx:
            w.u32(g)
        w.lines(self.bio)
        for v in (self.dorsal, self.position, self.height_raw, self.weight):
            w.u8(v)
        w.pstr(self.birthplace); w.pstr(self.birthdate)
        w.u16(self.value)
        w.pstr(self.prev_club)
        assert len(self.attrs) == 21
        w.raw(bytes(self.attrs))
        w.pstr(self.team)
        for v in self.current:
            w.u16(v)
        for s in self.seasons:
            if s.year == SEASON_END:
                raise ValueError("año de temporada no puede ser 240 (0xF0)")
            w.u8(s.year); w.pstr(s.team)
            for v in s.stats:
                w.u16(v)
        w.u8(SEASON_END)


@dataclass
class Coach:
    full_name: str
    short_name: str
    gfx: List[int]
    bio: List[str]

    @classmethod
    def read(cls, r: Reader) -> "Coach":
        return cls(r.pstr(), r.pstr(), [r.u32(), r.u32()], r.lines())

    def write(self, w: Writer):
        w.pstr(self.full_name); w.pstr(self.short_name)
        for g in self.gfx:
            w.u32(g)
        w.lines(self.bio)


# Variantes de cabecera de equipo: (nº punteros gráficos, tiene estadísticas)
TEAM_FORMATS = {"ACB": (12, True), "EUROPA": (9, False), "ALLSTAR": (2, False)}


@dataclass
class Team:
    kind: str                 # "ACB", "EUROPA", "ALLSTAR"
    short_name: str           # "Barcelona" (el que aparece en menús)
    long_name: str            # "Unicaja Málaga"
    gfx: List[int]            # punteros a BASKET96.DGF (escudo, fotos ...)
    club_name: str            # "Fútbol Club Barcelona"
    address: str
    arena: str
    capacity: int
    president: str
    sponsor: str
    budget: int               # pesetas
    history: List[str]
    tag: str                  # nombre repetido antes del palmarés
    palmares: bytes           # 26 bytes (títulos e historial; sin decodificar)
    stats: Optional[List[int]]  # 15 estadísticas del equipo (solo ACB)
    coach: Coach
    players: List[Player]

    @classmethod
    def read(cls, r: Reader, kind: str) -> "Team":
        ng, has_stats = TEAM_FORMATS[kind]
        short, long_ = r.pstr(), r.pstr()
        gfx = [r.u32() for _ in range(ng)]
        club, addr, arena = r.pstr(), r.pstr(), r.pstr()
        cap = r.u16()
        pres, spons = r.pstr(), r.pstr()
        budget = r.u32()
        hist = r.lines()
        tag = r.pstr()
        palm = r.raw(26)
        stats = [r.u16() for _ in range(15)] if has_stats else None
        coach = Coach.read(r)
        n = r.u8()
        players = [Player.read(r) for _ in range(n)]
        return cls(kind, short, long_, gfx, club, addr, arena, cap, pres, spons,
                   budget, hist, tag, palm, stats, coach, players)

    def write(self, w: Writer):
        ng, has_stats = TEAM_FORMATS[self.kind]
        assert len(self.gfx) == ng
        w.pstr(self.short_name); w.pstr(self.long_name)
        for g in self.gfx:
            w.u32(g)
        w.pstr(self.club_name); w.pstr(self.address); w.pstr(self.arena)
        w.u16(self.capacity)
        w.pstr(self.president); w.pstr(self.sponsor)
        w.u32(self.budget)
        w.lines(self.history)
        w.pstr(self.tag)
        w.raw(self.palmares)
        if has_stats:
            for v in self.stats:
                w.u16(v)
        self.coach.write(w)
        if len(self.players) > 255:
            raise ValueError("demasiados jugadores")
        w.u8(len(self.players))
        for p in self.players:
            p.write(w)


def _plausible(t: Team) -> bool:
    ok = lambda s: s.isprintable() and len(s) > 0
    return (len(t.players) > 0 and ok(t.short_name) and ok(t.coach.full_name)
            and all(ok(p.full_name) and ok(p.team) for p in t.players))


@dataclass
class Database:
    header: bytes             # texto de copyright (0x34 bytes) + u16
    teams: List[Team]
    trailer: bytes            # 32 bytes finales (8 punteros a DGF)

    HEADER_LEN = 0x36

    @classmethod
    def parse(cls, data: bytes) -> "Database":
        r = Reader(data, cls.HEADER_LEN)
        teams: List[Team] = []
        kinds = ["ACB", "EUROPA", "ALLSTAR"]
        k = 0
        while r.pos < len(data):
            start = r.pos
            team = None
            # Las secciones van en orden: ACB -> EUROPA -> ALLSTAR
            for kind in kinds[k:]:
                r.pos = start
                try:
                    t = Team.read(r, kind)
                except Exception:
                    continue
                if _plausible(t):
                    team, k = t, kinds.index(kind)
                    break
            if team is None:
                r.pos = start
                break
            teams.append(team)
        return cls(data[:cls.HEADER_LEN], teams, data[r.pos:])

    def serialize(self) -> bytes:
        w = Writer()
        w.raw(self.header)
        for t in self.teams:
            t.write(w)
        w.raw(self.trailer)
        return bytes(w.b)

    @classmethod
    def load(cls, path: str) -> "Database":
        with open(path, "rb") as f:
            return cls.parse(f.read())

    def save(self, path: str, backup: bool = True):
        import os
        import shutil
        if backup and os.path.exists(path) and not os.path.exists(path + ".BAK"):
            shutil.copy2(path, path + ".BAK")
        if os.path.exists(path):
            os.chmod(path, 0o666)  # los archivos del CD vienen como solo lectura
        with open(path, "wb") as f:
            f.write(self.serialize())

    # ---- utilidades ----------------------------------------------------
    def all_players(self) -> List[Tuple[Team, Player]]:
        return [(t, p) for t in self.teams for p in t.players]

    def find_player(self, text: str) -> List[Player]:
        text = text.lower()
        return [p for _, p in self.all_players()
                if text in p.full_name.lower() or text in p.short_name.lower()]

    def find_team(self, text: str) -> List[Team]:
        text = text.lower()
        return [t for t in self.teams
                if text in t.short_name.lower() or text in t.long_name.lower()]


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "../BASKET96.DBC"
    raw = open(path, "rb").read()
    db = Database.parse(raw)
    out = db.serialize()
    print(f"Equipos: {len(db.teams)}  Jugadores: {sum(len(t.players) for t in db.teams)}"
          f"  Tráiler: {len(db.trailer)} bytes")
    print("Round-trip idéntico:", out == raw)
