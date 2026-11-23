"""Абстракция ввода: действия -> клавиши.

Игровая логика клавиатуру напрямую не читает, только InputState.
Привязки по умолчанию заданы здесь; загрузка/сохранение controls.json
добавится на этапе 10.
"""
from dataclasses import dataclass

import pygame

# Имена действий
MOVE_UP, MOVE_DOWN = "move_up", "move_down"
MOVE_LEFT, MOVE_RIGHT = "move_left", "move_right"
SHOOT_UP, SHOOT_DOWN = "shoot_up", "shoot_down"
SHOOT_LEFT, SHOOT_RIGHT = "shoot_left", "shoot_right"
BLINK, RESTART, DEBUG = "blink", "restart", "debug"

ACTIONS: tuple[str, ...] = (
    MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT,
    SHOOT_UP, SHOOT_DOWN, SHOOT_LEFT, SHOOT_RIGHT,
    BLINK, RESTART, DEBUG,
)

# Действия-«события»: срабатывают один раз по нажатию, а не пока зажато
PRESS_ACTIONS: frozenset[str] = frozenset({BLINK, RESTART, DEBUG})

Bindings = dict[str, int]

DEFAULT_BINDINGS: Bindings = {
    MOVE_UP: pygame.K_w, MOVE_DOWN: pygame.K_s,
    MOVE_LEFT: pygame.K_a, MOVE_RIGHT: pygame.K_d,
    SHOOT_UP: pygame.K_UP, SHOOT_DOWN: pygame.K_DOWN,
    SHOOT_LEFT: pygame.K_LEFT, SHOOT_RIGHT: pygame.K_RIGHT,
    BLINK: pygame.K_SPACE, RESTART: pygame.K_r, DEBUG: pygame.K_F1,
}


@dataclass
class InputState:
    """Результат опроса ввода за один тик логики."""
    move_vec: pygame.Vector2         # единичный вектор движения или (0, 0)
    shoot_dir: pygame.Vector2 | None  # единичный вектор стрельбы или None
    blink_pressed: bool = False
    restart_pressed: bool = False
    debug_pressed: bool = False


def _axis_vector(keys, bindings: Bindings, left: str, right: str, up: str, down: str) -> pygame.Vector2:
    """Суммирует четыре направления в вектор; противоположные клавиши гасятся."""
    vec = pygame.Vector2(
        int(bool(keys[bindings[right]])) - int(bool(keys[bindings[left]])),
        int(bool(keys[bindings[down]])) - int(bool(keys[bindings[up]])),
    )
    if vec.length_squared() > 0:
        vec.normalize_ip()
    return vec


class InputHandler:
    """Сопоставляет события и состояние клавиатуры с действиями."""

    def __init__(self, bindings: Bindings | None = None) -> None:
        self.bindings: Bindings = dict(bindings or DEFAULT_BINDINGS)
        self._latched: set[str] = set()  # нажатия между тиками не теряются

    def handle_event(self, event: pygame.event.Event) -> None:
        """Запоминает нажатия действий-событий (blink, restart, debug)."""
        if event.type != pygame.KEYDOWN:
            return
        for action in PRESS_ACTIONS:
            if self.bindings[action] == event.key:
                self._latched.add(action)

    def poll(self) -> InputState:
        """Опрос на один тик логики; сбрасывает запомненные нажатия."""
        keys = pygame.key.get_pressed()
        state = InputState(
            move_vec=_axis_vector(keys, self.bindings, MOVE_LEFT, MOVE_RIGHT, MOVE_UP, MOVE_DOWN),
            shoot_dir=None,
            blink_pressed=BLINK in self._latched,
            restart_pressed=RESTART in self._latched,
            debug_pressed=DEBUG in self._latched,
        )
        shoot = _axis_vector(keys, self.bindings, SHOOT_LEFT, SHOOT_RIGHT, SHOOT_UP, SHOOT_DOWN)
        state.shoot_dir = shoot if shoot.length_squared() > 0 else None
        self._latched.clear()
        return state
