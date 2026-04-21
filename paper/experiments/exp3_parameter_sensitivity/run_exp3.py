#!/usr/bin/env python3
"""
Experiment 3: balance analysis supplementary to Experiment 1.

This experiment reuses Exp1 score-guided results and aggregates them into
task-level rows for tradeoff analysis. Each row corresponds to one
`(algorithm, origin, depart_time, budget, score_seed)` task after averaging
over algorithm seeds when needed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper.experiments.common.io_utils import save_results
from paper.experiments.exp3_parameter_sensitivity.exp3_balance_common import (
    DEFAULT_EXP1_RESULTS,
    DEFAULT_EXP3_RESULTS,
    DEFAULT_EXP3_RESULTS_QUICK,
    EXP3_RESULTS_DIR,
    EXP3_TARGET_BUDGETS,
    filter_exp1_scope,
    load_exp1_frame,
    parse_csv_ints,
    parse_csv_tokens,
    build_task_level_frame,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Exp3 quality-speed balance rows from Exp1 results.")
    parser.add_argument("--quick", action="store_true", help="Use a small subset for smoke testing.")
    parser.add_argument(
        "--preset",
        type=str,
        default="none",
        choices=["none", "recent2_adapted"],
        help="Convenience preset for algorithm scope and output naming.",
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_EXP1_RESULTS, help="Path to the Exp1 results JSON.")
    parser.add_argument("--output", type=Path, default=None, help="Optional explicit output path.")
    parser.add_argument("--origins", type=str, default="", help="Optional comma-separated origin names.")
    parser.add_argument("--depart-times", type=str, default="", help="Optional comma-separated depart times.")
    parser.add_argument("--budgets", type=str, default="", help="Optional comma-separated budgets in minutes.")
    parser.add_argument("--score-seeds", type=str, default="", help="Optional comma-separated score seeds.")
    parser.add_argument("--algorithms", type=str, default="", help="Optional comma-separated algorithm names.")
    parser.add_argument("--max-origins", type=int, default=0, help="Limit to the first N origins when no --origins is given.")
    args = parser.parse_args()

    if args.preset == "recent2_adapted" and not args.algorithms:
        args.algorithms = "Ours (Full),ZhouWang2025-ALNS (adapted),Zhang2025-DynPref (adapted)"

    input_path = args.input.resolve()
    if args.output:
        output_path = args.output.resolve()
    elif args.preset != "none":
        suffix = "_quick" if args.quick else ""
        output_path = (EXP3_RESULTS_DIR / f"exp3_results_{args.preset}{suffix}.json").resolve()
    else:
        output_path = (DEFAULT_EXP3_RESULTS_QUICK if args.quick else DEFAULT_EXP3_RESULTS).resolve()

    metadata, exp1_df = load_exp1_frame(input_path)
    filtered_df, scope = filter_exp1_scope(
        exp1_df,
        metadata=metadata,
        quick=args.quick,
        origins=parse_csv_tokens(args.origins),
        depart_times=parse_csv_ints(args.depart_times),
        budgets=parse_csv_ints(args.budgets),
        score_seeds=parse_csv_ints(args.score_seeds),
        algorithms=parse_csv_tokens(args.algorithms),
        max_origins=args.max_origins,
    )
    task_df = build_task_level_frame(filtered_df)
    missing_target_budgets = [int(x) for x in EXP3_TARGET_BUDGETS if int(x) not in set(scope["budgets"])]

    out_metadata = {
        "experiment": "exp3_exp1_balance_analysis",
        "quick_mode": bool(args.quick),
        "source_exp1_results": str(input_path),
        "primary_quality_metric": "stop_score_total",
        "primary_efficiency_metric": "elapsed_ms",
        "primary_balance_metric": "ideal_distance",
        "aggregation_level": "query_score_seed_task",
        "selected_scope": scope,
        "target_budgets_minutes": list(EXP3_TARGET_BUDGETS),
        "missing_target_budgets_minutes": missing_target_budgets,
        "source_primary_metric": metadata.get("primary_metric"),
        "source_objective_mode": metadata.get("objective_mode"),
        "source_score_seed_count": metadata.get("score_seed_count"),
        "preset": args.preset,
    }
    save_results(task_df.to_dict(orient="records"), output_path, metadata=out_metadata)

    print("=" * 72)
    print("EXP3 BALANCE ANALYSIS (SUPPLEMENT TO EXP1)")
    print(f"Source: {input_path}")
    print(f"Output: {output_path}")
    print(f"Rows: {len(task_df)}")
    print(f"Origins: {scope['origins']}")
    print(f"Budgets: {scope['budgets']}")
    print(f"Score seeds: {scope['score_seeds']}")
    if missing_target_budgets:
        print(f"Missing target budgets from source Exp1 results: {missing_target_budgets}")
    print("=" * 72)


if __name__ == "__main__":
    main()
