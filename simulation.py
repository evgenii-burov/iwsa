"""Один тик игровой логики в состоянии PLAY.

Порядок тика (из спецификации; ввод уже опрошен в main.py):
  2) игрок (движение, blink)            — blink появится на этапе 5
  3) выстрелы игрока и его пули
  4) ИИ и движение врагов               — поведение появится на этапах 6-8
  5-7) вражеские пули, лучи снайпера, контактный урон — этапы 6-9
  8) удаление мёртвых
Логика не вызывает рендер и не читает клавиатуру напрямую.
"""
import math

import pygame

from config import cfg
from entities import Bullet, EnemyBase
from input import InputState
from physics import collide_circle_with_tiles, raycast_tiles, sweep_segment_circle, update_player_velocity
from world import World


def step_play(world: World, inp: InputState, dt: float) -> None:
    _move_player(world, inp, dt)
    _player_fire(world, inp, dt)
    _move_player_bullets(world, dt)
    _update_enemies(world, dt)
    _remove_dead(world)
    world.time += dt


# --- 2) игрок ---

def _move_player(world: World, inp: InputState, dt: float) -> None:
    player = world.player
    update_player_velocity(player.vel, inp.move_vec, dt)
    player.pos += player.vel * dt
    collide_circle_with_tiles(player.pos, player.vel, player.radius, world.room.is_solid)


# --- 3) стрельба ---

def _player_fire(world: World, inp: InputState, dt: float) -> None:
    """Автоогонь с таймером, переносящим остаток: частота не зависит от шага логики."""
    player = world.player
    player.fire_timer -= dt
    if inp.shoot_dir is None:
        player.fire_timer = max(player.fire_timer, 0.0)  # «запас» выстрелов не копим
        return
    period = 1.0 / cfg.FIRE_RATE
    while player.fire_timer <= 0:
        world.bullets.append(_make_player_bullet(world, inp.shoot_dir))
        player.fire_timer += period


def _make_player_bullet(world: World, direction: pygame.Vector2) -> Bullet:
    spread = world.rng.uniform(-cfg.FIRE_SPREAD_DEG, cfg.FIRE_SPREAD_DEG) if cfg.FIRE_SPREAD_DEG else 0.0
    velocity = direction.rotate(spread) * cfg.BULLET_SPEED
    return Bullet(world.player.pos.copy(), velocity, cfg.BULLET_DAMAGE)


def _move_player_bullets(world: World, dt: float) -> None:
    for bullet in world.bullets:
        if bullet.from_player and bullet.alive:
            _advance_bullet(world, bullet, dt)


def _advance_bullet(world: World, bullet: Bullet, dt: float) -> None:
    """Двигает пулю как отрезок: ближайшее из «стена» и «враг» останавливает её."""
    start = bullet.pos.copy()
    end = start + bullet.vel * dt
    length = start.distance_to(end)
    if length == 0:
        return
    direction = (end - start) / length
    wall_dist = raycast_tiles(start, direction, length, world.room.is_solid)
    best = math.inf if wall_dist is None else wall_dist
    target: EnemyBase | None = None
    for enemy in world.enemies:
        if enemy.is_spawning or enemy.is_dead:  # проявляющиеся враги не твёрдые
            continue
        t = sweep_segment_circle(start, end, enemy.pos, enemy.radius)
        if t is not None and t * length <= best:
            best, target = t * length, enemy
    if target is not None:
        target.hp -= bullet.damage
        target.hit_timer = cfg.HIT_FLASH_TIME
        bullet.alive = False
    elif wall_dist is not None:
        bullet.alive = False
    else:
        bullet.pos = end


# --- 4) враги ---

def _update_enemies(world: World, dt: float) -> None:
    for enemy in world.enemies:
        enemy.spawn_left = max(0.0, enemy.spawn_left - dt)
        enemy.hit_timer = max(0.0, enemy.hit_timer - dt)


# --- 8) удаление ---

def _remove_dead(world: World) -> None:
    world.enemies[:] = [e for e in world.enemies if not e.is_dead]
    world.bullets[:] = [b for b in world.bullets if b.alive]
