"""
statistics_engine.py
Pure-Python analytics: no Pygame, no numpy/scipy. Everything here is
importable and testable in isolation (see test_statistics_engine.py).

Responsibilities:
  - Drain an algorithm generator to completion and compute per-run metrics.
  - Run the full 7-variant comparison (BFS, DFS, UCS, Greedy, A*@0/50/100)
    on one maze.
  - Descriptive statistics from first principles: mean, median, stdev,
    IQR, skewness.
  - Manual Pearson correlation + OLS trend line.
  - Min-max normalized "personality" profile for the radar chart.
"""

import math
from typing import List, Dict, Any

import config
from algorithms import bfs, dfs, ucs, greedy, astar

VARIANTS = ["BFS", "DFS", "UCS / Dijkstra", "Greedy Best-First",
            "A* (greed=0)", "A* (greed=50)", "A* (greed=100)"]


# --------------------------------------------------------------------------
# Running algorithms to completion
# --------------------------------------------------------------------------
def run_to_completion(generator):
    """Drain a search generator, returning its final ('done': True) state."""
    final_state = None
    for state in generator:
        final_state = state
        if state.get("done"):
            break
    return final_state


def run_variant(grid, variant_name):
    """
    Run one named variant (one of VARIANTS) on `grid` to completion and
    return a metrics dict. This is the single entry point both the
    Analytics dashboard and the test scripts use.
    """
    start, end = grid.start, grid.end

    if variant_name == "BFS":
        gen, greed = bfs(grid, start, end), 0
    elif variant_name == "DFS":
        gen, greed = dfs(grid, start, end), 0
    elif variant_name == "UCS / Dijkstra":
        gen, greed = ucs(grid, start, end), 0
    elif variant_name == "Greedy Best-First":
        gen, greed = greedy(grid, start, end), 0
    elif variant_name.startswith("A*"):
        greed = int(variant_name.split("=")[1].rstrip(")"))
        gen = astar(grid, start, end, greed=greed)
    else:
        raise ValueError(f"Unknown variant: {variant_name}")

    final = run_to_completion(gen)
    return _build_metrics(grid, variant_name, final, greed)


def _build_metrics(grid, variant_name, final_state, greed) -> Dict[str, Any]:
    path = final_state.get("path") or []
    nodes_explored = final_state.get("nodes_explored", 0)

    path_cost = grid.path_cost(path, greed=greed)
    terrain_penalty = grid.terrain_penalty(path)
    coins = grid.coins_on_path(path)
    coins_collected = len(coins)
    score = coins_collected * config.COIN_VALUE - path_cost
    path_length = max(0, len(path) - 1)  # steps, not cells
    efficiency = (score / nodes_explored) if nodes_explored else 0.0

    return {
        "variant": variant_name,
        "path": path,
        "nodes_explored": nodes_explored,
        "path_length": path_length,
        "path_cost": round(path_cost, 2),
        "terrain_penalty": round(terrain_penalty, 2),
        "coins_collected": coins_collected,
        "score": round(score, 2),
        "efficiency": round(efficiency, 4),
        "greed": greed,
    }


def run_all_variants(grid) -> List[Dict[str, Any]]:
    """Run all 7 comparison variants on the same maze."""
    return [run_variant(grid, name) for name in VARIANTS]


