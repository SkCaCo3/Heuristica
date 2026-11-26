"""
algorithms package
Exposes every search algorithm plus a uniform registry the rest of the app
(visualizer, statistics_engine) can use without special-casing each one.
"""

from .bfs import bfs
from .dfs import dfs
from .ucs import ucs
from .greedy import greedy
from .astar import astar

# Human-readable label -> callable(grid, start, end, **kwargs) -> generator.
# BFS/DFS/UCS/Greedy ignore any extra kwargs; only astar consumes `greed`.
ALGORITHMS = {
    "BFS": bfs,
    "DFS": dfs,
    "UCS / Dijkstra": ucs,
    "Greedy Best-First": greedy,
    "A*": astar,
}

USES_GREED = {"A*"}

__all__ = ["bfs", "dfs", "ucs", "greedy", "astar", "ALGORITHMS", "USES_GREED"]
