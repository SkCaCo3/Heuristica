"""
config.py
Central configuration: window/grid dimensions, colors, terrain costs, fonts.
Nothing in here has side effects other than font loading, which fails over
gracefully to system fonts if the bundled .ttf files are not present.
"""

# ----------------------------------------------------------------------
# Window / grid geometry
# ----------------------------------------------------------------------
GRID_ROWS = 25
GRID_COLS = 35
CELL_SIZE = 24

SIDEBAR_WIDTH = 320
GRID_PIXEL_WIDTH = GRID_COLS * CELL_SIZE
GRID_PIXEL_HEIGHT = GRID_ROWS * CELL_SIZE

WINDOW_WIDTH = GRID_PIXEL_WIDTH + SIDEBAR_WIDTH
WINDOW_HEIGHT = max(GRID_PIXEL_HEIGHT, 700)

FPS = 60

# ----------------------------------------------------------------------
# Terrain types & costs
# ----------------------------------------------------------------------
WALL = "WALL"
PLAIN = "PLAIN"
MUD = "MUD"
WATER = "WATER"
START = "START"
END = "END"

TERRAIN_COST = {
    PLAIN: 1,
    MUD: 5,
    WATER: 10,
    START: 0,
    END: 0,
    WALL: float("inf"),
}

MIN_TERRAIN_COST = 1  # floor used by the heuristic's admissibility argument

# Fraction of open (non-wall) cells assigned to each weighted terrain type
MUD_FRACTION = 0.14
WATER_FRACTION = 0.08

# Fraction of internal walls knocked down after the perfect maze is carved
LOOP_FRACTION = 0.18

# Coins
COIN_CLUSTER_COUNT = 5
COIN_CLUSTER_SIZE = 6          # target cells per cluster (flood fill budget)
COIN_VALUE = 100

# Greed
GREED_COIN_DISCOUNT = 0.95      # effective_cost = cost * (1 - 0.95 * greed/100)

# ----------------------------------------------------------------------
# Colors (dark, modern technical palette)
# ----------------------------------------------------------------------
COLOR_BG = (18, 20, 26)
COLOR_SIDEBAR_BG = (24, 27, 35)
COLOR_PANEL = (30, 34, 44)
COLOR_PANEL_BORDER = (52, 58, 74)

COLOR_TEXT = (226, 230, 240)
COLOR_TEXT_DIM = (140, 148, 168)
COLOR_ACCENT = (94, 170, 255)
COLOR_ACCENT_DIM = (58, 96, 140)
COLOR_WARN = (255, 150, 90)
COLOR_GOOD = (110, 220, 150)

COLOR_WALL = (14, 15, 19)
COLOR_PLAIN = (46, 50, 61)
COLOR_MUD = (120, 84, 42)
COLOR_WATER = (35, 98, 160)
COLOR_START = (90, 200, 130)
COLOR_END = (220, 90, 90)

COLOR_VISITED = (70, 90, 130)
COLOR_FRONTIER = (210, 190, 90)
COLOR_CURRENT = (255, 255, 255)
COLOR_PATH = (255, 210, 60)
COLOR_COIN = (255, 215, 60)
COLOR_COIN_COLLECTED = (120, 110, 60)

BUTTON_BG = (40, 45, 58)
BUTTON_BG_HOVER = (54, 61, 80)
BUTTON_BG_ACTIVE = (58, 110, 170)
BUTTON_BORDER = (70, 78, 98)

ALGO_COLORS = {
    "BFS": (120, 190, 255),
    "DFS": (255, 150, 120),
    "UCS": (150, 220, 150),
    "GREEDY": (230, 170, 255),
    "ASTAR": (255, 210, 90),
}

# Font asset locations (loaded lazily by fonts.py, which is the only module
# in this project that imports pygame.font -- keeping that import out of
# config.py lets grid.py/generator.py/algorithms/statistics_engine.py stay
# fully Pygame-free and independently testable).
import os as _os
FONT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "assets", "fonts")
MONO_REGULAR = _os.path.join(FONT_DIR, "JetBrainsMono-Regular.ttf")
MONO_BOLD = _os.path.join(FONT_DIR, "JetBrainsMono-Bold.ttf")
SANS_REGULAR = _os.path.join(FONT_DIR, "IBMPlexSans-Regular.ttf")
SANS_BOLD = _os.path.join(FONT_DIR, "IBMPlexSans-Bold.ttf")
