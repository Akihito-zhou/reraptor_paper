#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
APP_API_DIR = PROJECT_ROOT / "apps" / "api"
if str(APP_API_DIR) not in sys.path:
    sys.path.insert(0, str(APP_API_DIR))

from paper.experiments.common.config import EXP2_TIMEOUT_SECONDS, RESULTS_BASE_DIR
from paper.experiments.common.planner_bridge import load_planner
from paper.experiments.common.utils import compute_route_metrics
from paper.experiments.exp2_ablation_study.project_theme_support import (
    ProjectThemeChallenge,
    build_project_theme_challenges,
    evaluate_project_theme_route,
)
from paper.experiments.exp2_ablation_study.run_exp2_supporting import (
    NEGATIVE_PRESSURE_PRESETS,
    make_algorithm,
)
from paper.experiments.exp4_route_visualization.exp4_common import Exp4Case, save_json, trip_edges_to_route_dict


RESULTS_PATH = RESULTS_BASE_DIR / "exp2_ablation_study" / "exp2_supporting_results.json"
ROUTE_RESULTS_DIR = RESULTS_BASE_DIR / "exp2_ablation_study" / "supporting_routes"
MANIFEST_PATH = RESULTS_BASE_DIR / "exp2_ablation_study" / "exp2_supporting_route_cases.json"


@dataclass(frozen=True)
class RouteCaseSpec:
    case_id: str
    title: str
    theme_name: str
    origin_code: str
    depart_time: int
    budget_minutes: int
    seed: int
    pressure_name: str
    qualitative_focus: str
    selection_reason: str


DEFAULT_ROUTE_CASES: tuple[RouteCaseSpec, ...] = (
    RouteCaseSpec(
        case_id="support_century_ride_proven_theme",
        title="Supporting Case: Century-Ride Proven Theme",
        theme_name="century-ride",
        origin_code="676888",
        depart_time=840,
        budget_minutes=480,
        seed=2,
        pressure_name="default",
        qualitative_focus="Compare how negative pruning firmly adheres to a sparse theme and explicitly outscores unconstrained search via long 16-leg sweeps.",
        selection_reason="Selected from formal supporting results as a century-ride case where Full solidly outscores NoNeg in ride-minutes without degenerate back-tracking.",
    ),
    RouteCaseSpec(
        case_id="support_random_subset_abundant_theme",
        title="Supporting Case: Random-Subset Abundant Theme",
        theme_name="random-subset",
        origin_code="675464",
        depart_time=840,
        budget_minutes=240,
        seed=0,
        pressure_name="default",
        qualitative_focus="Inspect an abundant route-theme query where negative pruning natively aligns with the random available subsets.",
        selection_reason="Selected from formal supporting results as a strong random-subset case with massive spatial exploration for Full.",
    ),
)


def _load_rows(path: Path) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise ValueError(f"Unexpected results payload: {path}")
    return rows


