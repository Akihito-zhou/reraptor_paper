#!/usr/bin/env python3
"""Run canonical ReRAPTOR hyperparameter sensitivity configurations."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper.experiments.common.config import (
    DEPART_TIMES_MINUTES,
    EXP1_STOP_DWELL_MINUTES,
    EXP1_STOP_SCORE_MAX,
    EXP1_STOP_SCORE_MIN,
    EXP1_STOP_SCORE_SEED,
    EXP2_TIMEOUT_SECONDS,
    ORIGINS,
    RANDOM_SEEDS,
    RESULTS_BASE_DIR,
)
from paper.experiments.common.io_utils import save_results
from paper.experiments.common.json_list_store import build_resume_state
from paper.experiments.common.planner_bridge import load_planner, resolve_origin
from paper.experiments.common.stop_scoring import build_random_stop_score_map
from paper.experiments.exp2_ablation_study.run_exp2 import (
    normalize_score_seeds,
    parse_csv_ints,
    parse_csv_tokens,
    shared_config_snapshot,
)
from paper.experiments.exp3_parameter_sensitivity.sensitivity_protocol import (
    SensitivitySpec,
    select_specs,
)


DEFAULT_SCORE_SEEDS = (20260323, 20260324, 20260325, 20260326, 20260327)
CANONICAL_BUDGETS = (120, 240, 360, 480)
INTERACTION_ORIGINS = ("hakata", "fukudaimae", "noke")
INTERACTION_SCORE_SEEDS = (20260323, 20260325)

logging.basicConfig(level=logging.INFO, format="%(message)s")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)


def run_key(
    *,
    config_id: str,
    origin: str,
    depart_time: int,
    budget_minutes: int,
    seed: int,
    score_seed: int,
) -> tuple[str, str, int, int, int, int]:
    return (
        str(config_id),
        str(origin),
        int(depart_time),
        int(budget_minutes),
        int(seed),
        int(score_seed),
    )


def row_to_key(row: dict[str, Any]) -> tuple[str, str, int, int, int, int] | None:
    try:
        return run_key(
            config_id=str(row["sensitivity_config_id"]),
            origin=str(row["origin"]),
            depart_time=int(row["depart_time"]),
            budget_minutes=int(row["budget_minutes"]),
            seed=int(row["seed"]),
            score_seed=int(row["score_seed"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def is_resume_row_compatible(row: dict[str, Any]) -> bool:
    required = {
        "algorithm",
        "sensitivity_config_id",
        "sensitivity_panel",
        "sensitivity_factor",
        "origin",
        "origin_name",
        "depart_time",
        "budget_minutes",
        "seed",
        "score_seed",
        "elapsed_ms",
        "stop_score_total",
        "labels",
        "termination_reason",
        "resource_cap_hit",
        "candidate_trim_events",
        "beam_trim_events",
    }
    return required.issubset(row)


def metadata_for_run(
    *,
    panel: str,
    specs: list[SensitivitySpec],
    origins: list[str],
    depart_times: list[int],
    budgets: list[int],
    seeds: list[int],
    score_seeds: list[int],
    score_min: int,
    score_max: int,
    dwell_minutes: int,
    objective_mode: str,
    timeout_seconds: float,
    total_runs: int,
    output_tag: str,
) -> dict[str, Any]:
    return {
        "experiment": "exp3_hyperparameter_sensitivity",
        "panel": panel,
        "primary_metric": "stop_score_total",
        "primary_metric_label": "Stop Score",
        "origins": origins,
        "depart_times": depart_times,
        "budgets": budgets,
        "seeds": seeds,
        "score_seeds": score_seeds,
        "score_seed_count": len(score_seeds),
        "stop_score_min": score_min,
        "stop_score_max": score_max,
        "dwell_minutes": dwell_minutes,
        "objective_mode": objective_mode,
        "timeout_seconds": timeout_seconds,
        "total_runs": total_runs,
        "output_tag": output_tag,
        "sensitivity_config_count": len(specs),
        "sensitivity_config_ids": [spec.config_id for spec in specs],
        "sensitivity_configurations": {
            spec.config_id: spec.snapshot() for spec in specs
        },
        "baseline": {
            "config_id": "default",
            "source": (
                "a dedicated 600-task sensitivity default shard generated "
                "once in the same queue as all OAT configurations"
            ),
            "equivalence_reference": (
                "paper/results/exp2_ablation_study/"
                "exp2_results_canonical_exp2_full_queueenv_20260725.json"
            ),
            "policy": (
                "The Experiment 2 Full result is used only for default-"
                "equivalence auditing. Runtime comparisons use the dedicated "
                "sensitivity default shard to control for current-code and "
                "queue conditions."
            ),
        },
        "scoring_semantics": {
            "version": "stop-score-v2-query-elapsed",
            "scored_stops": "unique_non_origin",
            "origin_scores": False,
            "initial_waiting_included": True,
            "effective_time": (
                "last_arrival-query_departure+dwell_per_unique_non_origin_stop"
            ),
            "budget_boundary_inclusive": True,
        },
        "execution_protocol": {
            "run_order": (
                "score_seed-origin-departure-budget-algorithm_seed-"
                "sensitivity_config"
            ),
            "parallel_execution": False,
            "planner_loading_in_elapsed_ms": False,
            "route_validation_in_elapsed_ms": False,
            "elapsed_timer": "time.perf_counter",
            "planner_instance": "single_cached_instance_per_process",
            "timeout_seconds_per_run": timeout_seconds,
        },
        "shared_config": shared_config_snapshot(),
    }


def safe_output_tag(raw: str) -> str:
    return "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in raw.strip()
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run canonical Stop Score hyperparameter sensitivity."
    )
    parser.add_argument(
        "--panel",
        choices=("oat", "interaction", "all"),
        default="oat",
    )
    parser.add_argument(
        "--configs",
        default="",
        help="Comma-separated exact sensitivity config ids.",
    )
    parser.add_argument(
        "--include-default",
        action="store_true",
        help="Run the default configuration instead of reusing canonical Exp2 Full.",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--checkpoint-every", type=int, default=10)
    parser.add_argument("--timeout-seconds", type=float, default=EXP2_TIMEOUT_SECONDS)
    parser.add_argument("--score-seed", type=int, default=EXP1_STOP_SCORE_SEED)
    parser.add_argument("--score-seeds", default="")
    parser.add_argument("--score-min", type=int, default=EXP1_STOP_SCORE_MIN)
    parser.add_argument("--score-max", type=int, default=EXP1_STOP_SCORE_MAX)
    parser.add_argument("--dwell-minutes", type=int, default=EXP1_STOP_DWELL_MINUTES)
    parser.add_argument(
        "--objective-mode",
        choices=("score_guided",),
        default="score_guided",
    )
    parser.add_argument("--origins", default="")
    parser.add_argument("--depart-times", default="")
    parser.add_argument("--budgets", default="")
    parser.add_argument("--seeds", default="")
    parser.add_argument("--output-tag", default="")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    requested = parse_csv_tokens(args.configs)
    specs = select_specs(
        panel=args.panel,
        requested_ids=requested,
        include_default=args.include_default,
    )
    if not specs:
        raise ValueError("No sensitivity configurations selected.")

    default_origins = (
        list(INTERACTION_ORIGINS) if args.panel == "interaction" else list(ORIGINS)
    )
    default_score_seeds = (
        list(INTERACTION_SCORE_SEEDS)
        if args.panel == "interaction"
        else list(DEFAULT_SCORE_SEEDS)
    )
    origins = parse_csv_tokens(args.origins) or default_origins
    depart_times = parse_csv_ints(args.depart_times) or list(DEPART_TIMES_MINUTES)
    budgets = parse_csv_ints(args.budgets) or list(CANONICAL_BUDGETS)
    seeds = parse_csv_ints(args.seeds) or [int(RANDOM_SEEDS[0])]
    score_seeds = normalize_score_seeds(
        score_seed=args.score_seed,
        score_seeds_override=(
            parse_csv_ints(args.score_seeds)
            if args.score_seeds
            else default_score_seeds
        ),
    )

    if args.output:
        output_path = args.output.resolve()
    else:
        tag = safe_output_tag(args.output_tag) or args.panel
        output_path = (
            RESULTS_BASE_DIR
            / "exp3_parameter_sensitivity"
            / f"sensitivity_results_{tag}.json"
        )

    total_runs = (
        len(specs)
        * len(origins)
        * len(depart_times)
        * len(budgets)
        * len(seeds)
        * len(score_seeds)
    )
    metadata = metadata_for_run(
        panel=args.panel,
        specs=specs,
        origins=origins,
        depart_times=depart_times,
        budgets=budgets,
        seeds=seeds,
        score_seeds=score_seeds,
        score_min=args.score_min,
        score_max=args.score_max,
        dwell_minutes=args.dwell_minutes,
        objective_mode=args.objective_mode,
        timeout_seconds=args.timeout_seconds,
        total_runs=total_runs,
        output_tag=args.output_tag,
    )

    results: list[dict[str, Any]] = []
    completed: set[tuple[str, str, int, int, int, int]] = set()
    if args.resume:
        results, loaded_keys, resume_stats = build_resume_state(
            output_path,
            row_to_key=row_to_key,
            is_compatible=is_resume_row_compatible,
        )
        completed = {
            key for key in loaded_keys if isinstance(key, tuple) and len(key) == 6
        }
        print(f"Resume: kept {len(completed)} rows; audit={resume_stats}")

    pending_runs = total_runs - len(completed)
    print("=" * 76)
    print("EXPERIMENT 3: CANONICAL HYPERPARAMETER SENSITIVITY")
    print(f"Panel: {args.panel}")
    print(f"Configs: {[spec.config_id for spec in specs]}")
    print(f"Tasks: total={total_runs}, completed={len(completed)}, pending={pending_runs}")
    print(f"Output: {output_path}")
    print("=" * 76)
    if pending_runs <= 0:
        print("Nothing to run.")
        return

    planner = load_planner()
    stop_score_maps = {
        score_seed: build_random_stop_score_map(
            planner,
            seed=score_seed,
            score_min=args.score_min,
            score_max=args.score_max,
        )
        for score_seed in score_seeds
    }

    run_index = 0
    newly_saved = 0
    started = time.perf_counter()
    interrupted = False
    try:
        for score_seed in score_seeds:
            algorithms = []
            for spec in specs:
                objective = spec.objective(
                    stop_scores=stop_score_maps[score_seed],
                    dwell_minutes=args.dwell_minutes,
                    search_mode=args.objective_mode,
                )
                algorithms.append(
                    (
                        spec,
                        spec.algorithm(
                            objective=objective,
                            timeout_seconds=args.timeout_seconds,
                        ),
                    )
                )
            for origin in origins:
                origin_code = resolve_origin(planner, origin)
                for depart_time in depart_times:
                    for budget in budgets:
                        for seed in seeds:
                            for spec, algorithm in algorithms:
                                key = run_key(
                                    config_id=spec.config_id,
                                    origin=origin,
                                    depart_time=depart_time,
                                    budget_minutes=budget,
                                    seed=seed,
                                    score_seed=score_seed,
                                )
                                if key in completed:
                                    continue
                                run_index += 1
                                print(
                                    f"[{run_index:5d}/{pending_runs}] "
                                    f"{spec.config_id:22s} | {origin:10s} | "
                                    f"dept={depart_time // 60:02d}:00 | "
                                    f"budget={budget // 60}h | score_seed={score_seed}",
                                    end="",
                                    flush=True,
                                )
                                try:
                                    row = algorithm.evaluate(
                                        planner,
                                        origin_code,
                                        depart_time,
                                        budget,
                                        seed=seed,
                                    )
                                    row.update(
                                        {
                                            "origin": origin,
                                            "origin_name": origin,
                                            "origin_code": origin_code,
                                            "score_seed": score_seed,
                                            "score_min": args.score_min,
                                            "score_max": args.score_max,
                                            "dwell_minutes": args.dwell_minutes,
                                            "objective_mode": args.objective_mode,
                                            "timeout_seconds": args.timeout_seconds,
                                            "sensitivity_config_id": spec.config_id,
                                            "sensitivity_panel": spec.panel,
                                            "sensitivity_factor": spec.factor,
                                            "sensitivity_factor_value": spec.factor_value,
                                            "sensitivity_parameters": spec.snapshot(),
                                        }
                                    )
                                    results.append(row)
                                    completed.add(key)
                                    newly_saved += 1
                                    print(
                                        f" -> {row.get('stop_score_total', 0.0):.1f}, "
                                        f"{row.get('elapsed_ms', 0.0):.1f} ms, "
                                        f"{row.get('labels', 0)} labels, "
                                        f"{row.get('termination_reason', 'completed')}"
                                    )
                                    if (
                                        args.checkpoint_every > 0
                                        and newly_saved % args.checkpoint_every == 0
                                    ):
                                        save_results(
                                            results,
                                            output_path,
                                            metadata=metadata,
                                        )
                                except Exception as error:
                                    print(f" -> ERROR: {error}")
                                    logging.exception("Sensitivity evaluation failed")
    except KeyboardInterrupt:
        interrupted = True
        print("\nInterrupted; saving checkpoint.")

    save_results(results, output_path, metadata=metadata)
    elapsed = time.perf_counter() - started
    print(
        f"Saved {len(results)}/{total_runs} rows in {elapsed:.2f}s -> {output_path}"
    )
    if interrupted:
        raise SystemExit(130)


if __name__ == "__main__":
    main()
