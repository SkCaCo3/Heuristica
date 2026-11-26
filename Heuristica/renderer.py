"""
renderer.py
Pure drawing functions: terrain cells, coins, the algorithm's live state
(visited/frontier/current/path), and reusable UI chrome (panels, buttons,
sliders, text). No game-state logic lives here -- callers pass in exactly
what should appear on screen this frame.
"""

import pygame
import config
import fonts

TERRAIN_COLOR = {
    config.WALL: config.COLOR_WALL,
    config.PLAIN: config.COLOR_PLAIN,
    config.MUD: config.COLOR_MUD,
    config.WATER: config.COLOR_WATER,
    config.START: config.COLOR_START,
    config.END: config.COLOR_END,
}


# --------------------------------------------------------------------------
# Grid rendering
# --------------------------------------------------------------------------
def draw_grid(surface, grid, origin=(0, 0), cell_size=config.CELL_SIZE,
              visited=None, frontier=None, current=None, path=None,
              collected_coins=None):
    """
    Draw the maze. Layering (back to front): terrain -> visited ->
    frontier -> path -> coins -> current node -> start/end outline.
    """
    visited = visited or set()
    frontier = frontier or set()
    path = path or []
    path_set = set(path)
    collected_coins = collected_coins or set()

    ox, oy = origin

    for r in range(grid.rows):
        for c in range(grid.cols):
            cell = (r, c)
            terrain = grid.terrain_at(cell)
            x = ox + c * cell_size
            y = oy + r * cell_size
            rect = pygame.Rect(x, y, cell_size, cell_size)

            color = TERRAIN_COLOR[terrain]
            pygame.draw.rect(surface, color, rect)

            if terrain != config.WALL:
                if cell in path_set:
                    _blend_rect(surface, rect, config.COLOR_PATH, 200)
                elif cell in frontier:
                    _blend_rect(surface, rect, config.COLOR_FRONTIER, 160)
                elif cell in visited:
                    _blend_rect(surface, rect, config.COLOR_VISITED, 170)

            if cell in grid.coins:
                _draw_coin(surface, rect, collected=cell in collected_coins or cell in path_set)

            pygame.draw.rect(surface, (0, 0, 0, 40), rect, 1)

    if current is not None and grid.is_passable(current):
        r, c = current
        rect = pygame.Rect(ox + c * cell_size, oy + r * cell_size, cell_size, cell_size)
        pygame.draw.rect(surface, config.COLOR_CURRENT, rect, 3)

    # Outline start/end so they stay legible under overlays
    for cell, color in ((grid.start, config.COLOR_START), (grid.end, config.COLOR_END)):
        if cell is None:
            continue
        r, c = cell
        rect = pygame.Rect(ox + c * cell_size, oy + r * cell_size, cell_size, cell_size)
        pygame.draw.rect(surface, color, rect, 2)


def _blend_rect(surface, rect, color, alpha):
    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    overlay.fill((*color, alpha))
    surface.blit(overlay, rect.topleft)


def _draw_coin(surface, rect, collected=False):
    color = config.COLOR_COIN_COLLECTED if collected else config.COLOR_COIN
    center = rect.center
    radius = max(3, rect.width // 4)
    pygame.draw.circle(surface, color, center, radius)
    pygame.draw.circle(surface, (0, 0, 0), center, radius, 1)


# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------
def draw_text(surface, text, pos, size=18, color=config.COLOR_TEXT,
              font_fn=None, bold=False, align="left"):
    font_fn = font_fn or fonts.sans
    font = font_fn(size, bold=bold)
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if align == "left":
        rect.topleft = pos
    elif align == "center":
        rect.midtop = pos
    elif align == "right":
        rect.topright = pos
    surface.blit(rendered, rect)
    return rect


# --------------------------------------------------------------------------
# UI chrome
# --------------------------------------------------------------------------
class Button:
    """A clickable rectangle with hover/active states. Framework-agnostic
    enough to be reused for menu buttons, sidebar algorithm picks, etc."""

    def __init__(self, rect, label, size=18, bold=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.size = size
        self.bold = bold

    def draw(self, surface, hovered=False, active=False):
        bg = config.BUTTON_BG_ACTIVE if active else (
            config.BUTTON_BG_HOVER if hovered else config.BUTTON_BG)
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, config.BUTTON_BORDER, self.rect, 1, border_radius=6)
        font = fonts.sans(self.size, bold=self.bold)
        rendered = font.render(self.label, True, config.COLOR_TEXT)
        surface.blit(rendered, rendered.get_rect(center=self.rect.center))

    def hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def clicked(self, mouse_pos, mouse_down):
        return mouse_down and self.rect.collidepoint(mouse_pos)


class Slider:
    """Horizontal 0-100 slider used for the A* greed control."""

    def __init__(self, rect, value=0):
        self.rect = pygame.Rect(rect)
        self.value = value
        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.dragging = True
            self._set_from_mouse(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_mouse(event.pos[0])

    def _set_from_mouse(self, mouse_x):
        frac = (mouse_x - self.rect.x) / max(1, self.rect.width)
        self.value = int(max(0, min(100, round(frac * 100))))

    def draw(self, surface, label="Greed"):
        track = pygame.Rect(self.rect.x, self.rect.centery - 3, self.rect.width, 6)
        pygame.draw.rect(surface, config.COLOR_PANEL_BORDER, track, border_radius=3)
        fill_w = int(self.rect.width * (self.value / 100))
        fill = pygame.Rect(self.rect.x, self.rect.centery - 3, fill_w, 6)
        pygame.draw.rect(surface, config.COLOR_ACCENT, fill, border_radius=3)

        handle_x = self.rect.x + fill_w
        pygame.draw.circle(surface, config.COLOR_ACCENT, (handle_x, self.rect.centery), 9)
        pygame.draw.circle(surface, config.COLOR_TEXT, (handle_x, self.rect.centery), 9, 2)

        draw_text(surface, f"{label}: {self.value}%", (self.rect.x, self.rect.y - 22),
                  size=16, color=config.COLOR_TEXT_DIM, font_fn=fonts.mono)


def draw_panel(surface, rect, border=True):
    pygame.draw.rect(surface, config.COLOR_PANEL, rect, border_radius=8)
    if border:
        pygame.draw.rect(surface, config.COLOR_PANEL_BORDER, rect, 1, border_radius=8)
