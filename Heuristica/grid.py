"""
grid.py
The Grid class is the single source of truth for maze layout: terrain,
walls, start/end, and coins. It knows nothing about Pygame or algorithms;
it only answers questions like "what are this cell's costs and neighbors".
"""

from collections import deque
import config


class Grid:
    """
    A grid of (row, col) cells. `terrain[r][c]` holds one of the terrain
    constants from config (WALL, PLAIN, MUD, WATER, START, END).

    Cells are connected by 4-directional adjacency. A cell being WALL makes
    it impassable; all other terrain types are passable at their listed
    cost. `coins` is a set of (row, col) cells that currently hold a coin.
    """

    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.terrain = [[config.WALL for _ in range(cols)] for _ in range(rows)]
        self.start = None
        self.end = None
        self.coins = set()

    # ------------------------------------------------------------------
    # Basic queries
    # ------------------------------------------------------------------
    def in_bounds(self, cell):
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_wall(self, cell):
        r, c = cell
        return self.terrain[r][c] == config.WALL

    def is_passable(self, cell):
        return self.in_bounds(cell) and not self.is_wall(cell)

    def terrain_at(self, cell):
        r, c = cell
        return self.terrain[r][c]

    def set_terrain(self, cell, terrain_type):
        r, c = cell
        self.terrain[r][c] = terrain_type

    def neighbors(self, cell):
        """4-directional passable neighbors of `cell`."""
        r, c = cell
        candidates = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
        return [n for n in candidates if self.is_passable(n)]

    def all_open_cells(self):
        return [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if self.terrain[r][c] != config.WALL
        ]

    # ------------------------------------------------------------------
    # Costs
    # ------------------------------------------------------------------
    def base_cost(self, cell):
        """Terrain cost of entering `cell`, ignoring coins/greed."""
        t = self.terrain_at(cell)
        cost = config.TERRAIN_COST[t]
        if cost == float("inf"):
            return cost
        return max(cost, config.MIN_TERRAIN_COST) if t not in (config.START, config.END) else cost

    def effective_cost(self, cell, greed=0):
        """
        Cost of entering `cell`, accounting for the A* greed parameter.
        At greed=0 this equals base_cost. As greed rises toward 100, cells
        holding a coin become progressively cheaper (never below 0),
        making it worthwhile for A* to detour onto costly terrain to
        collect them. Only affects cells that currently have a coin.
        """
        base = self.base_cost(cell)
        if base == float("inf"):
            return base
        if cell in self.coins and greed > 0:
            discount = 1 - config.GREED_COIN_DISCOUNT * (greed / 100.0)
            discount = max(0.0, discount)
            return base * discount
        return base

    # ------------------------------------------------------------------
    # Connectivity
    # ------------------------------------------------------------------
    def is_connected(self, a, b):
        """BFS reachability check between two passable cells."""
        if not self.is_passable(a) or not self.is_passable(b):
            return False
        if a == b:
            return True
        visited = {a}
        queue = deque([a])
        while queue:
            cur = queue.popleft()
            if cur == b:
                return True
            for n in self.neighbors(cur):
                if n not in visited:
                    visited.add(n)
                    queue.append(n)
        return b in visited

    def reachable_set(self, source):
        """All cells reachable from `source` (BFS flood fill)."""
        if not self.is_passable(source):
            return set()
        visited = {source}
        queue = deque([source])
        while queue:
            cur = queue.popleft()
            for n in self.neighbors(cur):
                if n not in visited:
                    visited.add(n)
                    queue.append(n)
        return visited

    # ------------------------------------------------------------------
    # Coins
    # ------------------------------------------------------------------
    def add_coin(self, cell):
        self.coins.add(cell)

    def has_coin(self, cell):
        return cell in self.coins

    def coins_on_path(self, path):
        """Coins collected if the given path (list of cells) is walked."""
        return [cell for cell in path if cell in self.coins]

    # ------------------------------------------------------------------
    # Path cost
    # ------------------------------------------------------------------
    def path_cost(self, path, greed=0):
        """
        Real terrain cost of a path (list of cells including start),
        summing the cost of every cell entered (i.e. all cells after the
        first). This mirrors what the algorithms actually optimize.
        """
        if not path or len(path) < 2:
            return 0
        total = 0.0
        for cell in path[1:]:
            total += self.effective_cost(cell, greed=greed)
        return total

    def terrain_penalty(self, path):
        """
        Extra cost paid above the cheapest-possible (all-Plain) path of the
        same length -- i.e. how much the path spent on Mud/Water specifically.
        """
        if not path or len(path) < 2:
            return 0
        penalty = 0.0
        for cell in path[1:]:
            base = self.base_cost(cell)
            if base == float("inf"):
                continue
            penalty += max(0.0, base - config.MIN_TERRAIN_COST)
        return penalty
