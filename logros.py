"""
Logros para el modo mánager de PC Basket 4.5.

El juego no se modifica: el editor vigila las partidas guardadas
(SAVE*/LIGAS*.DAT) y, cada vez que el usuario pulsa «Guardar» en el juego,
comprueba las condiciones de los logros. El progreso se guarda en
LOGROS.JSON, en la carpeta del juego.

Formato conocido de LIGAS*.DAT (ver FORMATO_DBC.md, «Partidas guardadas»):
    0x0000  u32   año de la temporada
    0x0020  612   calendario: 34 jornadas x 9 partidos (pares de equipos 0-17)
    0x0286  u8    jornada que toca jugar (1 al empezar; jugadas = valor - 1)
    0x051C  50 bloques de 0x52C bytes, uno por equipo (mismo orden que el DBC)
            +0x0C  nombre del mánager (" Ordenador " = equipo de la CPU)
            +0x38  12 jugadores de 0x68 bytes; el primer byte 0xFF cierra la lista
                   +0 índice del jugador en su equipo ORIGINAL del DBC
                   +1 equipo original
                   +2 dorsal
    0x119E2 612   resultados de la liga regular: 34 jornadas x 9 partidos x 2 bytes
                  (tanteo del 1.º y del 2.º equipo del calendario; 0-0 = sin jugar)
"""
from __future__ import annotations

import datetime
import glob
import json
import os
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set

N_TEAMS = 50
N_ACB = 18
TEAMS_OFS = 0x51C
TEAM_SIZE = 0x52C
MANAGER_OFS = 0x0C
ROSTER_OFS = 0x38
PLAYER_SIZE = 0x68
MAX_PLAYERS = 12
CPU_NAME = "Ordenador"
CALENDAR_OFS = 0x20
ROUND_OFS = 0x286
SCORES_OFS = 0x119E2
N_ROUNDS = 34
GAMES_PER_ROUND = N_ACB // 2
MAX_LOSSES_IRON = 4     # «Mano de hierro»: menos de 5 derrotas
CORUNA = 3          # Leyma Coruña (equipo 3 del DBC)

PROGRESS_FILE = "LOGROS.JSON"


# --------------------------------------------------------------------------
# Lectura de la partida guardada
# --------------------------------------------------------------------------
@dataclass
class SaveTeam:
    index: int
    manager: str
    roster: List[tuple] = field(default_factory=list)   # (equipo original, índice)

    @property
    def human(self) -> bool:
        return bool(self.manager) and self.manager != CPU_NAME


@dataclass
class Game:
    round: int
    home: int
    away: int
    home_pts: int
    away_pts: int

    @property
    def played(self) -> bool:
        return self.home_pts + self.away_pts > 0

    def won(self, team: int) -> bool:
        return self.played and (
            (team == self.home and self.home_pts > self.away_pts) or
            (team == self.away and self.away_pts > self.home_pts))

    def involves(self, team: int) -> bool:
        return team in (self.home, self.away)


@dataclass
class LeagueSave:
    path: str
    year: int
    teams: List[SaveTeam]
    games: List[Game] = field(default_factory=list)   # liga regular, en orden

    @classmethod
    def load(cls, path: str) -> "LeagueSave":
        with open(path, "rb") as f:
            return cls.parse(f.read(), path)

    @classmethod
    def parse(cls, d: bytes, path: str = "") -> "LeagueSave":
        if len(d) < TEAMS_OFS + N_TEAMS * TEAM_SIZE:
            raise ValueError("partida incompleta")
        year = int.from_bytes(d[0:4], "little")
        teams = []
        for t in range(N_TEAMS):
            b = TEAMS_OFS + t * TEAM_SIZE
            raw = d[b + MANAGER_OFS:b + ROSTER_OFS].split(b"\0")[0]
            st = SaveTeam(t, raw.decode("cp850", "replace").strip())
            for k in range(MAX_PLAYERS):
                p = b + ROSTER_OFS + k * PLAYER_SIZE
                if d[p] == 0xFF:
                    break
                st.roster.append((d[p + 1], d[p]))
            teams.append(st)
        games = []
        if len(d) >= SCORES_OFS + N_ROUNDS * N_ACB:
            for r in range(N_ROUNDS):
                for k in range(GAMES_PER_ROUND):
                    c = CALENDAR_OFS + r * N_ACB + 2 * k
                    sc = SCORES_OFS + r * N_ACB + 2 * k
                    games.append(Game(r + 1, d[c], d[c + 1], d[sc], d[sc + 1]))
        return cls(path, year, teams, games)

    def rounds_played(self) -> int:
        return len({g.round for g in self.games if g.played})

    def regular_season_over(self) -> bool:
        return bool(self.games) and all(g.played for g in self.games)

    def record(self, team: int) -> tuple:
        """(victorias, derrotas) en la liga regular."""
        mine = [g for g in self.games if g.played and g.involves(team)]
        w = sum(g.won(team) for g in mine)
        return w, len(mine) - w

    def human_teams(self) -> List[SaveTeam]:
        return [t for t in self.teams if t.human]


# --------------------------------------------------------------------------
# Logros
# --------------------------------------------------------------------------
@dataclass
class Achievement:
    id: str
    name: str
    description: str
    check: Optional[Callable[[LeagueSave], bool]] = None   # None = aún no se detecta


def _signed_someone(s: LeagueSave) -> bool:
    return any(orig != t.index for t in s.human_teams() for orig, _ in t.roster)


