"""Сущности мира: чистые данные без отрисовки.

На этапе 2 враги это «заглушки» (позиция + тип); поведение появится на
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


@dataclass
class EnemyBase:
    kind: str                # "C", "G" или "S" (метка из файла комнаты)
    pos: pygame.Vector2
    radius: float
    vel: pygame.Vector2 = field(default_factory=pygame.Vector2)


ENEMY_RADIUS: dict[str, float] = {
    "C": cfg.CHASER_RADIUS,
    "G": cfg.GUNNER_RADIUS,
    "S": cfg.SNIPER_RADIUS,
}


def make_enemy(kind: str, pos: tuple[float, float]) -> EnemyBase:
    return EnemyBase(kind=kind, pos=pygame.Vector2(pos), radius=ENEMY_RADIUS[kind])
