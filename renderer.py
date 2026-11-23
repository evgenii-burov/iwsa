"""Вся отрисовка игрового мира (единственное место с pygame.draw).

Читает состояние мира и ничего в нём не меняет.
"""
import pygame

from config import cfg
from entities import EnemyBase
from room import Room
from world import World

ENEMY_COLORS: dict[str, tuple[int, int, int]] = {
    "C": cfg.COLOR_CHASER,
    "G": cfg.COLOR_GUNNER,
    "S": cfg.COLOR_SNIPER,
}


def _build_room_surface(room: Room, draw_grid: bool) -> pygame.Surface:
    """Статичная картинка комнаты (пол, стены, при необходимости сетка)."""
    surface = pygame.Surface((cfg.SCREEN_W, cfg.SCREEN_H))
    surface.fill(cfg.COLOR_FLOOR)
    for ty in range(cfg.ROOM_H):
        for tx in range(cfg.ROOM_W):
            rect = pygame.Rect(tx * cfg.TILE, ty * cfg.TILE, cfg.TILE, cfg.TILE)
            if room.is_solid(tx, ty):
                pygame.draw.rect(surface, cfg.COLOR_WALL, rect)
            elif draw_grid:
                pygame.draw.rect(surface, cfg.COLOR_GRID, rect, 1)
    return surface


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self._cache: dict[tuple[int, bool], pygame.Surface] = {}

    def _room_surface(self, world: World, draw_grid: bool) -> pygame.Surface:
        key = (id(world.room), draw_grid)
        if key not in self._cache:
            self._cache[key] = _build_room_surface(world.room, draw_grid)
        return self._cache[key]

    def draw_world(self, world: World, draw_grid: bool = False) -> None:
        self.screen.fill(cfg.COLOR_BG)
        self.screen.blit(self._room_surface(world, draw_grid), (0, 0))
        for enemy in world.enemies:
            self._draw_enemy(enemy)
        player = world.player
        pygame.draw.circle(self.screen, cfg.COLOR_PLAYER, player.pos, player.radius)

    def _draw_enemy(self, enemy: EnemyBase) -> None:
        pygame.draw.circle(self.screen, ENEMY_COLORS[enemy.kind], enemy.pos, enemy.radius)
