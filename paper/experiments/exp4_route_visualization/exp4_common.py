from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
APP_API_DIR = PROJECT_ROOT / "apps" / "api"
if str(APP_API_DIR) not in sys.path:
    sys.path.insert(0, str(APP_API_DIR))

from paper.experiments.common.config import FIGURES_BASE_DIR, RESULTS_BASE_DIR
from paper.experiments.exp3_parameter_sensitivity.exp3_balance_common import (
    OURS_NAME,
    REFERENCE_NAME,
    add_tradeoff_metrics,
    build_head_to_head_detail,
    build_query_level_frame,
    build_task_level_frame,
    classify_tradeoff,
    load_exp1_frame,
)
from services.planner_models import ChallengePlan, LegPlan
from services.planner_utils import derive_quadrant_labels, format_minutes


EXP1_RESULTS_PATH = (
    RESULTS_BASE_DIR
    / "exp1_algorithm_comparison"
    / "exp1_results_canonical_final_10alg_manuscript_20260723.json"
)
EXP3_RESULTS_PATH = (
    RESULTS_BASE_DIR
    / "exp3_parameter_sensitivity"
    / "exp3_results_canonical_exp1_final_10alg_20260727.json"
)

EXP4_RESULTS_DIR = RESULTS_BASE_DIR / "exp4_route_visualization"
EXP4_FIGURES_DIR = FIGURES_BASE_DIR / "exp4"
EXP4_ROUTES_DIR = EXP4_RESULTS_DIR / "routes"
EXP4_CASES_PATH = EXP4_RESULTS_DIR / "exp4_cases.json"
EXP4_ANALYSIS_MD_PATH = EXP4_RESULTS_DIR / "exp4_full_text_analysis.md"
EXP4_SUMMARY_MD_PATH = EXP4_FIGURES_DIR / "exp4_case_summary.md"
EXP4_MAIN_PANEL_PATH = EXP4_FIGURES_DIR / "exp4_main_cases.png"
EXP4_APPENDIX_PANEL_PATH = EXP4_FIGURES_DIR / "exp4_appendix_cases.png"

EXP1_ALGO_NAME_BY_KEY = {
    "ours": "Ours (Full)",
    "nsga2": "NSGA-II",
    "vns": "VNS",
    "ils2opt": "ILS+2opt",
    "sa": "SA",
    "mcraptor": "McRAPTOR",
    "greedy": "Greedy (L=3)",
    "pure_raptor": "Pure RAPTOR",
}
DISPLAY_NAME_BY_KEY = {
    "ours": "Ours",
    "nsga2": "NSGA-II",
    "vns": "VNS",
    "ils2opt": "ILS+2opt",
    "sa": "SA",
    "mcraptor": "McRAPTOR",
    "greedy": "Greedy",
    "pure_raptor": "Pure RAPTOR",
}
ALGO_KEY_BY_NAME = {value: key for key, value in EXP1_ALGO_NAME_BY_KEY.items()}

QUERY_GROUP_COLS = ["origin_name", "origin_code", "depart_time", "budget_minutes", "query_key", "budget_label"]
TASK_GROUP_COLS = QUERY_GROUP_COLS[:-2] + ["score_seed", "task_key", "query_key", "budget_label"]


@dataclass(frozen=True)
class Exp4Case:
    id: str
    title: str
    family: str
    source_exp: str
    scenario: str
    paper_role: str
    paper_group: str
    origin_name: str
    origin_code: str
    depart_time: int
    budget_minutes: int
    score_seed: int
    seed: int
    primary_metric: str
    primary_label: str
    selection_reason: str
    qualitative_focus: str
    algorithms: tuple[str, ...] = field(default=("ours", "nsga2", "vns"))
    selection_evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Exp4SelectionContext:
    metadata: dict[str, Any]
    exp1_df: pd.DataFrame
    task_df: pd.DataFrame
    query_df: pd.DataFrame
    query_tradeoff_df: pd.DataFrame
    task_tradeoff_df: pd.DataFrame


def slugify(text: str) -> str:
    out = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return out or "case"


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def load_manifest(path: Path = EXP4_CASES_PATH) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _score_seed_task_mask(df: pd.DataFrame, *, origin_name: str, depart_time: int, budget_minutes: int) -> pd.Series:
    return (
        (df["origin_name"].astype(str) == str(origin_name))
        & (df["depart_time"].astype(int) == int(depart_time))
        & (df["budget_minutes"].astype(int) == int(budget_minutes))
    )


