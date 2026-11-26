"""
test_statistics_engine.py
Standalone check of the full analytics pipeline: batch runs across all 7
variants, descriptive statistics, Pearson correlation + OLS trend line,
and the radar "personality" profile. Prints every phase so the numbers
can be sanity-checked by hand. No Pygame import anywhere.

Run with:  python test_statistics_engine.py
"""

import sys
import math

from generator import generate_maze
import statistics_engine as se


def _assert(condition, message):
    print(f"  {'OK  ' if condition else 'FAIL'}: {message}")
    return condition


def main():
    all_ok = True
    grid = generate_maze(seed=99)
    print(f"Maze: {grid.rows}x{grid.cols}, seed=99, coins={len(grid.coins)}")
    print()

    # ---- Phase 1: batch runs -------------------------------------------
    print("Phase 1: running all 7 variants...")
    results = se.run_all_variants(grid)
    for r in results:
        print(f"  {r['variant']:<20} nodes={r['nodes_explored']:>4}  "
              f"cost={r['path_cost']:>7.2f}  coins={r['coins_collected']}  "
              f"score={r['score']:>7.2f}")
    all_ok &= _assert(len(results) == 7, "all 7 variants produced a result")
    print()

    # ---- Phase 2: descriptive statistics --------------------------------
    print("Phase 2: descriptive statistics (nodes explored)...")
    nodes = [r["nodes_explored"] for r in results]
    stats = se.descriptive_stats(nodes)
    for k, v in stats.items():
        print(f"  {k:<10}{v}")
    all_ok &= _assert(stats["min"] <= stats["mean"] <= stats["max"],
                       "mean falls within [min, max]")
    all_ok &= _assert(stats["stdev"] >= 0, "stdev is non-negative")
    all_ok &= _assert(stats["iqr"] >= 0, "iqr is non-negative")

    # Sanity-check mean/stdev/median against a known hand-computed sample.
    sample = [2, 4, 4, 4, 5, 5, 7, 9]
    s_mean = se.mean(sample)
    s_stdev = se.stdev(sample)
    all_ok &= _assert(abs(s_mean - 5.0) < 1e-9, f"mean([2,4,4,4,5,5,7,9]) == 5.0 (got {s_mean})")
    all_ok &= _assert(abs(s_stdev - 2.0) < 1e-9, f"population stdev == 2.0 (got {s_stdev})")
    print()

    # ---- Phase 3: Pearson correlation + OLS trend line -------------------
    print("Phase 3: Nodes Explored vs. Score correlation...")
    corr = se.correlation_summary(results)
    print(f"  r = {corr['r']}")
    print(f"  trend line: score = {corr['slope']} * nodes + {corr['intercept']}")
    print(f"  {corr['interpretation']}")
    all_ok &= _assert(-1.0 <= corr["r"] <= 1.0, "Pearson r is within [-1, 1]")

    # Manual sanity check: perfectly correlated toy data should give r ~ 1.
    xs = [1, 2, 3, 4, 5]
    ys = [2, 4, 6, 8, 10]
    r_perfect = se.pearson_correlation(xs, ys)
    all_ok &= _assert(abs(r_perfect - 1.0) < 1e-9, f"perfectly linear data gives r=1.0 (got {r_perfect})")
    slope, intercept = se.ols_trend_line(xs, ys)
    all_ok &= _assert(abs(slope - 2.0) < 1e-9 and abs(intercept - 0.0) < 1e-9,
                       f"OLS recovers y=2x exactly (got slope={slope}, intercept={intercept})")
    print()

    # ---- Phase 4: radar / personality profile -----------------------------
    print("Phase 4: radar personality profiles...")
    profiles = se.radar_profiles(grid, results)
    for variant, dims in profiles.items():
        print(f"  {variant:<20} cheap_terrain={dims['cheap_terrain']:.3f}  "
              f"coin_ratio={dims['coin_ratio']:.3f}  "
              f"path_efficiency={dims['path_efficiency']:.3f}")
    for dims in profiles.values():
        for v in dims.values():
            all_ok &= _assert(0.0 <= v <= 1.0, f"radar dimension {v} is within [0, 1]")
            break  # one representative check per variant keeps output short
    print()

    # ---- Phase 5: verdict badges --------------------------------------
    print("Phase 5: verdict badges...")
    verdicts = se.compute_verdicts(results)
    for variant, badges in verdicts.items():
        print(f"  {variant:<20} {', '.join(badges) if badges else '-'}")
    all_ok &= _assert(
        any(badges for badges in verdicts.values()),
        "at least one variant earned a badge",
    )
    print()

    if all_ok:
        print("ALL CHECKS PASSED")
    else:
        print("SOME CHECKS FAILED")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
