"""Raycast, sweep и стрельба игрока (этап 4)."""
import random

import pygame
import pytest

from config import cfg
from entities import Bullet, make_enemy
from input import InputState
from physics import raycast_tiles, sweep_segment_circle
from room import parse_room
from simulation import step_play
from world import World

T = cfg.TILE
V = pygame.Vector2


def open_room():
    """Пустая комната с рамкой, P слева, три врага справа (их потом удаляем из мира)."""
    grid = [["#" if x in (0, cfg.ROOM_W - 1) or y in (0, cfg.ROOM_H - 1) else "." for x in range(cfg.ROOM_W)]
            for y in range(cfg.ROOM_H)]
    grid[9][3] = "P"
    grid[3][28] = grid[9][28] = grid[15][28] = "C"
    return parse_room("\n".join("".join(r) for r in grid), "test.txt")


def make_world(enemies=()):
    world = World.from_room(open_room(), 0, rng=random.Random(1))
    world.enemies[:] = list(enemies)
    world.player.pos = V(5 * T + T / 2, 9 * T + T / 2)
    return world


def inp(shoot=None, move=(0, 0)):
    return InputState(move_vec=V(move), shoot_dir=V(shoot).normalize() if shoot else None)


def ready_enemy(pos):
    enemy = make_enemy("C", pos)
    enemy.spawn_left = 0.0
    return enemy


# --- raycast ---

def test_raycast_hits_wall_at_expected_distance():
    world = make_world()
    origin = V(5.5 * T, 9.5 * T)
    dist = raycast_tiles(origin, V(1, 0), 10000, world.room.is_solid)
    assert dist == pytest.approx((cfg.ROOM_W - 1) * T - origin.x)


def test_raycast_respects_max_dist():
    world = make_world()
    assert raycast_tiles(V(5.5 * T, 9.5 * T), V(1, 0), 50, world.room.is_solid) is None


def test_raycast_diagonal_and_inside_wall():
    solid = lambda tx, ty: tx >= 10
    assert raycast_tiles(V(0, 0), V(1, 1).normalize(), 1000, solid) == pytest.approx(10 * T * 2 ** 0.5)
    assert raycast_tiles(V(10.5 * T, 3), V(1, 0), 100, solid) == 0.0


def test_raycast_axis_aligned_negative_direction():
    solid = lambda tx, ty: tx < 2
    assert raycast_tiles(V(5 * T, 100), V(-1, 0), 1000, solid) == pytest.approx(3 * T)


# --- sweep ---

def test_sweep_hits_and_misses():
    assert sweep_segment_circle(V(0, 0), V(100, 0), V(50, 0), 10) == pytest.approx(0.4)
    assert sweep_segment_circle(V(0, 0), V(100, 0), V(50, 20), 10) is None
    assert sweep_segment_circle(V(0, 0), V(30, 0), V(50, 0), 10) is None   # не дотянулась
    assert sweep_segment_circle(V(0, 0), V(100, 0), V(-50, 0), 10) is None  # circle сзади


def test_sweep_start_inside_circle_is_immediate():
    assert sweep_segment_circle(V(50, 0), V(100, 0), V(52, 0), 10) == 0.0


def test_sweep_grazing_tangent():
    assert sweep_segment_circle(V(0, 10), V(100, 10), V(50, 0), 10) == pytest.approx(0.5)


# --- стрельба ---

def count_shots(world, seconds, dt, shoot=(1, 0)):
    """Сколько пуль создано за время; пули пускаем медленными, чтобы никто не долетел до стены."""
    total = 0
    for _ in range(round(seconds / dt)):
        before = len(world.bullets)
        step_play(world, inp(shoot=shoot), dt)
        total += len(world.bullets) - before
    return total


@pytest.mark.parametrize("dt", [1 / 30, 1 / 60, 1 / 144])
def test_fire_rate_independent_of_step(dt, monkeypatch):
    monkeypatch.setattr(cfg, "BULLET_SPEED", 5.0)
    shots = count_shots(make_world(), 2.0, dt)
    assert shots == pytest.approx(2 * cfg.FIRE_RATE, abs=1)


def test_no_burst_saved_while_not_shooting():
    world = make_world()
    for _ in range(120):
        step_play(world, inp(), cfg.DT)
    step_play(world, inp(shoot=(1, 0)), cfg.DT)
    assert len(world.bullets) == 1  # один выстрел сразу, без «накопленной» очереди


