#!/usr/bin/env python3
"""
8h trade-off experiment for score-vs-wall-clock analysis.

This script evaluates selected algorithms under a range of compute budgets
while keeping the travel-time budget fixed (default: 8h / 480 minutes).
It is intended to support the "quality-time trade-off" narrative rather than
the original full-algorithm comparison in Exp1.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper.experiments.common.config import (
    EXP1_STOP_DWELL_MINUTES,
    EXP1_STOP_SCORE_MAX,
    EXP1_STOP_SCORE_MIN,
    EXP1_STOP_SCORE_SEED,
    RANDOM_SEEDS,
    RESULTS_BASE_DIR,
)
from paper.experiments.common.io_utils import load_results, save_results
from paper.experiments.common.planner_bridge import load_planner, resolve_origin
from paper.experiments.common.stop_scoring import StopScoringProfile, build_random_stop_score_map


def parse_csv_tokens(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [x.strip() for x in str(raw).split(",") if x.strip()]


def parse_csv_ints(raw: str | None) -> list[int]:
    return [int(x) for x in parse_csv_tokens(raw)]


def row_to_key(row: dict[str, Any]) -> tuple[str, str, int, int, int, int] | None:
    try:
        return (
            str(row["algorithm"]),
            str(row.get("origin_name", row["origin"])),
            int(row["depart_time"]),
            int(row["budget_minutes"]),
            int(row["compute_budget_seconds"]),
            int(row["seed"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def build_resume_state(path: Path) -> tuple[list[dict[str, Any]], set[tuple[str, str, int, int, int, int]]]:
    if not path.exists():
        return [], set()
    try:
        _, rows = load_results(path)
    except Exception:
        return [], set()

    cleaned: list[dict[str, Any]] = []
    completed: set[tuple[str, str, int, int, int, int]] = set()
    for row in rows:
        key = row_to_key(row)
        if key is None or key in completed:
            continue
        cleaned.append(row)
        completed.add(key)
    return cleaned, completed


def build_algorithm(name: str, *, compute_budget_seconds: int):
    algo_name = str(name).strip().lower()
    if algo_name in {"ours", "ours_full", "ours-full"}:
        from paper.experiments.algorithms.ours_full import OursFull

        return OursFull(timeout_seconds=float(compute_budget_seconds))

    if algo_name in {"nsga2", "nsga-ii", "nsga_ii"}:
        import paper.experiments.algorithms.nsga2 as nsga2_module

        nsga2_module.WALL_CLOCK_LIMIT_SEC = float(compute_budget_seconds)
        return nsga2_module.NSGA2()

    if algo_name in {"ils", "ils+2opt", "ils_2opt"}:
        import paper.experiments.algorithms.ils_2opt as ils_module

        ils_module.WALL_CLOCK_LIMIT_SEC = float(compute_budget_seconds)
        return ils_module.ILS2Opt()

    if algo_name in {"vns"}:
        import paper.experiments.algorithms.vns as vns_module

        vns_module.WALL_CLOCK_LIMIT_SEC = float(compute_budget_seconds)
        return vns_module.VNS()

    if algo_name in {"sa", "simulatedannealing", "simulated_annealing"}:
        import paper.experiments.algorithms.sa as sa_module

        sa_module.WALL_CLOCK_LIMIT_SEC = float(compute_budget_seconds)
        return sa_module.SimulatedAnnealing()

    if algo_name in {"pure_raptor", "pure-raptor", "pureraptor"}:
        import paper.experiments.algorithms.pure_raptor as pure_module

        pure_module.WALL_CLOCK_LIMIT_SEC = float(compute_budget_seconds)
        return pure_module.PureRaptor()

    if algo_name in {"mcraptor", "mc_raptor", "mc-raptor"}:
        from paper.experiments.algorithms.mcraptor import McRaptorBaseline

        return McRaptorBaseline()

    raise ValueError(f"Unsupported algorithm name: {name}")


def run_experiment(
    *,
    origins: list[str],
    depart_times: list[int],
    budget_minutes: int,
    compute_budgets_seconds: list[int],
    seeds: list[int],
    algorithm_names: list[str],
    output_tag: str,
    score_seed: int,
    score_min: int,
    score_max: int,
    dwell_minutes: int,
    resume: bool,
    checkpoint_every: int,
) -> Path:
    print("=" * 60)
    print(" STARTING EXP1 8H TRADE-OFF EXPERIMENT")
    print(f" Resume Mode: {resume}")
    print(f" Travel Budget: {budget_minutes} minutes")
    print(f" Compute Budgets: {compute_budgets_seconds}")
    print(f" Algorithms: {algorithm_names}")
    print("=" * 60)

    print("Loading PlannerService and GTFS Data...")
    planner = load_planner()
    print("Planner loaded successfully.\n")

    objective = StopScoringProfile(
        stop_scores=build_random_stop_score_map(
            planner,
            seed=score_seed,
            score_min=score_min,
            score_max=score_max,
        ),
        dwell_minutes=dwell_minutes,
    )

    output_dir = RESULTS_BASE_DIR / "exp1_algorithm_comparison"
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_tag = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in output_tag.strip())
    output_path = output_dir / f"exp1_tradeoff_{safe_tag}.json"

    results: list[dict[str, Any]] = []
    completed: set[tuple[str, str, int, int, int, int]] = set()
    if resume:
        results, completed = build_resume_state(output_path)
        if completed:
            print(f"Loaded {len(completed)} completed runs from {output_path}")

    total_runs = len(origins) * len(depart_times) * len(compute_budgets_seconds) * len(seeds) * len(algorithm_names)
    pending_runs = max(0, total_runs - len(completed))
    print(f"Total Configurations to Evaluate: {total_runs}")
    print(f"Already Completed (resume): {len(completed)}")
    print(f"Pending This Run: {pending_runs}")
    print("-" * 60)
    if pending_runs == 0:
        print("Nothing to run. Existing results already cover all combinations.")
        return output_path

    newly_saved = 0
    current_run = 0

    for origin_name in origins:
        origin_code = resolve_origin(planner, origin_name)
        for depart_time in depart_times:
            for compute_budget_seconds in compute_budgets_seconds:
                for seed in seeds:
                    for algorithm_name in algorithm_names:
                        algo = build_algorithm(algorithm_name, compute_budget_seconds=compute_budget_seconds)
                        algo.objective = objective
                        key = (
                            str(algo.name),
                            origin_name,
                            int(depart_time),
                            int(budget_minutes),
                            int(compute_budget_seconds),
                            int(seed),
                        )
                        if key in completed:
                            continue

                        current_run += 1
                        desc = (
                            f"[{current_run:4d}/{pending_runs:4d}] "
                            f"{algo.name:<18} | {origin_name:<10} | "
                            f"dept={depart_time//60:02d}:{depart_time%60:02d} | "
                            f"travel=8h | compute={compute_budget_seconds}s | seed={seed}"
                        )
                        print(desc, end="", flush=True)

                        row = algo.evaluate(
                            planner=planner,
                            origin=origin_code,
                            depart_time=depart_time,
                            budget_minutes=budget_minutes,
                            seed=seed,
                        )
                        row["origin_code"] = origin_code
                        row["origin_name"] = origin_name
                        row["compute_budget_seconds"] = int(compute_budget_seconds)
                        row["algorithm_family"] = algorithm_name
                        results.append(row)
                        completed.add(key)
                        newly_saved += 1
                        print(
                            " -> OK "
                            f"(score={row.get('stop_score_total', 0.0):.1f}, "
                            f"elapsed={row.get('elapsed_ms', 0.0):.1f} ms)"
                        )

                        if checkpoint_every > 0 and newly_saved % checkpoint_every == 0:
                            save_results(
                                results,
                                output_path,
                                metadata={
                                    "experiment": "exp1_8h_tradeoff",
                                    "travel_budget_minutes": budget_minutes,
                                    "compute_budgets_seconds": compute_budgets_seconds,
                                    "algorithms": algorithm_names,
                                    "origins": origins,
                                    "depart_times": depart_times,
                                    "seeds": seeds,
                                    "stop_score_seed": score_seed,
                                    "stop_score_min": score_min,
                                    "stop_score_max": score_max,
                                    "dwell_minutes": dwell_minutes,
                                    "output_tag": output_tag,
                                },
                            )
                            print(f"    [checkpoint] saved {len(results)} rows -> {output_path}")

    save_results(
        results,
        output_path,
        metadata={
            "experiment": "exp1_8h_tradeoff",
            "travel_budget_minutes": budget_minutes,
            "compute_budgets_seconds": compute_budgets_seconds,
            "algorithms": algorithm_names,
            "origins": origins,
            "depart_times": depart_times,
            "seeds": seeds,
            "stop_score_seed": score_seed,
            "stop_score_min": score_min,
            "stop_score_max": score_max,
            "dwell_minutes": dwell_minutes,
            "output_tag": output_tag,
        },
    )
    print("Done!")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Exp1 8h trade-off experiment")
    parser.add_argument("--resume", action="store_true", help="Resume from an existing result file")
    parser.add_argument("--checkpoint-every", type=int, default=5, help="Save every N runs")
    parser.add_argument("--origins", type=str, default="hakata,meinohama", help="Comma-separated origin names")
    parser.add_argument("--depart-times", type=str, default="420,600", help="Comma-separated departure times in minutes")
    parser.add_argument("--budget", type=int, default=8 * 60, help="Travel-time budget in minutes")
    parser.add_argument("--compute-budgets", type=str, default="30,60,120,300,600", help="Comma-separated wall-clock budgets in seconds")
    parser.add_argument("--seeds", type=str, default="0,1,2", help="Comma-separated seed ids")
    parser.add_argument("--algorithms", type=str, default="ours,nsga2", help="Comma-separated algorithm ids")
    parser.add_argument("--output-tag", type=str, default="default", help="Suffix for result filename")
    parser.add_argument("--score-seed", type=int, default=EXP1_STOP_SCORE_SEED)
    parser.add_argument("--score-min", type=int, default=EXP1_STOP_SCORE_MIN)
    parser.add_argument("--score-max", type=int, default=EXP1_STOP_SCORE_MAX)
    parser.add_argument("--dwell-minutes", type=int, default=EXP1_STOP_DWELL_MINUTES)
    args = parser.parse_args()

    run_experiment(
        origins=parse_csv_tokens(args.origins),
        depart_times=parse_csv_ints(args.depart_times),
        budget_minutes=int(args.budget),
        compute_budgets_seconds=parse_csv_ints(args.compute_budgets),
        seeds=parse_csv_ints(args.seeds) or RANDOM_SEEDS[:3],
        algorithm_names=parse_csv_tokens(args.algorithms),
        output_tag=(args.output_tag.strip() or "default"),
        score_seed=int(args.score_seed),
        score_min=int(args.score_min),
        score_max=int(args.score_max),
        dwell_minutes=int(args.dwell_minutes),
        resume=bool(args.resume),
        checkpoint_every=int(args.checkpoint_every),
    )


if __name__ == "__main__":
    main()
