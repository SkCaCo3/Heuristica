"""
generator.py
Procedural maze generation:
  1. Recursive backtracking carves a perfect maze (spanning tree - no loops).
  2. ~18% of internal walls are knocked out to create loops/alternate routes.
  3. Start/End are placed at opposite corners.
  4. Connectivity is verified (and repaired if a bad wall removal somehow
     breaks it, though carving a wall can only ever add connectivity).
  5. Mud/Water are distributed across open cells.
  6. Coins are clustered onto costly terrain via flood fill from random
     anchors, without ever touching Start/End.
"""

import random
import sys
from collections import deque

import config
from grid import Grid

# Recursive backtracking recurses roughly once per carved cell; guard
# against Python's default 1000-frame limit on larger grids.
sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))


def generate_maze(rows=config.GRID_ROWS, cols=config.GRID_COLS, seed=None):
    """
    Build and return a fully populated Grid: carved maze, start/end,
    terrain, and coins. `seed` makes the layout reproducible; omit it
    (or pass None) for a fresh random maze every call.
    """
    rng = random.Random(seed)

    grid = _carve_perfect_maze(rows, cols, rng)
    _add_loops(grid, rng)
    _place_start_end(grid)
    _ensure_connectivity(grid, rng)
    _distribute_terrain(grid, rng)
    _place_coin_clusters(grid, rng)

    return grid


