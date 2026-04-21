#!/usr/bin/env python3
"""
Heals the corrupted baseline data in for Experiment 1 without discarding the
3+ hours of metaheuristic execution. Replaces the results for algorithms that were
handicapped by the `MAX_ROUTES` clipping bug or the McRAPTOR tuple unpacking bug.
"""

import sys
import json
from pathlib import Path

# Add experiments root to PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.config import (
    ORIGINS,
    DEPART_TIMES_MINUTES,
    BUDGETS_MINUTES,
    RANDOM_SEEDS,
    NUM_REPEATS,
    RESULTS_BASE_DIR,
)
from common.planner_bridge import load_planner, resolve_origin
from common.io_utils import save_results
from algorithms.ours_full import OursFull
from algorithms.pure_raptor import PureRaptor
from algorithms.mcraptor import McRaptorBaseline

def heal_experiment():
    results_dir = RESULTS_BASE_DIR / "exp1_algorithm_comparison"
    results_dir.mkdir(parents=True, exist_ok=True)
    results_path = results_dir / "exp1_results.json"
    
    # Load existing results
    if results_path.exists():
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        existing = data.get("results", [])
    else:
        existing = []

    # Algorithms to recompute due to bugs
    to_heal = ["Ours (Full)", "Pure RAPTOR", "McRAPTOR"]

    filtered = [row for row in existing if row.get("algorithm") not in to_heal]
    print(f"Loaded {len(filtered)} healthy baseline results.")

    print("Loading PlannerService and GTFS Data (This will now load ALL routes)...")
    planner = load_planner()
    print("Planner loaded successfully.\n")

    seeds = RANDOM_SEEDS[:NUM_REPEATS]
    algos_to_run = [OursFull(), McRaptorBaseline(), PureRaptor()]
    
    total_runs = len(ORIGINS) * len(DEPART_TIMES_MINUTES) * len(BUDGETS_MINUTES) * len(seeds) * len(algos_to_run)
    current_run = 0

    print("=" * 60)
    print(f" HEALING EXPERIMENT 1 ({total_runs} Configs expected)")
    print(" NOTE: Pure RAPTOR configs will take up to 60s each.")
    print("=" * 60)

    for origin_name in ORIGINS:
        try:
            origin_code = resolve_origin(planner, origin_name)
        except ValueError as e:
            print(f"[!] Skipping {origin_name}: {e}")
            continue

        for depart_time in DEPART_TIMES_MINUTES:
            for budget in BUDGETS_MINUTES:
                for seed in seeds:
                    for algo in algos_to_run:
                        current_run += 1
                        
                        info = (
                            f"[{current_run:4d}/{total_runs:4d}] "
                            f"{algo.name:<18} | {origin_name[:10]:<10} | dept={depart_time//60:02d}:{depart_time%60:02d}"
                        )
                        print(f"{info}", end="", flush=True)
                        
                        try:
                            row = algo.evaluate(
                                planner=planner,
                                origin=origin_code,
                                depart_time=depart_time,
                                budget_minutes=budget,
                                seed=seed,
                            )
                            row["origin_name"] = origin_name
                            filtered.append(row)
                            print(f" -> OK ({row['elapsed_ms']:.1f} ms) | Score: {row.get('composite_score', 0):.2f}")
                            
                            # Save intermediary to prevent data loss on crash
                            save_results(filtered, results_path, metadata={"experiment": "exp1_heal", "patched": True})
                        except Exception as e:
                            print(f" -> ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"✅ Successfully healed target algorithm runs in {results_path}")


if __name__ == "__main__":
    heal_experiment()
