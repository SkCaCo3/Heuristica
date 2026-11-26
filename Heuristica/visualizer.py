"""
visualizer.py
The Play screen: owns the maze, the sidebar controls, and the currently
running algorithm generator. Every algorithm is a generator, so animating
it is just calling next() a controlled number of times per frame -- pause,
resume, and speed control fall out of that almost for free.
"""

import pygame

import config
import fonts
import renderer
from renderer import Button, Slider, draw_text, draw_panel
from grid import Grid  # noqa: F401  (type hint clarity)
from generator import generate_maze
from algorithms import ALGORITHMS, USES_GREED
import statistics_engine as se

SPEED_STEPS_PER_SEC = {1: 12, 2: 30, 5: 90}
SPEED_LABELS = [1, 2, 5, "Instant"]


class Visualizer:
    """Encapsulates the Play screen. `run(screen, clock)` blocks until the
    user asks to go back to the Menu or open Analytics, returning that
    target as a string."""

    def __init__(self):
        self.grid = generate_maze()
        self.algo_name = "A*"
        self.generator = None
        self.state = None          # last yielded step dict
        self.running_algo = False
        self.paused = False
        self.speed_index = 0       # index into SPEED_LABELS
        self.step_accumulator = 0.0
        self.collected_coins = set()

        self._build_layout()

    # ------------------------------------------------------------------
    def _build_layout(self):
        sidebar_x = config.GRID_PIXEL_WIDTH + 16
        w = config.SIDEBAR_WIDTH - 32
        y = 16

        self.algo_buttons = []
        for name in ALGORITHMS:
            self.algo_buttons.append(Button((sidebar_x, y, w, 34), name, size=15))
            y += 40

        y += 8
        self.greed_slider = Slider((sidebar_x + 4, y + 22, w - 8, 6), value=0)
        y += 46

        btn_w = (w - 8) // 2
        self.btn_solve = Button((sidebar_x, y, w, 36), "Solve", size=16)
        y += 42
        self.btn_pause = Button((sidebar_x, y, btn_w, 34), "Pause", size=14)
        self.btn_speed = Button((sidebar_x + btn_w + 8, y, btn_w, 34), "1x", size=14)
        y += 40
        self.btn_reset = Button((sidebar_x, y, btn_w, 34), "Reset", size=14)
        self.btn_regen = Button((sidebar_x + btn_w + 8, y, btn_w, 34), "New Maze", size=13)
        y += 44

        self.btn_analytics = Button((sidebar_x, y, w, 32), "Analytics", size=14)
        y += 38
        self.btn_tutorial = Button((sidebar_x, y, btn_w, 32), "Help", size=13)
        self.btn_menu = Button((sidebar_x + btn_w + 8, y, btn_w, 32), "Menu", size=13)

        self.telemetry_top = y + 46

    # ------------------------------------------------------------------
    def _start_solve(self):
        self.paused = False
        self.collected_coins = set()
        algo_fn = ALGORITHMS[self.algo_name]
        if self.algo_name in USES_GREED:
            self.generator = algo_fn(self.grid, self.grid.start, self.grid.end,
                                      greed=self.greed_slider.value)
        else:
            self.generator = algo_fn(self.grid, self.grid.start, self.grid.end)
        self.state = None
        self.running_algo = True

    def _reset_visualization(self):
        self.generator = None
        self.state = None
        self.running_algo = False
        self.paused = False
        self.collected_coins = set()

    def _regenerate_maze(self):
        self.grid = generate_maze()
        self._reset_visualization()

    def _step_once(self):
        if self.generator is None:
            return
        try:
            self.state = next(self.generator)
        except StopIteration:
            self.running_algo = False
            return
        if self.state.get("done"):
            self.running_algo = False
            path = self.state.get("path") or []
            self.collected_coins = set(self.grid.coins_on_path(path))

    def _drain_instantly(self):
        while self.running_algo and self.generator is not None:
            self._step_once()

    # ------------------------------------------------------------------
    def handle_event(self, event):
        """Returns 'menu', 'analytics', 'tutorial', or None."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            for i, btn in enumerate(self.algo_buttons):
                if btn.hovered(pos):
                    names = list(ALGORITHMS.keys())
                    self.algo_name = names[i]
                    self._reset_visualization()

            if self.btn_solve.hovered(pos):
                self._start_solve()
            elif self.btn_pause.hovered(pos) and self.running_algo:
                self.paused = not self.paused
            elif self.btn_speed.hovered(pos):
                self.speed_index = (self.speed_index + 1) % len(SPEED_LABELS)
            elif self.btn_reset.hovered(pos):
                self._reset_visualization()
            elif self.btn_regen.hovered(pos):
                self._regenerate_maze()
            elif self.btn_analytics.hovered(pos):
                return "analytics"
            elif self.btn_tutorial.hovered(pos):
                return "tutorial"
            elif self.btn_menu.hovered(pos):
                return "menu"

        if self.algo_name in USES_GREED:
            self.greed_slider.handle_event(event)

        return None

    # ------------------------------------------------------------------
    def update(self, dt):
        if not self.running_algo or self.paused or self.generator is None:
            return

        speed = SPEED_LABELS[self.speed_index]
        if speed == "Instant":
            self._drain_instantly()
            return

        rate = SPEED_STEPS_PER_SEC[speed]
        self.step_accumulator += rate * dt
        while self.step_accumulator >= 1.0 and self.running_algo:
            self._step_once()
            self.step_accumulator -= 1.0

    # ------------------------------------------------------------------
    def draw(self, surface):
        surface.fill(config.COLOR_BG)

        visited = self.state["visited"] if self.state else set()
        frontier = self.state["frontier"] if self.state else set()
        current = self.state.get("current") if self.state else None
        path = self.state.get("path") if self.state else None

        renderer.draw_grid(
            surface, self.grid, origin=(0, 0),
            visited=visited, frontier=frontier, current=current,
            path=path, collected_coins=self.collected_coins,
        )

        self._draw_sidebar(surface)

    def _draw_sidebar(self, surface):
        sidebar_rect = pygame.Rect(config.GRID_PIXEL_WIDTH, 0,
                                    config.SIDEBAR_WIDTH, config.WINDOW_HEIGHT)
        pygame.draw.rect(surface, config.COLOR_SIDEBAR_BG, sidebar_rect)

        mouse_pos = pygame.mouse.get_pos()
        names = list(ALGORITHMS.keys())
        for name, btn in zip(names, self.algo_buttons):
            btn.draw(surface, hovered=btn.hovered(mouse_pos), active=(name == self.algo_name))

        if self.algo_name in USES_GREED:
            self.greed_slider.draw(surface)

        self.btn_solve.draw(surface, hovered=self.btn_solve.hovered(mouse_pos),
                             active=self.running_algo and not self.paused)
        pause_label = "Resume" if self.paused else "Pause"
        self.btn_pause.label = pause_label
        self.btn_pause.draw(surface, hovered=self.btn_pause.hovered(mouse_pos), active=self.paused)
        self.btn_speed.label = f"{SPEED_LABELS[self.speed_index]}x" \
            if SPEED_LABELS[self.speed_index] != "Instant" else "Instant"
        self.btn_speed.draw(surface, hovered=self.btn_speed.hovered(mouse_pos))
        self.btn_reset.draw(surface, hovered=self.btn_reset.hovered(mouse_pos))
        self.btn_regen.draw(surface, hovered=self.btn_regen.hovered(mouse_pos))
        self.btn_analytics.draw(surface, hovered=self.btn_analytics.hovered(mouse_pos))
        self.btn_tutorial.draw(surface, hovered=self.btn_tutorial.hovered(mouse_pos))
        self.btn_menu.draw(surface, hovered=self.btn_menu.hovered(mouse_pos))

        self._draw_telemetry(surface, sidebar_rect)

    def _draw_telemetry(self, surface, sidebar_rect):
        x = sidebar_rect.x + 16
        y = self.telemetry_top
        w = sidebar_rect.width - 32
        panel_h = sidebar_rect.height - y - 16
        panel = pygame.Rect(x - 8, y, w + 16, panel_h)
        draw_panel(surface, panel)

        y += 12
        x += 4
        draw_text(surface, "TELEMETRY", (x, y), size=13, color=config.COLOR_TEXT_DIM,
                  font_fn=fonts.mono, bold=True)
        y += 24

        state = self.state
        path = state.get("path") if state else None
        rows = [("Algorithm", self.algo_name)]
        if state:
            rows.append(("Nodes Explored", str(state.get("nodes_explored", 0))))
            rows.append(("Frontier Size", str(len(state.get("frontier", set())))))
            cur = state.get("current")
            rows.append(("Current Node", f"{cur}" if cur else "-"))
            if "cost_so_far" in state:
                rows.append(("Cost So Far", f"{state['cost_so_far']:.1f}"))
            if self.algo_name in USES_GREED:
                rows.append(("Greed", f"{self.greed_slider.value}%"))

        if path:
            cost = self.grid.path_cost(path, greed=self.greed_slider.value
                                        if self.algo_name in USES_GREED else 0)
            coins = len(self.collected_coins)
            score = coins * config.COIN_VALUE - cost
            rows.append(("Path Length", f"{len(path) - 1} steps"))
            rows.append(("Path Cost", f"{cost:.1f}"))
            rows.append(("Coins Collected", str(coins)))
            rows.append(("Score", f"{score:.1f}"))
        elif not rows or state is None:
            rows.append(("Status", "Press Solve"))

        for label, value in rows:
            draw_text(surface, label, (x, y), size=13, color=config.COLOR_TEXT_DIM,
                      font_fn=fonts.sans)
            draw_text(surface, value, (x, y + 16), size=15, color=config.COLOR_TEXT,
                      font_fn=fonts.mono, bold=True)
            y += 40