def _build_selection_context(path: Path = EXP1_RESULTS_PATH) -> Exp4SelectionContext:
    metadata, exp1_df = load_exp1_frame(path)
    task_base = build_task_level_frame(exp1_df)
    task_df = add_tradeoff_metrics(
        task_base,
        group_cols=["origin_name", "depart_time", "budget_minutes", "score_seed"],
    )
    query_df = build_query_level_frame(task_base)
    query_tradeoff_df = build_head_to_head_detail(query_df, group_cols=QUERY_GROUP_COLS)
    task_tradeoff_df = build_head_to_head_detail(task_df, group_cols=TASK_GROUP_COLS)
    return Exp4SelectionContext(
        metadata=metadata,
        exp1_df=exp1_df,
        task_df=task_df,
        query_df=query_df,
        query_tradeoff_df=query_tradeoff_df,
        task_tradeoff_df=task_tradeoff_df,
    )


def _query_row_to_lookup(row: pd.Series) -> dict[str, Any]:
    return {
        "origin_name": str(row["origin_name"]),
        "origin_code": str(row["origin_code"]),
        "depart_time": int(row["depart_time"]),
        "budget_minutes": int(row["budget_minutes"]),
        "query_key": str(row["query_key"]),
        "budget_label": str(row["budget_label"]),
    }


def _task_part_for_query(task_tradeoff_df: pd.DataFrame, query_info: dict[str, Any]) -> pd.DataFrame:
    part = task_tradeoff_df.copy()
    for col in ["origin_name", "origin_code", "depart_time", "budget_minutes", "query_key"]:
        part = part[part[col] == query_info[col]]
    return part.reset_index(drop=True)


def _query_part(query_df: pd.DataFrame, query_info: dict[str, Any]) -> pd.DataFrame:
    part = query_df.copy()
    for col in ["origin_name", "origin_code", "depart_time", "budget_minutes", "query_key"]:
        part = part[part[col] == query_info[col]]
    return part.reset_index(drop=True)


def _choose_representative_task_from_tradeoff(
    task_tradeoff_df: pd.DataFrame,
    *,
    query_row: pd.Series,
    desired_tradeoff: str,
) -> pd.Series:
    query_info = _query_row_to_lookup(query_row)
    part = _task_part_for_query(task_tradeoff_df, query_info)
    if part.empty:
        raise ValueError(f"No task-level rows found for query {query_info['query_key']}")

    candidate = part[part["tradeoff_category"] == desired_tradeoff].copy()
    if candidate.empty:
        candidate = part.copy()

    score_scale = max(abs(float(query_row.get("score_diff", 0.0))), 1.0)
    time_scale = max(abs(float(query_row.get("elapsed_diff_ms", 0.0))), 1.0)
    candidate["selection_distance"] = (
        ((pd.to_numeric(candidate["score_diff"], errors="coerce") - float(query_row.get("score_diff", 0.0))) / score_scale) ** 2
        + ((pd.to_numeric(candidate["elapsed_diff_ms"], errors="coerce") - float(query_row.get("elapsed_diff_ms", 0.0))) / time_scale) ** 2
    )
    candidate = candidate.sort_values(
        ["selection_distance", "score_seed"],
        ascending=[True, True],
    ).reset_index(drop=True)
    return candidate.iloc[0]


