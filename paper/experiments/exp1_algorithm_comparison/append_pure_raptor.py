#!/usr/bin/env python3
"""
Appends Pure RAPTOR results to an existing exp1_results.json without re-running
all the other baselines.
"""

import logging
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
from algorithms.pure_raptor import PureRaptor


def backfill_pure_raptor():
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

    # Filter out any broken Pure RAPTOR runs (the 0.0ms ones we made earlier)
    filtered = [row for row in existing if row.get("algorithm") != "Pure RAPTOR"]
    print(f"Loaded {len(filtered)} existing benchmark results.")

    print("Loading PlannerService and GTFS Data...")
    planner = load_planner()
    print("Planner loaded successfully.\n")

    seeds = RANDOM_SEEDS[:NUM_REPEATS]
    algo = PureRaptor()
    
    total_runs = len(ORIGINS) * len(DEPART_TIMES_MINUTES) * len(BUDGETS_MINUTES) * len(seeds)
    current_run = 0

    print("=" * 60)
    print(f" BACKFILLING PURE RAPTOR ({total_runs} Configs expected)")
    print(" NOTE: This will take up to 60s per evaluation due to lack of pruning.")
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
                    current_run += 1
                    
                    # Check if already computed properly in existing? 
                    # Generally, since we filtered it out, we must compute it.
                    
                    info = (
                        f"[{current_run:3d}/{total_runs:3d}] "
                        f"{algo.name:<18} | {origin_name[:10]:<10} | dept={depart_time//60:02d}:{depart_time%60:02d} | budget={budget//60}h"
                    )
                    if NUM_REPEATS > 1:
                        info += f" | seed={seed}"
                        
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
                        print(f" -> OK ({row['elapsed_ms']:.1f} ms)")
                        
                        # Save intermediary to prevent data loss on crash
                        save_results(filtered, results_path, metadata={"experiment": "exp1_append", "patched": True})
                    except Exception as e:
                        print(f" -> ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"✅ Successfully appended Pure RAPTOR runs to {results_path}")


if __name__ == "__main__":
    backfill_pure_raptor()
