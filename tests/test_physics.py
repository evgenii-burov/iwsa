"""Столкновения круга с тайлами."""
import pygame
import pytest

from config import cfg
from physics import collide_circle_with_tiles

T = cfg.TILE
R = cfg.PLAYER_RADIUS


def solid_at(*tiles):
    wall = set(tiles)
    return lambda tx, ty: (tx, ty) in wall


def floor_wall():
    """Сплошная стена из тайлов по всей строке y=5 (пол выше неё)."""
    return lambda tx, ty: ty >= 5


def test_no_contact_changes_nothing():
    pos, vel = pygame.Vector2(100, 100), pygame.Vector2(50, 0)
    assert not collide_circle_with_tiles(pos, vel, R, floor_wall())
    assert pos == pygame.Vector2(100, 100) and vel == pygame.Vector2(50, 0)


def test_pushed_out_of_flat_wall_and_normal_velocity_removed():
    pos, vel = pygame.Vector2(100, 5 * T - R + 4), pygame.Vector2(80, 200)
    assert collide_circle_with_tiles(pos, vel, R, floor_wall())
    assert pos.y == pytest.approx(5 * T - R)
    assert pos.x == pytest.approx(100)
    assert vel.y == pytest.approx(0)
    assert vel.x == pytest.approx(80)  # скольжение вдоль стены сохраняется


def test_no_ghost_bump_on_tile_seam():
    """Круг над стыком двух тайлов стены не должен терять касательную скорость."""
    pos, vel = pygame.Vector2(3 * T, 5 * T - R + 2), pygame.Vector2(120, 60)  # x = стык тайлов 2 и 3
    collide_circle_with_tiles(pos, vel, R, floor_wall())
    assert vel.x == pytest.approx(120)


def test_moving_away_keeps_velocity():
    pos, vel = pygame.Vector2(100, 5 * T - R + 1), pygame.Vector2(0, -90)
    collide_circle_with_tiles(pos, vel, R, floor_wall())
    assert vel.y == pytest.approx(-90)


def test_corner_pushes_diagonally():
    corner = solid_at((5, 5))
    pos = pygame.Vector2(5 * T - 3, 5 * T - 3)  # у угла тайла (5,5), центр не над гранью
    vel = pygame.Vector2(100, 100)
    assert collide_circle_with_tiles(pos, vel, R, corner)
    assert pygame.Vector2(5 * T, 5 * T).distance_to(pos) == pytest.approx(R, abs=1e-6)
    assert vel.dot(pygame.Vector2(1, 1).normalize()) == pytest.approx(0, abs=1e-6)


def test_center_inside_tile_exits_via_nearest_side():
    wall = solid_at((5, 5))
    pos = pygame.Vector2(5 * T + 5, 5 * T + 15)  # ближе всего к левой стороне
    collide_circle_with_tiles(pos, pygame.Vector2(), R, wall)
    assert pos.x == pytest.approx(5 * T - R)


def test_closed_room_keeps_fast_circle_inside():
    """Круг, летящий в стены на скорости, остаётся внутри рамки комнаты."""
    def inside(tx, ty):
        return not (1 <= tx <= 5 and 1 <= ty <= 5)
    pos, vel = pygame.Vector2(3 * T, 3 * T), pygame.Vector2(280, 170)
    for _ in range(600):
        pos += vel * cfg.DT
        collide_circle_with_tiles(pos, vel, R, inside)
        assert T + R - 1e-6 <= pos.x <= 6 * T - R + 1e-6
        assert T + R - 1e-6 <= pos.y <= 6 * T - R + 1e-6
