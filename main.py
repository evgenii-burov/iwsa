"""Окно, игровой цикл с фиксированным шагом, машина состояний."""
import argparse
import random
import sys
import time
from enum import Enum, auto
from pathlib import Path

import pygame

import ui
from config import cfg
from input import InputHandler, InputState
from physics import collide_circle_with_tiles
from renderer import Renderer
from room import Room, RoomError, load_all_rooms, pick_next_room
from world import World


class State(Enum):
    MENU = auto()
    PLAY = auto()
    PAUSE = auto()
    CONTROLS = auto()
    ROOM_CLEARED = auto()
    DEAD = auto()


class FpsCounter:
    """Считает кадры рендера и тики логики за период cfg.FPS_UPDATE_PERIOD."""

    def __init__(self) -> None:
        self.fps = 0.0
        self.ticks_per_s = 0.0
        self._frames = 0
        self._ticks = 0
        self._elapsed = 0.0

    def add_tick(self) -> None:
        self._ticks += 1

    def add_frame(self, frame_time: float) -> None:
        self._frames += 1
        self._elapsed += frame_time
        if self._elapsed >= cfg.FPS_UPDATE_PERIOD:
            self.fps = self._frames / self._elapsed
            self.ticks_per_s = self._ticks / self._elapsed
            self._frames = self._ticks = 0
            self._elapsed = 0.0


class Game:
    def __init__(self, rooms: list[Room], seed: int | None = None, room_index: int | None = None) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((cfg.SCREEN_W, cfg.SCREEN_H), pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption(cfg.TITLE)
        self.clock = pygame.time.Clock()
        self.font = ui.make_font()
        self.renderer = Renderer(self.screen)
        self.input = InputHandler()
        self.fps = FpsCounter()
        self.rng = random.Random(seed)
        self.rooms = rooms
        self.running = True
        self.show_debug = False
        # До этапа 10 игра стартует сразу в PLAY
        self.state = State.PLAY
        index = self.rng.randrange(len(rooms)) if room_index is None else room_index
        self.world = World.from_room(rooms[index], index)

    # --- Цикл ---

    def run(self, max_frames: int | None = None) -> None:
        accumulator = 0.0
        previous = time.perf_counter()
        frames = 0
        while self.running and (max_frames is None or frames < max_frames):
            now = time.perf_counter()
            frame_time = min(now - previous, cfg.MAX_FRAME_TIME)
            previous = now
            accumulator += frame_time

            self._process_events()
            while accumulator >= cfg.DT:
                self._tick(cfg.DT)
                self.fps.add_tick()
                accumulator -= cfg.DT

            self._render()
            self.fps.add_frame(frame_time)
            self.clock.tick(cfg.MAX_RENDER_FPS)
            frames += 1
        pygame.quit()

    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            self.input.handle_event(event)
            if event.type == pygame.KEYDOWN:
                self._on_keydown(event.key)

    def _on_keydown(self, key: int) -> None:
        # Esc зарезервирован под меню; пока меню нет (этап 10), он закрывает игру
        if key == pygame.K_ESCAPE and self.state is State.PLAY:
            self.running = False

    # --- Логика ---

    def _tick(self, dt: float) -> None:
        inp = self.input.poll()
        if inp.debug_pressed:
            self.show_debug = not self.show_debug
        if self.state is State.PLAY:
            self._tick_play(dt, inp)

    def _tick_play(self, dt: float, inp: InputState) -> None:
        if inp.restart_pressed:  # в PLAY: перезапуск текущей комнаты (отладка)
            self.load_room(self.world.room_index)
            return
        self._move_player_debug(dt, inp)
        self.world.time += dt

    def _move_player_debug(self, dt: float, inp: InputState) -> None:
        """ВРЕМЕННО (этап 2): прямое движение, чтобы проверить коллизии. Заменится на этапе 3."""
        player = self.world.player
        player.vel.update(inp.move_vec * cfg.PLAYER_DEBUG_SPEED)
        player.pos += player.vel * dt
        collide_circle_with_tiles(player.pos, player.vel, player.radius, self.world.room.is_solid)

    def load_room(self, index: int) -> None:
        self.world = World.from_room(self.rooms[index], index, self.world.rooms_cleared)

    def next_room_index(self) -> int:
        return pick_next_room(len(self.rooms), self.world.room_index, self.rng)

    # --- Рендер ---

    def _render(self) -> None:
        self.renderer.draw_world(self.world, draw_grid=self.show_debug)
        ui.draw_fps(self.screen, self.font, self.fps.fps, self.fps.ticks_per_s)
        pygame.display.flip()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=cfg.TITLE)
    parser.add_argument("--room", type=int, help="номер комнаты (с 1); по умолчанию случайная")
    parser.add_argument("--seed", type=int, help="seed генератора случайных чисел")
    parser.add_argument("--frames", type=int, help="закрыть игру после N кадров (для проверок)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        rooms = load_all_rooms(Path(__file__).parent / cfg.ROOMS_DIR)
    except RoomError as err:
        print(f"Ошибка комнаты:\n{err}", file=sys.stderr)
        return 1
    for room in rooms:
        for warning in room.warnings:
            print(f"Предупреждение: {warning}", file=sys.stderr)
    if args.room is not None and not 1 <= args.room <= len(rooms):
        print(f"--room: нужно число от 1 до {len(rooms)}", file=sys.stderr)
        return 2
    index = None if args.room is None else args.room - 1
    Game(rooms, seed=args.seed, room_index=index).run(max_frames=args.frames)
    return 0


if __name__ == "__main__":
    sys.exit(main())
