"""
algorithms/greedy.py
Greedy Best-First Search. Priority queue ordered purely by heuristic
distance h(n) to the goal -- real terrain cost is never consulted. Fast
because it beelines toward the goal, but easily fooled: it will happily
charge through Mud/Water if that cell merely *looks* closer to the exit.
Not optimal.
"""

from .common import PriorityQueue, reconstruct_path, manhattan, make_step


def greedy(grid, start, end):
    frontier = PriorityQueue()
    frontier.push(manhattan(start, end), start)
    came_from = {start: None}
    visited = set()
    nodes_explored = 0

    while frontier:
        _, current = frontier.pop()

        if current in visited:
            continue
        visited.add(current)
        nodes_explored += 1

        yield make_step(visited, frontier.items(), current, None, False, nodes_explored)

        if current == end:
            path = reconstruct_path(came_from, current)
            yield make_step(visited, [], current, path, True, nodes_explored)
            return

        for neighbor in grid.neighbors(current):
            if neighbor not in came_from:
                came_from[neighbor] = current
                frontier.push(manhattan(neighbor, end), neighbor)

    yield make_step(visited, [], None, [], True, nodes_explored)
