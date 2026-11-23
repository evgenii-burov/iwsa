"""HUD и сообщения. Здесь только текст (font.render + blit); примитивы рисует renderer."""
import pygame

from config import cfg


def make_font() -> pygame.font.Font:
    return pygame.font.Font(None, cfg.FONT_SIZE)


def draw_text(surface: pygame.Surface, font: pygame.font.Font, text: str, pos: tuple[int, int]) -> None:
    surface.blit(font.render(text, True, cfg.COLOR_TEXT), pos)


def draw_fps(surface: pygame.Surface, font: pygame.font.Font, fps: float, ticks_per_s: float) -> None:
    """Счётчик кадров рендера и тиков логики в левом верхнем углу."""
    draw_text(surface, font, f"FPS {fps:.0f}  logic {ticks_per_s:.0f} Hz", (cfg.HUD_MARGIN, cfg.HUD_MARGIN))
