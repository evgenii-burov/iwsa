import pygame

from entities.player.player import Player
from map.map import Map
from settings import COLOR_BACKGROUND, COLOR_TEXT, FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from camera import Camera

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.running = True
        self.show_debug = False

        self.map = Map()
        self.player = Player(self.map.center)
        self.camera = Camera(self.player.pos)

    def run(self):
        while self.running:
            # dt в секундах; ограничиваем сверху, чтобы после лага игрок не «телепортировался»
            dt = min(self.clock.tick(FPS) / 1000, 0.05)
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_F3:
                    self.show_debug = not self.show_debug

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.map.bounds)
        self.camera.update(dt, self.player.pos, self.map.bounds)

    def draw(self):
        self.screen.fill(COLOR_BACKGROUND)
        self.map.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)
        if self.show_debug:
            self.draw_debug()
        pygame.display.flip()

    def draw_debug(self):
        p = self.player
        text = (
            f"FPS: {self.clock.get_fps():.0f}  pos: ({p.pos.x:.0f}, {p.pos.y:.0f})"
            f"  speed: {p.vel.length():.0f}"
            f"  cam lag: {(p.pos - self.camera.pos).length():.0f}"
        )
        self.screen.blit(self.font.render(text, True, COLOR_TEXT), (10, 10))