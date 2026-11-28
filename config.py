"""Параметры игры и баланса.

Обращаться как `cfg.ИМЯ` (from config import cfg), а не через `from config import *`.
Единицы измерения: px — пиксели логического разрешения, s — секунды,
tiles — тайлы, 1/s — «темп» (экспоненциальное затухание/разгон).
"""
from dataclasses import dataclass

Color = tuple[int, int, int]


@dataclass
class Config:
    # --- Окно и цикл ---
    SCREEN_W: int = 960             # px, логическая ширина
    SCREEN_H: int = 540             # px, логическая высота
    TITLE: str = "Blink Arena"
    LOGIC_HZ: int = 60              # Гц, частота фиксированного шага логики
    MAX_FRAME_TIME: float = 0.25    # s, потолок накопления времени (защита от «спирали смерти»)
    MAX_RENDER_FPS: int = 120       # кадров/с, ограничитель рендера
    FPS_UPDATE_PERIOD: float = 0.5  # s, как часто обновляется показание FPS

    # --- Комната ---
    TILE: int = 30                  # px, размер тайла
    ROOM_W: int = 32                # tiles, ширина комнаты (с рамкой стен)
    ROOM_H: int = 18                # tiles, высота комнаты (с рамкой стен)
    MIN_ENEMIES: int = 3            # минимум врагов в комнате (валидатор)
    SPAWN_SAFE_DIST: float = 240.0  # px, враги не ближе этого к старту игрока
    MIN_CORRIDOR_WIDTH: int = 2     # tiles, уже — предупреждение валидатора
    ROOMS_DIR: str = "rooms"        # каталог с файлами комнат (рядом с игрой)

    # --- Физика ---
    COLLISION_ITERATIONS: int = 8   # макс. число выталкиваний круга из тайлов за тик
    COLLISION_EPS: float = 1e-9     # допуск при сравнении расстояний

    # --- Игрок ---
    PLAYER_RADIUS: float = 10.0     # px

    # Движение («Дум на шифте»): резкий старт и занос
    MAX_SPEED: float = 280.0            # px/s, предельная скорость вдоль ввода
    ACCEL_RATE: float = 14.0            # 1/s, темп разгона к MAX_SPEED (больше = резче старт)
    REVERSE_BRAKE_RATE: float = 6.0     # 1/s, темп гашения скорости против ввода
                                        # (меньше ACCEL_RATE: при развороте игрока заносит)
    LATERAL_GRIP: float = 5.0           # 1/s, гашение боковой скорости (меньше = больше заноса)
    SLIDE_RATE: float = 3.5             # 1/s, затухание скорости без ввода (меньше = дольше скользит)
    STOP_SPEED: float = 1.0             # px/s, ниже этого скорость без ввода обнуляется

    # --- Стрельба игрока ---
    FIRE_RATE: float = 10.0             # выстрелов/с
    BULLET_SPEED: float = 600.0         # px/s
    BULLET_DAMAGE: int = 1              # урон одной пули
    FIRE_SPREAD_DEG: float = 0.0        # градусы, разброс (случайный в ±значение)
    BULLET_RADIUS: float = 3.0          # px, только для отрисовки (попадание считается точкой)

    # --- Враги: общее ---
    SEPARATION_ITERATIONS: int = 4      # проходов расталкивания кругов за тик (для скученных врагов)
    PLAYER_PUSH_SHARE: float = 1.0      # доля сдвига при столкновении игрока с врагом, которую берёт
                                        # на себя игрок (1 = враг блокирует и не сдвигается, 0.5 = поровну)
    ENEMY_PUSH_SHARE: float = 0.5       # то же для пары враг-враг (0.5 = расходятся поровну)
    SPAWN_TIME: float = 0.8             # s, «проявление» без урона и без твёрдости
    HIT_FLASH_TIME: float = 0.08        # s, мигание врага при попадании

    # --- Враги: радиусы и здоровье (поведение появится на этапах 6-8) ---
    CHASER_RADIUS: float = 10.0         # px
    GUNNER_RADIUS: float = 12.0         # px
    SNIPER_RADIUS: float = 12.0         # px
    CHASER_HP: int = 3                  # единиц здоровья
    GUNNER_HP: int = 4
    SNIPER_HP: int = 5

    # --- Цвета ---
    COLOR_BG: Color = (10, 10, 16)
    COLOR_FLOOR: Color = (28, 30, 44)
    COLOR_WALL: Color = (84, 90, 124)
    COLOR_GRID: Color = (36, 38, 54)
    COLOR_PLAYER: Color = (80, 220, 255)
    COLOR_CHASER: Color = (255, 110, 90)
    COLOR_GUNNER: Color = (255, 200, 70)
    COLOR_SNIPER: Color = (190, 120, 255)
    COLOR_TEXT: Color = (220, 220, 230)
    COLOR_BULLET: Color = (255, 255, 200)
    COLOR_HIT_FLASH: Color = (255, 255, 255)

    # --- HUD ---
    FONT_SIZE: int = 22             # px
    HUD_MARGIN: int = 36            # px, отступ текста от края (рамка стен занимает 30)

    @property
    def DT(self) -> float:
        """Длительность шага логики, s."""
        return 1.0 / self.LOGIC_HZ


cfg = Config()
