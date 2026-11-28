"""Расталкивание кругов: игрок-враг и враг-враг."""
import random

import pygame
import pytest

from config import cfg
from entities import make_enemy
from input import InputState
from physics import separate_circles
from room import parse_room
from simulation import step_play
from world import World

T = cfg.TILE
V = pygame.Vector2


def open_room():
    grid = [["#" if x in (0, cfg.ROOM_W - 1) or y in (0, cfg.ROOM_H - 1) else "." for x in range(cfg.ROOM_W)]
            for y in range(cfg.ROOM_H)]
    grid[9][3] = "P"
    grid[3][28] = grid[9][28] = grid[15][28] = "C"
    return parse_room("\n".join("".join(r) for r in grid), "test.txt")


def make_world(enemies=(), player=(5 * T, 9.5 * T)):
    world = World.from_room(open_room(), 0, rng=random.Random(1))
    world.enemies[:] = list(enemies)
    world.player.pos = V(player)
    return world


def solid_enemy(kind, pos):
    enemy = make_enemy(kind, pos)
    enemy.spawn_left = 0.0
    return enemy


def move(dx, dy):
    return InputState(move_vec=V(dx, dy), shoot_dir=None)


# --- separate_circles ---

def test_no_overlap_returns_none_and_changes_nothing():
    a, b = V(0, 0), V(30, 0)
    assert separate_circles(a, 10, b, 10, 0.5) is None
    assert a == V(0, 0) and b == V(30, 0)


def test_touching_circles_are_not_overlapping():
    assert separate_circles(V(0, 0), 10, V(20, 0), 10, 0.5) is None


def test_full_share_moves_only_a():
    a, b = V(0, 0), V(15, 0)
    normal = separate_circles(a, 10, b, 10, 1.0)
    assert normal == V(-1, 0)
    assert a.x == pytest.approx(-5) and b.x == pytest.approx(15)
    assert a.distance_to(b) == pytest.approx(20)


def test_half_share_moves_both_equally():
    a, b = V(0, 0), V(10, 0)
    separate_circles(a, 10, b, 10, 0.5)
    assert a.x == pytest.approx(-5) and b.x == pytest.approx(15)


def test_zero_share_moves_only_b():
    a, b = V(0, 0), V(15, 0)
    separate_circles(a, 10, b, 10, 0.0)
    assert a == V(0, 0) and b.distance_to(a) == pytest.approx(20)


def test_coincident_centers_are_separated():
    a, b = V(50, 50), V(50, 50)
    assert separate_circles(a, 10, b, 12, 0.5) is not None
    assert a.distance_to(b) == pytest.approx(22)


def test_different_radii_touch_exactly():
    a, b = V(0, 0), V(5, 5)
    separate_circles(a, 10, b, 14, 0.3)
    assert a.distance_to(b) == pytest.approx(24)


# --- в тике ---

@pytest.mark.parametrize("kind", ["C", "G", "S"])
def test_player_cannot_walk_into_enemy(kind):
    enemy = solid_enemy(kind, (9 * T, 9.5 * T))
    world = make_world([enemy])
    for _ in range(120):
        step_play(world, move(1, 0), cfg.DT)
        assert world.player.pos.distance_to(enemy.pos) >= world.player.radius + enemy.radius - 1e-6


def test_enemy_blocks_player_and_is_not_moved_by_default():
    enemy = solid_enemy("G", (9 * T, 9.5 * T))
    world = make_world([enemy])
    start = enemy.pos.copy()
    for _ in range(120):
        step_play(world, move(1, 0), cfg.DT)
    assert enemy.pos == start
    assert world.player.vel.x == pytest.approx(0, abs=1e-6)  # нормальная составляющая погашена


def test_player_slides_along_enemy():
    """При косом подходе нормальная скорость гасится, а касательная сохраняется: игрок огибает врага."""
    enemy = solid_enemy("G", (9 * T, 9.5 * T))
    world = make_world([enemy], player=(7 * T, 9.5 * T - 8))
    for _ in range(60):
        step_play(world, move(1, -0.3 / 0.95), cfg.DT)  # вправо и чуть вверх
    assert world.player.pos.x > enemy.pos.x   # обошёл


def test_shared_push_moves_enemy_too(monkeypatch):
    monkeypatch.setattr(cfg, "PLAYER_PUSH_SHARE", 0.5)
    enemy = solid_enemy("C", (9 * T, 9.5 * T))
    world = make_world([enemy])
    start_x = enemy.pos.x
    for _ in range(60):
        step_play(world, move(1, 0), cfg.DT)
    assert enemy.pos.x > start_x


def test_spawning_enemy_is_passable():
    enemy = make_enemy("G", (9 * T, 9.5 * T))   # проявляется: не твёрдый
    world = make_world([enemy])
    for _ in range(round(0.5 / cfg.DT)):
        step_play(world, move(1, 0), cfg.DT)
    assert enemy.is_spawning
    assert world.player.pos.x > enemy.pos.x      # прошёл насквозь


def test_overlapping_enemies_are_pushed_apart():
    a, b = solid_enemy("C", (15 * T, 9.5 * T)), solid_enemy("G", (15 * T + 5, 9.5 * T))
    world = make_world([a, b])
    step_play(world, move(0, 0), cfg.DT)
    assert a.pos.distance_to(b.pos) >= a.radius + b.radius - 1e-6


def test_enemy_crowd_stays_out_of_walls_and_each_other():
    enemies = [solid_enemy("C", (1.5 * T + i * 2, 9.5 * T + i)) for i in range(6)]  # куча у левой стены
    world = make_world(enemies, player=(10 * T, 3 * T))
    for _ in range(30):
        step_play(world, move(0, 0), cfg.DT)
    for e in world.enemies:
        assert e.pos.x >= T + e.radius - 1e-6           # внутри комнаты (стена: x < T)
    for i, a in enumerate(world.enemies):
        for b in world.enemies[i + 1:]:
            assert a.pos.distance_to(b.pos) >= a.radius + b.radius - 0.5


def test_player_pinned_between_enemy_and_wall_never_enters_wall():
    enemy = solid_enemy("G", (4 * T, 9.5 * T))
    world = make_world([enemy], player=(1.5 * T + 2, 9.5 * T))
    for _ in range(120):
        step_play(world, move(1, 0), cfg.DT)
        assert world.player.pos.x >= T + world.player.radius - 1e-6


def test_pushed_enemy_gets_wall_collision():
    enemy = solid_enemy("C", (1.5 * T, 9.5 * T))
    world = make_world([enemy], player=(1.5 * T + 15, 9.5 * T))
    for _ in range(30):
        step_play(world, move(-1, 0), cfg.DT)           # игрок давит врага в стену
    assert enemy.pos.x >= T + enemy.radius - 1e-6
