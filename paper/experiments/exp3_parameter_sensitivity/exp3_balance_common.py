from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from paper.experiments.common.config import FIGURES_BASE_DIR, RESULTS_BASE_DIR
from paper.experiments.common.io_utils import load_results


EXP3_RESULTS_DIR = RESULTS_BASE_DIR / "exp3_parameter_sensitivity"
EXP3_FIGURES_DIR = FIGURES_BASE_DIR / "exp3"
DEFAULT_EXP1_RESULTS = RESULTS_BASE_DIR / "exp1_algorithm_comparison" / "exp1_results_recent_baselines_2h4h6h8h.json"
DEFAULT_EXP3_RESULTS = EXP3_RESULTS_DIR / "exp3_results.json"
DEFAULT_EXP3_RESULTS_QUICK = EXP3_RESULTS_DIR / "exp3_results_quick.json"
EXP3_TARGET_BUDGETS = [2 * 60, 4 * 60, 6 * 60, 8 * 60]
EXP3_QUICK_TARGET_BUDGETS = [2 * 60, 4 * 60]

OURS_NAME = "Ours (Full)"
REFERENCE_NAME = "NSGA-II"
ALGORITHM_ORDER = [
    "Ours (Full)",
    "NSGA-II",
    "ZhouWang2025-ALNS (adapted)",
    "Zhang2025-DynPref (adapted)",
    "ILS+2opt",
    "VNS",
    "SA",
    "McRAPTOR",
    "Greedy (L=3)",
    "Pure RAPTOR",
]
TRADEOFF_ORDER = [
    "higher score + faster",
    "higher score + similar time",
    "higher score + slower",
    "similar score + faster",
    "similar score + similar time",
    "similar score + slower",
    "lower score + faster",
    "lower score + similar time",
    "lower score + slower",
]


def parse_csv_tokens(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in str(raw).split(",") if item.strip()]


def parse_csv_ints(raw: str | None) -> list[int]:
    return [int(item) for item in parse_csv_tokens(raw)]


def _coerce_int_list(raw: Any) -> list[int]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return parse_csv_ints(raw)
    if isinstance(raw, (list, tuple, set)):
        return [int(item) for item in raw]
    return [int(raw)]


def budget_label(minutes: int) -> str:
    return f"{int(minutes) // 60}h"


def _ordered_subset(values: list[Any], preferred_order: list[Any], limit: int | None = None) -> list[Any]:
    seen: set[Any] = set()
    ordered: list[Any] = []
    for item in preferred_order:
        if item in values and item not in seen:
            ordered.append(item)
            seen.add(item)
    for item in values:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    if limit is not None and limit > 0:
        ordered = ordered[:limit]
    return ordered


