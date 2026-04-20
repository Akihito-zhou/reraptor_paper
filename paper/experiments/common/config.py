"""
Global experiment configuration.

All experiments share these settings to ensure fair, reproducible comparisons.
"""
from __future__ import annotations

from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]          # reroute_fukuoka/
PLANNER_DATA_DIR = PROJECT_ROOT / "apps" / "api" / "data"
RESULTS_BASE_DIR = PROJECT_ROOT / "paper" / "results"
FIGURES_BASE_DIR = PROJECT_ROOT / "paper" / "figures"

# ─── Query Set ────────────────────────────────────────────────────────────────
# At least 10 origins × 3 departure times × 2 budgets (weekday / weekend)
ORIGINS = [
    "hakata",       # 博多駅 — 大型枢纽
    "tenjin",       # 天神 — 次级枢纽
    "nishijin",     # 西新 — 中等节点
    "ohori-koen",   # 大濠公園 — 观光区
    "yakuin",       # 薬院 — 住宅区
    "kashii",       # 香椎 — 郊区东
    "noke",         # 野芥 — 郊区西
    "meinohama",    # 姪浜 — 起点站
    "kaizuka",      # 貝塚 — 边缘站
    "fukudaimae",   # 福大前 — 大学区
]

DEPART_TIMES_MINUTES = [
    7 * 60,         # 07:00 — 早朝
    10 * 60,        # 10:00 — 午前
    14 * 60,        # 14:00 — 午後
]

BUDGETS_MINUTES = [
    4 * 60,         # 4h — 半日
    8 * 60,         # 8h — 全日 (default)
]

# ─── Reproducibility ──────────────────────────────────────────────────────────
NUM_REPEATS = 5
RANDOM_SEEDS = list(range(NUM_REPEATS))

# ─── Fair Comparison Protocol ─────────────────────────────────────────────────
WALL_CLOCK_LIMIT_SEC = 60          # Max wall-clock seconds for metaheuristics
GA_POPULATION_SIZE = 100
GA_GENERATIONS = 200
SA_INITIAL_TEMP = 1000.0
SA_COOLING_RATE = 0.995

# ─── Experiment 2 Resource Policy ─────────────────────────────────────────────
# Time-budgeted evaluation is standard in routing/orienteering benchmarks.
# For the no-pruning ablation only, add a hard label cap as a memory-safe stop.
EXP2_TIMEOUT_SECONDS = WALL_CLOCK_LIMIT_SEC
EXP2_NO_PRUNING_MAX_LABELS = 1_000_000

# ─── Scoring Weights (default) ────────────────────────────────────────────────
SCORE_WEIGHTS = {
    "ride_minutes": 0.40,
    "unique_stops": 0.25,
    "hull_area":    0.20,
    "quadrant":     0.15,
}

# Score-based Exp1 defaults
EXP1_STOP_SCORE_SEED = 20260323
EXP1_STOP_SCORE_MIN = 1
EXP1_STOP_SCORE_MAX = 100
EXP1_STOP_DWELL_MINUTES = 10

# ─── Beam Search Defaults ─────────────────────────────────────────────────────
BEAM_WIDTH = 50
MAX_QUEUE_SIZE = 1500
MAX_EXPANSIONS = 90000
TRANSFER_BUFFER_MINUTES = 3

# ─── Quick Mode (for testing) ─────────────────────────────────────────────────
QUICK_ORIGINS = ["hakata"]
QUICK_DEPART_TIMES = [7 * 60]
QUICK_BUDGETS = [4 * 60]
QUICK_NUM_REPEATS = 1