def test_bullet_flies_in_requested_direction_with_speed():
    world = make_world()
    start = world.player.pos.copy()
    step_play(world, inp(shoot=(1, -1)), cfg.DT)
    bullet = world.bullets[0]
    assert bullet.vel.length() == pytest.approx(cfg.BULLET_SPEED)
    assert bullet.vel.x > 0 > bullet.vel.y
    assert bullet.pos.distance_to(start) == pytest.approx(cfg.BULLET_SPEED * cfg.DT)


def test_spread_is_bounded(monkeypatch):
    monkeypatch.setattr(cfg, "FIRE_SPREAD_DEG", 10.0)
    world = make_world()
    angles = []
    for _ in range(100):
        world.player.fire_timer = 0
        world.bullets.clear()
        step_play(world, inp(shoot=(1, 0)), cfg.DT)
        angles.append(world.bullets[0].vel.angle_to(V(1, 0)))
    assert max(abs(a) for a in angles) <= 10.0 + 1e-6
    assert max(angles) - min(angles) > 5  # разброс действительно есть


def test_bullet_destroyed_by_wall():
    world = make_world()
    world.bullets.append(Bullet(V(28.5 * T, 9.5 * T), V(cfg.BULLET_SPEED, 0), 1))
    for _ in range(10):
        step_play(world, inp(), cfg.DT)
    assert not world.bullets


def test_bullet_damages_enemy_and_kills_it():
    enemy = ready_enemy((10 * T, 9.5 * T))
    world = make_world([enemy])
    hp0 = enemy.hp
    for _ in range(40):
        step_play(world, inp(shoot=(1, 0)), cfg.DT)
        if enemy.hp < hp0:
            break
    assert enemy.hp == hp0 - cfg.BULLET_DAMAGE
    assert enemy.hit_timer > 0
    for _ in range(240):
        step_play(world, inp(shoot=(1, 0)), cfg.DT)
    assert enemy.is_dead and enemy not in world.enemies


def test_fast_bullet_does_not_tunnel_through_enemy(monkeypatch):
    monkeypatch.setattr(cfg, "BULLET_SPEED", 20000.0)  # за тик пролетает почти всю комнату
    enemy = ready_enemy((15 * T, 9.5 * T))
    world = make_world([enemy])
    hp0 = enemy.hp
    step_play(world, inp(shoot=(1, 0)), cfg.DT)
    assert enemy.hp == hp0 - cfg.BULLET_DAMAGE


def test_nearest_enemy_takes_the_hit():
    near, far = ready_enemy((9 * T, 9.5 * T)), ready_enemy((14 * T, 9.5 * T))
    world = make_world([near, far])
    near_hp0, far_hp0 = near.hp, far.hp
    for _ in range(20):   # две пули долетают до ближнего (3 HP), дальний прикрыт им
        step_play(world, inp(shoot=(1, 0)), cfg.DT)
    assert near.hp < near_hp0
    assert far.hp == far_hp0 and far.hit_timer == 0


def test_wall_in_front_of_enemy_blocks_bullet():
    enemy = ready_enemy((12 * T, 9.5 * T))
    world = make_world([enemy])
    world.room.solid[9][8] = True                       # колонна между игроком и врагом
    hp0 = enemy.hp
    for _ in range(60):
        step_play(world, inp(shoot=(1, 0)), cfg.DT)
    assert enemy.hp == hp0 and enemy.hit_timer == 0
    assert not world.bullets or all(b.pos.x < 8 * T for b in world.bullets)


def test_spawning_enemy_is_not_hit():
    enemy = make_enemy("C", (9 * T, 9.5 * T))           # spawn_left = SPAWN_TIME
    world = make_world([enemy])
    hp0 = enemy.hp
    for _ in range(20):                                 # 0.33 c < SPAWN_TIME
        step_play(world, inp(shoot=(1, 0)), cfg.DT)
    assert enemy.is_spawning and enemy.hp == hp0


def test_spawn_ends_after_spawn_time():
    enemy = make_enemy("G", (20 * T, 3 * T))
    world = make_world([enemy])
    for _ in range(round(cfg.SPAWN_TIME / cfg.DT) + 2):
        step_play(world, inp(), cfg.DT)
    assert not enemy.is_spawning
