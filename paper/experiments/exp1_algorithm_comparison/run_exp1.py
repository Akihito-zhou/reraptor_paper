#!/usr/bin/env python3
"""
Experiment 1: Algorithm Comparison & Pareto Front Analysis.

Runs all baseline algorithms against the default query set and saves
the raw metrics to results/exp1_results.json.
"""
from __future__ import annotations

import argparse
import sys
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
    QUICK_ORIGINS,
    QUICK_DEPART_TIMES,
    QUICK_BUDGETS,
    QUICK_NUM_REPEATS,
    EXP1_STOP_DWELL_MINUTES,
    EXP1_STOP_SCORE_MAX,
    EXP1_STOP_SCORE_MIN,
    EXP1_STOP_SCORE_SEED,
)
from common.planner_bridge import load_planner, resolve_origin
from common.io_utils import load_results, save_results
from common.stop_scoring import StopScoringProfile, build_random_stop_score_map
from algorithms import build_all_algorithms


def parse_csv_tokens(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [x.strip() for x in str(raw).split(",") if x.strip()]


def parse_csv_ints(raw: str | None) -> list[int]:
    return [int(x) for x in parse_csv_tokens(raw)]


def seeds_for_algorithm(algo, seeds: list[int], *, repeat_deterministic_seeds: bool) -> list[int]:
    if repeat_deterministic_seeds or getattr(algo, "stochastic", False):
        return list(seeds)
    return [int(seeds[0])] if seeds else [0]


def normalize_score_seeds(
    *,
    score_seed: int,
    score_seeds_override: list[int] | None,
) -> list[int]:
    if score_seeds_override:
        ordered: list[int] = []
        seen: set[int] = set()
        for value in score_seeds_override:
            seed_value = int(value)
            if seed_value in seen:
                continue
            ordered.append(seed_value)
            seen.add(seed_value)
        if ordered:
            return ordered
    return [int(score_seed)]


def row_to_key(row: dict, *, default_score_seed: int | None = None) -> tuple[str, str, int, int, int, int] | None:
    try:
        score_seed = row.get("score_seed", default_score_seed)
        if score_seed is None:
            return None
        return (
            str(row["algorithm"]),
            str(row.get("origin_name", row["origin"])),
            int(row["depart_time"]),
            int(row["budget_minutes"]),
            int(row["seed"]),
            int(score_seed),
        )
    except (KeyError, TypeError, ValueError):
        return None


def infer_default_score_seed(metadata: dict) -> int | None:
    score_seeds = metadata.get("score_seeds")
    if isinstance(score_seeds, list) and len(score_seeds) == 1:
        try:
            return int(score_seeds[0])
        except (TypeError, ValueError):
            return None
    stop_score_seed = metadata.get("stop_score_seed")
    if stop_score_seed is None:
        return None
    try:
        return int(stop_score_seed)
    except (TypeError, ValueError):
        return None


def build_resume_state(path: Path) -> tuple[list[dict], set[tuple[str, str, int, int, int, int]], dict[str, int]]:
    if not path.exists():
        return [], set(), {
            "loaded": 0,
            "kept": 0,
            "dropped_malformed": 0,
            "dropped_incompatible": 0,
            "dropped_duplicate": 0,
            "backfilled_score_seed": 0,
        }

    try:
        metadata, rows = load_results(path)
    except Exception:
        return [], set(), {
            "loaded": 0,
            "kept": 0,
            "dropped_malformed": 0,
            "dropped_incompatible": 0,
            "dropped_duplicate": 0,
            "backfilled_score_seed": 0,
        }
    default_score_seed = infer_default_score_seed(metadata)
    cleaned: list[dict] = []
    completed: set[tuple[str, str, int, int, int, int]] = set()
    stats = {
        "loaded": len(rows),
        "kept": 0,
        "dropped_malformed": 0,
        "dropped_incompatible": 0,
        "dropped_duplicate": 0,
        "backfilled_score_seed": 0,
    }
    for row in rows:
        normalized_row = row
        if "score_seed" not in row and default_score_seed is not None:
            normalized_row = dict(row)
            normalized_row["score_seed"] = default_score_seed
            stats["backfilled_score_seed"] += 1

        key = row_to_key(normalized_row, default_score_seed=default_score_seed)
        if key is None:
            stats["dropped_malformed"] += 1
            continue
        required = {"stop_score_total", "score_per_hour", "dwell_minutes_total", "effective_time_minutes"}
        if not required.issubset(normalized_row.keys()):
            stats["dropped_incompatible"] += 1
            continue
        if key in completed:
            stats["dropped_duplicate"] += 1
            continue
        cleaned.append(normalized_row)
        completed.add(key)
    stats["kept"] = len(cleaned)
    return cleaned, completed, stats


def build_experiment_metadata(
    *,
    quick_mode: bool,
    score_seeds: list[int],
    score_min: int,
    score_max: int,
    dwell_minutes: int,
    objective_mode: str,
    origins: list[str],
    depart_times: list[int],
    budgets: list[int],
    seeds: list[int],
    repeat_deterministic_seeds: bool,
    algorithm_seeds: dict[str, list[int]],
    algorithms: list,
    total_runs: int,
    output_tag: str | None,
    include_recent_adapted_baselines: bool = False,
    algorithms_override: list[str] | None = None,
) -> dict:
    metadata = {
        "experiment": "exp1_algorithm_comparison",
        "quick_mode": quick_mode,
        "primary_metric": "stop_score_total",
        "primary_metric_label": "Stop Score",
        "score_seeds": list(score_seeds),
        "score_seed_count": len(score_seeds),
        "stop_score_min": score_min,
        "stop_score_max": score_max,
        "dwell_minutes": dwell_minutes,
        "objective_mode": objective_mode,
        "origins": origins,
        "depart_times": depart_times,
        "budgets": budgets,
        "seeds": seeds,
        "seed_policy": {
            "repeat_deterministic_seeds": repeat_deterministic_seeds,
            "deterministic_repeats": (len(seeds) if repeat_deterministic_seeds else 1),
            "stochastic_repeats": len(seeds),
            "algorithm_seed_counts": {
                algo.name: len(algorithm_seeds[algo.name]) for algo in algorithms
            },
        },
        "total_runs": total_runs,
        "output_tag": output_tag,
        "include_recent_adapted_baselines": bool(include_recent_adapted_baselines),
        "algorithms_override": list(algorithms_override or []),
    }
    if len(score_seeds) == 1:
        metadata["stop_score_seed"] = int(score_seeds[0])
    return metadata


def run_experiment(
    quick_mode: bool = False,
    *,
    resume: bool = False,
    checkpoint_every: int = 20,
    score_seed: int = EXP1_STOP_SCORE_SEED,
    score_seeds_override: list[int] | None = None,
    score_min: int = EXP1_STOP_SCORE_MIN,
    score_max: int = EXP1_STOP_SCORE_MAX,
    dwell_minutes: int = EXP1_STOP_DWELL_MINUTES,
    origins_override: list[str] | None = None,
    depart_times_override: list[int] | None = None,
    budgets_override: list[int] | None = None,
    seeds_override: list[int] | None = None,
    output_tag: str | None = None,
    repeat_deterministic_seeds: bool = False,
    objective_mode: str = "score_guided",
    include_recent_adapted_baselines: bool = False,
    algorithms_override: list[str] | None = None,
) -> None:
    print(f"============================================================")
    print(f" STARTING EXPERIMENT 1: Algorithm Comparison")
    print(f" Quick Mode: {quick_mode}")
    print(f" Resume Mode: {resume}")
    print(f"============================================================")

    print("Loading PlannerService and GTFS Data...")
    planner = load_planner()
    print("Planner loaded successfully.\n")
    score_seeds = normalize_score_seeds(score_seed=score_seed, score_seeds_override=score_seeds_override)
    objectives = {
        stop_score_seed: StopScoringProfile(
            stop_scores=build_random_stop_score_map(
                planner,
                seed=stop_score_seed,
                score_min=score_min,
                score_max=score_max,
            ),
            dwell_minutes=dwell_minutes,
            search_mode=objective_mode,
        )
        for stop_score_seed in score_seeds
    }

    origins = list(origins_override) if origins_override else (QUICK_ORIGINS if quick_mode else ORIGINS)
    depart_times = list(depart_times_override) if depart_times_override else (QUICK_DEPART_TIMES if quick_mode else DEPART_TIMES_MINUTES)
    budgets = list(budgets_override) if budgets_override else (QUICK_BUDGETS if quick_mode else BUDGETS_MINUTES)
    if seeds_override:
        seeds = list(seeds_override)
        repeats = len(seeds)
    else:
        repeats = QUICK_NUM_REPEATS if quick_mode else NUM_REPEATS
        seeds = RANDOM_SEEDS[:repeats]
    algorithms = build_all_algorithms(
        include_recent_adapted=include_recent_adapted_baselines,
        algorithm_filter=algorithms_override,
    )
    if not algorithms:
        raise ValueError("No algorithms selected. Check --algorithms filter.")
    algorithm_seeds = {
        algo.name: seeds_for_algorithm(algo, seeds, repeat_deterministic_seeds=repeat_deterministic_seeds)
        for algo in algorithms
    }

    output_dir = RESULTS_BASE_DIR / "exp1_algorithm_comparison"
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_tag:
        safe_tag = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in output_tag.strip())
        output_name = f"exp1_results_{safe_tag}.json"
    else:
        output_name = "exp1_results_quick.json" if quick_mode else "exp1_results.json"
    output_path = output_dir / output_name

    results: list[dict] = []
    completed: set[tuple[str, str, int, int, int, int]] = set()
    if resume:
        results, completed, stats = build_resume_state(output_path)
        if completed:
            print(f"Loaded {len(completed)} completed runs from {output_path}")
        dropped = stats["dropped_malformed"] + stats["dropped_incompatible"] + stats["dropped_duplicate"]
        if dropped:
            print(
                "[resume] ignored rows: "
                f"malformed={stats['dropped_malformed']}, "
                f"incompatible={stats['dropped_incompatible']}, "
                f"duplicate={stats['dropped_duplicate']}"
            )
        if stats["backfilled_score_seed"]:
            print(f"[resume] backfilled score_seed for {stats['backfilled_score_seed']} legacy rows")

    total_runs = (
        len(score_seeds)
        * len(origins)
        * len(depart_times)
        * len(budgets)
        * sum(len(algorithm_seeds[algo.name]) for algo in algorithms)
    )
    pending_runs = max(0, total_runs - len(completed))
    current_run = 0

    metadata = build_experiment_metadata(
        quick_mode=quick_mode,
        score_seeds=score_seeds,
        score_min=score_min,
        score_max=score_max,
        dwell_minutes=dwell_minutes,
        objective_mode=objective_mode,
        origins=origins,
        depart_times=depart_times,
        budgets=budgets,
        seeds=seeds,
        repeat_deterministic_seeds=repeat_deterministic_seeds,
        algorithm_seeds=algorithm_seeds,
        algorithms=algorithms,
        total_runs=total_runs,
        output_tag=output_tag,
        include_recent_adapted_baselines=include_recent_adapted_baselines,
        algorithms_override=algorithms_override,
    )

    print(f"Total Configurations to Evaluate: {total_runs}")
    print(f"Already Completed (resume): {len(completed)}")
    print(f"Pending This Run: {pending_runs}")
    print(f"Stop Score Seeds: {score_seeds}")
    print("-" * 60)
    if pending_runs == 0:
        print("Nothing to run. Existing results already cover all combinations.")
        return

    newly_saved = 0
    interrupted = False

    try:
        for stop_score_seed in score_seeds:
            objective = objectives[stop_score_seed]
            for origin_name in origins:
                try:
                    origin_code = resolve_origin(planner, origin_name)
                except ValueError as e:
                    print(f"[!] Skipping {origin_name}: {e}")
                    continue

                for depart_time in depart_times:
                    for budget in budgets:
                        for algo in algorithms:
                            algo.objective = objective
                            algo_seeds = algorithm_seeds[algo.name]
                            for seed in algo_seeds:
                                key = (
                                    algo.name,
                                    origin_name,
                                    int(depart_time),
                                    int(budget),
                                    int(seed),
                                    int(stop_score_seed),
                                )
                                if key in completed:
                                    continue

                                current_run += 1
                                info_str = f"[{current_run:4d}/{pending_runs:4d}] "
                                info_str += (
                                    f"{algo.name:<18} | {origin_name[:10]:<10} | "
                                    f"dept={depart_time//60:02d}:{depart_time%60:02d} | "
                                    f"budget={budget//60}h | score_seed={stop_score_seed}"
                                )
                                if repeats > 1:
                                    info_str += f" | seed={seed}"
                                print(f"{info_str}", end="", flush=True)

                                try:
                                    row = algo.evaluate(
                                        planner=planner,
                                        origin=origin_code,
                                        depart_time=depart_time,
                                        budget_minutes=budget,
                                        seed=seed,
                                    )
                                    row["origin_code"] = origin_code
                                    row["origin_name"] = origin_name
                                    row["score_seed"] = int(stop_score_seed)
                                    results.append(row)
                                    completed.add(key)
                                    newly_saved += 1
                                    print(
                                        " -> OK "
                                        f"(score={row.get('stop_score_total', 0.0):.1f}, "
                                        f"elapsed={row['elapsed_ms']:.1f} ms)"
                                    )

                                    if checkpoint_every > 0 and (newly_saved % checkpoint_every == 0):
                                        save_results(results, output_path, metadata=metadata)
                                        print(f"    [checkpoint] saved {len(results)} rows -> {output_path}")
                                except Exception as e:
                                    print(f" -> ERROR: {e}")
    except KeyboardInterrupt:
        interrupted = True
        print("\n[!] Interrupted by user. Saving partial results...")

    print("\n" + "=" * 60)
    save_results(results, output_path, metadata=metadata)
    if interrupted:
        print("Stopped early. Partial results are preserved.")
        sys.exit(130)
    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Experiment 1: Algorithm Comparison")
    parser.add_argument("--quick", action="store_true", help="Run in quick mode for rapid testing")
    parser.add_argument("--resume", action="store_true", help="Resume from an existing results file when available")
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=20,
        help="Save partial results every N successful runs (<=0 to disable checkpoints)",
    )
    parser.add_argument("--score-seed", type=int, default=EXP1_STOP_SCORE_SEED)
    parser.add_argument(
        "--score-seeds",
        type=str,
        default="",
        help="Comma-separated stop-score seeds; overrides --score-seed when provided",
    )
    parser.add_argument("--score-min", type=int, default=EXP1_STOP_SCORE_MIN)
    parser.add_argument("--score-max", type=int, default=EXP1_STOP_SCORE_MAX)
    parser.add_argument("--dwell-minutes", type=int, default=EXP1_STOP_DWELL_MINUTES)
    parser.add_argument("--origins", type=str, default="", help="Comma-separated origin names")
    parser.add_argument("--depart-times", type=str, default="", help="Comma-separated departure times in minutes")
    parser.add_argument("--budgets", type=str, default="", help="Comma-separated budgets in minutes")
    parser.add_argument("--seeds", type=str, default="", help="Comma-separated seed ids")
    parser.add_argument("--output-tag", type=str, default="", help="Custom suffix for result filename")
    parser.add_argument(
        "--objective-mode",
        type=str,
        default="score_guided",
        choices=["score_guided", "legacy_balanced"],
        help="Stop-score search objective mode",
    )
    parser.add_argument(
        "--repeat-deterministic-seeds",
        action="store_true",
        help="Also repeat deterministic algorithms over all requested seeds",
    )
    parser.add_argument(
        "--include-recent-adapted-baselines",
        action="store_true",
        help="Include 2024+ adapted baselines in the algorithm pool",
    )
    parser.add_argument(
        "--algorithms",
        type=str,
        default="",
        help="Comma-separated algorithm name filters (case-insensitive token match)",
    )
    args = parser.parse_args()
    
    run_experiment(
        quick_mode=args.quick,
        resume=args.resume,
        checkpoint_every=args.checkpoint_every,
        score_seed=args.score_seed,
        score_seeds_override=parse_csv_ints(args.score_seeds),
        score_min=args.score_min,
        score_max=args.score_max,
        dwell_minutes=args.dwell_minutes,
        origins_override=parse_csv_tokens(args.origins),
        depart_times_override=parse_csv_ints(args.depart_times),
        budgets_override=parse_csv_ints(args.budgets),
        seeds_override=parse_csv_ints(args.seeds),
        output_tag=(args.output_tag.strip() or None),
        repeat_deterministic_seeds=args.repeat_deterministic_seeds,
        objective_mode=args.objective_mode,
        include_recent_adapted_baselines=args.include_recent_adapted_baselines,
        algorithms_override=parse_csv_tokens(args.algorithms),
    )
