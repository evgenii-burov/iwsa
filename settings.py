"""Общие константы игры."""

# Окно
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "I Wanna Be the Blinker"

# Комната (игровое поле), центрируется в окне
ROOM_WIDTH = 2560
ROOM_HEIGHT = 1440
GRID_SIZE = 128
CAMERA_LAG_TIME = 0.18   # с
CAMERA_MAX_LEAD = 250    # px

COLOR_GRID = (38, 41, 60)

# Игрок (круглый)
PLAYER_RADIUS = 14        # радиус хитбокса и спрайта, px
PLAYER_MAX_SPEED = 700    # предельная скорость, px/с
PLAYER_FRICTION = 2     # сила торможения, 1/с: меньше = скользит дольше (лёд ~1.0, Doom ~3.5)
# Ускорение считается автоматически: ACCEL = MAX_SPEED * FRICTION.
# Время разгона до ~63% скорости = 1 / FRICTION секунд.
PLAYER_WALL_BOUNCE = 0.0  # 0 = гасим скорость о стену, 0.5 = отскок вполсилы

# Цвета
COLOR_BACKGROUND = (12, 12, 18)
COLOR_FLOOR = (28, 30, 44)
COLOR_WALL = (90, 95, 130)
COLOR_PLAYER = (80, 220, 255)
COLOR_TEXT = (220, 220, 230)