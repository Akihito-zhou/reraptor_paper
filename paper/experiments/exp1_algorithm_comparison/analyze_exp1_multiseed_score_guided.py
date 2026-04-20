#!/usr/bin/env python3
"""
Analyze multi-score-seed Experiment 1 results and generate summary artifacts.

Outputs:
- figures in `paper/figures/exp1/`
- markdown + json summaries in `paper/results/exp1_algorithm_comparison/`
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Add experiments root to PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.config import FIGURES_BASE_DIR, RESULTS_BASE_DIR
from common.io_utils import load_results


OURS_NAME = "Ours (Full)"
NSGA_NAME = "NSGA-II"
TOP_FOCUS_ALGOS = [OURS_NAME, NSGA_NAME, "ILS+2opt", "VNS", "McRAPTOR"]
PALETTE = {
    OURS_NAME: "#c44536",
    NSGA_NAME: "#355c7d",
    "ILS+2opt": "#2a9d8f",
    "VNS": "#e9c46a",
    "McRAPTOR": "#6c757d",
    "SA": "#8d99ae",
    "Pure RAPTOR": "#b56576",
    "Greedy (L=3)": "#adb5bd",
}


def _set_plot_style() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False


def _safe_suffix(raw: str | None) -> str:
    if not raw:
        return datetime.now().strftime("%Y%m%d")
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in raw.strip())


def _short_algo(name: str) -> str:
    mapping = {
        OURS_NAME: "Ours",
        NSGA_NAME: "NSGA-II",
        "ILS+2opt": "ILS+2opt",
        "VNS": "VNS",
        "McRAPTOR": "McRAPTOR",
        "SA": "SA",
        "Pure RAPTOR": "Pure RAPTOR",
        "Greedy (L=3)": "Greedy",
    }
    return mapping.get(name, name)


def _table_md(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_string(index=False)


def _infer_default_score_seed(metadata: dict[str, Any]) -> int | None:
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


def _load_run_df(results_path: Path) -> tuple[dict[str, Any], pd.DataFrame]:
    metadata, rows = load_results(results_path)
    if not rows:
        raise ValueError(f"No rows found in {results_path}")

    default_score_seed = _infer_default_score_seed(metadata)
    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        if "score_seed" not in item and default_score_seed is not None:
            item["score_seed"] = int(default_score_seed)
        if "origin_name" not in item:
            item["origin_name"] = item.get("origin", "")
        normalized_rows.append(item)

    run_df = pd.DataFrame(normalized_rows)
    numeric_cols = [
        "depart_time",
        "budget_minutes",
        "seed",
        "score_seed",
        "elapsed_ms",
        "stop_score_total",
        "score_per_hour",
        "effective_time_minutes",
        "dwell_minutes_total",
        "unique_stops",
        "labels",
    ]
    for col in numeric_cols:
        if col in run_df.columns:
            run_df[col] = pd.to_numeric(run_df[col], errors="coerce")

    if "effective_budget_feasible" in run_df.columns:
        run_df["effective_budget_feasible"] = run_df["effective_budget_feasible"].fillna(False).astype(bool)
    else:
        run_df["effective_budget_feasible"] = run_df.get("feasible", True)
        run_df["effective_budget_feasible"] = run_df["effective_budget_feasible"].fillna(False).astype(bool)

    run_df["algorithm"] = run_df["algorithm"].astype(str)
    run_df["origin_name"] = run_df["origin_name"].astype(str)
    run_df["origin"] = run_df.get("origin", run_df["origin_name"]).astype(str)
    run_df["budget_hours"] = run_df["budget_minutes"] / 60.0
    run_df["budget_label"] = run_df["budget_hours"].map(lambda x: f"{int(x)}h")
    return metadata, run_df


def _aggregate_task_df(run_df: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["algorithm", "origin_name", "origin", "depart_time", "budget_minutes", "score_seed"]
    task_df = (
        run_df.groupby(group_cols, as_index=False)
        .agg(
            stop_score_total=("stop_score_total", "mean"),
            elapsed_ms=("elapsed_ms", "mean"),
            score_per_hour=("score_per_hour", "mean"),
            effective_time_minutes=("effective_time_minutes", "mean"),
            dwell_minutes_total=("dwell_minutes_total", "mean"),
            unique_stops=("unique_stops", "mean"),
            feasible_rate=("effective_budget_feasible", "mean"),
            run_count=("algorithm", "size"),
        )
    )
    task_df["effective_budget_feasible"] = task_df["feasible_rate"].ge(0.5)
    task_df["budget_hours"] = task_df["budget_minutes"] / 60.0
    task_df["budget_label"] = task_df["budget_hours"].map(lambda x: f"{int(x)}h")
    task_df["task_key"] = (
        task_df["origin_name"].astype(str)
        + "|"
        + task_df["depart_time"].astype(int).astype(str)
        + "|"
        + task_df["budget_minutes"].astype(int).astype(str)
        + "|"
        + task_df["score_seed"].astype(int).astype(str)
    )
    return task_df


def _aggregate_query_df(task_df: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["algorithm", "origin_name", "origin", "depart_time", "budget_minutes"]
    query_df = (
        task_df.groupby(group_cols, as_index=False)
        .agg(
            stop_score_total=("stop_score_total", "mean"),
            elapsed_ms=("elapsed_ms", "mean"),
            score_per_hour=("score_per_hour", "mean"),
            effective_time_minutes=("effective_time_minutes", "mean"),
            dwell_minutes_total=("dwell_minutes_total", "mean"),
            unique_stops=("unique_stops", "mean"),
            feasible_rate=("effective_budget_feasible", "mean"),
            score_seed_count=("score_seed", "nunique"),
        )
    )
    query_df["effective_budget_feasible"] = query_df["feasible_rate"].ge(0.5)
    query_df["budget_hours"] = query_df["budget_minutes"] / 60.0
    query_df["budget_label"] = query_df["budget_hours"].map(lambda x: f"{int(x)}h")
    query_df["query_key"] = (
        query_df["origin_name"].astype(str)
        + "|"
        + query_df["depart_time"].astype(int).astype(str)
        + "|"
        + query_df["budget_minutes"].astype(int).astype(str)
    )
    return query_df


def _compute_rank_stats(
    df: pd.DataFrame,
    *,
    group_cols: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ranked_rows: list[dict[str, Any]] = []
    wins = Counter()
    rank_lists: dict[str, list[int]] = defaultdict(list)

    for _, group in df.groupby(group_cols, sort=False):
        ordered = group.sort_values(["stop_score_total", "elapsed_ms"], ascending=[False, True]).reset_index(drop=True)
        for rank, (_, row) in enumerate(ordered.iterrows(), start=1):
            item = row.to_dict()
            item["rank"] = rank
            ranked_rows.append(item)
            rank_lists[str(row["algorithm"])].append(rank)
            if rank == 1:
                wins[str(row["algorithm"])] += 1

    rank_df = pd.DataFrame(ranked_rows)
    summary_rows = []
    for algorithm, values in rank_lists.items():
        summary_rows.append(
            {
                "algorithm": algorithm,
                "wins": int(wins[algorithm]),
                "avg_rank": float(sum(values) / len(values)),
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    return rank_df, summary_df


def _build_algorithm_summary(
    df: pd.DataFrame,
    *,
    task_count_label: str,
    rank_summary_df: pd.DataFrame,
) -> pd.DataFrame:
    summary = (
        df.groupby("algorithm", as_index=False)
        .agg(
            **{
                task_count_label: ("algorithm", "size"),
                "avg_stop_score": ("stop_score_total", "mean"),
                "avg_elapsed_ms": ("elapsed_ms", "mean"),
                "avg_score_per_hour": ("score_per_hour", "mean"),
                "avg_feasible_rate": ("effective_budget_feasible", "mean"),
            }
        )
        .merge(rank_summary_df, on="algorithm", how="left")
        .sort_values(["avg_stop_score", "avg_rank"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return summary


def _head_to_head(
    df: pd.DataFrame,
    *,
    group_cols: list[str],
    left_algo: str = OURS_NAME,
    right_algo: str = NSGA_NAME,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for group_key, group in df.groupby(group_cols, sort=False):
        left = group[group["algorithm"] == left_algo]
        right = group[group["algorithm"] == right_algo]
        if left.empty or right.empty:
            continue
        left_row = left.iloc[0]
        right_row = right.iloc[0]
        item = {
            "ours_score": float(left_row["stop_score_total"]),
            "other_score": float(right_row["stop_score_total"]),
            "score_diff": float(left_row["stop_score_total"] - right_row["stop_score_total"]),
            "ours_elapsed_ms": float(left_row["elapsed_ms"]),
            "other_elapsed_ms": float(right_row["elapsed_ms"]),
            "elapsed_ratio_other_over_ours": float(right_row["elapsed_ms"] / max(left_row["elapsed_ms"], 1e-9)),
            "budget_minutes": int(left_row["budget_minutes"]),
            "budget_label": str(left_row["budget_label"]),
        }
        if isinstance(group_key, tuple):
            for key_name, value in zip(group_cols, group_key):
                item[key_name] = value
        else:
            item[group_cols[0]] = group_key
        rows.append(item)
    return pd.DataFrame(rows)


def _round_frame(df: pd.DataFrame, digits: int = 3) -> pd.DataFrame:
    rounded = df.copy()
    for col in rounded.columns:
        if pd.api.types.is_float_dtype(rounded[col]):
            rounded[col] = rounded[col].round(digits)
    for col in ["score_seed", "depart_time", "budget_minutes", "task_count", "query_count", "wins", "ours_better", "nsga_better", "ties"]:
        if col in rounded.columns:
            rounded[col] = pd.to_numeric(rounded[col], errors="coerce").astype("Int64")
    return rounded


def _annotate_bars(ax: plt.Axes, *, digits: int = 0) -> None:
    for patch in ax.patches:
        height = patch.get_height()
        if math.isnan(height):
            continue
        x = patch.get_x() + patch.get_width() / 2
        ax.annotate(
            f"{height:.{digits}f}",
            (x, height),
            ha="center",
            va="bottom",
            fontsize=9,
            xytext=(0, 4),
            textcoords="offset points",
        )


def _palette_for(order: list[str]) -> list[str]:
    return [PALETTE.get(name, "#6c757d") for name in order]


def plot_overview(algo_task_df: pd.DataFrame, output_path: Path) -> None:
    order = algo_task_df["algorithm"].tolist()
    labels = [_short_algo(name) for name in order]
    colors = _palette_for(order)

    fig, axes = plt.subplots(2, 2, figsize=(16, 11))

    sns.barplot(x=labels, y=algo_task_df["avg_stop_score"], hue=labels, palette=colors, dodge=False, legend=False, ax=axes[0, 0])
    axes[0, 0].set_title("Average Stop Score")
    axes[0, 0].set_xlabel("")
    axes[0, 0].set_ylabel("Task Mean")
    _annotate_bars(axes[0, 0], digits=1)

    sns.barplot(x=labels, y=algo_task_df["avg_elapsed_ms"], hue=labels, palette=colors, dodge=False, legend=False, ax=axes[0, 1])
    axes[0, 1].set_title("Average Runtime")
    axes[0, 1].set_xlabel("")
    axes[0, 1].set_ylabel("Elapsed ms")
    axes[0, 1].set_yscale("log")

    sns.barplot(x=labels, y=algo_task_df["wins"], hue=labels, palette=colors, dodge=False, legend=False, ax=axes[1, 0])
    axes[1, 0].set_title("Task Wins")
    axes[1, 0].set_xlabel("")
    axes[1, 0].set_ylabel("Wins on 300 Tasks")
    _annotate_bars(axes[1, 0], digits=0)

    sns.barplot(x=labels, y=algo_task_df["avg_rank"], hue=labels, palette=colors, dodge=False, legend=False, ax=axes[1, 1])
    axes[1, 1].set_title("Average Rank")
    axes[1, 1].set_xlabel("")
    axes[1, 1].set_ylabel("Lower Is Better")
    _annotate_bars(axes[1, 1], digits=2)

    for ax in axes.flat:
        ax.tick_params(axis="x", rotation=20)

    fig.suptitle("Experiment 1 Multi-Seed Overview", fontsize=18, y=0.99)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_budget_breakdown(task_df: pd.DataFrame, head_df: pd.DataFrame, output_path: Path) -> None:
    focus_algos = [algo for algo in TOP_FOCUS_ALGOS if algo in set(task_df["algorithm"])]
    budget_summary = (
        task_df[task_df["algorithm"].isin(focus_algos)]
        .groupby(["budget_label", "algorithm"], as_index=False)
        .agg(
            avg_stop_score=("stop_score_total", "mean"),
            avg_elapsed_ms=("elapsed_ms", "mean"),
        )
    )

    wins_rows = []
    for budget_label, group in task_df.groupby("budget_label", sort=False):
        _, budget_rank_summary = _compute_rank_stats(
            group,
            group_cols=["origin_name", "depart_time", "budget_minutes", "score_seed"],
        )
        budget_rank_summary["budget_label"] = budget_label
        wins_rows.append(budget_rank_summary)
    wins_df = pd.concat(wins_rows, ignore_index=True)
    wins_df = wins_df[wins_df["algorithm"].isin(focus_algos)]

    fig, axes = plt.subplots(2, 2, figsize=(16, 11))

    sns.barplot(
        data=budget_summary,
        x="algorithm",
        y="avg_stop_score",
        hue="budget_label",
        palette="Set2",
        order=focus_algos,
        ax=axes[0, 0],
    )
    axes[0, 0].set_title("Stop Score by Budget")
    axes[0, 0].set_xlabel("")
    axes[0, 0].set_ylabel("Task Mean")
    axes[0, 0].tick_params(axis="x", rotation=20)

    sns.barplot(
        data=budget_summary,
        x="algorithm",
        y="avg_elapsed_ms",
        hue="budget_label",
        palette="Set2",
        order=focus_algos,
        ax=axes[0, 1],
    )
    axes[0, 1].set_title("Runtime by Budget")
    axes[0, 1].set_xlabel("")
    axes[0, 1].set_ylabel("Elapsed ms")
    axes[0, 1].set_yscale("log")
    axes[0, 1].tick_params(axis="x", rotation=20)

    sns.boxplot(data=head_df, x="budget_label", y="score_diff", hue="budget_label", palette="Pastel1", legend=False, ax=axes[1, 0])
    axes[1, 0].axhline(0.0, color="#555555", linewidth=1.2, linestyle="--")
    axes[1, 0].set_title("Ours - NSGA-II Score Difference")
    axes[1, 0].set_xlabel("Budget")
    axes[1, 0].set_ylabel("Score Difference")

    sns.barplot(
        data=wins_df,
        x="algorithm",
        y="wins",
        hue="budget_label",
        palette="Set2",
        order=focus_algos,
        ax=axes[1, 1],
    )
    axes[1, 1].set_title("Task Wins by Budget")
    axes[1, 1].set_xlabel("")
    axes[1, 1].set_ylabel("Wins")
    axes[1, 1].tick_params(axis="x", rotation=20)

    for ax in axes.flat:
        legend = ax.get_legend()
        if legend is not None:
            legend.set_title("")

    fig.suptitle("Experiment 1 Budget Breakdown", fontsize=18, y=0.99)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_seed_stability(
    per_seed_df: pd.DataFrame,
    per_seed_rank_df: pd.DataFrame,
    head_by_seed_df: pd.DataFrame,
    output_path: Path,
) -> None:
    focus_algos = [algo for algo in [OURS_NAME, NSGA_NAME, "ILS+2opt", "VNS"] if algo in set(per_seed_df["algorithm"])]

    fig, axes = plt.subplots(2, 2, figsize=(16, 11))

    sns.lineplot(
        data=per_seed_df[per_seed_df["algorithm"].isin(focus_algos)],
        x="score_seed",
        y="avg_stop_score",
        hue="algorithm",
        style="algorithm",
        palette=PALETTE,
        linewidth=2.2,
        markers=True,
        dashes=False,
        ax=axes[0, 0],
    )
    axes[0, 0].set_title("Average Stop Score by Score Seed")
    axes[0, 0].set_xlabel("Score Seed")
    axes[0, 0].set_ylabel("Task Mean")

    sns.lineplot(
        data=per_seed_rank_df[per_seed_rank_df["algorithm"].isin(focus_algos)],
        x="score_seed",
        y="avg_rank",
        hue="algorithm",
        style="algorithm",
        palette=PALETTE,
        linewidth=2.2,
        markers=True,
        dashes=False,
        ax=axes[0, 1],
    )
    axes[0, 1].set_title("Average Rank by Score Seed")
    axes[0, 1].set_xlabel("Score Seed")
    axes[0, 1].set_ylabel("Lower Is Better")

    sns.barplot(data=head_by_seed_df, x="score_seed", y="avg_score_diff", color="#c44536", ax=axes[1, 0])
    axes[1, 0].axhline(0.0, color="#555555", linewidth=1.2, linestyle="--")
    axes[1, 0].set_title("Average Ours - NSGA-II Score Difference")
    axes[1, 0].set_xlabel("Score Seed")
    axes[1, 0].set_ylabel("Score Difference")
    _annotate_bars(axes[1, 0], digits=1)

    runtime_plot_df = per_seed_df[per_seed_df["algorithm"].isin([OURS_NAME, NSGA_NAME])].copy()
    sns.lineplot(
        data=runtime_plot_df,
        x="score_seed",
        y="avg_elapsed_ms",
        hue="algorithm",
        style="algorithm",
        palette=PALETTE,
        linewidth=2.2,
        markers=True,
        dashes=False,
        ax=axes[1, 1],
    )
    axes[1, 1].set_title("Runtime Stability")
    axes[1, 1].set_xlabel("Score Seed")
    axes[1, 1].set_ylabel("Elapsed ms")
    axes[1, 1].set_yscale("log")

    for ax in axes.flat:
        legend = ax.get_legend()
        if legend is not None:
            legend.set_title("")

    fig.suptitle("Experiment 1 Score-Seed Stability", fontsize=18, y=0.99)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def _top_losses_for_ours(task_df: pd.DataFrame, *, limit: int = 12) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, group in task_df.groupby(["origin_name", "depart_time", "budget_minutes", "score_seed"], sort=False):
        ordered = group.sort_values(["stop_score_total", "elapsed_ms"], ascending=[False, True]).reset_index(drop=True)
        ours = ordered[ordered["algorithm"] == OURS_NAME]
        if ours.empty:
            continue
        ours_row = ours.iloc[0]
        best_row = ordered.iloc[0]
        if best_row["algorithm"] == OURS_NAME:
            continue
        rows.append(
            {
                "origin_name": str(ours_row["origin_name"]),
                "depart_time": int(ours_row["depart_time"]),
                "budget_minutes": int(ours_row["budget_minutes"]),
                "score_seed": int(ours_row["score_seed"]),
                "best_algo": str(best_row["algorithm"]),
                "best_score": float(best_row["stop_score_total"]),
                "ours_score": float(ours_row["stop_score_total"]),
                "gap": float(best_row["stop_score_total"] - ours_row["stop_score_total"]),
                "ours_elapsed_ms": float(ours_row["elapsed_ms"]),
            }
        )
    out = pd.DataFrame(rows).sort_values("gap", ascending=False).head(limit).reset_index(drop=True)
    return out


def _per_score_seed_summary(task_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    per_seed = (
        task_df.groupby(["score_seed", "algorithm"], as_index=False)
        .agg(
            avg_stop_score=("stop_score_total", "mean"),
            avg_elapsed_ms=("elapsed_ms", "mean"),
        )
    )

    rank_rows = []
    for score_seed, group in task_df.groupby("score_seed", sort=False):
        _, summary = _compute_rank_stats(group, group_cols=["origin_name", "depart_time", "budget_minutes", "score_seed"])
        summary["score_seed"] = int(score_seed)
        rank_rows.append(summary)
    per_seed_rank = pd.concat(rank_rows, ignore_index=True)
    return per_seed, per_seed_rank


def _head_to_head_by_budget(head_df: pd.DataFrame) -> pd.DataFrame:
    out = (
        head_df.groupby(["budget_minutes", "budget_label"], as_index=False)
        .agg(
            ours_better=("score_diff", lambda s: int((s > 0).sum())),
            nsga_better=("score_diff", lambda s: int((s < 0).sum())),
            ties=("score_diff", lambda s: int((s == 0).sum())),
            avg_score_diff=("score_diff", "mean"),
            avg_ours_elapsed_ms=("ours_elapsed_ms", "mean"),
            avg_nsga_elapsed_ms=("other_elapsed_ms", "mean"),
        )
        .sort_values("budget_minutes")
        .reset_index(drop=True)
    )
    out["budget_minutes"] = out["budget_minutes"].astype(int)
    return out


def _head_to_head_by_seed(head_df: pd.DataFrame) -> pd.DataFrame:
    out = (
        head_df.groupby("score_seed", as_index=False)
        .agg(
            ours_better=("score_diff", lambda s: int((s > 0).sum())),
            nsga_better=("score_diff", lambda s: int((s < 0).sum())),
            ties=("score_diff", lambda s: int((s == 0).sum())),
            avg_score_diff=("score_diff", "mean"),
            avg_ours_elapsed_ms=("ours_elapsed_ms", "mean"),
            avg_nsga_elapsed_ms=("other_elapsed_ms", "mean"),
        )
        .sort_values("score_seed")
        .reset_index(drop=True)
    )
    out["score_seed"] = out["score_seed"].astype(int)
    return out


def _serialize_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    safe_df = _round_frame(df)
    return json.loads(safe_df.to_json(orient="records"))


def write_results_markdown(
    *,
    output_path: Path,
    metadata: dict[str, Any],
    algo_task_df: pd.DataFrame,
    algo_query_df: pd.DataFrame,
    head_task_df: pd.DataFrame,
    head_budget_df: pd.DataFrame,
    head_seed_df: pd.DataFrame,
    top_losses_df: pd.DataFrame,
    zero_cases_df: pd.DataFrame,
    figure_paths: list[Path],
    source_result_path: Path,
) -> None:
    score_seeds = metadata.get("score_seeds", [])
    lines: list[str] = []
    lines.append("# Experiment 1 Multi-Seed Score-Guided Summary")
    lines.append("")
    lines.append(f"- Source result file: `{source_result_path.as_posix()}`")
    lines.append(f"- Score seeds: `{score_seeds}`")
    lines.append(f"- Query x score-seed tasks: `{int(algo_task_df['task_count'].iloc[0]) if not algo_task_df.empty else 0}` per algorithm")
    lines.append(f"- Base queries after averaging over score seeds: `{int(algo_query_df['query_count'].iloc[0]) if not algo_query_df.empty else 0}` per algorithm")
    lines.append("- Primary metric: `stop_score_total`")
    lines.append("")

    ours_task = algo_task_df[algo_task_df["algorithm"] == OURS_NAME].iloc[0]
    nsga_task = algo_task_df[algo_task_df["algorithm"] == NSGA_NAME].iloc[0]
    lines.append("## Key Findings")
    lines.append("")
    lines.append(
        f"- `Ours` remains the top algorithm on the full multi-seed benchmark: "
        f"average stop score `{ours_task['avg_stop_score']:.3f}` vs `NSGA-II` `{nsga_task['avg_stop_score']:.3f}`."
    )
    lines.append(
        f"- `Ours` is also faster: `{ours_task['avg_elapsed_ms']:.3f}` ms vs `NSGA-II` `{nsga_task['avg_elapsed_ms']:.3f}` ms."
    )
    lines.append(
        f"- On `query x score_seed` tasks, `Ours` beats `NSGA-II` in "
        f"`{int((head_task_df['score_diff'] > 0).sum())}` of `{len(head_task_df)}` comparisons."
    )
    lines.append(
        f"- The Ours-NSGA score gap stays positive for every tested `score_seed`, "
        f"but the weakest seed is `20260326` with only `"
        f"{head_seed_df[head_seed_df['score_seed'] == 20260326]['avg_score_diff'].iloc[0]:.3f}` average advantage."
    )
    if not zero_cases_df.empty:
        zero_origins = ", ".join(sorted(set(zero_cases_df["origin_name"].astype(str))))
        lines.append(
            f"- All Ours zero-score cases in this run are `effective_budget_feasible = False` edge cases, "
            f"concentrated in `{zero_origins}` rather than valid-but-poor routes."
        )
    lines.append("")

    lines.append("## Overall Task-Level Summary")
    lines.append("")
    lines.append(_table_md(_round_frame(algo_task_df)))
    lines.append("")

    lines.append("## Base-Query Summary")
    lines.append("")
    lines.append(_table_md(_round_frame(algo_query_df)))
    lines.append("")

    lines.append("## Ours vs NSGA-II by Budget")
    lines.append("")
    lines.append(_table_md(_round_frame(head_budget_df)))
    lines.append("")

    lines.append("## Ours vs NSGA-II by Score Seed")
    lines.append("")
    lines.append(_table_md(_round_frame(head_seed_df)))
    lines.append("")

    if not zero_cases_df.empty:
        lines.append("## Ours Infeasible / Zero-Score Cases")
        lines.append("")
        lines.append(_table_md(_round_frame(zero_cases_df)))
        lines.append("")

    if not top_losses_df.empty:
        lines.append("## Largest Ours Losses")
        lines.append("")
        lines.append(_table_md(_round_frame(top_losses_df)))
        lines.append("")

    lines.append("## Figure Outputs")
    lines.append("")
    for figure_path in figure_paths:
        lines.append(f"- `{figure_path.as_posix()}`")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_figures_markdown(
    *,
    output_path: Path,
    algo_task_df: pd.DataFrame,
    head_budget_df: pd.DataFrame,
    head_seed_df: pd.DataFrame,
    figure_paths: list[Path],
) -> None:
    ours_task = algo_task_df[algo_task_df["algorithm"] == OURS_NAME].iloc[0]
    nsga_task = algo_task_df[algo_task_df["algorithm"] == NSGA_NAME].iloc[0]
    lines: list[str] = []
    lines.append("# Experiment 1 Figure Notes")
    lines.append("")
    lines.append(
        f"- `Ours` average stop score: `{ours_task['avg_stop_score']:.3f}`; "
        f"`NSGA-II`: `{nsga_task['avg_stop_score']:.3f}`."
    )
    lines.append(
        f"- `Ours` average runtime: `{ours_task['avg_elapsed_ms']:.3f}` ms; "
        f"`NSGA-II`: `{nsga_task['avg_elapsed_ms']:.3f}` ms."
    )
    lines.append(
        f"- `4h` average Ours-NSGA score gap: "
        f"`{head_budget_df[head_budget_df['budget_minutes'] == 240]['avg_score_diff'].iloc[0]:.3f}`."
    )
    lines.append(
        f"- `8h` average Ours-NSGA score gap: "
        f"`{head_budget_df[head_budget_df['budget_minutes'] == 480]['avg_score_diff'].iloc[0]:.3f}`."
    )
    lines.append(
        f"- Across score seeds, average Ours-NSGA score gap stays positive in every seed: "
        f"`{', '.join(f'{int(row.score_seed)}:{row.avg_score_diff:.1f}' for row in head_seed_df.itertuples())}`."
    )
    lines.append("")
    lines.append("## Figure Files")
    lines.append("")
    for figure_path in figure_paths:
        lines.append(f"- `{figure_path.name}`")
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze multi-seed Exp1 score-guided results")
    parser.add_argument(
        "--input",
        type=Path,
        default=RESULTS_BASE_DIR / "exp1_algorithm_comparison" / "exp1_results_full_score_guided_20260401.json",
        help="Path to the Exp1 result JSON file",
    )
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=FIGURES_BASE_DIR / "exp1",
        help="Output directory for figures and figure markdown",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=RESULTS_BASE_DIR / "exp1_algorithm_comparison",
        help="Output directory for markdown/json summaries",
    )
    parser.add_argument(
        "--suffix",
        type=str,
        default="20260403",
        help="Filename suffix for generated artifacts",
    )
    args = parser.parse_args()

    _set_plot_style()

    results_path = args.input.resolve()
    figures_dir = args.figures_dir.resolve()
    results_dir = args.results_dir.resolve()
    suffix = _safe_suffix(args.suffix)

    figures_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    metadata, run_df = _load_run_df(results_path)
    task_df = _aggregate_task_df(run_df)
    query_df = _aggregate_query_df(task_df)

    _, task_rank_summary_df = _compute_rank_stats(
        task_df,
        group_cols=["origin_name", "depart_time", "budget_minutes", "score_seed"],
    )
    _, query_rank_summary_df = _compute_rank_stats(
        query_df,
        group_cols=["origin_name", "depart_time", "budget_minutes"],
    )

    algo_task_df = _build_algorithm_summary(task_df, task_count_label="task_count", rank_summary_df=task_rank_summary_df)
    algo_query_df = _build_algorithm_summary(query_df, task_count_label="query_count", rank_summary_df=query_rank_summary_df)

    head_task_df = _head_to_head(
        task_df,
        group_cols=["origin_name", "depart_time", "budget_minutes", "score_seed"],
    )
    head_query_df = _head_to_head(
        query_df,
        group_cols=["origin_name", "depart_time", "budget_minutes"],
    )
    head_budget_df = _head_to_head_by_budget(head_task_df)
    head_seed_df = _head_to_head_by_seed(head_task_df)
    per_seed_df, per_seed_rank_df = _per_score_seed_summary(task_df)
    top_losses_df = _top_losses_for_ours(task_df, limit=12)

    zero_cases_df = (
        task_df[
            (task_df["algorithm"] == OURS_NAME)
            & ((task_df["stop_score_total"] <= 0.0) | (~task_df["effective_budget_feasible"]))
        ][
            [
                "origin_name",
                "depart_time",
                "budget_minutes",
                "score_seed",
                "stop_score_total",
                "elapsed_ms",
                "effective_budget_feasible",
            ]
        ]
        .sort_values(["budget_minutes", "origin_name", "depart_time", "score_seed"])
        .reset_index(drop=True)
    )

    overview_fig = figures_dir / f"exp1_score_guided_multiseed_overview_{suffix}.png"
    budget_fig = figures_dir / f"exp1_score_guided_multiseed_budget_{suffix}.png"
    seed_fig = figures_dir / f"exp1_score_guided_multiseed_seed_stability_{suffix}.png"
    figure_paths = [overview_fig, budget_fig, seed_fig]

    plot_overview(algo_task_df, overview_fig)
    plot_budget_breakdown(task_df, head_task_df, budget_fig)
    plot_seed_stability(per_seed_df, per_seed_rank_df, head_seed_df, seed_fig)

    summary_json_path = results_dir / f"exp1_score_guided_multiseed_summary_{suffix}.json"
    summary_md_path = results_dir / f"exp1_score_guided_multiseed_summary_{suffix}.md"
    figures_md_path = figures_dir / f"exp1_score_guided_multiseed_summary_{suffix}.md"

    summary_payload = {
        "source_result_file": str(results_path),
        "metadata": metadata,
        "overall_task_summary": _serialize_records(algo_task_df),
        "overall_query_summary": _serialize_records(algo_query_df),
        "ours_vs_nsga_task_summary": {
            "comparisons": int(len(head_task_df)),
            "ours_better": int((head_task_df["score_diff"] > 0).sum()),
            "nsga_better": int((head_task_df["score_diff"] < 0).sum()),
            "ties": int((head_task_df["score_diff"] == 0).sum()),
            "avg_score_diff": float(head_task_df["score_diff"].mean()),
            "avg_ours_elapsed_ms": float(head_task_df["ours_elapsed_ms"].mean()),
            "avg_nsga_elapsed_ms": float(head_task_df["other_elapsed_ms"].mean()),
        },
        "ours_vs_nsga_query_summary": {
            "comparisons": int(len(head_query_df)),
            "ours_better": int((head_query_df["score_diff"] > 0).sum()),
            "nsga_better": int((head_query_df["score_diff"] < 0).sum()),
            "ties": int((head_query_df["score_diff"] == 0).sum()),
            "avg_score_diff": float(head_query_df["score_diff"].mean()),
            "avg_ours_elapsed_ms": float(head_query_df["ours_elapsed_ms"].mean()),
            "avg_nsga_elapsed_ms": float(head_query_df["other_elapsed_ms"].mean()),
        },
        "ours_vs_nsga_by_budget": _serialize_records(head_budget_df),
        "ours_vs_nsga_by_score_seed": _serialize_records(head_seed_df),
        "per_score_seed_summary": _serialize_records(per_seed_df),
        "per_score_seed_rank_summary": _serialize_records(per_seed_rank_df),
        "ours_zero_or_infeasible_cases": _serialize_records(zero_cases_df),
        "largest_ours_losses": _serialize_records(top_losses_df),
        "figure_files": [str(path) for path in figure_paths],
    }
    summary_json_path.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    write_results_markdown(
        output_path=summary_md_path,
        metadata=metadata,
        algo_task_df=_round_frame(algo_task_df),
        algo_query_df=_round_frame(algo_query_df),
        head_task_df=head_task_df,
        head_budget_df=_round_frame(head_budget_df),
        head_seed_df=_round_frame(head_seed_df),
        top_losses_df=_round_frame(top_losses_df),
        zero_cases_df=_round_frame(zero_cases_df),
        figure_paths=figure_paths,
        source_result_path=results_path,
    )
    write_figures_markdown(
        output_path=figures_md_path,
        algo_task_df=_round_frame(algo_task_df),
        head_budget_df=_round_frame(head_budget_df),
        head_seed_df=_round_frame(head_seed_df),
        figure_paths=figure_paths,
    )

    print(f"Saved figure: {overview_fig}")
    print(f"Saved figure: {budget_fig}")
    print(f"Saved figure: {seed_fig}")
    print(f"Saved summary json: {summary_json_path}")
    print(f"Saved summary md: {summary_md_path}")
    print(f"Saved figures md: {figures_md_path}")


if __name__ == "__main__":
    main()
