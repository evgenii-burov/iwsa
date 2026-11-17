import pygame

from settings import COLOR_FLOOR, COLOR_GRID, COLOR_WALL, GRID_SIZE, ROOM_HEIGHT, ROOM_WIDTH


class Map:
    """Одна прямоугольная комната, центрированная в окне."""

    WALL_THICKNESS = 4

    def __init__(self):
        self.bounds = pygame.Rect(0, 0, ROOM_WIDTH, ROOM_HEIGHT)

    @property
    def center(self):
        return pygame.Vector2(self.bounds.center)

    def draw(self, surface, camera):
        off = camera.offset
        ox, oy = int(off.x), int(off.y)
        room = self.bounds.move(-ox, -oy)
        pygame.draw.rect(surface, COLOR_FLOOR, room)

        visible = camera.view_rect.clip(self.bounds)
        for x in range(-(-visible.left // GRID_SIZE) * GRID_SIZE, visible.right, GRID_SIZE):
            pygame.draw.line(surface, COLOR_GRID, (x - ox, visible.top - oy), (x - ox, visible.bottom - oy))
        for y in range(-(-visible.top // GRID_SIZE) * GRID_SIZE, visible.bottom, GRID_SIZE):
            pygame.draw.line(surface, COLOR_GRID, (visible.left - ox, y - oy), (visible.right - ox, y - oy))

        pygame.draw.rect(surface, COLOR_WALL, room, self.WALL_THICKNESS)