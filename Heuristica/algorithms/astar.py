"""
algorithms/astar.py
A* Search: f(n) = g(n) + h(n), with Manhattan distance as h(n). Because the
minimum traversable terrain cost is always >= 1 (config.MIN_TERRAIN_COST),
Manhattan distance never overestimates the true remaining cost, so the
heuristic stays admissible and A* remains guaranteed-optimal at greed=0.

The `greed` parameter (0-100) is A*'s second dimension. It does NOT touch
the heuristic h(n) -- nudging only the priority of exploring toward coins
would not actually change which path gets chosen, since A* still minimizes
g + h. Instead greed changes the *real* cost g(n) of entering a coin cell
via grid.effective_cost(), which is what actually redirects the final path.
"""

from .common import PriorityQueue, reconstruct_path, manhattan, make_step


def astar(grid, start, end, greed=0):
    frontier = PriorityQueue()
    frontier.push(manhattan(start, end), start)
    came_from = {start: None}
    best_g = {start: 0}
    visited = set()
    nodes_explored = 0

    while frontier:
        _, current = frontier.pop()

        if current in visited:
            continue
        visited.add(current)
        nodes_explored += 1
        g_current = best_g[current]

        yield make_step(
            visited, frontier.items(), current, None, False, nodes_explored,
            extra={"cost_so_far": g_current, "greed": greed},
        )

        if current == end:
            path = reconstruct_path(came_from, current)
            yield make_step(
                visited, [], current, path, True, nodes_explored,
                extra={"cost_so_far": g_current, "greed": greed},
            )
            return

        for neighbor in grid.neighbors(current):
            step_cost = grid.effective_cost(neighbor, greed=greed)
            new_g = g_current + step_cost
            if neighbor not in best_g or new_g < best_g[neighbor]:
                best_g[neighbor] = new_g
                came_from[neighbor] = current
                f_score = new_g + manhattan(neighbor, end)
                frontier.push(f_score, neighbor)

    yield make_step(visited, [], None, [], True, nodes_explored)
