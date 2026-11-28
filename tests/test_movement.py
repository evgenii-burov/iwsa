"""Модель движения игрока (этап 3)."""
import math

import pygame
import pytest

from config import cfg
from physics import update_player_velocity

RIGHT = pygame.Vector2(1, 0)
LEFT = pygame.Vector2(-1, 0)
UP = pygame.Vector2(0, -1)
NONE = pygame.Vector2(0, 0)


def run(vel, direction, seconds, dt=cfg.DT):
    for _ in range(round(seconds / dt)):
        update_player_velocity(vel, direction, dt)
    return vel


def test_accelerates_toward_max_speed_without_exceeding():
    vel = run(pygame.Vector2(), RIGHT, 1.0)
    assert vel.x == pytest.approx(cfg.MAX_SPEED, rel=1e-3)
    assert vel.x <= cfg.MAX_SPEED


def test_sharp_start():
    """За 0.1 с игрок набирает больше 75% скорости (резкий старт)."""
    vel = run(pygame.Vector2(), RIGHT, 0.1)
    assert vel.x > 0.75 * cfg.MAX_SPEED


def test_diagonal_input_does_not_speed_up():
    diag = pygame.Vector2(1, 1).normalize()
    vel = run(pygame.Vector2(), diag, 1.0)
    assert vel.length() == pytest.approx(cfg.MAX_SPEED, rel=1e-3)


def test_reversal_skids_and_then_moves_the_other_way():
    """Разворот: сначала занос (медленнее разгона), затем скорость меняет знак и растёт."""
    vel = pygame.Vector2(cfg.MAX_SPEED, 0)
    elapsed = 0.0
    while vel.x > 0 and elapsed < 2.0:
        update_player_velocity(vel, LEFT, cfg.DT)
        elapsed += cfg.DT
    assert vel.x <= 0, "игрок так и не развернулся"
    # время смены знака: MAX - (MAX - a0) * exp(-r t) = 0, где a0 = -MAX
    assert elapsed == pytest.approx(math.log(2) / cfg.REVERSE_BRAKE_RATE, abs=2 * cfg.DT)
    assert elapsed > math.log(2) / cfg.ACCEL_RATE   # дольше, чем при обычном разгоне
    run(vel, LEFT, 1.0)
    assert vel.x == pytest.approx(-cfg.MAX_SPEED, rel=1e-2)


def test_lateral_velocity_decays_with_grip():
    vel = pygame.Vector2(0, 200)             # летим вниз
    run(vel, RIGHT, 0.5)                      # жмём вправо
    assert abs(vel.y) == pytest.approx(200 * math.exp(-cfg.LATERAL_GRIP * 0.5), rel=1e-3)


def test_less_grip_means_more_drift(monkeypatch):
    vel_a = run(pygame.Vector2(0, 200), RIGHT, 0.3)
    monkeypatch.setattr(cfg, "LATERAL_GRIP", cfg.LATERAL_GRIP / 2)
    vel_b = run(pygame.Vector2(0, 200), RIGHT, 0.3)
    assert vel_b.y > vel_a.y


def test_slide_without_input_follows_exponential():
    vel = run(pygame.Vector2(cfg.MAX_SPEED, 0), NONE, 0.5)
    assert vel.x == pytest.approx(cfg.MAX_SPEED * math.exp(-cfg.SLIDE_RATE * 0.5), rel=1e-3)


def test_tiny_speed_snaps_to_zero():
    vel = pygame.Vector2(0.5, 0)
    update_player_velocity(vel, NONE, cfg.DT)
    assert vel == pygame.Vector2(0, 0)


def test_result_independent_of_step_size():
    a = run(pygame.Vector2(50, -120), UP, 0.5, dt=1 / 60)
    b = run(pygame.Vector2(50, -120), UP, 0.5, dt=1 / 240)
    assert a.x == pytest.approx(b.x, abs=1e-6) and a.y == pytest.approx(b.y, abs=1e-6)


def test_speed_above_max_returns_to_max():
    """После blink скорость может быть выше предела; она плавно возвращается к MAX_SPEED."""
    vel = run(pygame.Vector2(2 * cfg.MAX_SPEED, 0), RIGHT, 1.0)
    assert vel.x == pytest.approx(cfg.MAX_SPEED, rel=1e-2)
