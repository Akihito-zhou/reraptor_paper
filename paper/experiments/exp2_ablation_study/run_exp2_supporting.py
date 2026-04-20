#!/usr/bin/env python3
"""
Experiment 2 supporting studies.

Focused studies:
1. beam_tail_risk
2. negative_project_theme_alignment

The negative-pruning study is aligned to the real project theme-first route
generation logic. It focuses on route-theme challenges where removing theme
penalties can let beam search drift off-theme.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper.experiments.algorithms.ours_full import OursFull
from paper.experiments.common.config import (
    BEAM_WIDTH,
    BUDGETS_MINUTES,
    EXP1_STOP_DWELL_MINUTES,
    EXP1_STOP_SCORE_MAX,
    EXP1_STOP_SCORE_MIN,
    EXP1_STOP_SCORE_SEED,
    EXP2_TIMEOUT_SECONDS,
    QUICK_DEPART_TIMES,
    QUICK_NUM_REPEATS,
    QUICK_ORIGINS,
    RANDOM_SEEDS,
    RESULTS_BASE_DIR,
)
from paper.experiments.common.json_list_store import build_resume_state, save_json_rows_atomic
from paper.experiments.common.planner_bridge import load_planner, resolve_origin
from paper.experiments.common.stop_scoring import StopScoringProfile, build_random_stop_score_map
from paper.experiments.exp2_ablation_study.project_theme_support import (
    ProjectThemeChallenge,
    build_project_theme_challenges,
    evaluate_project_theme_route,
    make_project_theme_accept_fn,
    make_project_theme_dominance_fn,
    make_project_theme_score_fn,
    sample_project_theme_starts,
)


THEME_TOKEN_MAP: dict[str, list[str]] = {
    "coastal_keyword": ["\u6d5c", "\u6e2f", "\u6d77", "\u6e7e", "\u30de\u30ea\u30f3"],
    "mountain_keyword": ["\u5c71", "\u5c71\u4e18", "\u5742", "\u5cb3", "\u30d2\u30eb"],
    "shrine_keyword": ["\u795e\u793e", "\u5bae", "\u5929\u6e80\u5bae", "\u516b\u5e61"],
    "park_keyword": ["\u516c\u5712", "\u30d1\u30fc\u30af", "\u7dd1\u5730", "\u690d\u7269\u5712"],
    "university_keyword": ["\u5927\u5b66", "\u5b66\u5712", "\u30ad\u30e3\u30f3\u30d1\u30b9", "\u4e5d\u5927"],
}

DEFAULT_CANDIDATE_CAP_SHORT = 30
DEFAULT_CANDIDATE_CAP_LONG = 20


@dataclass(frozen=True)
class ThemeProfile:
    name: str
    target_stops: frozenset[str]
    min_ratio: float
    penalty_weight: float
    bonus_per_hit: float
    min_stops_apply: int


@dataclass(frozen=True)
class PressurePreset:
    name: str
    beam_width: int
    candidate_cap_short: int | None
    candidate_cap_long: int | None


@dataclass(frozen=True)
class RunTask:
    experiment: str
    algo_key: str
    origin: str
    depart_time: int
    budget_minutes: int
    seed: int
    score_seed: int
    theme_name: str = "none"
    start_mode: str = ""
    pressure_name: str = "default"
    beam_width: int = BEAM_WIDTH
    candidate_cap_short: int | None = DEFAULT_CANDIDATE_CAP_SHORT
    candidate_cap_long: int | None = DEFAULT_CANDIDATE_CAP_LONG


NEGATIVE_PRESSURE_PRESETS: dict[str, PressurePreset] = {
    "relaxed": PressurePreset("relaxed", beam_width=80, candidate_cap_short=45, candidate_cap_long=30),
    "default": PressurePreset(
        "default",
        beam_width=int(BEAM_WIDTH),
        candidate_cap_short=DEFAULT_CANDIDATE_CAP_SHORT,
        candidate_cap_long=DEFAULT_CANDIDATE_CAP_LONG,
    ),
    "tight": PressurePreset("tight", beam_width=24, candidate_cap_short=12, candidate_cap_long=8),
    "very_tight": PressurePreset("very_tight", beam_width=12, candidate_cap_short=8, candidate_cap_long=6),
}


def parse_csv_tokens(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [x.strip() for x in str(raw).split(",") if x.strip()]


def parse_csv_ints(raw: str | None) -> list[int]:
    return [int(x) for x in parse_csv_tokens(raw)]


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


def parse_experiment_list(raw: str) -> list[str]:
    allowed = {"beam_tail_risk", "negative_project_theme_alignment"}
    selected = [item.strip() for item in raw.split(",") if item.strip()]
    if not selected:
        return ["beam_tail_risk", "negative_project_theme_alignment"]
    unknown = [item for item in selected if item not in allowed]
    if unknown:
        raise ValueError(f"Unknown experiment(s): {unknown}. Allowed: {sorted(allowed)}")
    return selected


def parse_negative_pressure_levels(raw: str | None) -> list[PressurePreset]:
    selected = parse_csv_tokens(raw)
    if not selected:
        selected = ["default", "tight"]
    unknown = [item for item in selected if item not in NEGATIVE_PRESSURE_PRESETS]
    if unknown:
        raise ValueError(
            f"Unknown negative-pressure level(s): {unknown}. Allowed: {sorted(NEGATIVE_PRESSURE_PRESETS)}"
        )
    return [NEGATIVE_PRESSURE_PRESETS[item] for item in selected]


def run_key(
    *,
    experiment: str,
    algorithm: str,
    theme_name: str,
    pressure_name: str,
    origin: str,
    depart_time: int,
    budget_minutes: int,
    seed: int,
    score_seed: int,
) -> tuple[str, str, str, str, str, int, int, int, int]:
    return (
        experiment,
        algorithm,
        theme_name,
        pressure_name,
        origin,
        int(depart_time),
        int(budget_minutes),
        int(seed),
        int(score_seed),
    )


def row_to_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, int, int, int, int] | None:
    try:
        return run_key(
            experiment=str(row["experiment"]),
            algorithm=str(row["algorithm"]),
            theme_name=str(row.get("theme_name", "none")),
            pressure_name=str(row["pressure_name"]),
            origin=str(row["origin"]),
            depart_time=int(row["depart_time"]),
            budget_minutes=int(row["budget_minutes"]),
            seed=int(row["seed"]),
            score_seed=int(row["score_seed"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _is_resume_row_compatible(row: dict[str, Any]) -> bool:
    required = {
        "experiment",
        "algorithm",
        "origin",
        "depart_time",
        "budget_minutes",
        "seed",
        "score_seed",
        "elapsed_ms",
        "feasible",
        "pressure_name",
    }
    return required.issubset(row.keys())


def _route_health_metrics(path_edges: list[Any]) -> dict[str, Any]:
    if not path_edges:
        return {"waiting_ratio": 0.0, "revisit_ratio": 0.0, "backtrack_count": 0, "route_hash": ""}

    stop_seq: list[str] = [str(path_edges[0].from_code)]
    for edge in path_edges:
        stop_seq.append(str(edge.to_code))
    total_time = max(0, int(path_edges[-1].arrive) - int(path_edges[0].depart))
    ride_minutes = sum(max(0, int(edge.arrive) - int(edge.depart)) for edge in path_edges)
    waiting = max(0, total_time - ride_minutes)
    stop_counts = Counter(stop_seq)
    backtrack_count = 0
    for idx in range(1, len(path_edges)):
        if str(path_edges[idx].to_code) == str(path_edges[idx - 1].from_code):
            backtrack_count += 1
    signature = "->".join(stop_seq)
    return {
        "waiting_ratio": round((waiting / total_time) if total_time > 0 else 0.0, 6),
        "revisit_ratio": round(((len(stop_seq) - len(stop_counts)) / len(stop_seq)) if stop_seq else 0.0, 6),
        "backtrack_count": int(backtrack_count),
        "route_hash": hashlib.sha1(signature.encode("utf-8")).hexdigest()[:12],
    }


def _unique_scored_stop_codes(path_edges: list[Any]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for edge in path_edges:
        code = str(edge.to_code)
        if code in seen:
            continue
        seen.add(code)
        ordered.append(code)
    return ordered


def _mean_top(values: list[float], count: int) -> float:
    if not values or count <= 0:
        return 0.0
    safe = min(len(values), int(count))
    if safe <= 0:
        return 0.0
    ordered = sorted((float(v) for v in values), reverse=True)[:safe]
    return float(sum(ordered) / safe)


def _task_condition_metrics(
    *,
    objective: StopScoringProfile,
    theme_profile: ThemeProfile | None,
    budget_minutes: int,
) -> dict[str, float | int | str]:
    all_scores = {str(code): float(score) for code, score in objective.stop_scores.items()}
    if theme_profile is None or not all_scores:
        return {
            "theme_required_ratio": 0.0,
            "theme_min_stops_apply": 0,
            "theme_target_size": 0,
            "theme_density": 0.0,
            "theme_score_mass_share_all": 0.0,
            "top20_theme_share": 0.0,
            "top10_theme_score_mean": 0.0,
            "top10_non_theme_score_mean": 0.0,
            "score_conflict_gap": 0.0,
            "theme_required_share_gap": 0.0,
            "theme_top_share_gap": 0.0,
            "theme_conflict_index": 0.0,
            "budget_tightness": 0.0,
            "budget_label": f"{int(budget_minutes) // 60}h",
        }

    theme_target = set(theme_profile.target_stops)
    theme_scores = [score for code, score in all_scores.items() if code in theme_target]
    non_theme_scores = [score for code, score in all_scores.items() if code not in theme_target]
    total_score_mass = float(sum(all_scores.values()))
    total_stop_count = max(1, len(all_scores))
    top_count = min(20, len(all_scores))
    top_entries = list(objective._score_ranked_stop_entries[:top_count])
    top_theme_hits = sum(1 for code, _score in top_entries if str(code) in theme_target)
    theme_density = float(len(theme_target) / total_stop_count)
    theme_score_mass_share = float(sum(theme_scores) / total_score_mass) if total_score_mass > 0.0 else 0.0
    top_theme_share = float(top_theme_hits / top_count) if top_count > 0 else 0.0
    top_theme_mean = _mean_top(theme_scores, 10)
    top_non_theme_mean = _mean_top(non_theme_scores, 10)
    score_span = max(1.0, max(all_scores.values()) - min(all_scores.values()))
    score_conflict_gap = float(top_non_theme_mean - top_theme_mean)
    required_share_gap = max(0.0, float(theme_profile.min_ratio) - theme_score_mass_share)
    top_share_gap = max(0.0, float(theme_profile.min_ratio) - top_theme_share)
    normalized_gap = max(0.0, score_conflict_gap) / score_span
    conflict_index = required_share_gap + top_share_gap + normalized_gap + (1.0 - theme_density)
    budget_tightness = (
        float(objective.dwell_minutes * int(theme_profile.min_stops_apply)) / float(max(1, int(budget_minutes)))
    )
    return {
        "theme_required_ratio": round(float(theme_profile.min_ratio), 6),
        "theme_min_stops_apply": int(theme_profile.min_stops_apply),
        "theme_target_size": int(len(theme_target)),
        "theme_density": round(theme_density, 6),
        "theme_score_mass_share_all": round(theme_score_mass_share, 6),
        "top20_theme_share": round(top_theme_share, 6),
        "top10_theme_score_mean": round(top_theme_mean, 6),
        "top10_non_theme_score_mean": round(top_non_theme_mean, 6),
        "score_conflict_gap": round(score_conflict_gap, 6),
        "theme_required_share_gap": round(required_share_gap, 6),
        "theme_top_share_gap": round(top_share_gap, 6),
        "theme_conflict_index": round(conflict_index, 6),
        "budget_tightness": round(budget_tightness, 6),
        "budget_label": f"{int(budget_minutes) // 60}h",
    }


def _build_theme_profiles(
    planner: Any,
    *,
    quick: bool,
    penalty_scale: float,
    bonus_scale: float,
    min_ratio_scale: float,
) -> list[ThemeProfile]:
    stations = [
        (str(code), station)
        for code, station in planner.stations.items()
        if station is not None and station.lat and station.lon
    ]
    if not stations:
        return []

    min_size = 6 if quick else 10
    profiles: list[ThemeProfile] = []
    for theme_name, tokens in THEME_TOKEN_MAP.items():
        hits: set[str] = set()
        for code, station in stations:
            name = str(getattr(station, "name", "") or "")
            if any(tok in name for tok in tokens):
                hits.add(code)
        if len(hits) >= min_size:
            profiles.append(
                ThemeProfile(
                    name=theme_name,
                    target_stops=frozenset(hits),
                    min_ratio=max(0.05, min(0.95, 0.35 * min_ratio_scale)),
                    penalty_weight=max(0.0, 100000.0 * penalty_scale),
                    bonus_per_hit=max(0.0, 20.0 * bonus_scale),
                    min_stops_apply=4,
                )
            )
    profiles.sort(key=lambda item: item.name)
    return profiles


def build_tasks(
    *,
    planner: Any,
    selected_experiments: list[str],
    quick: bool,
    seeds: list[int],
    score_seeds: list[int],
    project_challenges: list[ProjectThemeChallenge],
    project_starts_per_theme: int,
    negative_pressure_presets: list[PressurePreset],
) -> list[RunTask]:
    tasks: list[RunTask] = []
    route_project_challenges = [challenge for challenge in project_challenges if challenge.theme_mode == "route"]
    if not route_project_challenges:
        route_project_challenges = list(project_challenges)
    if quick:
        beam_origins = QUICK_ORIGINS
        beam_departs = QUICK_DEPART_TIMES
        beam_budgets = [8 * 60]
        theme_departs = [10 * 60]
        theme_budgets = [8 * 60]
        theme_subset = route_project_challenges[: min(2, len(route_project_challenges))]
    else:
        beam_origins = ["hakata", "tenjin", "nishijin", "meinohama"]
        beam_departs = [10 * 60, 14 * 60]
        beam_budgets = [8 * 60, 12 * 60]
        theme_departs = [10 * 60, 14 * 60]
        theme_budgets = [int(b) for b in BUDGETS_MINUTES]
        theme_subset = route_project_challenges

    default_pressure = NEGATIVE_PRESSURE_PRESETS["default"]

    if "beam_tail_risk" in selected_experiments:
        for origin in beam_origins:
            for depart_time in beam_departs:
                for budget_minutes in beam_budgets:
                    for seed in seeds:
                        for score_seed in score_seeds:
                            for algo_key in ["full", "no_beam"]:
                                tasks.append(
                                    RunTask(
                                        "beam_tail_risk",
                                        algo_key,
                                        origin,
                                        depart_time,
                                        budget_minutes,
                                        seed,
                                        score_seed,
                                        pressure_name=default_pressure.name,
                                        beam_width=default_pressure.beam_width,
                                        candidate_cap_short=default_pressure.candidate_cap_short,
                                        candidate_cap_long=default_pressure.candidate_cap_long,
                                    )
                                )

    if "negative_project_theme_alignment" in selected_experiments:
        for challenge in theme_subset:
            for pressure in negative_pressure_presets:
                for seed in seeds:
                    starts = sample_project_theme_starts(
                        planner=planner,
                        challenge=challenge,
                        seed=seed,
                        max_starts=project_starts_per_theme,
                    )
                    for origin_code, start_mode in starts:
                        for depart_time in theme_departs:
                            for budget_minutes in theme_budgets:
                                for algo_key in ["full", "no_neg"]:
                                    tasks.append(
                                        RunTask(
                                            "negative_project_theme_alignment",
                                            algo_key,
                                            origin_code,
                                            depart_time,
                                            budget_minutes,
                                            seed,
                                            0,
                                            challenge.challenge_id,
                                            start_mode,
                                            pressure.name,
                                            pressure.beam_width,
                                            pressure.candidate_cap_short,
                                            pressure.candidate_cap_long,
                                        )
                                    )
    return tasks


def make_algorithm(
    *,
    planner: Any,
    algo_key: str,
    objective: StopScoringProfile | None,
    timeout_seconds_main: float,
    timeout_seconds_beam: float,
    for_experiment: str,
    theme_profile: ThemeProfile | None,
    project_challenge: ProjectThemeChallenge | None,
    beam_width: int,
    candidate_cap_short: int | None,
    candidate_cap_long: int | None,
) -> OursFull:
    timeout_seconds = timeout_seconds_beam if for_experiment == "beam_tail_risk" else timeout_seconds_main
    if project_challenge is not None:
        include_negative = algo_key == "full"
        algo = OursFull(
            use_beam=True,
            use_dominance=True,
            use_negative_score=False,
            timeout_seconds=timeout_seconds,
            beam_width=int(beam_width),
            objective_candidate_cap_short=None,
            objective_candidate_cap_long=None,
            custom_score_fn=make_project_theme_score_fn(planner, project_challenge, include_negative=include_negative),
            custom_accept_fn=make_project_theme_accept_fn(project_challenge, include_negative=include_negative),
            custom_dominance_fn=make_project_theme_dominance_fn(),
        )
        algo.objective = None
        algo.name = "Ours (Full)" if algo_key == "full" else "Ours (NoNeg)"
        return algo

    theme_kwargs: dict[str, Any] = {}
    if theme_profile is not None:
        theme_kwargs = {
            "theme_name": theme_profile.name,
            "theme_target_stops": theme_profile.target_stops,
            "theme_min_ratio": theme_profile.min_ratio,
            "theme_penalty_weight": theme_profile.penalty_weight,
            "theme_bonus_per_hit": theme_profile.bonus_per_hit,
            "theme_min_stops_apply": theme_profile.min_stops_apply,
        }

    common_kwargs = {
        "timeout_seconds": timeout_seconds,
        "beam_width": int(beam_width),
        "objective_candidate_cap_short": candidate_cap_short,
        "objective_candidate_cap_long": candidate_cap_long,
    }
    if algo_key == "full":
        algo = OursFull(
            use_beam=True,
            use_dominance=True,
            use_negative_score=True,
            **common_kwargs,
            **theme_kwargs,
        )
    elif algo_key == "no_beam":
        algo = OursFull(
            use_beam=False,
            use_dominance=True,
            use_negative_score=True,
            **common_kwargs,
            **theme_kwargs,
        )
    elif algo_key == "no_neg":
        algo = OursFull(
            use_beam=True,
            use_dominance=True,
            use_negative_score=False,
            **common_kwargs,
            **theme_kwargs,
        )
    else:
        raise ValueError(f"Unsupported algo key: {algo_key}")
    algo.objective = objective
    return algo


def evaluate_task(
    *,
    algo: OursFull,
    planner: Any,
    objective: StopScoringProfile | None,
    origin_code: str,
    origin_name: str,
    depart_time: int,
    budget_minutes: int,
    seed: int,
    score_seed: int,
    theme_profile: ThemeProfile | None,
    project_challenge: ProjectThemeChallenge | None,
    score_min: int,
    score_max: int,
    start_mode: str,
    pressure_name: str,
    beam_width: int,
    candidate_cap_short: int | None,
    candidate_cap_long: int | None,
) -> dict[str, Any]:
    algo._last_labels_count = 0
    algo._last_termination_reason = "completed"

    t0 = time.perf_counter()
    path_edges = algo.solve(planner, origin_code, depart_time, budget_minutes, seed=seed)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    structural_feasible, violation_reason = algo._validate_path_edges(
        path_edges=path_edges,
        planner=planner,
        origin=origin_code,
        depart_time=depart_time,
        budget_minutes=budget_minutes,
    )
    route_metrics = _route_health_metrics(path_edges if structural_feasible else [])
    if project_challenge is not None:
        effective_feasible = bool(structural_feasible)
        task_feasible = bool(structural_feasible)
        project_metrics = evaluate_project_theme_route(
            path_edges=path_edges if task_feasible else [],
            challenge=project_challenge,
            planner=planner,
            start_mode=start_mode,
        )
        scored_stop_count = len(_unique_scored_stop_codes(path_edges)) if task_feasible else 0
        stop_score_total = float(project_metrics.get("primary_objective_total", 0.0) or 0.0)
        theme_stop_count = int(project_metrics.get("theme_stop_count", 0) or 0)
        theme_score_total = float(project_metrics.get("theme_score_total", 0.0) or 0.0)
        theme_hit_ratio = float(project_metrics.get("theme_hit_ratio", 0.0) or 0.0)
        theme_score_share = float(project_metrics.get("theme_score_share", 0.0) or 0.0)
        off_theme_score_share = float(project_metrics.get("off_theme_score_share", 0.0) or 0.0)
        off_theme_stop_count = int(project_metrics.get("off_theme_stop_count", 0) or 0)
        off_theme_score_total = float(project_metrics.get("off_theme_leg_count", 0) or 0) if project_challenge.theme_mode == "route" else float(off_theme_stop_count)
        stop_metrics = {
            "dwell_minutes_total": 0,
            "effective_time_minutes": stop_score_total,
            "effective_budget_overrun_minutes": max(0.0, stop_score_total - float(budget_minutes)),
            "score_per_hour": float(project_metrics.get("score_per_hour", 0.0) or 0.0),
        }
        condition_metrics = {
            "theme_required_ratio": 0.0,
            "theme_min_stops_apply": int(project_challenge.target),
            "theme_target_size": int(project_metrics.get("theme_target_size", 0) or 0),
            "theme_density": float(project_metrics.get("target_density", 0.0) or 0.0),
            "theme_score_mass_share_all": theme_score_share,
            "top20_theme_share": theme_score_share,
            "top10_theme_score_mean": theme_score_total,
            "top10_non_theme_score_mean": float(off_theme_stop_count),
            "score_conflict_gap": 0.0,
            "theme_required_share_gap": 0.0,
            "theme_top_share_gap": 0.0,
            "theme_conflict_index": round(1.0 - float(project_metrics.get("target_density", 0.0) or 0.0), 6),
            "budget_tightness": round(float(project_challenge.min_minutes) / float(max(1, budget_minutes)), 6),
            "budget_label": f"{int(budget_minutes) // 60}h",
            "theme_kind": str(project_metrics.get("theme_kind", project_challenge.theme_mode)),
            "project_scoring_type": str(project_metrics.get("project_scoring_type", project_challenge.scoring_type)),
            "project_target": int(project_metrics.get("project_target", project_challenge.target)),
            "start_mode": str(project_metrics.get("start_mode", start_mode)),
            "theme_leg_count": int(project_metrics.get("theme_leg_count", 0) or 0),
            "off_theme_leg_count": int(project_metrics.get("off_theme_leg_count", 0) or 0),
            "primary_objective_name": str(project_metrics.get("primary_objective_name", "ride_minutes")),
            "effective_min_minutes": int(project_metrics.get("effective_min_minutes", 0) or 0),
            "effective_min_legs": int(project_metrics.get("effective_min_legs", 0) or 0),
        }
        theme_target = set()
        theme_satisfied = bool(project_metrics.get("theme_satisfied", False))
    else:
        assert objective is not None
        raw_metrics = objective.metrics_from_edges(path_edges, budget_minutes=budget_minutes) if path_edges else objective.zero_metrics()
        effective_feasible = bool(raw_metrics.get("effective_budget_feasible", True))
        task_feasible = bool(structural_feasible and effective_feasible)

        stop_metrics = raw_metrics if task_feasible else objective.zero_metrics()
        scored_stops = _unique_scored_stop_codes(path_edges) if task_feasible else []
        condition_metrics = _task_condition_metrics(
            objective=objective,
            theme_profile=theme_profile,
            budget_minutes=budget_minutes,
        )
        theme_target = set(theme_profile.target_stops) if theme_profile is not None else set()
        theme_stop_count = sum(1 for code in scored_stops if code in theme_target)
        theme_score_total = float(sum(objective.score_for_stop(code) for code in scored_stops if code in theme_target))
        scored_stop_count = int(stop_metrics.get("scored_stop_count", 0) or 0)
        stop_score_total = float(stop_metrics.get("stop_score_total", 0.0) or 0.0)
        off_theme_stop_count = max(0, scored_stop_count - int(theme_stop_count))
        off_theme_score_total = max(0.0, stop_score_total - float(theme_score_total))
        theme_hit_ratio = (theme_stop_count / scored_stop_count) if scored_stop_count > 0 else 0.0
        theme_score_share = (theme_score_total / stop_score_total) if stop_score_total > 0.0 else 0.0
        off_theme_score_share = (off_theme_score_total / stop_score_total) if stop_score_total > 0.0 else 0.0
        theme_satisfied = bool(
            theme_profile is not None
            and scored_stop_count >= int(theme_profile.min_stops_apply)
            and theme_hit_ratio >= float(theme_profile.min_ratio)
        )

    return {
        "algorithm": algo.name,
        "origin": origin_name,
        "origin_code": origin_code,
        "depart_time": int(depart_time),
        "budget_minutes": int(budget_minutes),
        "seed": int(seed),
        "score_seed": int(score_seed),
        "score_min": int(score_min),
        "score_max": int(score_max),
        "dwell_minutes": int(objective.dwell_minutes) if objective is not None else 0,
        "objective_mode": str(objective.search_mode) if objective is not None else "project_theme_first",
        "pressure_name": str(pressure_name),
        "beam_width": int(beam_width),
        "candidate_cap_short": candidate_cap_short,
        "candidate_cap_long": candidate_cap_long,
        "elapsed_ms": round(elapsed_ms, 3),
        "feasible": bool(task_feasible),
        "structural_feasible": bool(structural_feasible),
        "effective_budget_feasible": bool(effective_feasible),
        "violation_reason": "" if task_feasible else (violation_reason if not structural_feasible else "effective_budget_exceeded"),
        "stop_score_total": round(stop_score_total, 6),
        "scored_stop_count": scored_stop_count,
        "dwell_minutes_total": int(stop_metrics.get("dwell_minutes_total", 0) or 0),
        "effective_time_minutes": round(float(stop_metrics.get("effective_time_minutes", 0.0) or 0.0), 6),
        "effective_budget_overrun_minutes": round(float(stop_metrics.get("effective_budget_overrun_minutes", 0.0) or 0.0), 6),
        "score_per_hour": round(float(stop_metrics.get("score_per_hour", 0.0) or 0.0), 6),
        "theme_name": (
            project_challenge.challenge_id
            if project_challenge is not None
            else (theme_profile.name if theme_profile is not None else "none")
        ),
        "theme_target_size": int(condition_metrics.get("theme_target_size", len(theme_target)) or 0),
        "theme_stop_count": int(theme_stop_count),
        "theme_score_total": round(theme_score_total, 6),
        "theme_hit_ratio": round(theme_hit_ratio, 6),
        "theme_score_share": round(theme_score_share, 6),
        "theme_satisfied": bool(theme_satisfied),
        "off_theme_stop_count": int(off_theme_stop_count),
        "off_theme_score_total": round(off_theme_score_total, 6),
        "off_theme_score_share": round(off_theme_score_share, 6),
        "waiting_ratio": float(route_metrics["waiting_ratio"]),
        "revisit_ratio": float(route_metrics["revisit_ratio"]),
        "backtrack_count": int(route_metrics["backtrack_count"]),
        "route_hash": str(route_metrics["route_hash"]),
        "labels": int(getattr(algo, "_last_labels_count", 0)),
        "scored_labels": int(getattr(algo, "_last_scored_labels", 0)),
        "negative_repeat_hits": int(getattr(algo, "_last_negative_repeat_hits", 0)),
        "negative_ratio_hits": int(getattr(algo, "_last_negative_ratio_hits", 0)),
        "negative_theme_hits": int(getattr(algo, "_last_theme_negative_hits", 0)),
        "negative_theme_line_hits": int(getattr(algo, "_last_theme_line_negative_hits", 0)),
        "negative_total_hits": int(getattr(algo, "_last_negative_repeat_hits", 0))
        + int(getattr(algo, "_last_negative_ratio_hits", 0))
        + int(getattr(algo, "_last_theme_negative_hits", 0))
        + int(getattr(algo, "_last_theme_line_negative_hits", 0)),
        "beam_trim_events": int(getattr(algo, "_last_beam_trim_events", 0)),
        "beam_trimmed_labels": int(getattr(algo, "_last_beam_trimmed_labels", 0)),
        "candidate_trim_events": int(getattr(algo, "_last_candidate_trim_events", 0)),
        "candidate_trimmed_edges": int(getattr(algo, "_last_candidate_trimmed_edges", 0)),
        "termination_reason": str(getattr(algo, "_last_termination_reason", "completed")),
        "resource_cap_hit": str(getattr(algo, "_last_termination_reason", "completed")) in {"timeout", "label_cap"},
        "timeout_seconds": float(getattr(algo, "timeout_seconds", 0.0) or 0.0),
        **condition_metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Exp2 supporting studies.")
    parser.add_argument("--quick", action="store_true", help="Run a small smoke subset first.")
    parser.add_argument("--resume", action="store_true", help="Resume from an existing supporting results file.")
    parser.add_argument("--checkpoint-every", type=int, default=8, help="Save every N new rows.")
    parser.add_argument("--experiments", type=str, default="beam_tail_risk,negative_project_theme_alignment")
    parser.add_argument("--timeout-seconds", type=float, default=EXP2_TIMEOUT_SECONDS)
    parser.add_argument("--beam-timeout-seconds", type=float, default=EXP2_TIMEOUT_SECONDS)
    parser.add_argument("--score-seed", type=int, default=EXP1_STOP_SCORE_SEED)
    parser.add_argument("--score-seeds", type=str, default="")
    parser.add_argument("--score-min", type=int, default=EXP1_STOP_SCORE_MIN)
    parser.add_argument("--score-max", type=int, default=EXP1_STOP_SCORE_MAX)
    parser.add_argument("--dwell-minutes", type=int, default=EXP1_STOP_DWELL_MINUTES)
    parser.add_argument("--objective-mode", type=str, default="score_guided", choices=["score_guided", "legacy_balanced"])
    parser.add_argument("--seeds", type=str, default="")
    parser.add_argument("--seed-count", type=int, default=1)
    parser.add_argument("--max-themes", type=int, default=6)
    parser.add_argument("--project-starts-per-theme", type=int, default=5)
    parser.add_argument(
        "--negative-pressure-levels",
        type=str,
        default="default,tight",
        help="Comma-separated shared pressure presets for the negative-pruning study.",
    )
    parser.add_argument("--theme-penalty-scale", type=float, default=1.0)
    parser.add_argument("--theme-bonus-scale", type=float, default=1.0)
    parser.add_argument("--theme-min-ratio-scale", type=float, default=1.0)
    parser.add_argument("--output-tag", type=str, default="", help="Custom suffix for result filename.")
    args = parser.parse_args()

    selected_experiments = parse_experiment_list(args.experiments)
    score_seeds = normalize_score_seeds(score_seed=args.score_seed, score_seeds_override=parse_csv_ints(args.score_seeds))
    seeds_override = parse_csv_ints(args.seeds)
    if seeds_override:
        seeds = seeds_override
    elif args.quick:
        seeds = RANDOM_SEEDS[: max(1, min(max(1, QUICK_NUM_REPEATS), len(RANDOM_SEEDS)))]
    else:
        seeds = RANDOM_SEEDS[: max(1, min(max(1, args.seed_count), len(RANDOM_SEEDS)))]
    negative_pressure_presets = parse_negative_pressure_levels(args.negative_pressure_levels)

    out_dir = RESULTS_BASE_DIR / "exp2_ablation_study"
    if args.output_tag.strip():
        safe_tag = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in args.output_tag.strip())
        out_file = out_dir / f"exp2_supporting_results_{safe_tag}.json"
    else:
        out_file = out_dir / ("exp2_supporting_results_quick.json" if args.quick else "exp2_supporting_results.json")

    print("=" * 72)
    print("STARTING EXP2 SUPPORTING EXPERIMENTS")
    print(f"quick={args.quick}, resume={args.resume}")
    print(f"experiments={selected_experiments}")
    print(f"algorithm_seeds={seeds}")
    print(f"score_seeds={score_seeds}")
    print(f"negative_pressure_levels={[item.name for item in negative_pressure_presets]}")
    print("=" * 72)

    planner = load_planner()
    objectives = {
        score_seed: StopScoringProfile(
            stop_scores=build_random_stop_score_map(planner, seed=score_seed, score_min=args.score_min, score_max=args.score_max),
            dwell_minutes=args.dwell_minutes,
            search_mode=args.objective_mode,
        )
        for score_seed in score_seeds
    }
    project_challenges = build_project_theme_challenges(planner, quick=args.quick)
    if args.max_themes > 0:
        project_challenges = project_challenges[: args.max_themes]
    project_challenge_by_name = {challenge.challenge_id: challenge for challenge in project_challenges}

    tasks = build_tasks(
        planner=planner,
        selected_experiments=selected_experiments,
        quick=args.quick,
        seeds=seeds,
        score_seeds=score_seeds,
        project_challenges=project_challenges,
        project_starts_per_theme=max(1, int(args.project_starts_per_theme)),
        negative_pressure_presets=negative_pressure_presets,
    )

    results: list[dict[str, Any]] = []
    completed: set[tuple[str, str, str, str, str, int, int, int, int]] = set()
    if args.resume:
        results, completed_raw, _resume_stats = build_resume_state(
            out_file,
            row_to_key=row_to_key,
            is_compatible=_is_resume_row_compatible,
        )
        completed = {key for key in completed_raw if isinstance(key, tuple)}

    pending_tasks: list[RunTask] = []
    for task in tasks:
        project_challenge = project_challenge_by_name.get(task.theme_name) if task.experiment == "negative_project_theme_alignment" else None
        algo = make_algorithm(
            planner=planner,
            algo_key=task.algo_key,
            objective=objectives[int(task.score_seed)] if task.experiment == "beam_tail_risk" else None,
            timeout_seconds_main=args.timeout_seconds,
            timeout_seconds_beam=args.beam_timeout_seconds,
            for_experiment=task.experiment,
            theme_profile=None,
            project_challenge=project_challenge,
            beam_width=task.beam_width,
            candidate_cap_short=task.candidate_cap_short,
            candidate_cap_long=task.candidate_cap_long,
        )
        key = run_key(
            experiment=task.experiment,
            algorithm=algo.name,
            theme_name=task.theme_name,
            pressure_name=task.pressure_name,
            origin=task.origin,
            depart_time=task.depart_time,
            budget_minutes=task.budget_minutes,
            seed=task.seed,
            score_seed=task.score_seed,
        )
        if key not in completed:
            pending_tasks.append(task)

    print(f"Total runs: {len(tasks)}")
    print(f"Pending this run: {len(pending_tasks)}")
    print("-" * 72)

    newly_saved = 0
    for idx, task in enumerate(pending_tasks, start=1):
        project_challenge = project_challenge_by_name.get(task.theme_name) if task.experiment == "negative_project_theme_alignment" else None
        algo = make_algorithm(
            planner=planner,
            algo_key=task.algo_key,
            objective=objectives[int(task.score_seed)] if task.experiment == "beam_tail_risk" else None,
            timeout_seconds_main=args.timeout_seconds,
            timeout_seconds_beam=args.beam_timeout_seconds,
            for_experiment=task.experiment,
            theme_profile=None,
            project_challenge=project_challenge,
            beam_width=task.beam_width,
            candidate_cap_short=task.candidate_cap_short,
            candidate_cap_long=task.candidate_cap_long,
        )
        if task.experiment == "negative_project_theme_alignment":
            origin_code = str(task.origin)
            station = getattr(planner, "stations", {}).get(origin_code)
            origin_name = str(getattr(station, "name", "") or origin_code)
        else:
            try:
                origin_code = resolve_origin(planner, task.origin)
                origin_name = task.origin
            except ValueError as exc:
                print(f"[{idx:4d}/{len(pending_tasks)}] skip origin={task.origin}: {exc}")
                continue

        desc = (
            f"[{idx:4d}/{len(pending_tasks)}] {task.experiment:25s} | {algo.name:12s} | "
            f"{origin_name[:10]:10s} | {task.depart_time//60:02d}:00 | {task.budget_minutes//60:2d}h | "
            f"seed={task.seed} | score_seed={task.score_seed} | pressure={task.pressure_name}"
        )
        if task.theme_name != "none":
            desc += f" | theme={task.theme_name}"
        if task.start_mode:
            desc += f" | start={task.start_mode}"
        print(desc, end="", flush=True)

        try:
            row = evaluate_task(
                algo=algo,
                planner=planner,
                objective=objectives[int(task.score_seed)] if task.experiment == "beam_tail_risk" else None,
                origin_code=origin_code,
                origin_name=origin_name,
                depart_time=task.depart_time,
                budget_minutes=task.budget_minutes,
                seed=task.seed,
                score_seed=task.score_seed,
                theme_profile=None,
                project_challenge=project_challenge,
                score_min=args.score_min,
                score_max=args.score_max,
                start_mode=task.start_mode,
                pressure_name=task.pressure_name,
                beam_width=task.beam_width,
                candidate_cap_short=task.candidate_cap_short,
                candidate_cap_long=task.candidate_cap_long,
            )
            row["experiment"] = task.experiment
            row["algo_key"] = task.algo_key
            results.append(row)
            newly_saved += 1
            print(
                f" -> OK ({row['elapsed_ms']:.1f} ms, score={row['stop_score_total']:.1f}, "
                f"theme_score={row['theme_score_total']:.1f}, theme_hit={row['theme_hit_ratio']:.3f}, "
                f"labels={row['labels']}, term={row['termination_reason']})"
            )
        except Exception as exc:
            print(f" -> ERROR: {exc}")

        if args.checkpoint_every > 0 and newly_saved > 0 and (newly_saved % args.checkpoint_every == 0):
            save_json_rows_atomic(out_file, results)
            print(f"    [checkpoint] saved {len(results)} rows -> {out_file}")

    save_json_rows_atomic(out_file, results)
    print("-" * 72)
    print(f"Results saved: {out_file}")
    print("Done.")


if __name__ == "__main__":
    main()
