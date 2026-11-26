"""
menu.py
Landing screen: title, tagline, nav buttons, and a subtle scrolling maze
background built from a small generated maze tiled and panned over time.
"""

import pygame

import config
import fonts
from renderer import Button, draw_text
from generator import generate_maze


class Menu:
    def __init__(self):
        self.scroll_x = 0.0
        self.scroll_y = 0.0
        self.bg_maze = generate_maze(rows=14, cols=18)
        self.bg_cell = 22

        cx = config.WINDOW_WIDTH // 2
        btn_w, btn_h, gap = 260, 48, 16
        start_y = config.WINDOW_HEIGHT // 2 + 10

        self.buttons = {
            "play": Button((cx - btn_w // 2, start_y, btn_w, btn_h), "Generate / Play", size=18),
            "analytics": Button((cx - btn_w // 2, start_y + (btn_h + gap), btn_w, btn_h),
                                 "Analytics", size=18),
            "tutorial": Button((cx - btn_w // 2, start_y + 2 * (btn_h + gap), btn_w, btn_h),
                                "How to Play", size=18),
            "quit": Button((cx - btn_w // 2, start_y + 3 * (btn_h + gap), btn_w, btn_h),
                            "Quit", size=18),
        }

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, btn in self.buttons.items():
                if btn.hovered(event.pos):
                    return key
        return None

    def update(self, dt):
        self.scroll_x = (self.scroll_x + dt * 12) % self.bg_cell
        self.scroll_y = (self.scroll_y + dt * 6) % self.bg_cell

    def draw(self, surface):
        surface.fill(config.COLOR_BG)
        self._draw_background(surface)

        overlay = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*config.COLOR_BG, 165))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "HEURISTICA", (config.WINDOW_WIDTH // 2, 90), size=64,
                  color=config.COLOR_ACCENT, font_fn=fonts.mono, bold=True, align="center")
        draw_text(surface, '"Seeing the Logic"', (config.WINDOW_WIDTH // 2, 165), size=22,
                  color=config.COLOR_TEXT_DIM, font_fn=fonts.sans, align="center")

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons.values():
            btn.draw(surface, hovered=btn.hovered(mouse_pos))

        draw_text(surface, "AI Lab Project  ·  The Outliers", (config.WINDOW_WIDTH // 2,
                  config.WINDOW_HEIGHT - 36), size=14, color=config.COLOR_TEXT_DIM,
                  align="center")

    def _draw_background(self, surface):
        cell = self.bg_cell
        cols = config.WINDOW_WIDTH // cell + 2
        rows = config.WINDOW_HEIGHT // cell + 2
        maze = self.bg_maze
        for r in range(rows):
            for c in range(cols):
                mr = r % maze.rows
                mc = c % maze.cols
                if maze.is_wall((mr, mc)):
                    continue
                x = c * cell - self.scroll_x
                y = r * cell - self.scroll_y
                rect = pygame.Rect(int(x), int(y), cell - 1, cell - 1)
                pygame.draw.rect(surface, config.COLOR_PANEL, rect, border_radius=2)
