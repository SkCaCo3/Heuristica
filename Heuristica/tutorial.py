"""
tutorial.py
"How to Play" screen: a scrollable, plain-language walkthrough of what the
maze represents, terrain costs, coins, each algorithm, the greed
parameter, scoring, and what "nodes explored" means. Written for an AI Lab
course audience -- understandable without a textbook.
"""

import pygame

import config
import fonts
from renderer import Button, draw_text, draw_panel

SECTIONS = [
    ("The Maze", [
        "Each cell is one of: Wall (impassable), Plain, Mud, or Water.",
        "Start and End are fixed at opposite corners. Every generated",
        "maze is guaranteed fully connected -- a path always exists.",
    ]),
    ("Terrain Costs", [
        "Plain = 1, Mud = 5, Water = 10. Higher cost means an algorithm",
        "that actually looks at cost will prefer to avoid that cell.",
        "The cost floor is 1, which is what keeps the A* heuristic valid.",
    ]),
    ("Coins", [
        "Coins cluster on costly terrain (Mud/Water), creating a real",
        "risk-vs-reward choice: detouring to grab one costs extra path",
        "cost, but is worth +100 points if the detour pays off.",
    ]),
    ("BFS (Breadth-First Search)", [
        "Explores in a widening ring, one step at a time, ignoring cost.",
        "Finds the path with the FEWEST STEPS -- not the cheapest one.",
        "Will walk straight through Mud/Water if that's fewer steps.",
    ]),
    ("DFS (Depth-First Search)", [
        "Plunges as deep as possible before backtracking. Ignores cost",
        "and ignores any notion of 'closer to the goal'. Not optimal --",
        "just whatever the stack happens to explore first.",
    ]),
    ("UCS / Dijkstra (Uniform Cost Search)", [
        "Always expands the cheapest-so-far cell next. Guarantees the",
        "minimum-COST path (not minimum steps). No knowledge of the",
        "goal's direction -- it explores cost-outward in all directions.",
    ]),
    ("Greedy Best-First Search", [
        "Always expands whichever cell LOOKS closest to the goal (by",
        "straight-line distance), ignoring real cost entirely. Fast, but",
        "easily fooled into charging through expensive terrain.",
    ]),
    ("A* Search", [
        "Combines both: f(n) = g(n) + h(n), real cost so far plus",
        "estimated distance remaining. At greed=0 this is the",
        "mathematically optimal path -- as good as UCS, usually faster.",
    ]),
    ("The Greed Parameter (A* only)", [
        "Greed (0-100%) makes coin cells progressively CHEAPER to enter,",
        "changing the real cost A* optimizes -- not just its priority.",
        "At 0% coins are ignored; at 100% A* actively hunts them.",
    ]),
    ("Scoring", [
        "Score = (Coins Collected x 100) - Path Cost.",
        "A coin in Water costs 10 to reach -- only worth detouring for",
        "if the +100 reward beats the extra cost of getting there.",
    ]),
    ("Nodes Explored", [
        "How many cells the algorithm actually visited before finishing.",
        "More nodes explored means more computational work -- the",
        "Analytics dashboard checks whether that work paid off in score.",
    ]),
]


class Tutorial:
    def __init__(self):
        self.scroll = 0
        self.max_scroll = 0
        self.btn_back = Button((config.WINDOW_WIDTH // 2 - 90,
                                 config.WINDOW_HEIGHT - 56, 180, 40), "Back", size=16)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.btn_back.hovered(event.pos):
                return "menu"
            if event.button == 4:
                self.scroll = max(0, self.scroll - 40)
            elif event.button == 5:
                self.scroll = min(self.max_scroll, self.scroll + 40)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "menu"
        return None

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(config.COLOR_BG)
        draw_text(surface, "How to Play", (config.WINDOW_WIDTH // 2, 24), size=34,
                  color=config.COLOR_ACCENT, font_fn=fonts.mono, bold=True, align="center")

        content_rect = pygame.Rect(60, 80, config.WINDOW_WIDTH - 120,
                                    config.WINDOW_HEIGHT - 160)
        draw_panel(surface, content_rect)

        clip = surface.get_clip()
        surface.set_clip(content_rect.inflate(-8, -8))

        x = content_rect.x + 24
        y = content_rect.y + 16 - self.scroll
        col_w = content_rect.width - 48

        for title, lines in SECTIONS:
            draw_text(surface, title, (x, y), size=18, color=config.COLOR_ACCENT,
                      font_fn=fonts.mono, bold=True)
            y += 26
            for line in lines:
                draw_text(surface, line, (x, y), size=15, color=config.COLOR_TEXT)
                y += 21
            y += 14

        content_height = y + self.scroll - (content_rect.y + 16)
        self.max_scroll = max(0, content_height - content_rect.height + 24)

        surface.set_clip(clip)

        mouse_pos = pygame.mouse.get_pos()
        self.btn_back.draw(surface, hovered=self.btn_back.hovered(mouse_pos))
