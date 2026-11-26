"""
test_algorithms.py
Standalone correctness check for the five search algorithms. Runs all of
them on a freshly generated maze and prints their metrics side by side.
No Pygame import anywhere in this file or anything it calls.

Run with:  python test_algorithms.py
"""

import sys

import config
from generator import generate_maze
from statistics_engine import run_variant, VARIANTS


def _assert(condition, message):
    if not condition:
        print(f"  FAIL: {message}")
        return False
    print(f"  OK:   {message}")
    return True


def main():
    seed = 42
    grid = generate_maze(seed=seed)
    print(f"Generated {grid.rows}x{grid.cols} maze (seed={seed})")
    print(f"Start: {grid.start}   End: {grid.end}")
    print(f"Coins placed: {len(grid.coins)}")
    print(f"Connected: {grid.is_connected(grid.start, grid.end)}")
    print()

    all_ok = True

    print(f"{'Variant':<20}{'Nodes':>8}{'Len':>6}{'Cost':>10}{'Coins':>7}{'Score':>10}{'Eff':>9}")
    print("-" * 72)
    results = {}
    for variant in VARIANTS:
        r = run_variant(grid, variant)
        results[variant] = r
        print(
            f"{r['variant']:<20}{r['nodes_explored']:>8}{r['path_length']:>6}"
            f"{r['path_cost']:>10.2f}{r['coins_collected']:>7}"
            f"{r['score']:>10.2f}{r['efficiency']:>9.4f}"
        )
    print()

    print("Correctness checks:")
    for variant in VARIANTS:
        r = results[variant]
        all_ok &= _assert(len(r["path"]) > 0, f"{variant} found a path")
        all_ok &= _assert(r["path"][0] == grid.start if r["path"] else False,
                           f"{variant} path starts at Start")
        all_ok &= _assert(r["path"][-1] == grid.end if r["path"] else False,
                           f"{variant} path ends at End")

    # UCS and A*(greed=0) must agree on minimum cost -- if they diverge,
    # the heuristic is not admissible (or there's a bug in one of them).
    ucs_cost = results["UCS / Dijkstra"]["path_cost"]
    astar0_cost = results["A* (greed=0)"]["path_cost"]
    all_ok &= _assert(
        abs(ucs_cost - astar0_cost) < 1e-6,
        f"UCS cost ({ucs_cost}) == A*(greed=0) cost ({astar0_cost})",
    )

    # BFS should minimize steps, not necessarily cost -- its path length
    # (in steps) should be <= every other algorithm's path length.
    bfs_len = results["BFS"]["path_length"]
    all_ok &= _assert(
        all(bfs_len <= results[v]["path_length"] for v in VARIANTS),
        f"BFS path length ({bfs_len} steps) is minimal among all variants",
    )

    # UCS should minimize cost -- its path cost should be <= every other
    # non-greedy-coin-hunting variant's cost among those that don't detour
    # for coins (BFS/DFS/Greedy/UCS/A*@0 all optimize distance-to-goal,
    # not coin collection).
    non_coin_hunting = ["BFS", "DFS", "UCS / Dijkstra", "Greedy Best-First", "A* (greed=0)"]
    all_ok &= _assert(
        all(ucs_cost <= results[v]["path_cost"] + 1e-6 for v in non_coin_hunting),
        f"UCS cost ({ucs_cost}) is minimal among non-coin-seeking variants",
    )

    # Higher greed should never decrease coins collected (monotonic
    # coin-seeking behavior as greed rises from 0 to 100).
    g0 = results["A* (greed=0)"]["coins_collected"]
    g50 = results["A* (greed=50)"]["coins_collected"]
    g100 = results["A* (greed=100)"]["coins_collected"]
    all_ok &= _assert(
        g0 <= g50 <= g100,
        f"Coins collected is non-decreasing with greed: {g0} <= {g50} <= {g100}",
    )

    print()
    # Re-run on a couple more seeds so the checks aren't an artifact of one maze.
    for extra_seed in (7, 123):
        g = generate_maze(seed=extra_seed)
        r_ucs = run_variant(g, "UCS / Dijkstra")
        r_astar0 = run_variant(g, "A* (greed=0)")
        all_ok &= _assert(
            abs(r_ucs["path_cost"] - r_astar0["path_cost"]) < 1e-6,
            f"[seed={extra_seed}] UCS cost == A*(greed=0) cost",
        )
        all_ok &= _assert(
            g.is_connected(g.start, g.end),
            f"[seed={extra_seed}] maze is fully connected",
        )

    print()
    if all_ok:
        print("ALL CHECKS PASSED")
    else:
        print("SOME CHECKS FAILED")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
