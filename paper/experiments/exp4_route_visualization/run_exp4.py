#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
APP_API_DIR = PROJECT_ROOT / "apps" / "api"
if str(APP_API_DIR) not in sys.path:
    sys.path.insert(0, str(APP_API_DIR))

from paper.experiments.algorithms import build_all_algorithms
from paper.experiments.common.config import (
    EXP1_STOP_DWELL_MINUTES,
    EXP1_STOP_SCORE_MAX,
    EXP1_STOP_SCORE_MIN,
    SCORE_WEIGHTS,
)
from paper.experiments.common.planner_bridge import load_planner
from paper.experiments.common.stop_scoring import StopScoringProfile, build_random_stop_score_map
from paper.experiments.common.utils import composite_score, compute_route_metrics
from paper.experiments.exp4_route_visualization.exp4_common import (
    DISPLAY_NAME_BY_KEY,
    EXP1_ALGO_NAME_BY_KEY,
    EXP1_RESULTS_PATH,
    EXP4_CASES_PATH,
    EXP4_ROUTES_DIR,
    Exp4Case,
    load_manifest,
    save_json,
    select_representative_cases,
    trip_edges_to_route_dict,
)


def parse_csv_tokens(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [x.strip() for x in str(raw).split(",") if x.strip()]


def make_exp1_algorithm(algo_key: str, *, objective: StopScoringProfile) -> Any:
    target_name = EXP1_ALGO_NAME_BY_KEY[algo_key]
    for algo in build_all_algorithms(objective=objective):
        if str(algo.name) == target_name:
            return algo
    raise ValueError(f"Could not build Exp1 algorithm for key={algo_key}")


def invalid_metrics(*, violation_reason: str, objective: StopScoringProfile) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "ride_minutes": 0,
        "distance_km": 0.0,
        "unique_stops": 0,
        "legs": 0,
        "hull_area": 0.0,
        "quadrant_coverage": 0,
        "total_time_minutes": 0,
        "composite_score": 0.0,
        "feasible": False,
        "violation_reason": str(violation_reason),
    }
    metrics.update(objective.zero_metrics())
    return metrics