# --------------------------------------------------------------------------
# 1. Recursive backtracking (perfect maze)
# --------------------------------------------------------------------------
def _carve_perfect_maze(rows, cols, rng):
    """
    Carve a perfect maze onto a `rows` x `cols` grid using recursive
    backtracking on a logical "half-size" cell lattice so that walls
    between cells are explicitly represented as WALL cells. This produces
    natural 1-cell-thick walls and open corridors on the full grid.
    """
    grid = Grid(rows, cols)

    # Every cell starts as WALL; we open up ("carve") PLAIN cells as we go.
    def carve(r, c):
        grid.set_terrain((r, c), config.PLAIN)
        directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]
        rng.shuffle(directions)
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid.is_wall((nr, nc)):
                # carve the wall between (r, c) and (nr, nc)
                grid.set_terrain((r + dr // 2, c + dc // 2), config.PLAIN)
                carve(nr, nc)

    carve(0, 0)
    return grid


def _add_loops(grid, rng):
    """Knock out ~LOOP_FRACTION of internal walls to create alternate routes."""
    internal_walls = [
        (r, c)
        for r in range(1, grid.rows - 1)
        for c in range(1, grid.cols - 1)
        if grid.is_wall((r, c))
    ]
    rng.shuffle(internal_walls)
    n_to_remove = int(len(internal_walls) * config.LOOP_FRACTION)

    for cell in internal_walls[:n_to_remove]:
        r, c = cell
        # Only remove a wall if it actually separates two open regions on
        # opposite sides (turns it into a useful loop rather than carving
        # into the border or an isolated pocket).
        vertical_open = grid.is_passable((r - 1, c)) and grid.is_passable((r + 1, c))
        horizontal_open = grid.is_passable((r, c - 1)) and grid.is_passable((r, c + 1))
        if vertical_open or horizontal_open:
            grid.set_terrain(cell, config.PLAIN)


# --------------------------------------------------------------------------
# 2. Start / End placement
# --------------------------------------------------------------------------
def _place_start_end(grid):
    start = _nearest_open_cell(grid, (0, 0))
    end = _nearest_open_cell(grid, (grid.rows - 1, grid.cols - 1))
    grid.set_terrain(start, config.START)
    grid.set_terrain(end, config.END)
    grid.start = start
    grid.end = end


def _nearest_open_cell(grid, target):
    if grid.is_passable(target):
        return target
    visited = {target}
    queue = deque([target])
    while queue:
        r, c = queue.popleft()
        for nr, nc in [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]:
            if 0 <= nr < grid.rows and 0 <= nc < grid.cols and (nr, nc) not in visited:
                visited.add((nr, nc))
                if grid.is_passable((nr, nc)):
                    return (nr, nc)
                queue.append((nr, nc))
    # Should not happen for a maze produced by _carve_perfect_maze, but
    # fail safe rather than crash.
    return target


# --------------------------------------------------------------------------
# 3. Connectivity guarantee
# --------------------------------------------------------------------------
def _ensure_connectivity(grid, rng):
    """
    Recursive backtracking already guarantees a fully connected spanning
    tree, and removing walls can only add edges, so Start and End should
    already be connected. This is a defensive check + auto-repair in case
    of future changes to the carving/loop logic.
    """
    if grid.is_connected(grid.start, grid.end):
        return

    reachable = grid.reachable_set(grid.start)
    unreachable = set(grid.all_open_cells()) - reachable
    # Carve a corridor from the nearest unreachable open cell back into the
    # reachable region, repeating until Start and End are connected.
    guard = 0
    while not grid.is_connected(grid.start, grid.end) and guard < grid.rows * grid.cols:
        guard += 1
        target = grid.end if grid.end not in reachable else next(iter(unreachable), None)
        if target is None:
            break
        _carve_corridor_towards(grid, target, reachable, rng)
        reachable = grid.reachable_set(grid.start)
        unreachable = set(grid.all_open_cells()) - reachable


def _carve_corridor_towards(grid, target, reachable, rng):
    """Greedily knock down walls in a straight line from `target` toward
    the nearest reachable cell, guaranteeing progress each call."""
    r, c = target
    reachable_list = list(reachable)
    if not reachable_list:
        return
    goal = min(reachable_list, key=lambda cell: abs(cell[0] - r) + abs(cell[1] - c))
    gr, gc = goal
    cr, cc = r, c
    steps = 0
    while (cr, cc) != (gr, gc) and steps < grid.rows + grid.cols:
        steps += 1
        if cr != gr:
            cr += 1 if gr > cr else -1
        elif cc != gc:
            cc += 1 if gc > cc else -1
        if grid.is_wall((cr, cc)):
            grid.set_terrain((cr, cc), config.PLAIN)


# --------------------------------------------------------------------------
# 4. Terrain distribution
# --------------------------------------------------------------------------
def _distribute_terrain(grid, rng):
    open_cells = [
        cell for cell in grid.all_open_cells()
        if grid.terrain_at(cell) == config.PLAIN
    ]
    rng.shuffle(open_cells)

    n_mud = int(len(open_cells) * config.MUD_FRACTION)
    n_water = int(len(open_cells) * config.WATER_FRACTION)

    for cell in open_cells[:n_mud]:
        grid.set_terrain(cell, config.MUD)
    for cell in open_cells[n_mud:n_mud + n_water]:
        grid.set_terrain(cell, config.WATER)

    # Terrain never blocks movement, so connectivity is unaffected; no
    # re-verification is necessary here.


# --------------------------------------------------------------------------
# 5. Coin clustering
# --------------------------------------------------------------------------
def _place_coin_clusters(grid, rng):
    costly_cells = [
        cell for cell in grid.all_open_cells()
        if grid.terrain_at(cell) in (config.MUD, config.WATER)
    ]
    if not costly_cells:
        return
    rng.shuffle(costly_cells)

    placed = 0
    anchors_tried = 0
    for anchor in costly_cells:
        if placed >= config.COIN_CLUSTER_COUNT:
            break
        anchors_tried += 1
        cluster = _flood_fill_cluster(grid, anchor, config.COIN_CLUSTER_SIZE, rng)
        for cell in cluster:
            grid.add_coin(cell)
        if cluster:
            placed += 1
        if anchors_tried > len(costly_cells):
            break


def _flood_fill_cluster(grid, anchor, target_size, rng):
    """
    Flood-fill outward from `anchor`, preferring costly terrain, to build a
    tight visible cluster of coin cells. Never includes Start or End.
    """
    if grid.terrain_at(anchor) in (config.START, config.END):
        return []

    cluster = []
    visited = {anchor}
    frontier = deque([anchor])

    while frontier and len(cluster) < target_size:
        cell = frontier.popleft()
        terrain = grid.terrain_at(cell)
        if terrain not in (config.START, config.END, config.WALL):
            cluster.append(cell)

        neighbors = grid.neighbors(cell)
        rng.shuffle(neighbors)
        # Prefer costly neighbors first so clusters hug Mud/Water.
        neighbors.sort(
            key=lambda n: grid.base_cost(n) if grid.base_cost(n) != float("inf") else -1,
            reverse=True,
        )
        for n in neighbors:
            if n not in visited:
                visited.add(n)
                frontier.append(n)

    return cluster