def _choose_balance_task(task_df: pd.DataFrame, *, query_row: pd.Series) -> pd.Series:
    query_info = _query_row_to_lookup(query_row)
    part = task_df[_score_seed_task_mask(task_df, **{k: query_info[k] for k in ["origin_name", "depart_time", "budget_minutes"]})].copy()
    if part.empty:
        raise ValueError(f"No task-level rows found for balance query {query_info['query_key']}")

    ours = part[part["algorithm"].astype(str) == OURS_NAME].copy()
    if ours.empty:
        raise ValueError(f"Missing Ours rows for balance query {query_info['query_key']}")

    gap_ratio_target = float(query_row.get("best_score_gap_ratio", 0.0))
    ideal_target = float(query_row.get("ideal_distance", 0.0))
    rows: list[dict[str, Any]] = []
    for _, ours_row in ours.iterrows():
        seed_part = part[part["score_seed"] == ours_row["score_seed"]].copy()
        if seed_part.empty:
            continue
        best_score = float(pd.to_numeric(seed_part["stop_score_total"], errors="coerce").max())
        sorted_ideal = seed_part.sort_values("ideal_distance")
        balance_margin = 0.0
        if len(sorted_ideal) >= 2:
            balance_margin = float(sorted_ideal.iloc[1]["ideal_distance"] - sorted_ideal.iloc[0]["ideal_distance"])
        score_gap_ratio = 0.0 if best_score <= 1e-9 else max(0.0, (best_score - float(ours_row["stop_score_total"])) / best_score)
        rows.append(
            {
                "score_seed": int(ours_row["score_seed"]),
                "score_gap_ratio": score_gap_ratio,
                "ideal_distance": float(ours_row["ideal_distance"]),
                "balance_margin": balance_margin,
                "balance_rank": float(ours_row["balance_rank"]),
                "is_best_score": bool(ours_row["is_best_score"]),
                "distance": abs(score_gap_ratio - gap_ratio_target) + abs(float(ours_row["ideal_distance"]) - ideal_target),
            }
        )

    candidate = pd.DataFrame(rows)
    if candidate.empty:
        raise ValueError(f"Could not build balance-task candidates for {query_info['query_key']}")

    constrained = candidate[(candidate["balance_rank"] <= 1.0 + 1e-9) & (~candidate["is_best_score"])].copy()
    if constrained.empty:
        constrained = candidate[candidate["balance_rank"] <= 1.0 + 1e-9].copy()
    if constrained.empty:
        constrained = candidate.copy()

    constrained = constrained.sort_values(
        ["distance", "score_gap_ratio", "ideal_distance", "balance_margin", "score_seed"],
        ascending=[True, True, True, False, True],
    ).reset_index(drop=True)
    chosen_seed = int(constrained.iloc[0]["score_seed"])
    selected = ours[ours["score_seed"] == chosen_seed].copy().sort_values("score_seed").reset_index(drop=True)
    return selected.iloc[0]


def _choose_representative_run_seed(
    exp1_df: pd.DataFrame,
    *,
    origin_name: str,
    depart_time: int,
    budget_minutes: int,
    score_seed: int,
    target_score_diff: float,
    target_time_diff_ms: float,
    desired_tradeoff: str,
) -> int:
    subset = exp1_df[
        (exp1_df["origin_name"].astype(str) == str(origin_name))
        & (exp1_df["depart_time"].astype(int) == int(depart_time))
        & (exp1_df["budget_minutes"].astype(int) == int(budget_minutes))
        & (exp1_df["score_seed"].astype(int) == int(score_seed))
        & (exp1_df["algorithm"].astype(str).isin([OURS_NAME, REFERENCE_NAME]))
    ].copy()
    if subset.empty:
        return 0

    left = subset[subset["algorithm"].astype(str) == OURS_NAME].copy()
    right = subset[subset["algorithm"].astype(str) == REFERENCE_NAME].copy()
    merged = left.merge(
        right,
        on=["origin_name", "origin_code", "depart_time", "budget_minutes", "seed", "score_seed"],
        suffixes=("_left", "_right"),
    )
    if merged.empty:
        seeds = sorted(int(x) for x in subset["seed"].dropna().unique().tolist())
        return seeds[0] if seeds else 0

    merged["score_diff"] = pd.to_numeric(merged["stop_score_total_left"], errors="coerce") - pd.to_numeric(merged["stop_score_total_right"], errors="coerce")
    merged["elapsed_diff_ms"] = pd.to_numeric(merged["elapsed_ms_left"], errors="coerce") - pd.to_numeric(merged["elapsed_ms_right"], errors="coerce")
    merged["tradeoff_category"] = merged.apply(
        lambda row: classify_tradeoff(float(row["score_diff"]), float(row["elapsed_diff_ms"])),
        axis=1,
    )
    constrained = merged[merged["tradeoff_category"] == desired_tradeoff].copy()
    if constrained.empty:
        constrained = merged.copy()

    score_scale = max(abs(float(target_score_diff)), 1.0)
    time_scale = max(abs(float(target_time_diff_ms)), 1.0)
    constrained["selection_distance"] = (
        ((pd.to_numeric(constrained["score_diff"], errors="coerce") - float(target_score_diff)) / score_scale) ** 2
        + ((pd.to_numeric(constrained["elapsed_diff_ms"], errors="coerce") - float(target_time_diff_ms)) / time_scale) ** 2
    )
    constrained = constrained.sort_values(["selection_distance", "seed"], ascending=[True, True]).reset_index(drop=True)
    return int(constrained.iloc[0]["seed"])


