"""Ввод и безоконный запуск игры."""
import pygame
import pytest

from config import cfg
from input import BLINK, DEFAULT_BINDINGS, InputHandler
from main import Game, main
from room import load_all_rooms
from pathlib import Path


@pytest.fixture(scope="module", autouse=True)
def pygame_session():
    pygame.init()
    pygame.display.set_mode((cfg.SCREEN_W, cfg.SCREEN_H))
    yield
    pygame.quit()


class FakeKeys:
    def __init__(self, *pressed):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed


def poll_with(monkeypatch, *pressed):
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: FakeKeys(*pressed))
    return InputHandler().poll()


def test_move_vector_is_normalized(monkeypatch):
    state = poll_with(monkeypatch, pygame.K_w, pygame.K_d)
    assert state.move_vec.length() == pytest.approx(1)
    assert state.move_vec.x > 0 > state.move_vec.y


def test_opposite_shoot_keys_cancel(monkeypatch):
    state = poll_with(monkeypatch, pygame.K_LEFT, pygame.K_RIGHT)
    assert state.shoot_dir is None


def test_diagonal_shoot(monkeypatch):
    state = poll_with(monkeypatch, pygame.K_UP, pygame.K_LEFT)
    assert state.shoot_dir is not None and state.shoot_dir.length() == pytest.approx(1)


def test_blink_press_survives_until_poll_then_clears(monkeypatch):
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: FakeKeys())
    handler = InputHandler()
    handler.handle_event(pygame.event.Event(pygame.KEYDOWN, key=DEFAULT_BINDINGS[BLINK]))
    assert handler.poll().blink_pressed
    assert not handler.poll().blink_pressed


def test_headless_run_and_fixed_step():
    rooms = load_all_rooms(Path(__file__).parent.parent / cfg.ROOMS_DIR)
    game = Game(rooms, seed=1, room_index=0)
    game.run(max_frames=30)  # не падает; pygame.quit() вызывается внутри
    assert game.fps.ticks_per_s >= 0


def test_cli_rejects_bad_room_number():
    assert main(["--room", "99", "--frames", "1"]) == 2


def test_player_never_enters_walls_with_random_input(monkeypatch):
    """Интеграция: случайный ввод на всех комнатах, круг игрока не пересекает стены."""
    import random
    rooms = load_all_rooms(Path(__file__).parent.parent / cfg.ROOMS_DIR)
    rng = random.Random(7)
    keys = [DEFAULT_BINDINGS[a] for a in ("move_up", "move_down", "move_left", "move_right")]
    for index in range(len(rooms)):
        game = Game(rooms, seed=1, room_index=index)
        for step in range(900):
            if step % 20 == 0:
                held = [k for k in keys if rng.random() < 0.5]
            monkeypatch.setattr(pygame.key, "get_pressed", lambda held=held: FakeKeys(*held))
            game._tick(cfg.DT)
            p = game.world.player
            for ty in range(int(p.pos.y // cfg.TILE) - 1, int(p.pos.y // cfg.TILE) + 2):
                for tx in range(int(p.pos.x // cfg.TILE) - 1, int(p.pos.x // cfg.TILE) + 2):
                    if game.world.room.is_solid(tx, ty):
                        nearest = pygame.Vector2(
                            min(max(p.pos.x, tx * cfg.TILE), (tx + 1) * cfg.TILE),
                            min(max(p.pos.y, ty * cfg.TILE), (ty + 1) * cfg.TILE),
                        )
                        assert nearest.distance_to(p.pos) >= p.radius - 1e-6
        pygame.quit()
        pygame.init()
