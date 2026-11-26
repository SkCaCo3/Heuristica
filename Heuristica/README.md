# Heuristica

**Seeing the Logic**, a weighted-terrain maze solver that turns five pathfinding algorithms into something you can _watch think_.

Built for an AI lab course project. Heuristica doesn't just run BFS, DFS, UCS, Greedy Best-First, and A*, it animates their exploration cell by cell, scores them on a coin-collection objective, and backs every claim with descriptive statistics instead of vibes.

> "Complexity is the enemy of understanding. Visualisation is the antidote."

---

## Why this exists

While most pathfinding demos just prove A* is fast, **Heuristica** explores a more useful question: fast at what, and at what cost? 

By running algorithms on the same maze with real terrain costs (Plain, Mud, Water) and risk/reward elements (coins), Heuristica makes theoretical differences visually obvious:

* **BFS** walks straight through mud because it counts steps, not cost.
* **UCS and A\*** naturally detour around costly terrain.
* **A*'s "greed" slider** shows how tweaking a single heuristic weight changes the path entirely—from ignoring coins to aggressively detouring for them. 

Finally, the **Analytics dashboard** answers the crucial question: does exploring more nodes actually produce a better outcome? (Spoiler: no. That's the point.)

---

## What it looks like in action

* **Generate:** Launch the app to instantly build a maze with varied terrain and coin clusters.
* **Visualize:** Pick an algorithm, hit solve, and watch the color-coded frontier expand toward the exit.
* **Compare:** Run BFS to watch it blindly flood-fill 300+ cells through mud. Reset, run A*, and watch it cut a clean, 90-cell path around the hazards.
* **Experiment:** Crank the Greed slider to 100% and watch A* actively detour into water just to chase coins.
* **Analyze:** Open the Analytics dashboard for a side-by-side, plotted breakdown of all five algorithms and A* greed variants.

---

## Core Features

### Maze Generation

* **Carve & Loop:** Recursive backtracking builds a perfect maze, then knocks out ~18% of internal walls to create alternate routes instead of a single corridor.
* **Auto-Place:** Start and End points spawn instantly at opposite corners—no manual setup required. 
* **Distribute Terrain:** Mud and Water are scattered across open cells, with complete maze connectivity verified (and auto-repaired) before placement.
* **Cluster Coins:** Using a flood-fill from random anchors, coins spawn *specifically* on costly terrain. They arrive in tight, visible clusters, ensuring real risk/reward decisions rather than random scattering.

### Five Algorithms, One Interface

|Algorithm|Structure|Uses Cost|Uses Heuristic|Optimal?|
|---|---|---|---|---|
|BFS|Queue|No|No|Steps only — breaks on weighted terrain by design|
|DFS|Stack|No|No|No — explores deep, not smart|
|UCS _(= Dijkstra)_|Priority queue|Yes|No|Yes|
|Greedy Best-First|Priority queue|No|Yes|No — fast, but can be fooled|
|A*|Priority queue|Yes|Yes|Yes (when greed = 0)|

Every algorithm is a **Python generator** — it `yield`s its state (`visited`, `frontier`, `current`, `path`) one step at a time. The visualizer just calls `next()` once per frame, which is what makes pausing, speed control, and step-by-step animation essentially free.

### The Greed Heuristic (A*'s second dimension)

A* takes a `greed` parameter from 0–100%. At `greed=0`, coins don't factor in at all — A* finds the mathematically optimal path to the exit. As greed increases, coin cells become progressively cheaper to step into (`effective_cost = terrain_cost × (1 − 0.95 × greed/100)`), so the algorithm starts detouring through Mud and Water specifically to collect them. At `greed=100`, it's actively coin-hunting.

This matters because a heuristic-only nudge (changing only the _priority_ of exploring toward coins) isn't enough to change A*'s final path — it still minimizes `g + h`. The actual fix had to change the _real_ cost of entering a coin cell. That distinction — between _what gets explored first_ and _what path gets chosen_ — is the kind of thing that's easy to say and hard to believe until you've watched it fail the first way.

### Scoring

```
Score = (Coins Collected × 100) − Path Cost
```

Simple, but it creates genuine tension: collecting a coin sitting in Water costs 10 to reach. Worth it only if the 100-point reward outweighs the detour. This is what the Greed slider is actually trading off.

### Visualization

- **Live Visualization:** Watch the algorithm "think" in real-time. Visited cells, the active frontier, and the final traced path are all distinctly color-coded.
- **Full Playback Control:** Pause, resume, or adjust the speed (1x / 2x / 5x / Instant) on the fly, right in the middle of a solve.
- **Dynamic Grid:** Coins render as clear targets on the board and dim out as the final path sweeps over them.
- **Real-Time Telemetry:** A live stats panel tracks nodes explored, path length, total cost, coins collected, and final score as the frontier expands.

### Analytics Dashboard

A separate screen, decoupled from the solver, comparing all 7 variants (BFS, DFS, UCS, Greedy, A\* at 0/50/100% greed) on the same maze — with the stats to back each claim, all computed from first principles (no numpy/scipy):
 
- **Summary Table** — nodes explored, cost, terrain penalty, coins, score, and efficiency per variant, with automatic verdict badges (*Fastest*, *Cheapest Path*, *Most Coins*, *Best Score*, *Most Efficient*). Backed by descriptive statistics (mean, median, std dev, IQR, skewness) across all 7 runs.
- **Scatter Plot** — Nodes Explored vs. Score, with a manually-calculated Pearson correlation coefficient and an OLS trend line. Answers "does searching harder actually pay off?" — usually a weak or negative correlation, which is the point.
- **Radar Graph** — a three-axis "personality" profile per algorithm (Cheap Terrain, Coin Ratio, Path Efficiency), built from each path's terrain-frequency distribution and min-max rescaled across algorithms so real differences are visible instead of clustering.
All of it lives in `statistics_engine.py` — zero Pygame imports, pure data logic, testable on its own. Every "intelligent algorithm" claim here is backed by a number, not just an animation that looks convincing.

---

## Project Structure

```
heuristica/
├── main.py                  # App entry point — state machine (Menu / Play / Analytics / Tutorial)
├── grid.py                  # Grid class — terrain storage, costs, neighbors, coins
├── generator.py             # Recursive backtracking maze gen + coin cluster placement
├── renderer.py              # Pygame drawing — terrain cells, coins, sidebar background
├── visualizer.py            # Animation loop, sidebar UI, algorithm wiring (the Play screen)
├── statistics_engine.py     # Pure-Python analytics: batch runs, descriptive stats, Pearson r, terrain profiles
├── analytics.py             # Analytics dashboard screen — Summary Table / Scatter / Radar tabs
├── menu.py                  # Landing screen — scrolling maze background, nav buttons
├── tutorial.py              # "How to Play" step-by-step modal
├── config.py                # Terrain types, costs, colors, window/grid dimensions
├── algorithms/
│   ├── bfs.py
│   ├── dfs.py
│   ├── ucs.py                # Labeled "UCS / Dijkstra" — same algorithm, one implementation
│   ├── greedy.py
│   └── astar.py              # Includes the greed-weighted coin heuristic
├── assets/
│   └── fonts/                # JetBrains Mono (headers/code feel), IBM Plex Sans (body/UI)
├── test_algorithms.py        # Standalone correctness check — no Pygame required
├── test_statistics_engine.py # Standalone analytics check — no Pygame required
└── README.md
```

---

## Terrain & Cost Reference

| Terrain | Cost | Description                                                 |
| ------- | ---- | ----------------------------------------------------------- |
| Plain   | 1    | Baseline movement                                           |
| Mud     | 5    | 5× effort — algorithms with cost-awareness detour around it |
| Water   | 10   | 10× effort — heaviest penalty, still passable               |
| Wall    | ∞    | Impassable                                                  |
| Start   | 0    | Entry point                                                 |
| End     | 0    | Exit point                                                  |
Minimum terrain cost is held at 1 (never below) specifically so the Manhattan-distance heuristic stays **admissible** — it never overestimates the true remaining cost, which is what keeps A* guaranteed-optimal at `greed=0`.

---

## Installation & Running

**Requirements:** Python 3.10+ and pip.

1. Clone this repository:

   ```bash
   git clone https://github.com/YOUR_USERNAME/Heuristica.git
   cd Heuristica
   ```

2. (Recommended) Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   Windows PowerShell:

   ```powershell
   .venv\\Scripts\\Activate.ps1
   ```

   macOS / Linux:

   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Run the game:

   ```bash
   python main.py
   ```

If you prefer, install the dependency directly with `python -m pip install pygame`.

**Note:** The bundled font files are not included in this repository. The app falls back to system fonts if they are unavailable.


**Verifying the logic without launching Pygame:**

```bash
python test_algorithms.py          # runs all 5 algorithms on a generated maze, prints metrics
python test_statistics_engine.py   # runs the full analytics pipeline, prints every phase
```

---

## Built With

Python · Pygame · JetBrains Mono & IBM Plex Sans

---

_Presented by The Outliers._