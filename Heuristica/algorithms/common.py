"""
algorithms/common.py
Small shared utilities used by every search algorithm: path reconstruction,
the Manhattan-distance heuristic, and a tie-breaking priority queue wrapper
so heapq never has to compare (row, col) tuples against each other when
priorities collide.
"""

import heapq
import itertools


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reconstruct_path(came_from, current):
    path = [current]
    while came_from.get(current) is not None:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


class PriorityQueue:
    """
    A min-heap keyed on an explicit priority, with a monotonically
    increasing tie-breaker so items with equal priority never need to be
    compared directly (avoids "cell1 < cell2" errors and keeps insertion
    order stable, which makes runs reproducible for a given seed).
    """

    def __init__(self):
        self._heap = []
        self._counter = itertools.count()

    def push(self, priority, item):
        heapq.heappush(self._heap, (priority, next(self._counter), item))

    def pop(self):
        priority, _, item = heapq.heappop(self._heap)
        return priority, item

    def __len__(self):
        return len(self._heap)

    def __bool__(self):
        return bool(self._heap)

    def items(self):
        """All items currently queued (for frontier visualization)."""
        return [item for _, _, item in self._heap]


def make_step(visited, frontier, current, path, done, nodes_explored, extra=None):
    """Build the standard state dict every algorithm generator yields."""
    state = {
        "visited": set(visited),
        "frontier": set(frontier),
        "current": current,
        "path": path,
        "done": done,
        "nodes_explored": nodes_explored,
    }
    if extra:
        state.update(extra)
    return state