def _row_lookup(rows: list[dict[str, Any]]) -> dict[tuple[str, str, int, int, int, str, str], dict[str, Any]]:
    out: dict[tuple[str, str, int, int, int, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (
            str(row.get("theme_name", "")),
            str(row.get("origin_code", "")),
            int(row.get("depart_time", 0)),
            int(row.get("budget_minutes", 0)),
            int(row.get("seed", 0)),
            str(row.get("pressure_name", "")),
            str(row.get("algorithm", "")),
        )
        out[key] = row
    return out


def _lookup_row(
    lookup: dict[tuple[str, str, int, int, int, str, str], dict[str, Any]],
    *,
    spec: RouteCaseSpec,
    algorithm_name: str,
) -> dict[str, Any]:
    key = (
        spec.theme_name,
        spec.origin_code,
        int(spec.depart_time),
        int(spec.budget_minutes),
        int(spec.seed),
        spec.pressure_name,
        algorithm_name,
    )
    if key not in lookup:
        raise KeyError(f"Formal supporting row not found for {key}")
    return lookup[key]


def _build_case(
    *,
    spec: RouteCaseSpec,
    planner: Any,
) -> Exp4Case:
    station = planner.stations.get(spec.origin_code)
    origin_name = str(getattr(station, "name", spec.origin_code) or spec.origin_code)
    return Exp4Case(
        id=spec.case_id,
        title=spec.title,
        family="exp2-supporting",
        source_exp="exp2",
        scenario=spec.theme_name,
        paper_role="support_case",
        paper_group="appendix",
        origin_name=origin_name,
        origin_code=spec.origin_code,
        depart_time=int(spec.depart_time),
        budget_minutes=int(spec.budget_minutes),
        score_seed=0,
        seed=int(spec.seed),
        primary_metric="ride_minutes",
        primary_label="RideMinutes",
        selection_reason=spec.selection_reason,
        qualitative_focus=spec.qualitative_focus,
        algorithms=("full", "no_neg"),
        selection_evidence={},
    )


def _export_case(
    *,
    spec: RouteCaseSpec,
    planner: Any,
    challenge: ProjectThemeChallenge,
    reference_rows: dict[tuple[str, str, int, int, int, str, str], dict[str, Any]],
) -> dict[str, Any]:
    case = _build_case(spec=spec, planner=planner)
    pressure = NEGATIVE_PRESSURE_PRESETS[spec.pressure_name]
    artifacts: list[dict[str, Any]] = []

    for algo_key, algo_name in [("full", "Ours (Full)"), ("no_neg", "Ours (NoNeg)")]:
        ref_row = _lookup_row(reference_rows, spec=spec, algorithm_name=algo_name)
        algo = make_algorithm(
            planner=planner,
            algo_key=algo_key,
            objective=None,
            timeout_seconds_main=EXP2_TIMEOUT_SECONDS,
            timeout_seconds_beam=EXP2_TIMEOUT_SECONDS,
            for_experiment="negative_project_theme_alignment",
            theme_profile=None,
            project_challenge=challenge,
            beam_width=pressure.beam_width,
            candidate_cap_short=pressure.candidate_cap_short,
            candidate_cap_long=pressure.candidate_cap_long,
        )
        t0 = time.perf_counter()
        path_edges = algo.solve(
            planner,
            spec.origin_code,
            spec.depart_time,
            spec.budget_minutes,
            seed=spec.seed,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        feasible, violation_reason = algo._validate_path_edges(
            path_edges=path_edges,
            planner=planner,
            origin=spec.origin_code,
            depart_time=spec.depart_time,
            budget_minutes=spec.budget_minutes,
        )
        path_edges = path_edges if feasible else []
        route_metrics = compute_route_metrics(path_edges, planner)
        theme_metrics = evaluate_project_theme_route(
            path_edges=path_edges,
            challenge=challenge,
            planner=planner,
            start_mode=str(ref_row.get("start_mode", "mixed_route_start") or "mixed_route_start"),
        )
        source_payload = {
            "algorithm_key": algo_key,
            "algorithm_name": algo_name,
            "elapsed_ms": round(elapsed_ms, 3),
            "feasible": bool(feasible),
            "violation_reason": "" if feasible else str(violation_reason or ""),
            "primary_metric_name": "ride_minutes",
            "primary_metric_label": "RideMinutes",
            "primary_metric_value": float(theme_metrics.get("primary_objective_total", 0.0) or 0.0),
        }
        merged_metrics = {
            **route_metrics,
            "theme_hit_ratio": float(theme_metrics.get("theme_hit_ratio", 0.0) or 0.0),
            "theme_score_total": float(theme_metrics.get("theme_score_total", 0.0) or 0.0),
            "theme_satisfied": bool(theme_metrics.get("theme_satisfied", False)),
            "off_theme_score_share": float(theme_metrics.get("off_theme_score_share", 0.0) or 0.0),
            "elapsed_ms": round(elapsed_ms, 3),
            "labels": int(getattr(algo, "_last_labels_count", 0)),
            "termination_reason": str(getattr(algo, "_last_termination_reason", "completed")),
            "theme_name": spec.theme_name,
            "pressure_name": spec.pressure_name,
        }
        route_payload = trip_edges_to_route_dict(
            case=case,
            algorithm_key=algo_key,
            algorithm_name=algo_name,
            path_edges=path_edges,
            planner=planner,
            metrics=merged_metrics,
            source_payload=source_payload,
        )
        route_payload["exp2_supporting"] = {
            "theme_name": spec.theme_name,
            "pressure_name": spec.pressure_name,
            "reference_row": ref_row,
            "theme_metrics": theme_metrics,
        }
        route_json_path = ROUTE_RESULTS_DIR / f"{spec.case_id}__{algo_key}.json"
        save_json(route_json_path, route_payload)
        artifacts.append(
            {
                "algorithm_key": algo_key,
                "algorithm_name": algo_name,
                "route_json_path": str(route_json_path),
                "elapsed_ms": round(elapsed_ms, 3),
                "feasible": bool(feasible),
                "violation_reason": "" if feasible else str(violation_reason or ""),
                "theme_hit_ratio": float(theme_metrics.get("theme_hit_ratio", 0.0) or 0.0),
                "theme_satisfied": bool(theme_metrics.get("theme_satisfied", False)),
                "ride_minutes": float(theme_metrics.get("primary_objective_total", 0.0) or 0.0),
                "labels": int(getattr(algo, "_last_labels_count", 0)),
                "termination_reason": str(getattr(algo, "_last_termination_reason", "completed")),
            }
        )

    return {
        "id": case.id,
        "title": case.title,
        "theme_name": spec.theme_name,
        "origin_code": spec.origin_code,
        "origin_name": case.origin_name,
        "depart_time": spec.depart_time,
        "budget_minutes": spec.budget_minutes,
        "seed": spec.seed,
        "pressure_name": spec.pressure_name,
        "selection_reason": spec.selection_reason,
        "qualitative_focus": spec.qualitative_focus,
        "artifacts": artifacts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export representative Exp2 supporting route cases.")
    parser.add_argument("--results", type=Path, default=RESULTS_PATH, help="Supporting results JSON to use for reference metadata.")
    args = parser.parse_args()

    rows = _load_rows(args.results)
    lookup = _row_lookup(rows)
    planner = load_planner()
    challenge_by_name = {challenge.challenge_id: challenge for challenge in build_project_theme_challenges(planner, quick=False)}

    manifest = {
        "experiment": "exp2_supporting_route_cases",
        "source_results": str(args.results),
        "cases": [],
    }
    for spec in DEFAULT_ROUTE_CASES:
        challenge = challenge_by_name.get(spec.theme_name)
        if challenge is None:
            raise KeyError(f"Project challenge not found: {spec.theme_name}")
        record = _export_case(
            spec=spec,
            planner=planner,
            challenge=challenge,
            reference_rows=lookup,
        )
        manifest["cases"].append(record)
        print(f"Exported: {record['id']}")

    save_json(MANIFEST_PATH, manifest)
    print(f"Saved manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