def _normalize_exp1_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    numeric_cols = [
        "depart_time",
        "budget_minutes",
        "seed",
        "score_seed",
        "elapsed_ms",
        "stop_score_total",
        "score_per_hour",
        "effective_time_minutes",
        "scored_stop_count",
        "labels",
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    bool_cols = ["feasible", "effective_budget_feasible", "resource_cap_hit"]
    for col in bool_cols:
        if col in out.columns:
            out[col] = out[col].astype("boolean").fillna(False).astype(bool)
        else:
            out[col] = False

    out["origin_name"] = out.get("origin_name", out.get("origin", "")).astype(str)
    out["origin_code"] = out.get("origin_code", out.get("origin", "")).astype(str)
    out["budget_label"] = out["budget_minutes"].fillna(0).astype(int).map(budget_label)
    return out


def load_exp1_frame(path: Path) -> tuple[dict[str, Any], pd.DataFrame]:
    metadata, rows = load_results(path)
    df = _normalize_exp1_frame(pd.DataFrame(rows))
    return metadata, df


def filter_exp1_scope(
    df: pd.DataFrame,
    *,
    metadata: dict[str, Any],
    quick: bool = False,
    origins: list[str] | None = None,
    depart_times: list[int] | None = None,
    budgets: list[int] | None = None,
    score_seeds: list[int] | None = None,
    algorithms: list[str] | None = None,
    max_origins: int = 0,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    out = df.copy()
    origin_values = [str(x) for x in metadata.get("origins", [])] or sorted(out["origin_name"].dropna().unique().tolist())
    depart_values = _coerce_int_list(metadata.get("depart_times")) or sorted(int(x) for x in out["depart_time"].dropna().unique().tolist())
    budget_values = _coerce_int_list(metadata.get("budgets")) or sorted(int(x) for x in out["budget_minutes"].dropna().unique().tolist())
    score_seed_values = _coerce_int_list(metadata.get("score_seeds")) or sorted(int(x) for x in out["score_seed"].dropna().unique().tolist())
    algo_values = [str(x) for x in ALGORITHM_ORDER if x in set(out["algorithm"].dropna().astype(str))]
    if not algo_values:
        algo_values = sorted(out["algorithm"].dropna().astype(str).unique().tolist())

    if origins:
        selected_origins = _ordered_subset(origin_values, [str(x) for x in origins])
    else:
        default_origin_limit = 3 if quick and max_origins <= 0 else None
        limit = max_origins if max_origins > 0 else default_origin_limit
        selected_origins = _ordered_subset(origin_values, origin_values, limit=limit)

    selected_depart_times = depart_times or depart_values
    if budgets:
        selected_budgets = budgets
    else:
        target_budgets = EXP3_QUICK_TARGET_BUDGETS if quick else EXP3_TARGET_BUDGETS
        selected_budgets = [int(x) for x in target_budgets if int(x) in budget_values]
        if not selected_budgets:
            selected_budgets = budget_values
    selected_score_seeds = score_seeds or (score_seed_values[:2] if quick else score_seed_values)
    selected_algorithms = algorithms or algo_values

    out = out[out["origin_name"].isin(selected_origins)]
    out = out[out["depart_time"].isin(selected_depart_times)]
    out = out[out["budget_minutes"].isin(selected_budgets)]
    out = out[out["score_seed"].isin(selected_score_seeds)]
    out = out[out["algorithm"].isin(selected_algorithms)]
    out = out.reset_index(drop=True)

    scope = {
        "origins": selected_origins,
        "depart_times": [int(x) for x in selected_depart_times],
        "budgets": [int(x) for x in selected_budgets],
        "score_seeds": [int(x) for x in selected_score_seeds],
        "algorithms": list(selected_algorithms),
    }
    return out, scope


def build_task_level_frame(exp1_df: pd.DataFrame) -> pd.DataFrame:
    if exp1_df.empty:
        return pd.DataFrame()

    base = exp1_df.copy()
    base["algorithm"] = base["algorithm"].astype(str)
    out = (
        base.groupby(
            ["algorithm", "origin_name", "origin_code", "depart_time", "budget_minutes", "score_seed"],
            as_index=False,
            observed=True,
        )
        .agg(
            seed_count=("seed", "nunique"),
            stop_score_total=("stop_score_total", "mean"),
            elapsed_ms=("elapsed_ms", "mean"),
            score_per_hour=("score_per_hour", "mean"),
            effective_time_minutes=("effective_time_minutes", "mean"),
            scored_stop_count=("scored_stop_count", "mean"),
            feasible_rate=("feasible", "mean"),
            effective_budget_feasible_rate=("effective_budget_feasible", "mean"),
            resource_cap_hit_rate=("resource_cap_hit", "mean"),
        )
        .reset_index(drop=True)
    )
    out["budget_label"] = out["budget_minutes"].astype(int).map(budget_label)
    out["task_key"] = (
        out["origin_name"].astype(str)
        + "|"
        + out["depart_time"].astype(int).astype(str)
        + "|"
        + out["budget_minutes"].astype(int).astype(str)
        + "|"
        + out["score_seed"].astype(int).astype(str)
    )
    out["query_key"] = (
        out["origin_name"].astype(str)
        + "|"
        + out["depart_time"].astype(int).astype(str)
        + "|"
        + out["budget_minutes"].astype(int).astype(str)
    )
    return sort_algorithms(out)


def load_task_frame(path: Path) -> tuple[dict[str, Any], pd.DataFrame]:
    metadata, rows = load_results(path)
    df = pd.DataFrame(rows)
    if df.empty:
        return metadata, df

    numeric_cols = [
        "depart_time",
        "budget_minutes",
        "score_seed",
        "seed_count",
        "stop_score_total",
        "elapsed_ms",
        "score_per_hour",
        "effective_time_minutes",
        "scored_stop_count",
        "feasible_rate",
        "effective_budget_feasible_rate",
        "resource_cap_hit_rate",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["budget_label"] = df.get("budget_label", df["budget_minutes"].astype(int).map(budget_label))
    return metadata, sort_algorithms(df)


def add_tradeoff_metrics(df: pd.DataFrame, *, group_cols: list[str]) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    out["is_pareto_front"] = False
    out["is_best_score"] = False
    out["is_fastest"] = False
    out["ideal_distance"] = np.nan
    out["ideal_l1_distance"] = np.nan

    for _, idx in out.groupby(group_cols, sort=False).groups.items():
        row_idx = list(idx)
        part = out.loc[row_idx]
        scores = pd.to_numeric(part["stop_score_total"], errors="coerce").to_numpy(dtype=float)
        times = pd.to_numeric(part["elapsed_ms"], errors="coerce").to_numpy(dtype=float)
        valid = np.isfinite(scores) & np.isfinite(times)
        if not valid.any():
            continue

        valid_scores = scores[valid]
        valid_times = times[valid]
        best_score = float(np.max(valid_scores))
        min_score = float(np.min(valid_scores))
        fastest = float(np.min(valid_times))
        slowest = float(np.max(valid_times))
        score_range = max(best_score - min_score, 1e-9)
        time_range = max(slowest - fastest, 1e-9)

        for i, target_idx in enumerate(row_idx):
            if not valid[i]:
                continue

            dominated = False
            for j in range(len(row_idx)):
                if i == j or not valid[j]:
                    continue
                better_or_equal = scores[j] >= scores[i] - 1e-9 and times[j] <= times[i] + 1e-9
                strictly_better = scores[j] > scores[i] + 1e-9 or times[j] < times[i] - 1e-9
                if better_or_equal and strictly_better:
                    dominated = True
                    break

            score_gap = 0.0 if score_range <= 1e-9 else (best_score - scores[i]) / score_range
            time_gap = 0.0 if time_range <= 1e-9 else (times[i] - fastest) / time_range

            out.at[target_idx, "is_pareto_front"] = not dominated
            out.at[target_idx, "is_best_score"] = scores[i] >= best_score - 1e-9
            out.at[target_idx, "is_fastest"] = times[i] <= fastest + 1e-9
            out.at[target_idx, "ideal_distance"] = math.sqrt(score_gap ** 2 + time_gap ** 2)
            out.at[target_idx, "ideal_l1_distance"] = score_gap + time_gap

    out["balance_rank"] = out.groupby(group_cols, sort=False)["ideal_distance"].rank(method="min", ascending=True)
    return sort_algorithms(out)


def build_query_level_frame(task_df: pd.DataFrame) -> pd.DataFrame:
    if task_df.empty:
        return pd.DataFrame()

    base = task_df.copy()
    base["algorithm"] = base["algorithm"].astype(str)
    out = (
        base.groupby(
            ["algorithm", "origin_name", "origin_code", "depart_time", "budget_minutes"],
            as_index=False,
            observed=True,
        )
        .agg(
            score_seed_count=("score_seed", "nunique"),
            stop_score_total=("stop_score_total", "mean"),
            elapsed_ms=("elapsed_ms", "mean"),
            score_per_hour=("score_per_hour", "mean"),
            effective_time_minutes=("effective_time_minutes", "mean"),
            scored_stop_count=("scored_stop_count", "mean"),
            feasible_rate=("feasible_rate", "mean"),
            effective_budget_feasible_rate=("effective_budget_feasible_rate", "mean"),
            resource_cap_hit_rate=("resource_cap_hit_rate", "mean"),
        )
        .reset_index(drop=True)
    )
    out["budget_label"] = out["budget_minutes"].astype(int).map(budget_label)
    out["query_key"] = (
        out["origin_name"].astype(str)
        + "|"
        + out["depart_time"].astype(int).astype(str)
        + "|"
        + out["budget_minutes"].astype(int).astype(str)
    )
    return add_tradeoff_metrics(out, group_cols=["origin_name", "depart_time", "budget_minutes"])


def sort_algorithms(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "algorithm" not in df.columns:
        return df
    out = df.copy()
    categories = _ordered_subset(out["algorithm"].dropna().astype(str).unique().tolist(), ALGORITHM_ORDER)
    out["algorithm"] = pd.Categorical(out["algorithm"], categories=categories, ordered=True)
    sort_cols = [col for col in ["budget_minutes", "origin_name", "depart_time", "score_seed", "algorithm"] if col in out.columns]
    return out.sort_values(sort_cols).reset_index(drop=True)


def build_algorithm_summary(df: pd.DataFrame, *, count_label: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = df.copy()
    base["algorithm"] = base["algorithm"].astype(str)
    summary = (
        base.groupby("algorithm", as_index=False, observed=True)
        .agg(
            **{
                count_label: ("algorithm", "size"),
                "avg_stop_score": ("stop_score_total", "mean"),
                "avg_elapsed_ms": ("elapsed_ms", "mean"),
                "avg_score_per_hour": ("score_per_hour", "mean"),
                "avg_effective_time_minutes": ("effective_time_minutes", "mean"),
                "pareto_front_rate": ("is_pareto_front", "mean"),
                "best_score_rate": ("is_best_score", "mean"),
                "fastest_rate": ("is_fastest", "mean"),
                "avg_ideal_distance": ("ideal_distance", "mean"),
                "avg_balance_rank": ("balance_rank", "mean"),
                "avg_feasible_rate": ("feasible_rate", "mean"),
                "avg_budget_feasible_rate": ("effective_budget_feasible_rate", "mean"),
                "avg_cap_hit_rate": ("resource_cap_hit_rate", "mean"),
            }
        )
        .sort_values(["avg_ideal_distance", "avg_stop_score", "avg_elapsed_ms"], ascending=[True, False, True])
        .reset_index(drop=True)
    )
    return summary


def build_budget_summary(df: pd.DataFrame, *, count_label: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = df.copy()
    base["algorithm"] = base["algorithm"].astype(str)
    summary = (
        base.groupby(["budget_minutes", "budget_label", "algorithm"], as_index=False, observed=True)
        .agg(
            **{
                count_label: ("algorithm", "size"),
                "avg_stop_score": ("stop_score_total", "mean"),
                "avg_elapsed_ms": ("elapsed_ms", "mean"),
                "avg_score_per_hour": ("score_per_hour", "mean"),
                "pareto_front_rate": ("is_pareto_front", "mean"),
                "avg_ideal_distance": ("ideal_distance", "mean"),
                "best_score_rate": ("is_best_score", "mean"),
                "fastest_rate": ("is_fastest", "mean"),
                "avg_feasible_rate": ("feasible_rate", "mean"),
                "avg_budget_feasible_rate": ("effective_budget_feasible_rate", "mean"),
                "avg_cap_hit_rate": ("resource_cap_hit_rate", "mean"),
            }
        )
        .sort_values(["budget_minutes", "algorithm"])
        .reset_index(drop=True)
    )
    return summary


def present_algorithm_summary(df: pd.DataFrame, *, count_label: str) -> pd.DataFrame:
    if df.empty:
        return df
    cols = [
        "algorithm",
        count_label,
        "avg_stop_score",
        "avg_elapsed_ms",
        "avg_score_per_hour",
        "avg_ideal_distance",
        "avg_balance_rank",
        "best_score_rate",
        "fastest_rate",
        "avg_budget_feasible_rate",
        "avg_cap_hit_rate",
    ]
    return df[[c for c in cols if c in df.columns]].copy()


def present_budget_summary(df: pd.DataFrame, *, count_label: str) -> pd.DataFrame:
    if df.empty:
        return df
    cols = [
        "budget_minutes",
        "budget_label",
        "algorithm",
        count_label,
        "avg_stop_score",
        "avg_elapsed_ms",
        "avg_score_per_hour",
        "avg_ideal_distance",
        "avg_balance_rank",
        "best_score_rate",
        "fastest_rate",
        "avg_budget_feasible_rate",
        "avg_cap_hit_rate",
    ]
    return df[[c for c in cols if c in df.columns]].copy()


def classify_tradeoff(score_diff: float, time_diff: float, *, score_tol: float = 1e-9, time_tol: float = 1e-6) -> str:
    if score_diff > score_tol:
        score_label = "higher score"
    elif score_diff < -score_tol:
        score_label = "lower score"
    else:
        score_label = "similar score"

    if time_diff < -time_tol:
        time_label = "faster"
    elif time_diff > time_tol:
        time_label = "slower"
    else:
        time_label = "similar time"

    return f"{score_label} + {time_label}"


def build_head_to_head_detail(
    df: pd.DataFrame,
    *,
    left_algo: str = OURS_NAME,
    right_algo: str = REFERENCE_NAME,
    group_cols: list[str],
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    left = df[df["algorithm"].astype(str) == left_algo].copy()
    right = df[df["algorithm"].astype(str) == right_algo].copy()
    if left.empty or right.empty:
        return pd.DataFrame()

    detail = left.merge(right, on=group_cols, suffixes=("_left", "_right"))
    if detail.empty:
        return detail

    detail["score_diff"] = detail["stop_score_total_left"] - detail["stop_score_total_right"]
    detail["elapsed_diff_ms"] = detail["elapsed_ms_left"] - detail["elapsed_ms_right"]
    detail["tradeoff_category"] = detail.apply(
        lambda row: classify_tradeoff(float(row["score_diff"]), float(row["elapsed_diff_ms"])),
        axis=1,
    )
    if "budget_label" not in detail.columns and "budget_minutes" in detail.columns:
        detail["budget_label"] = detail["budget_minutes"].astype(int).map(budget_label)
    return detail


def summarize_tradeoff_counts(detail_df: pd.DataFrame) -> pd.DataFrame:
    if detail_df.empty:
        return pd.DataFrame(columns=["tradeoff_category", "count", "rate"])
    counts = detail_df["tradeoff_category"].value_counts().reindex(TRADEOFF_ORDER, fill_value=0)
    out = counts.rename_axis("tradeoff_category").reset_index(name="count")
    out["rate"] = out["count"] / max(len(detail_df), 1)
    return out


def summarize_tradeoff_by_budget(detail_df: pd.DataFrame) -> pd.DataFrame:
    if detail_df.empty:
        return pd.DataFrame(columns=["budget_minutes", "budget_label", "tradeoff_category", "count", "rate"])

    rows: list[dict[str, Any]] = []
    for (budget_minutes, budget_text), part in detail_df.groupby(["budget_minutes", "budget_label"], sort=True):
        counts = part["tradeoff_category"].value_counts().reindex(TRADEOFF_ORDER, fill_value=0)
        total = max(len(part), 1)
        for category, count in counts.items():
            rows.append(
                {
                    "budget_minutes": int(budget_minutes),
                    "budget_label": str(budget_text),
                    "tradeoff_category": category,
                    "count": int(count),
                    "rate": float(count) / total,
                }
            )
    return pd.DataFrame(rows)


def df_markdown(df: pd.DataFrame, *, floatfmt: str = ".4f") -> str:
    if df.empty:
        return "_No data_"
    return df.to_markdown(index=False, floatfmt=floatfmt)
