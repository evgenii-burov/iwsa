"""Загрузка, валидация и выбор комнаты.

Формат файла rooms/room_NN.txt: 18 строк по 32 символа.
  #  стена   .  пол   P  старт игрока
  C  Chaser   G  Gunner   S  Sniper
"""
import math
import random
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from config import cfg

WALL, FLOOR, PLAYER_MARK = "#", ".", "P"
ENEMY_MARKS: frozenset[str] = frozenset({"C", "G", "S"})
VALID_MARKS: frozenset[str] = frozenset({WALL, FLOOR, PLAYER_MARK}) | ENEMY_MARKS

Tile = tuple[int, int]  # (x, y) в тайлах
NEIGHBORS: tuple[Tile, ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))
MAX_LISTED_COORDS = 6  # сколько координат показывать в одном сообщении


class RoomError(Exception):
    """Комната не прошла валидацию (в тексте: файл и координаты)."""


@dataclass(frozen=True)
class Spawn:
    kind: str   # "C", "G" или "S"
    tile: Tile


@dataclass
class Room:
    name: str
    solid: list[list[bool]]          # solid[y][x]
    player_tile: Tile
    spawns: list[Spawn]
    warnings: list[str] = field(default_factory=list)

    def is_solid(self, tx: int, ty: int) -> bool:
        """Твёрдый ли тайл; всё за пределами комнаты считается стеной."""
        if tx < 0 or ty < 0 or tx >= cfg.ROOM_W or ty >= cfg.ROOM_H:
            return True
        return self.solid[ty][tx]


def tile_center(tile: Tile) -> tuple[float, float]:
    """Центр тайла в пикселях."""
    return (tile[0] + 0.5) * cfg.TILE, (tile[1] + 0.5) * cfg.TILE


def _fmt_coords(coords: list[Tile]) -> str:
    shown = ", ".join(f"({x},{y})" for x, y in coords[:MAX_LISTED_COORDS])
    extra = len(coords) - MAX_LISTED_COORDS
    return shown + (f" и ещё {extra}" if extra > 0 else "")


def _check_shape(lines: list[str], name: str) -> list[str]:
    """Размер и допустимые символы. Если размер неверен, остальное не проверяем."""
    errors: list[str] = []
    if len(lines) != cfg.ROOM_H:
        errors.append(f"{name}: строк {len(lines)}, нужно {cfg.ROOM_H}")
    for y, line in enumerate(lines):
        if len(line) != cfg.ROOM_W:
            errors.append(f"{name} [строка {y}]: длина {len(line)}, нужно {cfg.ROOM_W}")
    if errors:
        return errors
    for y, line in enumerate(lines):
        for x, ch in enumerate(line):
            if ch not in VALID_MARKS:
                errors.append(f"{name} [x={x}, y={y}]: неизвестный символ {ch!r}")
    return errors


def _check_border(lines: list[str], name: str) -> list[str]:
    bad = [
        (x, y)
        for y in range(cfg.ROOM_H)
        for x in range(cfg.ROOM_W)
        if (x in (0, cfg.ROOM_W - 1) or y in (0, cfg.ROOM_H - 1)) and lines[y][x] != WALL
    ]
    return [f"{name}: в рамке по периметру не стена: {_fmt_coords(bad)}"] if bad else []


def _find_marks(lines: list[str], marks: frozenset[str]) -> list[Spawn]:
    return [
        Spawn(ch, (x, y))
        for y, line in enumerate(lines)
        for x, ch in enumerate(line)
        if ch in marks
    ]


def _flood_fill(solid: list[list[bool]], start: Tile) -> set[Tile]:
    """Все тайлы, достижимые от start по 4-соседству без стен."""
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for dx, dy in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if (nx, ny) in seen or not (0 <= nx < cfg.ROOM_W and 0 <= ny < cfg.ROOM_H):
                continue
            if not solid[ny][nx]:
                seen.add((nx, ny))
                queue.append((nx, ny))
    return seen


def _run_length(solid: list[list[bool]], x: int, y: int, dx: int, dy: int) -> int:
    """Длина непрерывного участка пола через (x, y) вдоль оси (dx, dy)."""
    count = 1
    for sign in (1, -1):
        cx, cy = x + dx * sign, y + dy * sign
        while 0 <= cx < cfg.ROOM_W and 0 <= cy < cfg.ROOM_H and not solid[cy][cx]:
            count += 1
            cx, cy = cx + dx * sign, cy + dy * sign
    return count


def _narrow_tiles(solid: list[list[bool]]) -> list[Tile]:
    """Тайлы пола, где по какой-либо оси проход уже MIN_CORRIDOR_WIDTH."""
    narrow: list[Tile] = []
    for y in range(cfg.ROOM_H):
        for x in range(cfg.ROOM_W):
            if solid[y][x]:
                continue
            width = min(_run_length(solid, x, y, 1, 0), _run_length(solid, x, y, 0, 1))
            if width < cfg.MIN_CORRIDOR_WIDTH:
                narrow.append((x, y))
    return narrow


def parse_room(text: str, name: str) -> Room:
    """Разбирает и проверяет текст комнаты; при ошибках бросает RoomError."""
    lines = text.splitlines()
    errors = _check_shape(lines, name)
    if errors:
        raise RoomError("\n".join(errors))
    errors = _check_border(lines, name)

    players = _find_marks(lines, frozenset({PLAYER_MARK}))
    enemies = _find_marks(lines, ENEMY_MARKS)
    if len(players) != 1:
        errors.append(f"{name}: меток P должно быть ровно одна, найдено {len(players)}: "
                      f"{_fmt_coords([p.tile for p in players])}")
    if len(enemies) < cfg.MIN_ENEMIES:
        errors.append(f"{name}: врагов {len(enemies)}, нужно минимум {cfg.MIN_ENEMIES}")

    solid = [[ch == WALL for ch in line] for line in lines]
    if len(players) == 1:
        start = players[0].tile
        reachable = _flood_fill(solid, start)
        for e in enemies:
            if e.tile not in reachable:
                errors.append(f"{name} [x={e.tile[0]}, y={e.tile[1]}]: метка {e.kind} недостижима от P")
            elif math.dist(tile_center(e.tile), tile_center(start)) < cfg.SPAWN_SAFE_DIST:
                errors.append(f"{name} [x={e.tile[0]}, y={e.tile[1]}]: враг {e.kind} ближе "
                              f"{cfg.SPAWN_SAFE_DIST:.0f} px к старту игрока")
    if errors:
        raise RoomError("\n".join(errors))

    warnings: list[str] = []
    narrow = _narrow_tiles(solid)
    if narrow:
        warnings.append(f"{name}: узкие проходы (< {cfg.MIN_CORRIDOR_WIDTH} тайлов): {_fmt_coords(narrow)}")
    return Room(name, solid, players[0].tile, enemies, warnings)


def load_room(path: Path) -> Room:
    return parse_room(path.read_text(encoding="utf-8"), path.name)


def load_all_rooms(directory: Path) -> list[Room]:
    """Загружает все rooms/room_*.txt; ошибка в любом файле останавливает запуск."""
    paths = sorted(directory.glob("room_*.txt"))
    if not paths:
        raise RoomError(f"{directory}: не найдено ни одного файла room_*.txt")
    return [load_room(p) for p in paths]


def pick_next_room(count: int, current: int | None, rng: random.Random) -> int:
    """Случайный индекс комнаты, не равный текущему (если комнат больше одной)."""
    if count <= 1 or current is None:
        return rng.randrange(count)
    index = rng.randrange(count - 1)
    return index + 1 if index >= current else index
