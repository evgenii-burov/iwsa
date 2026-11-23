"""Физика: столкновения круга с тайлами.

Остальное (расталкивание кругов, raycast, sweep отрезка) добавится на
следующих этапах. Функции работают с pygame.Vector2 и не знают про рендер.
"""
import math
from typing import Callable

import pygame

from config import cfg

IsSolid = Callable[[int, int], bool]


def _closest_point_on_tile(pos: pygame.Vector2, tx: int, ty: int) -> tuple[float, float]:
    """Ближайшая к pos точка прямоугольника тайла (tx, ty)."""
    left, top = tx * cfg.TILE, ty * cfg.TILE
    return (
        min(max(pos.x, left), left + cfg.TILE),
        min(max(pos.y, top), top + cfg.TILE),
    )


def _inside_tile_normal(pos: pygame.Vector2, tx: int, ty: int) -> tuple[pygame.Vector2, float]:
    """Центр круга внутри тайла: выходим через ближайшую сторону.

    Возвращает (нормаль наружу, расстояние от центра до этой стороны).
    """
    left, top = tx * cfg.TILE, ty * cfg.TILE
    sides = (
        (pos.x - left, pygame.Vector2(-1, 0)),
        (left + cfg.TILE - pos.x, pygame.Vector2(1, 0)),
        (pos.y - top, pygame.Vector2(0, -1)),
        (top + cfg.TILE - pos.y, pygame.Vector2(0, 1)),
    )
    return min(sides, key=lambda s: s[0])[::-1]


def _deepest_contact(
    pos: pygame.Vector2, radius: float, is_solid: IsSolid
) -> tuple[pygame.Vector2, float] | None:
    """Самое глубокое касание круга с твёрдыми тайлами: (нормаль, глубина) или None."""
    tx0, tx1 = math.floor((pos.x - radius) / cfg.TILE), math.floor((pos.x + radius) / cfg.TILE)
    ty0, ty1 = math.floor((pos.y - radius) / cfg.TILE), math.floor((pos.y + radius) / cfg.TILE)
    best: tuple[pygame.Vector2, float] | None = None
    best_d2 = radius * radius
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            if not is_solid(tx, ty):
                continue
            cx, cy = _closest_point_on_tile(pos, tx, ty)
            dx, dy = pos.x - cx, pos.y - cy
            d2 = dx * dx + dy * dy
            if d2 >= best_d2:
                continue
            if d2 > cfg.COLLISION_EPS:
                dist = math.sqrt(d2)
                best, best_d2 = (pygame.Vector2(dx, dy) / dist, radius - dist), d2
            else:
                normal, to_side = _inside_tile_normal(pos, tx, ty)
                best, best_d2 = (normal, radius + to_side), 0.0
    return best


def collide_circle_with_tiles(
    pos: pygame.Vector2, vel: pygame.Vector2, radius: float, is_solid: IsSolid
) -> bool:
    """Выталкивает круг из твёрдых тайлов (по ближайшей точке), меняя pos и vel на месте.

    Нормальная составляющая скорости гасится, касательная сохраняется: круг
    плавно скользит вдоль стен и огибает углы. Берём самое глубокое касание
    за раз, поэтому на стыке тайлов плоской стены нет «призрачных» толчков.
    Возвращает True, если было хотя бы одно касание.
    """
    touched = False
    for _ in range(cfg.COLLISION_ITERATIONS):
        contact = _deepest_contact(pos, radius, is_solid)
        if contact is None:
            break
        normal, depth = contact
        pos += normal * depth
        into_wall = vel.dot(normal)
        if into_wall < 0:
            vel -= normal * into_wall
        touched = True
    return touched
