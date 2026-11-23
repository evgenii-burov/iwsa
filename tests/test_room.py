"""Валидатор и загрузка комнат."""
import random
from pathlib import Path

import pytest

from config import cfg
from room import RoomError, load_all_rooms, parse_room, pick_next_room

ROOMS_DIR = Path(__file__).parent.parent / cfg.ROOMS_DIR


def make_text(mutate=None) -> str:
    """Корректная комната: рамка, P слева, три врага справа."""
    grid = [["#" if x in (0, cfg.ROOM_W - 1) or y in (0, cfg.ROOM_H - 1) else "." for x in range(cfg.ROOM_W)]
            for y in range(cfg.ROOM_H)]
    grid[9][3] = "P"
    grid[3][28], grid[9][28], grid[15][28] = "C", "G", "S"
    if mutate:
        mutate(grid)
    return "\n".join("".join(row) for row in grid)


def test_valid_room_parses():
    room = parse_room(make_text(), "ok.txt")
    assert room.player_tile == (3, 9)
    assert {s.kind for s in room.spawns} == {"C", "G", "S"}
    assert room.is_solid(0, 0) and not room.is_solid(5, 5)
    assert room.is_solid(-1, 5) and room.is_solid(5, cfg.ROOM_H)  # за пределами = стена


def test_all_shipped_rooms_are_valid():
    rooms = load_all_rooms(ROOMS_DIR)
    assert len(rooms) == 5
    for room in rooms:
        assert not room.warnings, room.warnings


def test_wrong_size_reports_file():
    with pytest.raises(RoomError, match="short.txt"):
        parse_room("#####\n#...#", "short.txt")


def test_broken_border_reports_coordinates():
    def hole(grid):
        grid[0][10] = "."
    with pytest.raises(RoomError, match=r"\(10,0\)"):
        parse_room(make_text(hole), "hole.txt")


def test_unknown_symbol():
    def junk(grid):
        grid[5][5] = "X"
    with pytest.raises(RoomError, match=r"x=5, y=5.*'X'"):
        parse_room(make_text(junk), "junk.txt")


def test_needs_exactly_one_player():
    def second_player(grid):
        grid[12][3] = "P"
    with pytest.raises(RoomError, match="ровно одна"):
        parse_room(make_text(second_player), "p2.txt")


def test_needs_three_enemies():
    def drop_enemy(grid):
        grid[15][28] = "."
    with pytest.raises(RoomError, match="минимум 3"):
        parse_room(make_text(drop_enemy), "few.txt")


def test_unreachable_enemy():
    def wall_off(grid):
        for y in range(1, cfg.ROOM_H - 1):
            grid[y][20] = "#"
    with pytest.raises(RoomError, match="недостижима"):
        parse_room(make_text(wall_off), "walled.txt")


def test_enemy_too_close_to_player():
    def close_enemy(grid):
        grid[9][5] = "C"
    with pytest.raises(RoomError, match="ближе"):
        parse_room(make_text(close_enemy), "close.txt")


def test_narrow_corridor_is_only_a_warning():
    def corridor(grid):
        for x in range(8, 20):
            grid[8][x] = "#"
            grid[10][x] = "#"
    room = parse_room(make_text(corridor), "narrow.txt")
    assert room.warnings and "узкие" in room.warnings[0]


def test_pick_next_room_never_repeats():
    rng = random.Random(1)
    for current in range(5):
        picks = {pick_next_room(5, current, rng) for _ in range(200)}
        assert current not in picks
        assert picks == set(range(5)) - {current}
