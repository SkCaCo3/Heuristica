"""
algorithms/ucs.py
Uniform Cost Search, labeled "UCS / Dijkstra" throughout the app since the
two are the same algorithm on a non-negative-weight graph: a priority
queue ordered strictly by accumulated real cost g(n), with no heuristic.
Guarantees the minimum-cost path.
"""

from .common import PriorityQueue, reconstruct_path, make_step


def ucs(grid, start, end):
    frontier = PriorityQueue()
    frontier.push(0, start)
    came_from = {start: None}
    best_cost = {start: 0}
    visited = set()
    nodes_explored = 0

    while frontier:
        cost_so_far, current = frontier.pop()

        if current in visited:
            continue
        visited.add(current)
        nodes_explored += 1

        yield make_step(
            visited, frontier.items(), current, None, False, nodes_explored,
            extra={"cost_so_far": cost_so_far},
        )

        if current == end:
            path = reconstruct_path(came_from, current)
            yield make_step(
                visited, [], current, path, True, nodes_explored,
                extra={"cost_so_far": cost_so_far},
            )
            return

        for neighbor in grid.neighbors(current):
            new_cost = cost_so_far + grid.base_cost(neighbor)
            if neighbor not in best_cost or new_cost < best_cost[neighbor]:
                best_cost[neighbor] = new_cost
                came_from[neighbor] = current
                frontier.push(new_cost, neighbor)

    yield make_step(visited, [], None, [], True, nodes_explored)
