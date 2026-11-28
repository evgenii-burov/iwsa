"""Состояние игрового мира: чистые данные, которые читает рендер."""
import random
from dataclasses import dataclass, field

import pygame

from entities import Bullet, EnemyBase, Player, make_enemy
from room import Room, tile_center


@dataclass
class World:
    room: Room
    room_index: int
    player: Player
    enemies: list[EnemyBase] = field(default_factory=list)
    bullets: list[Bullet] = field(default_factory=list)   # пули игрока и (позже) врагов
    time: float = 0.0            # s, время с начала комнаты
    rooms_cleared: int = 0       # счётчик зачищенных комнат
    rng: random.Random = field(default_factory=random.Random)  # разброс и прочая случайность

    @classmethod
    def from_room(cls, room: Room, room_index: int, rooms_cleared: int = 0,
                  rng: random.Random | None = None) -> "World":
        player = Player(pos=pygame.Vector2(tile_center(room.player_tile)))
        enemies = [make_enemy(s.kind, tile_center(s.tile)) for s in room.spawns]
        return cls(room, room_index, player, enemies, rooms_cleared=rooms_cleared,
                   rng=rng or random.Random())
