#!/usr/bin/env python3
"""
Experiment 2: Three-Component Search-Control Ablation on the stop-score task.

Evaluates the contribution of the three search-control components under the same
stop-score objective used in Experiment 1:
1. Two-stage Beam control (candidate and bucket width)
2. Heuristic Dominance reduction (local label filtering)
3. Negative-Score Penalty (penalty-guided down-ranking)

The task is to maximize stop-score total under a fixed budget with dwell time.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any

# Add project root to sys.path so we can import from apps and common
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper.experiments.common.config import (
    BUDGETS_MINUTES,
    DEPART_TIMES_MINUTES,
    EXP1_STOP_DWELL_MINUTES,
    EXP1_STOP_SCORE_MAX,
    EXP1_STOP_SCORE_MIN,
    EXP1_STOP_SCORE_SEED,
    EXP2_NO_PRUNING_MAX_LABELS,
    EXP2_TIMEOUT_SECONDS,
    ORIGINS,
    QUICK_BUDGETS,
    QUICK_DEPART_TIMES,
    QUICK_ORIGINS,
    RANDOM_SEEDS,
    QUICK_NUM_REPEATS,
    RESULTS_BASE_DIR,
)
import paper.experiments.common.config as experiment_config
from paper.experiments.common.io_utils import save_results
from paper.experiments.common.json_list_store import (
    build_resume_state,
)
from paper.experiments.common.planner_bridge import load_planner, resolve_origin
from paper.experiments.common.stop_scoring import StopScoringProfile, build_random_stop_score_map

# Import the base algorithm to instantiate ablation configurations
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.ours_full import OursFull

logging.basicConfig(level=logging.INFO, format="%(message)s")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)


def parse_csv_tokens(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [x.strip() for x in str(raw).split(",") if x.strip()]


def parse_csv_ints(raw: str | None) -> list[int]:
    return [int(x) for x in parse_csv_tokens(raw)]


def normalize_config_name(value: str) -> str:
    return "".join(character.lower() for character in str(value) if character.isalnum())


CONFIG_ALIASES = {
    "full": "Ours (Full)",
    "noneg": "Ours (NoNeg)",
    "nodom": "Ours (NoDom)",
    "nobeam": "Ours (NoBeam)",
    "nobeamnodom": "Ours (NoBeam-NoDom)",
    "nodomnoneg": "Ours (NoDom-NoNeg)",
    "nobeamnoneg": "Ours (NoBeam-NoNeg)",
    "nobeamnodomnoneg": "Ours (NoBeam-NoDom-NoNeg)",
}


def filter_ablation_configs(
    configs: list[OursFull], requested: list[str] | None
) -> list[OursFull]:
    tokens = [normalize_config_name(value) for value in (requested or [])]
    if not tokens:
        return configs
    expected_names = {
        normalize_config_name(CONFIG_ALIASES.get(token, token)) for token in tokens
    }
    selected = [
        config
        for config in configs
        if normalize_config_name(config.name) in expected_names
    ]
    found = {normalize_config_name(config.name) for config in selected}
    missing = sorted(expected_names - found)
    if missing:
        raise ValueError(f"Unknown ablation config filter(s): {missing}")
    return selected


def normalize_score_seeds(*, score_seed: int, score_seeds_override: list[int] | None) -> list[int]:
    if score_seeds_override:
        ordered: list[int] = []
        seen: set[int] = set()
        for value in score_seeds_override:
            safe = int(value)
            if safe in seen:
                continue
            ordered.append(safe)
            seen.add(safe)
        if ordered:
            return ordered
    return [int(score_seed)]


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {
            str(key): converted
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if (converted := _json_safe(item)) is not None
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [_json_safe(item) for item in value]
        safe = [item for item in items if item is not None]
        return sorted(safe, key=str) if isinstance(value, (set, frozenset)) else safe
    return None


def algorithm_parameter_snapshot(algo: Any) -> dict[str, Any]:
    parameters: dict[str, Any] = {
        "class": f"{algo.__class__.__module__}.{algo.__class__.__name__}",
        "name": str(algo.name),
        "category": str(getattr(algo, "category", "")),
        "stochastic": bool(getattr(algo, "stochastic", False)),
    }
    for key, value in sorted(vars(algo).items()):
        if key.startswith("_last_") or key == "objective":
            continue
        converted = _json_safe(value)
        if converted is not None:
            parameters[key] = converted
    return parameters


def shared_config_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for key in sorted(name for name in dir(experiment_config) if name.isupper()):
        converted = _json_safe(getattr(experiment_config, key))
        if converted is not None:
            snapshot[key] = converted
    return snapshot


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
    configs: list[OursFull],
    total_runs: int,
    output_tag: str,
    timeout_seconds: float,
    no_pruning_max_labels: int | None,
) -> dict[str, Any]:
    algorithm_seeds = {
        str(algo.name): [int(seed) for seed in seeds] for algo in configs
    }
    return {
        "experiment": "exp2_ablation_study",
        "quick_mode": bool(quick_mode),
        "primary_metric": "stop_score_total",
        "primary_metric_label": "Stop Score",
        "score_seeds": [int(value) for value in score_seeds],
        "score_seed_count": len(score_seeds),
        "stop_score_min": int(score_min),
        "stop_score_max": int(score_max),
        "dwell_minutes": int(dwell_minutes),
        "objective_mode": str(objective_mode),
        "origins": [str(value) for value in origins],
        "depart_times": [int(value) for value in depart_times],
        "budgets": [int(value) for value in budgets],
        "seeds": [int(value) for value in seeds],
        "seed_policy": {
            "repeat_deterministic_seeds": len(seeds) > 1,
            "deterministic_repeats": len(seeds),
            "stochastic_repeats": 0,
            "algorithm_seed_counts": {
                name: len(values) for name, values in algorithm_seeds.items()
            },
            "algorithm_seeds": algorithm_seeds,
        },
        "algorithm_parameters": {
            str(algo.name): algorithm_parameter_snapshot(algo) for algo in configs
        },
        "shared_config": shared_config_snapshot(),
        "scoring_semantics": {
            "version": "stop-score-v2-query-elapsed",
            "scored_stops": "unique_non_origin",
            "origin_scores": False,
            "initial_waiting_included": True,
            "effective_time": "last_arrival-query_departure+dwell_per_unique_non_origin_stop",
            "budget_boundary_inclusive": True,
            "empty_route_interpretation": "algorithm_failure_not_query_infeasibility",
        },
        "execution_protocol": {
            "run_order": "score_seed-origin-departure-budget-algorithm_seed-ablation_config",
            "parallel_execution": False,
            "planner_loading_in_elapsed_ms": False,
            "route_validation_in_elapsed_ms": False,
            "elapsed_timer": "time.perf_counter",
            "planner_instance": "single_cached_instance_per_process",
            "timeout_seconds_per_run": float(timeout_seconds),
            "no_pruning_max_labels": no_pruning_max_labels,
        },
        "total_runs": int(total_runs),
        "output_tag": str(output_tag),
        "ablation_config_count": len(configs),
    }


def build_ablation_configs(
    *,
    timeout_seconds: float,
    no_pruning_label_cap: int | None,
    objective: StopScoringProfile,
) -> list[OursFull]:
    configs = [
        OursFull(use_beam=True, use_dominance=True, use_negative_score=True, timeout_seconds=timeout_seconds),
        OursFull(use_beam=True, use_dominance=True, use_negative_score=False, timeout_seconds=timeout_seconds),
        OursFull(use_beam=True, use_dominance=False, use_negative_score=True, timeout_seconds=timeout_seconds),
        OursFull(use_beam=False, use_dominance=True, use_negative_score=True, timeout_seconds=timeout_seconds),
        # Isolate the joint effect of removing the two main space-control layers.
        OursFull(use_beam=False, use_dominance=False, use_negative_score=True, timeout_seconds=timeout_seconds),
        OursFull(use_beam=True, use_dominance=False, use_negative_score=False, timeout_seconds=timeout_seconds),
        OursFull(use_beam=False, use_dominance=True, use_negative_score=False, timeout_seconds=timeout_seconds),
        OursFull(
            use_beam=False,
            use_dominance=False,
            use_negative_score=False,
            timeout_seconds=timeout_seconds,
            max_labels=no_pruning_label_cap,
        ),
    ]
    for algo in configs:
        algo.objective = objective
    return configs


def run_key(
    *,
    algorithm: str,
    origin: str,
    depart_time: int,
    budget_minutes: int,
    seed: int,
    score_seed: int,
) -> tuple[str, str, int, int, int, int]:
    return (algorithm, origin, int(depart_time), int(budget_minutes), int(seed), int(score_seed))


def row_to_key(row: dict[str, Any]) -> tuple[str, str, int, int, int, int] | None:
    try:
        return run_key(
            algorithm=str(row["algorithm"]),
            origin=str(row["origin"]),
            depart_time=int(row["depart_time"]),
            budget_minutes=int(row["budget_minutes"]),
            seed=int(row["seed"]),
            score_seed=int(row["score_seed"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _is_resume_row_compatible(row: dict[str, Any]) -> bool:
    # Keep resume strict so older schema rows are recomputed instead of polluting new runs.
    required_fields = {
        "algorithm",
        "origin",
        "origin_name",
        "depart_time",
        "budget_minutes",
        "seed",
        "elapsed_ms",
        "feasible",
        "labels",
        "termination_reason",
        "stop_score_total",
        "score_seed",
        "effective_budget_feasible",
    }
    return required_fields.issubset(row.keys())


def main():
    parser = argparse.ArgumentParser(description="Run Experiment 2 (Ablation Study)")
    parser.add_argument("--quick", action="store_true", help="Run a minimal subset for testing")
    parser.add_argument("--resume", action="store_true", help="Resume from an existing results file when available")
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=10,
        help="Save partial results every N successful runs (<=0 to disable intermediate checkpoints)",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=EXP2_TIMEOUT_SECONDS,
        help="Per-run wall-clock timeout to prevent heavy ablations from hanging",
    )
    parser.add_argument(
        "--no-pruning-max-labels",
        type=int,
        default=EXP2_NO_PRUNING_MAX_LABELS,
        help="Hard label budget for the no-pruning configuration (<=0 to disable)",
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
    parser.add_argument(
        "--objective-mode",
        type=str,
        default="score_guided",
        choices=["score_guided", "legacy_balanced"],
        help="Stop-score search objective mode",
    )
    parser.add_argument("--origins", type=str, default="", help="Comma-separated origin names")
    parser.add_argument("--depart-times", type=str, default="", help="Comma-separated departure times in minutes")
    parser.add_argument("--budgets", type=str, default="", help="Comma-separated budgets in minutes")
    parser.add_argument(
        "--seeds",
        type=str,
        default="",
        help="Comma-separated algorithm seeds; defaults to only the first seed because ablation variants are deterministic",
    )
    parser.add_argument("--output-tag", type=str, default="", help="Custom suffix for result filename")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Explicit output path; useful for smoke validation outside paper results",
    )
    parser.add_argument(
        "--configs",
        type=str,
        default="",
        help=(
            "Comma-separated exact config names or aliases: full, noneg, nodom, "
            "nobeam, nobeamnodom, nodomnoneg, nobeamnoneg, "
            "nobeamnodomnoneg"
        ),
    )
    args = parser.parse_args()

    # Determine experiment scope
    origins_override = parse_csv_tokens(args.origins)
    depart_times_override = parse_csv_ints(args.depart_times)
    budgets_override = parse_csv_ints(args.budgets)
    seeds_override = parse_csv_ints(args.seeds)

    origins = list(origins_override) if origins_override else (QUICK_ORIGINS if args.quick else ORIGINS)
    depart_times = list(depart_times_override) if depart_times_override else (QUICK_DEPART_TIMES if args.quick else DEPART_TIMES_MINUTES)
    budgets = list(budgets_override) if budgets_override else (QUICK_BUDGETS if args.quick else BUDGETS_MINUTES)
    seeds = list(seeds_override) if seeds_override else [int(RANDOM_SEEDS[0])]
    score_seeds = normalize_score_seeds(
        score_seed=args.score_seed,
        score_seeds_override=parse_csv_ints(args.score_seeds),
    )

    out_dir = RESULTS_BASE_DIR / "exp2_ablation_study"
    if args.output is not None:
        out_file = args.output.resolve()
    elif args.output_tag.strip():
        safe_tag = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in args.output_tag.strip())
        out_file = out_dir / f"exp2_results_{safe_tag}.json"
    else:
        out_file = out_dir / ("exp2_results_quick.json" if args.quick else "exp2_results.json")

    print("=" * 60)
    print(" STARTING EXPERIMENT 2: Ablation Study")
    print(f" Quick Mode: {args.quick}")
    print(f" Resume Mode: {args.resume}")
    print(f" Checkpoint Every: {args.checkpoint_every if args.checkpoint_every > 0 else 'disabled'}")
    print(f" Timeout per run: {args.timeout_seconds:.1f}s")
    print(f" No-pruning max labels: {args.no_pruning_max_labels if args.no_pruning_max_labels > 0 else 'disabled'}")
    print(f" Stop Score Seeds: {score_seeds}")
    print(f" Objective Mode: {args.objective_mode}")
    print(f" Dwell Minutes: {args.dwell_minutes}")
    print("=" * 60)

    print("Loading PlannerService and GTFS Data...")
    planner = load_planner()
    print("Planner loaded successfully.\n")

    no_pruning_label_cap = args.no_pruning_max_labels if args.no_pruning_max_labels > 0 else None
    objectives = {
        stop_score_seed: StopScoringProfile(
            stop_scores=build_random_stop_score_map(
                planner,
                seed=stop_score_seed,
                score_min=args.score_min,
                score_max=args.score_max,
            ),
            dwell_minutes=args.dwell_minutes,
            search_mode=args.objective_mode,
        )
        for stop_score_seed in score_seeds
    }

    config_filter = parse_csv_tokens(args.configs)
    config_prototypes = filter_ablation_configs(
        build_ablation_configs(
            timeout_seconds=args.timeout_seconds,
            no_pruning_label_cap=no_pruning_label_cap,
            objective=next(iter(objectives.values())),
        ),
        config_filter,
    )
    config_count = len(config_prototypes)
    total_runs = config_count * len(score_seeds) * len(origins) * len(depart_times) * len(budgets) * len(seeds)
    metadata = build_experiment_metadata(
        quick_mode=args.quick,
        score_seeds=score_seeds,
        score_min=args.score_min,
        score_max=args.score_max,
        dwell_minutes=args.dwell_minutes,
        objective_mode=args.objective_mode,
        origins=origins,
        depart_times=depart_times,
        budgets=budgets,
        seeds=seeds,
        configs=config_prototypes,
        total_runs=total_runs,
        output_tag=args.output_tag.strip(),
        timeout_seconds=args.timeout_seconds,
        no_pruning_max_labels=no_pruning_label_cap,
    )

    results: list[dict[str, Any]] = []
    completed: set[tuple[str, str, int, int, int, int]] = set()
    if args.resume:
        results, completed_raw, resume_stats = build_resume_state(
            out_file,
            row_to_key=row_to_key,
            is_compatible=_is_resume_row_compatible,
        )
        completed = {key for key in completed_raw if isinstance(key, tuple)}
        if completed:
            print(f"Loaded {len(completed)} completed runs from {out_file}")
        dropped = (
            resume_stats["dropped_malformed"]
            + resume_stats["dropped_incompatible"]
            + resume_stats["dropped_duplicate"]
        )
        if dropped:
            print(
                "[resume] ignored rows: "
                f"malformed={resume_stats['dropped_malformed']}, "
                f"incompatible={resume_stats['dropped_incompatible']}, "
                f"duplicate={resume_stats['dropped_duplicate']}"
            )

    pending_runs = max(0, total_runs - len(completed))
    print(f"Total Configurations to Evaluate: {total_runs}")
    print(f"Already Completed (resume): {len(completed)}")
    print(f"Pending This Run: {pending_runs}")
    print("-" * 60)
    if pending_runs == 0:
        print("Nothing to run. Existing results already cover all combinations.")
        return

    run_idx = 1
    newly_saved = 0
    interrupted = False
    t_start = time.perf_counter()

    try:
        for stop_score_seed in score_seeds:
            configs = build_ablation_configs(
                timeout_seconds=args.timeout_seconds,
                no_pruning_label_cap=no_pruning_label_cap,
                objective=objectives[stop_score_seed],
            )
            configs = filter_ablation_configs(configs, config_filter)

            for origin in origins:
                try:
                    origin_code = resolve_origin(planner, origin)
                except ValueError as e:
                    print(f"[!] Skipping {origin}: {e}")
                    continue

                for dtime in depart_times:
                    for budget in budgets:
                        for seed in seeds:
                            for algo in configs:
                                key = run_key(
                                    algorithm=algo.name,
                                    origin=origin,
                                    depart_time=dtime,
                                    budget_minutes=budget,
                                    seed=seed,
                                    score_seed=stop_score_seed,
                                )
                                if key in completed:
                                    continue

                                desc = (
                                    f"[{run_idx:4d}/{pending_runs}] "
                                    f"{algo.name:25s} | {origin:10s} | "
                                    f"dept={dtime//60:02d}:00 | budget={budget//60}h | "
                                    f"score_seed={stop_score_seed}"
                                )
                                print(desc, end="", flush=True)

                                try:
                                    res = algo.evaluate(
                                        planner,
                                        origin_code,
                                        dtime,
                                        budget,
                                        seed=seed,
                                    )
                                    res["origin"] = origin
                                    res["origin_name"] = origin
                                    res["origin_code"] = origin_code
                                    res["timeout_seconds"] = args.timeout_seconds
                                    res["max_labels_cap"] = getattr(algo, "max_labels", None)
                                    res["score_seed"] = int(stop_score_seed)
                                    res["score_min"] = int(args.score_min)
                                    res["score_max"] = int(args.score_max)
                                    res["dwell_minutes"] = int(args.dwell_minutes)
                                    res["objective_mode"] = str(args.objective_mode)

                                    results.append(res)
                                    completed.add(key)
                                    newly_saved += 1
                                    term = res.get("termination_reason", "completed")
                                    term_suffix = "" if term == "completed" else f", term={term}"
                                    print(
                                        f" -> OK ({res.get('stop_score_total', 0.0):.1f} score, "
                                        f"{res['elapsed_ms']:.1f} ms, {res.get('labels', 0)} labels{term_suffix})"
                                    )

                                    if args.checkpoint_every > 0 and (newly_saved % args.checkpoint_every == 0):
                                        save_results(results, out_file, metadata=metadata)
                                        print(f"    [checkpoint] saved {len(results)} rows -> {out_file}")
                                except Exception as e:
                                    print(f" -> ERROR: {e}")
                                    logging.exception("Evaluation failed")

                                run_idx += 1
    except KeyboardInterrupt:
        interrupted = True
        print("\n[!] Interrupted by user. Saving partial results...")

    t_end = time.perf_counter()
    print("-" * 60)
    elapsed = t_end - t_start
    if interrupted:
        print(f"Run interrupted after {elapsed:.2f} seconds.")
    else:
        print(f"All runs completed in {elapsed:.2f} seconds.")

    # Save Results
    save_results(results, out_file, metadata=metadata)

    print(f"Results saved to {out_file}")
    print("=" * 60)
    if interrupted:
        print("Stopped early. Partial results are preserved.")
        sys.exit(130)
    print("Done!")


if __name__ == "__main__":
    main()
