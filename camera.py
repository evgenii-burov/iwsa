import math

import pygame

from settings import CAMERA_LAG_TIME, CAMERA_MAX_LEAD, SCREEN_HEIGHT, SCREEN_WIDTH


class Camera:
    """Камера, которая догоняет цель с запаздыванием.

    pos — центр камеры в мировых координатах (float).
    На экране мир рисуется со смещением offset (целым), чтобы все объекты
    сдвигались на одинаковое число пикселей и не «дрожали» друг относительно друга.
    """

    def __init__(self, target_pos):
        self.pos = pygame.Vector2(target_pos)
        self.half = pygame.Vector2(SCREEN_WIDTH, SCREEN_HEIGHT) / 2

    def update(self, dt, target_pos, world_bounds):
        # 1. Экспоненциальное сближение: при постоянной скорости цели v камера
        #    отстаёт на v * CAMERA_LAG_TIME. Не зависит от FPS.
        self.pos += (target_pos - self.pos) * (1 - math.exp(-dt / CAMERA_LAG_TIME))

        # 2. «Поводок»: игрок не может уйти от центра камеры дальше MAX_LEAD
        #    (защита от выхода за экран при очень высокой скорости или блинке)
        offset = target_pos - self.pos
        dist = offset.length()
        if dist > CAMERA_MAX_LEAD:
            self.pos = target_pos - offset * (CAMERA_MAX_LEAD / dist)

        # 3. Не показываем пустоту за пределами комнаты
        self.pos.x = self._clamp_axis(self.pos.x, self.half.x, world_bounds.left, world_bounds.right)
        self.pos.y = self._clamp_axis(self.pos.y, self.half.y, world_bounds.top, world_bounds.bottom)

    @staticmethod
    def _clamp_axis(value, half, low, high):
        if high - low <= 2 * half:  # комната меньше экрана по этой оси — центрируем
            return (low + high) / 2
        return max(low + half, min(value, high - half))

    @property
    def offset(self):
        """Целое смещение мира: экранная позиция = мировая - offset."""
        return pygame.Vector2(round(self.pos.x - self.half.x), round(self.pos.y - self.half.y))

    @property
    def view_rect(self):
        """Видимая область в мировых координатах."""
        off = self.offset
        return pygame.Rect(int(off.x), int(off.y), SCREEN_WIDTH, SCREEN_HEIGHT)

    def apply(self, world_pos):
        """Мировая позиция -> экранная (целые координаты)."""
        off = self.offset
        return (round(world_pos[0] - off.x), round(world_pos[1] - off.y))