def _round_float(value: Any, digits: int = 3) -> float:
    return round(float(value), digits)


def _serialize_case_evidence(mapping: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in mapping.items():
        out[str(key)] = _json_safe(value)
    return out


def _make_clear_lead_case(ctx: Exp4SelectionContext, *, exclude_query_keys: set[str]) -> Exp4Case:
    detail = ctx.query_tradeoff_df.copy()
    detail = detail[
        (detail["tradeoff_category"] == "higher score + faster")
        & (~detail["query_key"].astype(str).isin(exclude_query_keys))
        & (pd.to_numeric(detail["stop_score_total_left"], errors="coerce") > 0.0)
        & (pd.to_numeric(detail["stop_score_total_right"], errors="coerce") > 0.0)
    ].copy()
    if detail.empty:
        raise ValueError("No clear-lead query available for Exp4")

    detail["score_gap_ratio"] = pd.to_numeric(detail["score_diff"], errors="coerce") / pd.to_numeric(detail["stop_score_total_right"], errors="coerce").clip(lower=1e-9)
    detail["speedup_ratio"] = pd.to_numeric(detail["elapsed_ms_right"], errors="coerce") / pd.to_numeric(detail["elapsed_ms_left"], errors="coerce").clip(lower=1e-9)
    chosen_query = detail.sort_values(
        ["score_diff", "score_gap_ratio", "speedup_ratio"],
        ascending=[False, False, False],
    ).reset_index(drop=True).iloc[0]

    chosen_task = _choose_representative_task_from_tradeoff(
        ctx.task_tradeoff_df,
        query_row=chosen_query,
        desired_tradeoff="higher score + faster",
    )
    seed = _choose_representative_run_seed(
        ctx.exp1_df,
        origin_name=str(chosen_query["origin_name"]),
        depart_time=int(chosen_query["depart_time"]),
        budget_minutes=int(chosen_query["budget_minutes"]),
        score_seed=int(chosen_task["score_seed"]),
        target_score_diff=float(chosen_task["score_diff"]),
        target_time_diff_ms=float(chosen_task["elapsed_diff_ms"]),
        desired_tradeoff="higher score + faster",
    )

    selection_reason = (
        "Selected from the main Exp1/Exp3 results as the strongest query where Ours is both higher-scoring "
        "and faster than NSGA-II. "
        f"At query level, Ours averages {float(chosen_query['stop_score_total_left']):.1f} vs "
        f"{float(chosen_query['stop_score_total_right']):.1f} stop score while reducing generation time from "
        f"{float(chosen_query['elapsed_ms_right']):.1f} ms to {float(chosen_query['elapsed_ms_left']):.1f} ms."
    )
    evidence = _serialize_case_evidence(
        {
            "query_tradeoff_category": str(chosen_query["tradeoff_category"]),
            "query_score_gap": float(chosen_query["score_diff"]),
            "query_speedup_ratio": float(chosen_query["speedup_ratio"]),
            "query_ours_stop_score": float(chosen_query["stop_score_total_left"]),
            "query_nsga2_stop_score": float(chosen_query["stop_score_total_right"]),
            "query_ours_elapsed_ms": float(chosen_query["elapsed_ms_left"]),
            "query_nsga2_elapsed_ms": float(chosen_query["elapsed_ms_right"]),
            "task_score_seed": int(chosen_task["score_seed"]),
            "task_score_gap": float(chosen_task["score_diff"]),
            "task_ours_stop_score": float(chosen_task["stop_score_total_left"]),
            "task_nsga2_stop_score": float(chosen_task["stop_score_total_right"]),
            "representative_seed": int(seed),
        }
    )
    return Exp4Case(
        id="case_a_clear_score_lead",
        title="Case A: Ours Clearly Leads in Score and Time",
        family="success",
        source_exp="exp1_exp3_main_task",
        scenario="score-superiority",
        paper_role="success_case",
        paper_group="main",
        origin_name=str(chosen_query["origin_name"]),
        origin_code=str(chosen_query["origin_code"]),
        depart_time=int(chosen_query["depart_time"]),
        budget_minutes=int(chosen_query["budget_minutes"]),
        score_seed=int(chosen_task["score_seed"]),
        seed=seed,
        primary_metric="stop_score_total",
        primary_label="Stop Score",
        selection_reason=selection_reason,
        qualitative_focus=(
            "Inspect whether Ours reaches more high-value stops while still generating the route faster than the slower baseline."
        ),
        algorithms=("ours", "nsga2", "vns"),
        selection_evidence=evidence,
    )


def _make_balance_case(ctx: Exp4SelectionContext, *, exclude_query_keys: set[str]) -> Exp4Case:
    ours = ctx.query_df[ctx.query_df["algorithm"].astype(str) == OURS_NAME].copy()
    ours = ours[
        (~ours["query_key"].astype(str).isin(exclude_query_keys))
        & (pd.to_numeric(ours["balance_rank"], errors="coerce") <= 1.0 + 1e-9)
        & (~ours["is_best_score"].astype(bool))
        & (ours["is_pareto_front"].astype(bool))
    ].copy()
    if ours.empty:
        ours = ctx.query_df[ctx.query_df["algorithm"].astype(str) == OURS_NAME].copy()
        ours = ours[(pd.to_numeric(ours["balance_rank"], errors="coerce") <= 1.0 + 1e-9)].copy()
    if ours.empty:
        raise ValueError("No balance query available for Exp4")

    rows: list[dict[str, Any]] = []
    for _, ours_row in ours.iterrows():
        query_info = _query_row_to_lookup(ours_row)
        part = _query_part(ctx.query_df, query_info)
        best_score = float(pd.to_numeric(part["stop_score_total"], errors="coerce").max())
        second_ideal = float(part.sort_values("ideal_distance").iloc[1]["ideal_distance"]) if len(part) >= 2 else float(ours_row["ideal_distance"])
        rows.append(
            {
                **query_info,
                "stop_score_total": float(ours_row["stop_score_total"]),
                "elapsed_ms": float(ours_row["elapsed_ms"]),
                "ideal_distance": float(ours_row["ideal_distance"]),
                "best_score": best_score,
                "best_score_gap": max(0.0, best_score - float(ours_row["stop_score_total"])),
                "best_score_gap_ratio": 0.0 if best_score <= 1e-9 else max(0.0, (best_score - float(ours_row["stop_score_total"])) / best_score),
                "balance_margin": max(0.0, second_ideal - float(ours_row["ideal_distance"])),
            }
        )
    candidate = pd.DataFrame(rows)
    chosen_query = candidate.sort_values(
        ["best_score_gap_ratio", "ideal_distance", "balance_margin"],
        ascending=[True, True, False],
    ).reset_index(drop=True).iloc[0]

    query_row = ctx.query_df[
        (ctx.query_df["algorithm"].astype(str) == OURS_NAME)
        & (ctx.query_df["query_key"].astype(str) == str(chosen_query["query_key"]))
    ].copy().reset_index(drop=True).iloc[0]
    query_row = query_row.copy()
    query_row["best_score_gap_ratio"] = float(chosen_query["best_score_gap_ratio"])

    query_part = _query_part(ctx.query_df, _query_row_to_lookup(query_row))
    best_score_row = query_part.sort_values(
        ["stop_score_total", "elapsed_ms"],
        ascending=[False, True],
    ).reset_index(drop=True).iloc[0]
    faster_lower_quality = query_part[
        pd.to_numeric(query_part["stop_score_total"], errors="coerce")
        < float(query_row["stop_score_total"]) - 1e-9
    ].copy()
    faster_lower_quality = faster_lower_quality.sort_values(
        ["elapsed_ms", "stop_score_total"],
        ascending=[True, False],
    ).reset_index(drop=True)
    best_score_key = ALGO_KEY_BY_NAME.get(str(best_score_row["algorithm"]), "nsga2")
    fast_comparator_key = (
        ALGO_KEY_BY_NAME.get(str(faster_lower_quality.iloc[0]["algorithm"]), "sa")
        if not faster_lower_quality.empty
        else "sa"
    )
    comparison_keys = tuple(dict.fromkeys(("ours", best_score_key, fast_comparator_key)))
    chosen_task = _choose_balance_task(ctx.task_df, query_row=query_row)
    task_part = ctx.task_df[
        _score_seed_task_mask(
            ctx.task_df,
            origin_name=str(chosen_query["origin_name"]),
            depart_time=int(chosen_query["depart_time"]),
            budget_minutes=int(chosen_query["budget_minutes"]),
        )
        & (ctx.task_df["score_seed"].astype(int) == int(chosen_task["score_seed"]))
    ].copy()
    task_best = float(pd.to_numeric(task_part["stop_score_total"], errors="coerce").max())
    task_nsga = task_part[task_part["algorithm"].astype(str) == REFERENCE_NAME].copy()
    task_nsga_score = float(task_nsga.iloc[0]["stop_score_total"]) if not task_nsga.empty else 0.0
    task_nsga_time = float(task_nsga.iloc[0]["elapsed_ms"]) if not task_nsga.empty else 0.0
    seed = _choose_representative_run_seed(
        ctx.exp1_df,
        origin_name=str(chosen_query["origin_name"]),
        depart_time=int(chosen_query["depart_time"]),
        budget_minutes=int(chosen_query["budget_minutes"]),
        score_seed=int(chosen_task["score_seed"]),
        target_score_diff=float(chosen_task["stop_score_total"] - task_nsga_score),
        target_time_diff_ms=float(chosen_task["elapsed_ms"] - task_nsga_time),
        desired_tradeoff="lower score + faster" if float(chosen_task["stop_score_total"]) < task_nsga_score else "higher score + faster",
    )

    selection_reason = (
        "Selected as the cleanest balance case where Ours is the closest-to-ideal algorithm without being the top-scoring one. "
        f"Ours trails the best query-level score by only {float(chosen_query['best_score_gap_ratio']) * 100.0:.2f}% "
        f"and still ranks first by ideal-point distance on this query."
    )
    evidence = _serialize_case_evidence(
        {
            "query_best_score_gap_ratio": float(chosen_query["best_score_gap_ratio"]),
            "query_balance_margin": float(chosen_query["balance_margin"]),
            "query_ours_stop_score": float(chosen_query["stop_score_total"]),
            "query_ours_ideal_distance": float(chosen_query["ideal_distance"]),
            "query_best_score": float(chosen_query["best_score"]),
            "query_best_score_algorithm": str(best_score_row["algorithm"]),
            "query_best_score_elapsed_ms": float(best_score_row["elapsed_ms"]),
            "query_fast_lower_quality_algorithm": (
                str(faster_lower_quality.iloc[0]["algorithm"])
                if not faster_lower_quality.empty
                else ""
            ),
            "query_fast_lower_quality_score": (
                float(faster_lower_quality.iloc[0]["stop_score_total"])
                if not faster_lower_quality.empty
                else 0.0
            ),
            "query_fast_lower_quality_elapsed_ms": (
                float(faster_lower_quality.iloc[0]["elapsed_ms"])
                if not faster_lower_quality.empty
                else 0.0
            ),
            "task_score_seed": int(chosen_task["score_seed"]),
            "task_ours_stop_score": float(chosen_task["stop_score_total"]),
            "task_best_score": float(task_best),
            "task_nsga2_stop_score": float(task_nsga_score),
            "task_nsga2_elapsed_ms": float(task_nsga_time),
            "representative_seed": int(seed),
        }
    )
    return Exp4Case(
        id="case_b_quality_speed_balance",
        title="Case B: Ours Achieves the Best Quality-Speed Balance",
        family="balance",
        source_exp="exp1_exp3_main_task",
        scenario="quality-speed-balance",
        paper_role="balance_case",
        paper_group="main",
        origin_name=str(chosen_query["origin_name"]),
        origin_code=str(chosen_query["origin_code"]),
        depart_time=int(chosen_query["depart_time"]),
        budget_minutes=int(chosen_query["budget_minutes"]),
        score_seed=int(chosen_task["score_seed"]),
        seed=seed,
        primary_metric="stop_score_total",
        primary_label="Stop Score",
        selection_reason=selection_reason,
        qualitative_focus=(
            "Compare Ours against a slower high-quality baseline and a faster lower-quality heuristic to show why the ideal-point ranking favors Ours."
        ),
        algorithms=comparison_keys,
        selection_evidence=evidence,
    )


def _make_counterexample_case(ctx: Exp4SelectionContext, *, exclude_query_keys: set[str]) -> Exp4Case:
    detail = ctx.query_tradeoff_df.copy()
    detail = detail[
        (detail["tradeoff_category"] == "lower score + faster")
        & (~detail["query_key"].astype(str).isin(exclude_query_keys))
        & (pd.to_numeric(detail["stop_score_total_left"], errors="coerce") > 0.0)
        & (pd.to_numeric(detail["stop_score_total_right"], errors="coerce") > 0.0)
    ].copy()
    if detail.empty:
        raise ValueError("No counterexample query available for Exp4")

    detail["score_ratio"] = pd.to_numeric(detail["stop_score_total_left"], errors="coerce") / pd.to_numeric(detail["stop_score_total_right"], errors="coerce").clip(lower=1e-9)
    detail["speedup_ratio"] = pd.to_numeric(detail["elapsed_ms_right"], errors="coerce") / pd.to_numeric(detail["elapsed_ms_left"], errors="coerce").clip(lower=1e-9)
    constrained = detail[detail["score_ratio"] >= 0.80].copy()
    if constrained.empty:
        constrained = detail.copy()
    chosen_query = constrained.sort_values(
        ["score_diff", "score_ratio", "speedup_ratio"],
        ascending=[True, False, False],
    ).reset_index(drop=True).iloc[0]

    chosen_task = _choose_representative_task_from_tradeoff(
        ctx.task_tradeoff_df,
        query_row=chosen_query,
        desired_tradeoff="lower score + faster",
    )
    seed = _choose_representative_run_seed(
        ctx.exp1_df,
        origin_name=str(chosen_query["origin_name"]),
        depart_time=int(chosen_query["depart_time"]),
        budget_minutes=int(chosen_query["budget_minutes"]),
        score_seed=int(chosen_task["score_seed"]),
        target_score_diff=float(chosen_task["score_diff"]),
        target_time_diff_ms=float(chosen_task["elapsed_diff_ms"]),
        desired_tradeoff="lower score + faster",
    )

    selection_reason = (
        "Selected as an honest counterexample where NSGA-II reaches a meaningfully higher stop score, so Ours should not be described as universally best. "
        f"At query level, Ours is still faster ({float(chosen_query['elapsed_ms_left']):.1f} ms vs {float(chosen_query['elapsed_ms_right']):.1f} ms), "
        f"but the score gap remains {abs(float(chosen_query['score_diff'])):.1f}."
    )
    evidence = _serialize_case_evidence(
        {
            "query_tradeoff_category": str(chosen_query["tradeoff_category"]),
            "query_score_gap": float(chosen_query["score_diff"]),
            "query_score_ratio": float(chosen_query["score_ratio"]),
            "query_ours_stop_score": float(chosen_query["stop_score_total_left"]),
            "query_nsga2_stop_score": float(chosen_query["stop_score_total_right"]),
            "query_ours_elapsed_ms": float(chosen_query["elapsed_ms_left"]),
            "query_nsga2_elapsed_ms": float(chosen_query["elapsed_ms_right"]),
            "task_score_seed": int(chosen_task["score_seed"]),
            "task_score_gap": float(chosen_task["score_diff"]),
            "representative_seed": int(seed),
        }
    )
    return Exp4Case(
        id="case_c_contrastive_counterexample",
        title="Case C: A Counterexample Where Ours Does Not Win on Score",
        family="counterexample",
        source_exp="exp1_exp3_main_task",
        scenario="contrastive-counterexample",
        paper_role="contrast_case",
        paper_group="appendix",
        origin_name=str(chosen_query["origin_name"]),
        origin_code=str(chosen_query["origin_code"]),
        depart_time=int(chosen_query["depart_time"]),
        budget_minutes=int(chosen_query["budget_minutes"]),
        score_seed=int(chosen_task["score_seed"]),
        seed=seed,
        primary_metric="stop_score_total",
        primary_label="Stop Score",
        selection_reason=selection_reason,
        qualitative_focus=(
            "Use this case to show the limitation clearly: Ours can be faster yet still miss the highest-scoring route."
        ),
        algorithms=("ours", "nsga2", "vns"),
        selection_evidence=evidence,
    )


def select_representative_cases() -> list[Exp4Case]:
    ctx = _build_selection_context()
    cases: list[Exp4Case] = []
    used_queries: set[str] = set()

    case_a = _make_clear_lead_case(ctx, exclude_query_keys=used_queries)
    cases.append(case_a)
    used_queries.add(f"{case_a.origin_name}|{case_a.depart_time}|{case_a.budget_minutes}")

    case_b = _make_balance_case(ctx, exclude_query_keys=used_queries)
    cases.append(case_b)
    used_queries.add(f"{case_b.origin_name}|{case_b.depart_time}|{case_b.budget_minutes}")

    case_c = _make_counterexample_case(ctx, exclude_query_keys=used_queries)
    cases.append(case_c)
    return cases


def trip_edges_to_route_dict(
    *,
    case: Exp4Case,
    algorithm_key: str,
    algorithm_name: str,
    path_edges: list[Any],
    planner: Any,
    metrics: dict[str, Any],
    source_payload: dict[str, Any],
) -> dict[str, Any]:
    legs: list[LegPlan] = []
    for edge in path_edges:
        ride_minutes = max(0, int(edge.arrive) - int(edge.depart))
        legs.append(
            LegPlan(
                line_id=str(edge.line_id),
                line_name=str(edge.line_name),
                trip_id=str(edge.trip_id),
                from_code=str(edge.from_code),
                from_name=str(edge.from_name),
                to_code=str(edge.to_code),
                to_name=str(edge.to_name),
                depart=int(edge.depart),
                arrive=int(edge.arrive),
                ride_minutes=ride_minutes,
                distance_km=float(getattr(edge, "distance_km", 0.0)),
                stop_hops=int(getattr(edge, "stop_hops", 1) or 1),
                path=[
                    (float(edge.from_lat), float(edge.from_lon)),
                    (float(edge.to_lat), float(edge.to_lon)),
                ],
                from_lat=float(edge.from_lat),
                from_lon=float(edge.from_lon),
                to_lat=float(edge.to_lat),
                to_lon=float(edge.to_lon),
            )
        )

    plan = ChallengePlan(
        challenge_id=f"exp4-{case.id}-{slugify(algorithm_name)}",
        title=f"{case.title} - {algorithm_name}",
        tagline=case.qualitative_focus,
        theme_tags=[case.family, case.source_exp, case.scenario, case.paper_role],
        badge="exp4",
        legs=legs,
        start_stop_name=case.origin_name,
        wards=derive_quadrant_labels(legs, planner.quadrant_map),
        stations=planner.stations,
    )
    payload = plan.to_dict()
    payload["start_time"] = format_minutes(case.depart_time)
    visited_sequence = [edge.from_code for edge in path_edges] + ([path_edges[-1].to_code] if path_edges else [])
    repeat_count = max(0, len(visited_sequence) - len(set(visited_sequence)))
    payload["statistics"].update(
        {
            "repeated_stop_count": repeat_count,
            "unique_lines": len({str(edge.line_id) for edge in path_edges}),
            "primary_metric_name": source_payload["primary_metric_name"],
            "primary_metric_label": source_payload["primary_metric_label"],
            "primary_metric_value": source_payload["primary_metric_value"],
            "elapsed_ms": source_payload["elapsed_ms"],
            "stop_score_total": float(metrics.get("stop_score_total", 0.0)),
            "score_per_hour": float(metrics.get("score_per_hour", 0.0)),
            "effective_time_minutes": float(metrics.get("effective_time_minutes", 0.0)),
            "scored_stop_count": float(metrics.get("scored_stop_count", 0.0)),
        }
    )
    payload["exp4"] = {
        "case_id": case.id,
        "case_title": case.title,
        "source_experiment": case.source_exp,
        "scenario": case.scenario,
        "paper_role": case.paper_role,
        "paper_group": case.paper_group,
        "algorithm_key": algorithm_key,
        "algorithm_name": algorithm_name,
        "origin_name": case.origin_name,
        "origin_code": case.origin_code,
        "depart_time_minutes": case.depart_time,
        "depart_time_hhmm": format_minutes(case.depart_time),
        "budget_minutes": case.budget_minutes,
        "score_seed": case.score_seed,
        "seed": case.seed,
        "selection_reason": case.selection_reason,
        "qualitative_focus": case.qualitative_focus,
        "selection_evidence": _json_safe(case.selection_evidence),
        "timing_provenance": source_payload.get("timing_provenance", ""),
        "rerun_elapsed_ms": source_payload.get("rerun_elapsed_ms"),
        "metrics": {k: _json_safe(v) for k, v in metrics.items()},
    }
    return payload


def _json_safe(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    if isinstance(value, (int, str, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return str(value)
