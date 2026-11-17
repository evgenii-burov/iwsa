import math

import pygame

from settings import (
    COLOR_PLAYER,
    PLAYER_FRICTION,
    PLAYER_MAX_SPEED,
    PLAYER_RADIUS,
    PLAYER_WALL_BOUNCE,
)


class Player:
    """Круглый игрок со скольжением: ускорение от ввода + линейное трение."""

    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(0, 0)
        self.radius = PLAYER_RADIUS
        self.max_speed = PLAYER_MAX_SPEED
        self.friction = PLAYER_FRICTION
        # При трении, пропорциональном скорости, предельная скорость = accel / friction
        self.accel = self.max_speed * pow(self.friction, 3)

    def _read_direction(self, keys):
        direction = pygame.Vector2(
            (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
            (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP]),
        )
        if direction.length_squared() > 0:
            direction.normalize_ip()
        return direction

    def update(self, dt, keys, bounds):
        # 1. Ускорение от ввода
        self.vel += self._read_direction(keys) * self.accel * dt
        # 2. Трение: экспоненциальное затухание, не зависит от FPS
        self.vel *= math.exp(-self.friction * dt)
        # Совсем малую скорость обнуляем, чтобы игрок не «дрейфовал» бесконечно
        if self.vel.length_squared() < 1.0:
            self.vel.update(0, 0)
        # 3. Перемещение и границы
        self.pos += self.vel * dt
        self._collide_with(bounds)

    def _collide_with(self, bounds):
        r = self.radius
        if self.pos.x < bounds.left + r:
            self.pos.x = bounds.left + r
            self.vel.x = abs(self.vel.x) * PLAYER_WALL_BOUNCE
        elif self.pos.x > bounds.right - r:
            self.pos.x = bounds.right - r
            self.vel.x = -abs(self.vel.x) * PLAYER_WALL_BOUNCE
        if self.pos.y < bounds.top + r:
            self.pos.y = bounds.top + r
            self.vel.y = abs(self.vel.y) * PLAYER_WALL_BOUNCE
        elif self.pos.y > bounds.bottom - r:
            self.pos.y = bounds.bottom - r
            self.vel.y = -abs(self.vel.y) * PLAYER_WALL_BOUNCE

    def draw(self, surface, camera):
        pygame.draw.circle(surface, COLOR_PLAYER, camera.apply(self.pos), self.radius)