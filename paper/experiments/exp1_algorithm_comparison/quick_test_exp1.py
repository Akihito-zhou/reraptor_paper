#!/usr/bin/env python3
"""
Test script to run ~10 evaluations (2 origins x 5 algorithms)
with a 60-second hardware timeout limit to show the realistic
superiority of Ours (Full) against the baselines and the baseline Pure RAPTOR.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.planner_bridge import load_planner
from algorithms import ALL_ALGORITHMS
from common import config
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def run_60s_tests():
    planner = load_planner()
    
    # 60s hard timeout globally
    config.WALL_CLOCK_LIMIT_SEC = 60
    
    origins = {
        "677805": "Hakata (Center)",
        "678230": "Fukudaimae (Suburban)"
    }
    depart_minutes = 14 * 60
    budget_minutes = 8 * 60  # 8 hours budget

    # Select exactly 5 representative algorithms to hit ~10 runs
    target_algos = ["Ours (Full)", "Pure RAPTOR", "McRAPTOR", "NSGA-II", "Greedy (L=3)", "ILS+2opt"]
    selected_algos = [a for a in ALL_ALGORITHMS if a.name in target_algos]

    print("=" * 60)
    print(" 60-SECOND TIMEOUT SUPERIORITY TEST (12 Runs Total)")
    print("=" * 60)

    results = []
    
    for origin_code, origin_name in origins.items():
        print(f"\n[{origin_name}]")
        for algo in selected_algos:
            if hasattr(algo, "timeout_seconds"):
                algo.timeout_seconds = 60
                
            print(f"  -> {algo.name:15s} ...", end="", flush=True)
            try:
                row = algo.evaluate(
                    planner=planner,
                    origin=origin_code,
                    depart_time=depart_minutes,
                    budget_minutes=budget_minutes,
                    seed=42
                )
                
                score = row.get("composite_score", 0)
                feasible = row.get("feasible", False)
                time_ms = row.get("elapsed_ms", 0)
                
                print(f" Score: {score:.3f} | Feasible: {feasible} | Time: {time_ms:.1f}ms")
                row["algorithm"] = algo.name
                row["origin"] = origin_name
                results.append(row)
            except Exception as e:
                print(f" ERROR: {e}")

    # Generate charts
    df = pd.DataFrame(results)
    out_dir = Path("paper/figures/exp1_algorithm_comparison")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for origin_code, origin_name in origins.items():
        sub_df = df[df["origin"] == origin_name].sort_values(by="composite_score", ascending=False)
        plt.figure(figsize=(10, 6))
        sns.barplot(data=sub_df, x="algorithm", y="composite_score", hue="algorithm", palette="viridis", dodge=False)
        plt.xticks(rotation=45)
        plt.title(f"Algorithm Superiority (60s Limit): {origin_name}")
        plt.tight_layout()
        plot_path = out_dir / f"test_60s_{origin_code}.png"
        plt.savefig(plot_path, dpi=300)
        plt.close()
        print(f"Saved plot: {plot_path}")

if __name__ == "__main__":
    run_60s_tests()