def _sold_someone(s: LeagueSave) -> bool:
    mine = {t.index for t in s.human_teams()}
    return any(orig in mine and t.index != orig
               for t in s.teams for orig, _ in t.roster)


def _won_a_game(s: LeagueSave) -> bool:
    return any(s.record(t.index)[0] > 0 for t in s.human_teams() if t.index < N_ACB)


def _iron_hand(s: LeagueSave) -> bool:
    return s.regular_season_over() and any(
        s.record(t.index)[1] <= MAX_LOSSES_IRON for t in s.human_teams() if t.index < N_ACB)


ACHIEVEMENTS: List[Achievement] = [
    Achievement("primera_victoria", "La suerte del rookie",
                "Gana tu primer partido de liga.", _won_a_game),
    Achievement("fichaje", "Nuevo jugón en el equipo",
                "Haz un fichaje.", _signed_someone),
    Achievement("venta", "Hasta la vista baby",
                "Vende un jugador.", _sold_someone),
    Achievement("playoffs", "Entre los elegidos",
                "Clasifícate para los playoffs."),
    Achievement("liga", "Gigante del baloncesto",
                "Gana la liga."),
    Achievement("europa", "A hombros de gigantes",
                "Gana la Copa de Europa."),
    Achievement("max_anotador", "Jugón",
                "Ten al máximo anotador de la liga al final de la temporada."),
    Achievement("max_reboteador", "Pincho de merluza",
                "Ten al máximo reboteador de la liga al final de la temporada."),
    Achievement("liga_coruna", "Matagigantes",
                "Gana la liga con Leyma Coruña."),
    Achievement("europa_coruna", "Matagigantes Universal",
                "Gana la Copa de Europa con Leyma Coruña."),
    Achievement("mano_hierro", "Mano de hierro",
                "Termina la liga regular con menos de 5 derrotas.", _iron_hand),
]
BY_ID: Dict[str, Achievement] = {a.id: a for a in ACHIEVEMENTS}


def evaluate(save: LeagueSave) -> Set[str]:
    """Logros cuya condición se cumple en esta partida guardada."""
    if not save.human_teams():
        return set()
    out = set()
    for a in ACHIEVEMENTS:
        if a.check is None:
            continue
        try:
            if a.check(save):
                out.add(a.id)
        except Exception:  # noqa: BLE001 - un logro roto no debe romper los demás
            pass
    return out


# --------------------------------------------------------------------------
# Progreso (LOGROS.JSON en la carpeta del juego)
# --------------------------------------------------------------------------
def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


class Progress:
    def __init__(self, game_dir: str):
        self.path = os.path.join(game_dir, PROGRESS_FILE)
        self.since = _now()                  # solo cuentan partidas guardadas después
        self.unlocked: Dict[str, str] = {}   # id -> fecha
        self.seen: Dict[str, float] = {}     # partida -> mtime ya revisado
        try:
            with open(self.path, encoding="utf-8") as f:
                d = json.load(f)
            self.since = d.get("desde", self.since)
            self.unlocked = {k: v for k, v in d.get("logros", {}).items() if k in BY_ID}
            self.seen = d.get("revisadas", {})
        except (OSError, ValueError):
            self.save()

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"desde": self.since, "logros": self.unlocked,
                       "revisadas": self.seen}, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)

    def reset(self):
        self.since, self.unlocked, self.seen = _now(), {}, {}
        self.save()

    def unlock(self, ids) -> List[str]:
        new = [i for i in ids if i not in self.unlocked]
        for i in new:
            self.unlocked[i] = _now()
        return new


class Watcher:
    """Revisa las partidas guardadas que han cambiado desde la última vez."""

    def __init__(self, game_dir: str):
        self.game_dir = game_dir
        self.progress = Progress(game_dir)
        self.live_key = None            # liga que se está leyendo de la memoria
        self.live_baseline: Set[str] = set()

    def saves(self) -> List[str]:
        return sorted(glob.glob(os.path.join(self.game_dir, "SAVE*", "LIGAS*.DAT")))

    def poll(self) -> List[str]:
        """Devuelve los ids de los logros recién conseguidos."""
        since = datetime.datetime.fromisoformat(self.progress.since).timestamp()
        new, changed = [], False
        for path in self.saves():
            try:
                mtime = os.path.getmtime(path)
            except OSError:
                continue
            key = os.path.relpath(path, self.game_dir).upper()
            if mtime <= since or self.progress.seen.get(key) == mtime:
                continue
            try:
                save = LeagueSave.load(path)
            except (OSError, ValueError):
                continue        # el juego aún está escribiendo: se reintenta luego
            self.progress.seen[key] = mtime
            changed = True
            new += self.progress.unlock(evaluate(save))
        if changed:
            self.progress.save()
        return new

    def poll_live(self, save: Optional[LeagueSave]) -> List[str]:
        """Liga leída de la memoria del juego. Solo cuenta lo que pasa mientras
        se vigila: lo que ya se cumplía al cargar la liga no desbloquea nada
        (eso lo comprueban las partidas guardadas)."""
        if save is None or not save.human_teams():
            return []
        key = (tuple((t.index, t.manager) for t in save.human_teams()),
               tuple((g.home, g.away) for g in save.games))
        now = evaluate(save)
        if key != self.live_key:
            self.live_key, self.live_baseline = key, now
            return []
        new = self.progress.unlock(now - self.live_baseline)
        self.live_baseline |= now
        if new:
            self.progress.save()
        return new
