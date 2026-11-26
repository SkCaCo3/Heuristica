"""
algorithms/bfs.py
Breadth-First Search. Uses a plain FIFO queue, ignores terrain cost
entirely, and therefore minimizes the number of *steps* rather than the
total cost -- which is exactly why it will happily walk straight through
Mud or Water if that's the shortest route in cell-count.
"""

from collections import deque
from .common import reconstruct_path, make_step


def bfs(grid, start, end):
    frontier = deque([start])
    queued = {start}
    came_from = {start: None}
    visited = set()
    nodes_explored = 0

    while frontier:
        current = frontier.popleft()
        visited.add(current)
        nodes_explored += 1

        yield make_step(visited, frontier, current, None, False, nodes_explored)

        if current == end:
            path = reconstruct_path(came_from, current)
            yield make_step(visited, [], current, path, True, nodes_explored)
            return

        for neighbor in grid.neighbors(current):
            if neighbor not in queued:
                queued.add(neighbor)
                came_from[neighbor] = current
                frontier.append(neighbor)

    # Exhausted the frontier without reaching `end` (should not happen on a
    # connected maze, but handled defensively).
    yield make_step(visited, [], None, [], True, nodes_explored)
