"""
algorithms/dfs.py
Depth-First Search. Uses a LIFO stack, ignores terrain cost, and ignores
any heuristic -- it just plunges as deep as possible before backtracking.
Neither optimal in steps nor in cost.
"""

from .common import reconstruct_path, make_step


def dfs(grid, start, end):
    stack = [start]
    on_stack = {start}
    came_from = {start: None}
    visited = set()
    nodes_explored = 0

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        nodes_explored += 1

        yield make_step(visited, stack, current, None, False, nodes_explored)

        if current == end:
            path = reconstruct_path(came_from, current)
            yield make_step(visited, [], current, path, True, nodes_explored)
            return

        for neighbor in grid.neighbors(current):
            if neighbor not in visited:
                if neighbor not in came_from:
                    came_from[neighbor] = current
                stack.append(neighbor)

    yield make_step(visited, [], None, [], True, nodes_explored)