def evaluate_exp1_case(
    *,
    case: Exp4Case,
    algo_key: str,
    planner: Any,
    objective: StopScoringProfile,
) -> tuple[dict[str, Any], list[Any]]:
    algo = make_exp1_algorithm(algo_key, objective=objective)
    t0 = time.perf_counter()
    path_edges = algo.solve(
        planner,
        case.origin_code,
        case.depart_time,
        case.budget_minutes,
        seed=case.seed,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    feasible, violation_reason = algo._validate_path_edges(
        path_edges=path_edges,
        planner=planner,
        origin=case.origin_code,
        depart_time=case.depart_time,
        budget_minutes=case.budget_minutes,
    )
    if not feasible:
        metrics = invalid_metrics(violation_reason=violation_reason, objective=objective)
        return (
            {
                "algorithm_key": algo_key,
                "algorithm_name": DISPLAY_NAME_BY_KEY[algo_key],
                "elapsed_ms": round(elapsed_ms, 3),
                "feasible": False,
                "violation_reason": str(violation_reason),
                "primary_metric_name": "stop_score_total",
                "primary_metric_label": "Stop Score",
                "primary_metric_value": 0.0,
                "metrics": metrics,
            },
            [],
        )

    metrics = compute_route_metrics(path_edges, planner)
    metrics["composite_score"] = composite_score(metrics, SCORE_WEIGHTS)
    metrics["feasible"] = True
    metrics["violation_reason"] = ""
    metrics.update(objective.metrics_from_edges(path_edges, budget_minutes=case.budget_minutes))
    if metrics.get("effective_budget_feasible") is False:
        metrics = invalid_metrics(violation_reason="effective_budget_exceeded", objective=objective)
        return (
            {
                "algorithm_key": algo_key,
                "algorithm_name": DISPLAY_NAME_BY_KEY[algo_key],
                "elapsed_ms": round(elapsed_ms, 3),
                "feasible": False,
                "violation_reason": "effective_budget_exceeded",
                "primary_metric_name": "stop_score_total",
                "primary_metric_label": "Stop Score",
                "primary_metric_value": 0.0,
                "metrics": metrics,
            },
            [],
        )

    source_payload = {
        "algorithm_key": algo_key,
        "algorithm_name": DISPLAY_NAME_BY_KEY[algo_key],
        "elapsed_ms": round(elapsed_ms, 3),
        "feasible": True,
        "violation_reason": "",
        "primary_metric_name": "stop_score_total",
        "primary_metric_label": "Stop Score",
        "primary_metric_value": float(metrics.get("stop_score_total", 0.0)),
        "metrics": metrics,
    }
    return source_payload, path_edges


def run_case(
    *,
    case: Exp4Case,
    planner: Any,
    objective: StopScoringProfile,
    algorithm_keys: list[str],
    run_idx: int,
    total_runs: int,
) -> tuple[dict[str, Any], int]:
    record = case.to_dict()
    artifacts: list[dict[str, Any]] = []
    for algo_key in algorithm_keys:
        desc = (
            f"[{run_idx}/{total_runs}] {DISPLAY_NAME_BY_KEY[algo_key]:<11} | "
            f"case={case.id:<31} | origin={case.origin_name:<10} | "
            f"depart={case.depart_time // 60:02d}:{case.depart_time % 60:02d} | "
            f"budget={case.budget_minutes // 60}h | score_seed={case.score_seed} | seed={case.seed}"
        )
        print(desc, end="", flush=True)
        try:
            source_payload, path_edges = evaluate_exp1_case(
                case=case,
                algo_key=algo_key,
                planner=planner,
                objective=objective,
            )
            route_json_path = None
            if source_payload["feasible"] and path_edges:
                route_payload = trip_edges_to_route_dict(
                    case=case,
                    algorithm_key=algo_key,
                    algorithm_name=source_payload["algorithm_name"],
                    path_edges=path_edges,
                    planner=planner,
                    metrics=source_payload["metrics"],
                    source_payload=source_payload,
                )
                route_json_path = EXP4_ROUTES_DIR / f"{case.id}__{algo_key}.json"
                save_json(route_json_path, route_payload)

            metrics = source_payload["metrics"]
            artifacts.append(
                {
                    "algorithm_key": algo_key,
                    "algorithm_name": source_payload["algorithm_name"],
                    "elapsed_ms": source_payload["elapsed_ms"],
                    "feasible": source_payload["feasible"],
                    "violation_reason": source_payload["violation_reason"],
                    "primary_metric_name": source_payload["primary_metric_name"],
                    "primary_metric_label": source_payload["primary_metric_label"],
                    "primary_metric_value": source_payload["primary_metric_value"],
                    "route_json_path": str(route_json_path) if route_json_path else "",
                    "summary_metrics": {
                        "stop_score_total": float(metrics.get("stop_score_total", 0.0)),
                        "score_per_hour": float(metrics.get("score_per_hour", 0.0)),
                        "effective_time_minutes": float(metrics.get("effective_time_minutes", 0.0)),
                        "ride_minutes": float(metrics.get("ride_minutes", 0.0)),
                        "unique_stops": float(metrics.get("unique_stops", 0.0)),
                        "scored_stop_count": float(metrics.get("scored_stop_count", 0.0)),
                        "transfers": float(metrics.get("transfers", max(0, int(metrics.get("legs", 0)) - 1))),
                        "hull_area": float(metrics.get("hull_area", 0.0)),
                    },
                }
            )
            print(
                f" -> OK ({source_payload['elapsed_ms']:.1f} ms, "
                f"score={float(source_payload['primary_metric_value']):.1f}, "
                f"feasible={source_payload['feasible']})"
            )
        except Exception as exc:
            print(f" -> ERROR: {exc}")
            raise
        run_idx += 1
    record["artifacts"] = artifacts
    return record, run_idx


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Experiment 4 qualitative case-study pipeline.")
    parser.add_argument("--case-ids", type=str, default="", help="Optional comma-separated subset of case ids.")
    parser.add_argument(
        "--algorithms",
        type=str,
        default="",
        help="Optional comma-separated algorithm subset. Defaults to each case's own algorithm list.",
    )
    parser.add_argument("--select-only", action="store_true", help="Only select and save case metadata without rerunning routes.")
    args = parser.parse_args()

    selected_cases = select_representative_cases()
    selected_case_ids = set(parse_csv_tokens(args.case_ids)) if args.case_ids else set()
    if selected_case_ids:
        selected_cases = [case for case in selected_cases if case.id in selected_case_ids]

    requested_algorithms = parse_csv_tokens(args.algorithms)
    allowed_algorithms = set(EXP1_ALGO_NAME_BY_KEY.keys())
    unknown = [key for key in requested_algorithms if key not in allowed_algorithms]
    if unknown:
        raise ValueError(f"Unknown algorithms: {unknown}. Allowed: {sorted(allowed_algorithms)}")

    base_manifest: dict[str, Any] = {
        "experiment": "exp4_route_visualization",
        "positioning": "case-based qualitative visualization study for the score-guided main task",
        "generated_from": {
            "exp1_results": str(EXP1_RESULTS_PATH.relative_to(PROJECT_ROOT)),
            "exp3_results": "paper/results/exp3_parameter_sensitivity/exp3_results.json",
            "primary_metric": "stop_score_total",
            "runtime_metric": "elapsed_ms",
            "selection_note": "Cases are chosen from Exp1/Exp3 main-task results, not from the legacy multi-objective scenario experiment.",
        },
        "cases": [case.to_dict() for case in selected_cases],
    }

    if args.select_only:
        save_json(EXP4_CASES_PATH, base_manifest)
        print(f"Saved Exp4 case manifest: {EXP4_CASES_PATH}")
        return

    total_runs = 0
    case_algorithm_map: dict[str, list[str]] = {}
    for case in selected_cases:
        allowed = list(case.algorithms)
        chosen = [algo for algo in allowed if not requested_algorithms or algo in requested_algorithms]
        case_algorithm_map[case.id] = chosen
        total_runs += len(chosen)

    print(f"Total Runs: {total_runs}")
    print(f"Selected Cases: {len(selected_cases)}")
    print("-" * 60)
    if total_runs == 0:
        print("Nothing to run. No algorithm-case combinations selected.")
        return

    planner = load_planner()
    objective_cache: dict[int, StopScoringProfile] = {}
    for case in selected_cases:
        if int(case.score_seed) in objective_cache:
            continue
        objective_cache[int(case.score_seed)] = StopScoringProfile(
            stop_scores=build_random_stop_score_map(
                planner,
                seed=int(case.score_seed),
                score_min=EXP1_STOP_SCORE_MIN,
                score_max=EXP1_STOP_SCORE_MAX,
            ),
            dwell_minutes=EXP1_STOP_DWELL_MINUTES,
            search_mode="score_guided",
        )

    existing_cases_by_id: dict[str, dict[str, Any]] = {}
    if EXP4_CASES_PATH.exists():
        try:
            existing_manifest = load_manifest(EXP4_CASES_PATH)
            existing_cases_by_id = {
                str(case["id"]): case
                for case in existing_manifest.get("cases", [])
                if isinstance(case, dict) and "id" in case
            }
        except Exception:
            existing_cases_by_id = {}

    case_records: list[dict[str, Any]] = []
    run_idx = 1
    t0 = time.perf_counter()
    for case in selected_cases:
        chosen_algorithms = case_algorithm_map[case.id]
        case_record, run_idx = run_case(
            case=case,
            planner=planner,
            objective=objective_cache[int(case.score_seed)],
            algorithm_keys=chosen_algorithms,
            run_idx=run_idx,
            total_runs=total_runs,
        )
        case_records.append(case_record)

    merged_cases_by_id = dict(existing_cases_by_id)
    for case in case_records:
        merged_cases_by_id[str(case["id"])] = case
    ordered_ids = [str(case["id"]) for case in base_manifest["cases"]]
    merged_cases = [merged_cases_by_id[case_id] for case_id in ordered_ids if case_id in merged_cases_by_id]
    base_manifest["cases"] = merged_cases
    save_json(EXP4_CASES_PATH, base_manifest)
    elapsed = time.perf_counter() - t0
    print("-" * 60)
    print(f"Saved Exp4 artifacts manifest: {EXP4_CASES_PATH}")
    print(f"Wall-clock time: {elapsed / 60.0:.2f} min")


if __name__ == "__main__":
    main()
