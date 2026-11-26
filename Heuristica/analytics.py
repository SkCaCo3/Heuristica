"""
analytics.py
The Analytics dashboard screen. Runs all 7 comparison variants on the
current maze via statistics_engine (pure Python, no Pygame there) and
renders three tabs: Summary Table, Scatter Plot, Radar Graph.
"""

import math
import pygame

import config
import fonts
import statistics_engine as se
from renderer import Button, draw_text, draw_panel

TABLE_COLUMNS = [
    ("Variant", "variant", 168),
    ("Nodes", "nodes_explored", 70),
    ("Steps", "path_length", 60),
    ("Cost", "path_cost", 70),
    ("Penalty", "terrain_penalty", 70),
    ("Coins", "coins_collected", 60),
    ("Score", "score", 70),
    ("Efficiency", "efficiency", 80),
]

RADAR_DIMS = ["cheap_terrain", "coin_ratio", "path_efficiency"]
RADAR_LABELS = ["Cheap Terrain", "Coin Ratio", "Path Efficiency"]

VARIANT_COLORS = [
    (120, 190, 255), (255, 150, 120), (150, 220, 150), (230, 170, 255),
    (255, 210, 90), (255, 130, 200), (140, 255, 220),
]


class Analytics:
    def __init__(self, grid):
        self.grid = grid
        self.results = se.run_all_variants(grid)
        self.node_stats = se.descriptive_stats([r["nodes_explored"] for r in self.results])
        self.score_stats = se.descriptive_stats([r["score"] for r in self.results])
        self.correlation = se.correlation_summary(self.results)
        self.radar = se.radar_profiles(grid, self.results)
        self.verdicts = se.compute_verdicts(self.results)

        self.tab = "summary"
        tab_w, tab_h = 160, 36
        self.tab_buttons = {
            "summary": Button((40, 70, tab_w, tab_h), "Summary Table", size=14),
            "scatter": Button((40 + tab_w + 8, 70, tab_w, tab_h), "Scatter Plot", size=14),
            "radar": Button((40 + 2 * (tab_w + 8), 70, tab_w, tab_h), "Radar Graph", size=14),
        }
        self.btn_back = Button((config.WINDOW_WIDTH - 200, 70, 160, 36), "Back to Menu", size=14)

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, btn in self.tab_buttons.items():
                if btn.hovered(event.pos):
                    self.tab = key
            if self.btn_back.hovered(event.pos):
                return "menu"
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "menu"
        return None

    def update(self, dt):
        pass

    # ------------------------------------------------------------------
    def draw(self, surface):
        surface.fill(config.COLOR_BG)
        draw_text(surface, "Analytics Dashboard", (40, 20), size=30,
                  color=config.COLOR_ACCENT, font_fn=fonts.mono, bold=True)
        draw_text(surface, f"{self.grid.rows}x{self.grid.cols} maze  ·  "
                  f"{len(self.grid.coins)} coins  ·  7 variants compared",
                  (40, 54), size=14, color=config.COLOR_TEXT_DIM)

        mouse_pos = pygame.mouse.get_pos()
        for key, btn in self.tab_buttons.items():
            btn.draw(surface, hovered=btn.hovered(mouse_pos), active=(key == self.tab))
        self.btn_back.draw(surface, hovered=self.btn_back.hovered(mouse_pos))

        content_rect = pygame.Rect(40, 120, config.WINDOW_WIDTH - 80,
                                    config.WINDOW_HEIGHT - 160)
        draw_panel(surface, content_rect)

        if self.tab == "summary":
            self._draw_summary(surface, content_rect)
        elif self.tab == "scatter":
            self._draw_scatter(surface, content_rect)
        elif self.tab == "radar":
            self._draw_radar(surface, content_rect)

    # ------------------------------------------------------------------
    def _draw_summary(self, surface, rect):
        x0, y0 = rect.x + 20, rect.y + 16
        col_x = x0
        widths = [w for _, _, w in TABLE_COLUMNS]

        for (label, _, w) in TABLE_COLUMNS:
            draw_text(surface, label, (col_x, y0), size=13, color=config.COLOR_TEXT_DIM,
                      font_fn=fonts.mono, bold=True)
            col_x += w
        pygame.draw.line(surface, config.COLOR_PANEL_BORDER, (x0, y0 + 22),
                          (x0 + sum(widths), y0 + 22), 1)

        row_y = y0 + 32
        for i, r in enumerate(self.results):
            col_x = x0
            row_color = config.COLOR_TEXT if i % 2 == 0 else config.COLOR_TEXT_DIM
            for (_, key, w) in TABLE_COLUMNS:
                val = r[key]
                text = f"{val:.2f}" if isinstance(val, float) else str(val)
                draw_text(surface, text, (col_x, row_y), size=13, color=row_color,
                          font_fn=fonts.mono)
                col_x += w
            row_y += 22

            badges = self.verdicts.get(r["variant"], [])
            if badges:
                draw_text(surface, "  " + " · ".join(badges), (col_x, row_y - 22),
                          size=12, color=config.COLOR_GOOD, font_fn=fonts.sans)

        row_y += 20
        draw_text(surface, "Descriptive statistics — Nodes Explored across all 7 variants",
                  (x0, row_y), size=14, color=config.COLOR_ACCENT, bold=True)
        row_y += 24
        stat_line = "  ".join(f"{k}: {v}" for k, v in self.node_stats.items())
        draw_text(surface, stat_line, (x0, row_y), size=13, color=config.COLOR_TEXT,
                  font_fn=fonts.mono)

        row_y += 30
        draw_text(surface, "Descriptive statistics — Score across all 7 variants",
                  (x0, row_y), size=14, color=config.COLOR_ACCENT, bold=True)
        row_y += 24
        stat_line = "  ".join(f"{k}: {v}" for k, v in self.score_stats.items())
        draw_text(surface, stat_line, (x0, row_y), size=13, color=config.COLOR_TEXT,
                  font_fn=fonts.mono)

    # ------------------------------------------------------------------
    def _draw_scatter(self, surface, rect):
        plot_rect = pygame.Rect(rect.x + 60, rect.y + 20, rect.width - 300, rect.height - 100)
        pygame.draw.rect(surface, config.COLOR_BG, plot_rect)
        pygame.draw.rect(surface, config.COLOR_PANEL_BORDER, plot_rect, 1)

        xs = self.correlation["xs"]
        ys = self.correlation["ys"]
        labels = self.correlation["labels"]

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        x_pad = max(1, (x_max - x_min) * 0.12)
        y_pad = max(1, (y_max - y_min) * 0.12)
        x_min, x_max = x_min - x_pad, x_max + x_pad
        y_min, y_max = y_min - y_pad, y_max + y_pad

        def to_px(x, y):
            fx = (x - x_min) / (x_max - x_min) if x_max != x_min else 0.5
            fy = (y - y_min) / (y_max - y_min) if y_max != y_min else 0.5
            px = plot_rect.x + fx * plot_rect.width
            py = plot_rect.bottom - fy * plot_rect.height
            return int(px), int(py)

        # Axes labels
        draw_text(surface, "Nodes Explored", (plot_rect.centerx, plot_rect.bottom + 8),
                  size=13, color=config.COLOR_TEXT_DIM, align="center")
        score_label = draw_text(surface, "Score", (plot_rect.x - 44, plot_rect.centery),
                                 size=13, color=config.COLOR_TEXT_DIM)

        # Trend line
        slope, intercept = self.correlation["slope"], self.correlation["intercept"]
        p1 = to_px(x_min, slope * x_min + intercept)
        p2 = to_px(x_max, slope * x_max + intercept)
        pygame.draw.line(surface, config.COLOR_WARN, p1, p2, 2)

        # Points
        for x, y, label, color in zip(xs, ys, labels, VARIANT_COLORS):
            px, py = to_px(x, y)
            pygame.draw.circle(surface, color, (px, py), 7)
            pygame.draw.circle(surface, config.COLOR_TEXT, (px, py), 7, 1)
            draw_text(surface, label, (px + 10, py - 8), size=11, color=config.COLOR_TEXT)

        # Side panel: correlation readout
        side_x = plot_rect.right + 30
        draw_text(surface, f"r = {self.correlation['r']:.3f}", (side_x, rect.y + 24),
                  size=22, color=config.COLOR_ACCENT, font_fn=fonts.mono, bold=True)
        draw_text(surface, f"trend: y = {slope:.3f}x + {intercept:.2f}",
                  (side_x, rect.y + 56), size=13, color=config.COLOR_TEXT_DIM, font_fn=fonts.mono)

        wrapped = _wrap_text(self.correlation["interpretation"], 34)
        y = rect.y + 92
        for line in wrapped:
            draw_text(surface, line, (side_x, y), size=13, color=config.COLOR_TEXT)
            y += 20

    # ------------------------------------------------------------------
    def _draw_radar(self, surface, rect):
        cx = rect.x + rect.width // 3
        cy = rect.centery
        radius = min(rect.width // 3, rect.height // 2) - 40
        n = len(RADAR_DIMS)
        angles = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]

        # Grid rings
        for frac in (0.25, 0.5, 0.75, 1.0):
            points = [
                (cx + math.cos(a) * radius * frac, cy + math.sin(a) * radius * frac)
                for a in angles
            ]
            pygame.draw.polygon(surface, config.COLOR_PANEL_BORDER, points, 1)

        # Axis lines + labels
        for a, label in zip(angles, RADAR_LABELS):
            end = (cx + math.cos(a) * radius, cy + math.sin(a) * radius)
            pygame.draw.line(surface, config.COLOR_PANEL_BORDER, (cx, cy), end, 1)
            lx = cx + math.cos(a) * (radius + 30)
            ly = cy + math.sin(a) * (radius + 30)
            draw_text(surface, label, (lx, ly), size=13, color=config.COLOR_TEXT_DIM,
                      align="center")

        # One polygon per variant
        for (variant, dims), color in zip(self.radar.items(), VARIANT_COLORS):
            points = [
                (cx + math.cos(a) * radius * dims[d], cy + math.sin(a) * radius * dims[d])
                for a, d in zip(angles, RADAR_DIMS)
            ]
            poly_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(poly_surf, (*color, 55), points)
            pygame.draw.polygon(poly_surf, color, points, 2)
            surface.blit(poly_surf, (0, 0))

        # Legend
        legend_x = cx + radius + 90
        legend_y = cy - radius
        draw_text(surface, "Legend", (legend_x, legend_y - 26), size=14,
                  color=config.COLOR_ACCENT, bold=True)
        for (variant, _), color in zip(self.radar.items(), VARIANT_COLORS):
            pygame.draw.rect(surface, color, (legend_x, legend_y, 14, 14), border_radius=3)
            draw_text(surface, variant, (legend_x + 22, legend_y - 2), size=13,
                      color=config.COLOR_TEXT)
            legend_y += 24


def _wrap_text(text, width_chars):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width_chars:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines
