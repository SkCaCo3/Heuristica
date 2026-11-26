"""
main.py
App entry point. A small state machine switches between four screens:
Menu, Play (Visualizer), Analytics, and Tutorial. Each screen exposes the
same tiny interface -- handle_event(event), update(dt), draw(surface) --
so this loop never needs to know a screen's internals.
"""

import sys
import pygame

import config
from menu import Menu
from visualizer import Visualizer
from analytics import Analytics
from tutorial import Tutorial

MENU, PLAY, ANALYTICS, TUTORIAL = "menu", "play", "analytics", "tutorial"


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Heuristica — Seeing the Logic")
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.state = MENU
        self.screens = {MENU: Menu(), TUTORIAL: Tutorial()}
        self.visualizer = None   # created lazily, reused across Play visits
        self.analytics = None    # rebuilt each time Analytics is opened

    # ------------------------------------------------------------------
    def _current_screen(self):
        if self.state == PLAY:
            if self.visualizer is None:
                self.visualizer = Visualizer()
            return self.visualizer
        if self.state == ANALYTICS:
            if self.analytics is None:
                grid = self.visualizer.grid if self.visualizer else Visualizer().grid
                self.analytics = Analytics(grid)
            return self.analytics
        return self.screens[self.state]

    def _go_to(self, target):
        if target is None:
            return
        if target == ANALYTICS:
            # Rebuild so it always reflects the maze currently in Play.
            self.analytics = None
        self.state = target

    # ------------------------------------------------------------------
    def run(self):
        while True:
            dt = self.clock.tick(config.FPS) / 1000.0
            screen_obj = self._current_screen()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                result = screen_obj.handle_event(event)
                if result == "quit":
                    pygame.quit()
                    sys.exit(0)
                self._go_to(result)

            screen_obj = self._current_screen()  # state may have just changed
            screen_obj.update(dt)
            screen_obj.draw(self.screen)
            pygame.display.flip()


def main():
    App().run()


if __name__ == "__main__":
    main()
