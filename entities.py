"""Сущности мира: чистые данные без отрисовки.

Враги пока «заглушки» (позиция, здоровье, таймеры); поведение появится на
этапах 6-8, там же EnemyBase обрастёт подклассами Chaser, Gunner, Sniper.
"""
from dataclasses import dataclass, field

import pygame

from config import cfg


@dataclass
class Player:
    pos: pygame.Vector2
    vel: pygame.Vector2 = field(default_factory=pygame.Vector2)
    radius: float = cfg.PLAYER_RADIUS
    fire_timer: float = 0.0   # s, до следующего выстрела (остаток переносится между выстрелами)


@dataclass
class Bullet:
    pos: pygame.Vector2
    vel: pygame.Vector2       # px/s
    damage: int
    from_player: bool = True
    alive: bool = True


@dataclass
class EnemyBase:
    kind: str                 # "C", "G" или "S" (метка из файла комнаты)
    pos: pygame.Vector2
    radius: float
    hp: int
    vel: pygame.Vector2 = field(default_factory=pygame.Vector2)
    spawn_left: float = cfg.SPAWN_TIME   # s, пока > 0: «проявление», не твёрдый и не опасный
    hit_timer: float = 0.0               # s, пока > 0: враг мигает после попадания

    @property
    def is_spawning(self) -> bool:
        return self.spawn_left > 0

    @property
    def is_dead(self) -> bool:
        return self.hp <= 0


ENEMY_RADIUS: dict[str, float] = {
    "C": cfg.CHASER_RADIUS,
    "G": cfg.GUNNER_RADIUS,
    "S": cfg.SNIPER_RADIUS,
}

ENEMY_HP: dict[str, int] = {
    "C": cfg.CHASER_HP,
    "G": cfg.GUNNER_HP,
    "S": cfg.SNIPER_HP,
}


def make_enemy(kind: str, pos: tuple[float, float]) -> EnemyBase:
    return EnemyBase(kind=kind, pos=pygame.Vector2(pos), radius=ENEMY_RADIUS[kind], hp=ENEMY_HP[kind])
