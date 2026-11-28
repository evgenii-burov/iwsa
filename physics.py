"""Физика: столкновения круга с тайлами.

Движение игрока, расталкивание кругов, raycast по тайлам и sweep отрезка против круга.
Функции работают с pygame.Vector2 и не знают про рендер.
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


# --- Движение игрока ---

def update_player_velocity(vel: pygame.Vector2, move_dir: pygame.Vector2, dt: float) -> None:
    """Обновляет скорость игрока на месте по модели «разгон + занос».

    move_dir: единичный вектор ввода или (0, 0).
    Есть ввод: скорость делится на компоненту вдоль ввода и боковую.
      вдоль: к MAX_SPEED с темпом ACCEL_RATE; если скорость направлена против ввода,
             то к тому же MAX_SPEED, но медленнее (REVERSE_BRAKE_RATE) — отсюда
             занос при развороте. Цель именно MAX_SPEED, а не 0: простое затухание
             никогда не пересекло бы ноль, и игрок не смог бы тронуться назад;
      боковая: затухает с темпом LATERAL_GRIP.
    Нет ввода: скорость затухает с темпом SLIDE_RATE.
    Все формулы экспоненциальные, поэтому результат не зависит от размера шага dt.
    """
    if move_dir.length_squared() == 0:
        vel *= math.exp(-cfg.SLIDE_RATE * dt)
        if vel.length_squared() < cfg.STOP_SPEED * cfg.STOP_SPEED:
            vel.update(0, 0)
        return
    along = vel.dot(move_dir)
    sideways = vel - move_dir * along
    rate = cfg.ACCEL_RATE if along >= 0 else cfg.REVERSE_BRAKE_RATE
    along += (cfg.MAX_SPEED - along) * (1 - math.exp(-rate * dt))
    sideways *= math.exp(-cfg.LATERAL_GRIP * dt)
    vel.update(move_dir * along + sideways)


# --- Расталкивание кругов ---

def separate_circles(
    pos_a: pygame.Vector2, radius_a: float,
    pos_b: pygame.Vector2, radius_b: float,
    share_a: float,
) -> pygame.Vector2 | None:
    """Раздвигает два пересекающихся круга вдоль линии центров (pos_a и pos_b меняются на месте).

    share_a: доля сдвига, которую берёт на себя A (0..1); остальное достаётся B.
    1 = сдвигается только A (B непоколебим), 0.5 = поровну.
    Единая функция для всех пар (игрок-враг, враг-враг). Урон от касания она не
    наносит: контактный урон Chaser считается отдельно (contact_damage).
    Возвращает единичную нормаль от B к A, если круги пересекались, иначе None.
    """
    offset = pos_a - pos_b
    min_dist = radius_a + radius_b
    dist_sq = offset.length_squared()
    if dist_sq >= min_dist * min_dist:
        return None
    if dist_sq > cfg.COLLISION_EPS:
        dist = math.sqrt(dist_sq)
        normal = offset / dist
    else:  # центры совпали: направление выбираем произвольно, но детерминированно
        dist, normal = 0.0, pygame.Vector2(1, 0)
    overlap = min_dist - dist
    pos_a += normal * (overlap * share_a)
    pos_b -= normal * (overlap * (1.0 - share_a))
    return normal


def remove_velocity_into(vel: pygame.Vector2, normal: pygame.Vector2) -> None:
    """Гасит составляющую скорости, направленную против нормали (внутрь препятствия)."""
    into = vel.dot(normal)
    if into < 0:
        vel -= normal * into

# --- Лучи и отрезки ---

def raycast_tiles(
    origin: pygame.Vector2, direction: pygame.Vector2, max_dist: float, is_solid: IsSolid
) -> float | None:
    """Расстояние от origin до первой твёрдой клетки вдоль единичного direction.

    Алгоритм DDA по сетке тайлов. Если origin уже в твёрдой клетке: 0.
    Возвращает None, если до max_dist стены нет.
    """
    if direction.length_squared() == 0:
        return None
    tx, ty = math.floor(origin.x / cfg.TILE), math.floor(origin.y / cfg.TILE)
    if is_solid(tx, ty):
        return 0.0
    inf = math.inf
    step_x, step_y = (1 if direction.x > 0 else -1), (1 if direction.y > 0 else -1)
    delta_x = cfg.TILE / abs(direction.x) if direction.x else inf
    delta_y = cfg.TILE / abs(direction.y) if direction.y else inf
    next_x = ((tx + (step_x > 0)) * cfg.TILE - origin.x) / direction.x if direction.x else inf
    next_y = ((ty + (step_y > 0)) * cfg.TILE - origin.y) / direction.y if direction.y else inf
    while True:
        if next_x < next_y:
            dist, tx, next_x = next_x, tx + step_x, next_x + delta_x
        else:
            dist, ty, next_y = next_y, ty + step_y, next_y + delta_y
        if dist > max_dist:
            return None
        if is_solid(tx, ty):
            return dist


def sweep_segment_circle(
    start: pygame.Vector2, end: pygame.Vector2, center: pygame.Vector2, radius: float
) -> float | None:
    """Доля пути t (0..1), на которой отрезок start->end впервые входит в круг.

    Если start уже внутри круга: 0. Если отрезок круг не задевает: None.
    Решает |start + t*(end-start) - center|^2 = radius^2, поэтому быстрые пули
    не пролетают сквозь цели.
    """
    move = end - start
    offset = start - center
    c = offset.length_squared() - radius * radius
    if c <= 0:
        return 0.0
    a = move.length_squared()
    if a == 0:
        return None
    b = 2 * offset.dot(move)
    disc = b * b - 4 * a * c
    if disc < 0:
        return None
    t = (-b - math.sqrt(disc)) / (2 * a)
    return t if 0 <= t <= 1 else None