# --------------------------------------------------------------------------
# Descriptive statistics (first principles, no numpy/scipy)
# --------------------------------------------------------------------------
def mean(values: List[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def median(values: List[float]) -> float:
    values = sorted(values)
    n = len(values)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2 == 1:
        return float(values[mid])
    return (values[mid - 1] + values[mid]) / 2.0


def variance(values: List[float]) -> float:
    """Population variance (divides by n), matching the fixed set of runs
    being analyzed rather than treating them as a sample of a larger pop."""
    values = list(values)
    n = len(values)
    if n == 0:
        return 0.0
    m = mean(values)
    return sum((v - m) ** 2 for v in values) / n


def stdev(values: List[float]) -> float:
    return math.sqrt(variance(values))


def quartile(values: List[float], q: float) -> float:
    """Linear-interpolation quartile (q in [0, 1])."""
    values = sorted(values)
    n = len(values)
    if n == 0:
        return 0.0
    if n == 1:
        return float(values[0])
    pos = q * (n - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(values[lo])
    frac = pos - lo
    return values[lo] + (values[hi] - values[lo]) * frac


def iqr(values: List[float]) -> float:
    return quartile(values, 0.75) - quartile(values, 0.25)


def skewness(values: List[float]) -> float:
    """
    Sample (Fisher-Pearson adjusted) skewness. Returns 0 for fewer than 3
    points, since skewness is not meaningfully defined there.
    """
    values = list(values)
    n = len(values)
    if n < 3:
        return 0.0
    m = mean(values)
    s = stdev(values)
    if s == 0:
        return 0.0
    third_moment = sum((v - m) ** 3 for v in values) / n
    g1 = third_moment / (s ** 3)
    # Adjusted Fisher-Pearson standardized moment coefficient
    correction = math.sqrt(n * (n - 1)) / (n - 2)
    return correction * g1


def descriptive_stats(values: List[float]) -> Dict[str, float]:
    values = list(values)
    return {
        "mean": round(mean(values), 4),
        "median": round(median(values), 4),
        "stdev": round(stdev(values), 4),
        "iqr": round(iqr(values), 4),
        "skewness": round(skewness(values), 4),
        "min": round(min(values), 4) if values else 0.0,
        "max": round(max(values), 4) if values else 0.0,
    }


# --------------------------------------------------------------------------
# Pearson correlation + OLS trend line (manual)
# --------------------------------------------------------------------------
def pearson_correlation(xs: List[float], ys: List[float]) -> float:
    """
    Manual Pearson correlation coefficient r in [-1, 1]. Returns 0.0 for
    degenerate input (fewer than 2 points, or zero variance in either
    series) rather than raising, since a dashboard should degrade
    gracefully rather than crash on a small/uniform sample.
    """
    n = len(xs)
    if n < 2 or n != len(ys):
        return 0.0
    mx, my = mean(xs), mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    var_x = sum((x - mx) ** 2 for x in xs)
    var_y = sum((y - my) ** 2 for y in ys)
    denom = math.sqrt(var_x * var_y)
    if denom == 0:
        return 0.0
    return cov / denom


def ols_trend_line(xs: List[float], ys: List[float]):
    """
    Manual ordinary-least-squares fit y = slope * x + intercept.
    Returns (slope, intercept). Falls back to a flat line at the mean of
    ys if x has zero variance (undefined slope).
    """
    n = len(xs)
    if n < 2:
        return 0.0, (ys[0] if ys else 0.0)
    mx, my = mean(xs), mean(ys)
    var_x = sum((x - mx) ** 2 for x in xs)
    if var_x == 0:
        return 0.0, my
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = cov / var_x
    intercept = my - slope * mx
    return slope, intercept


def correlation_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Nodes Explored vs. Score across the 7 variants: the correlation
    coefficient, a trend line, and a plain-language interpretation.
    Correlation, not causation -- the summary explicitly says so.
    """
    xs = [r["nodes_explored"] for r in results]
    ys = [r["score"] for r in results]
    r = pearson_correlation(xs, ys)
    slope, intercept = ols_trend_line(xs, ys)

    magnitude = abs(r)
    if magnitude < 0.2:
        strength = "negligible"
    elif magnitude < 0.4:
        strength = "weak"
    elif magnitude < 0.6:
        strength = "moderate"
    elif magnitude < 0.8:
        strength = "strong"
    else:
        strength = "very strong"
    direction = "positive" if r > 0 else "negative" if r < 0 else "no"

    interpretation = (
        f"r = {r:.3f} indicates a {strength} {direction} linear relationship "
        f"between nodes explored and final score across these variants. "
        f"This describes an association observed on this one maze, not a "
        f"causal claim -- it does not prove that exploring more nodes causes "
        f"a better or worse score."
    )

    return {
        "r": round(r, 4),
        "slope": round(slope, 4),
        "intercept": round(intercept, 4),
        "xs": xs,
        "ys": ys,
        "labels": [res["variant"] for res in results],
        "interpretation": interpretation,
    }


# --------------------------------------------------------------------------
# Radar / personality profile
# --------------------------------------------------------------------------
def _min_max_normalize(values: List[float]) -> List[float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5 for _ in values]  # all identical -> mid-scale, not 0
    return [(v - lo) / (hi - lo) for v in values]


def radar_profiles(grid, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Three normalized dimensions per variant, built from each path's actual
    terrain-frequency distribution, min-max rescaled ACROSS variants so
    real differences are visible instead of clustering near 1.0:

      - Cheap Terrain: fraction of the path spent on Plain cells (higher
        = the algorithm avoided costly terrain).
      - Coin Ratio: coins collected relative to path length (higher =
        more coin-efficient detours).
      - Path Efficiency: score achieved per node explored, i.e. how much
        the search "earned" for the work it did.
    """
    cheap_terrain_raw, coin_ratio_raw, path_efficiency_raw = [], [], []

    for r in results:
        path = r["path"]
        if len(path) > 1:
            steps = path[1:]
            plain_steps = sum(
                1 for cell in steps if grid.terrain_at(cell) == config.PLAIN
            )
            cheap_terrain_raw.append(plain_steps / len(steps))
            coin_ratio_raw.append(r["coins_collected"] / len(steps))
        else:
            cheap_terrain_raw.append(0.0)
            coin_ratio_raw.append(0.0)
        path_efficiency_raw.append(r["efficiency"])

    cheap_terrain_norm = _min_max_normalize(cheap_terrain_raw)
    coin_ratio_norm = _min_max_normalize(coin_ratio_raw)
    path_efficiency_norm = _min_max_normalize(path_efficiency_raw)

    profiles = {}
    for i, r in enumerate(results):
        profiles[r["variant"]] = {
            "cheap_terrain": round(cheap_terrain_norm[i], 4),
            "coin_ratio": round(coin_ratio_norm[i], 4),
            "path_efficiency": round(path_efficiency_norm[i], 4),
        }
    return profiles


# --------------------------------------------------------------------------
# Verdict badges for the summary table
# --------------------------------------------------------------------------
def compute_verdicts(results: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Map variant name -> list of badge strings earned (Fastest, Cheapest
    Path, Most Coins, Best Score, Most Efficient). Ties are all awarded
    the badge rather than arbitrarily picking one.
    """
    verdicts = {r["variant"]: [] for r in results}

    def award(key, badge, minimize=True):
        target = (min if minimize else max)(r[key] for r in results)
        for r in results:
            if r[key] == target:
                verdicts[r["variant"]].append(badge)

    award("nodes_explored", "Fastest", minimize=True)
    award("path_cost", "Cheapest Path", minimize=True)
    award("coins_collected", "Most Coins", minimize=False)
    award("score", "Best Score", minimize=False)
    award("efficiency", "Most Efficient", minimize=False)

    return verdicts
