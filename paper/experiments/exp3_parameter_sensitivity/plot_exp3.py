#!/usr/bin/env python3
"""
Experiment 3 plotting and table generation for balance analysis supplementary to Experiment 1.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", tempfile.gettempdir())

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from paper.experiments.exp3_parameter_sensitivity.exp3_balance_common import (
    DEFAULT_EXP3_RESULTS,
    DEFAULT_EXP3_RESULTS_QUICK,
    EXP3_FIGURES_DIR,
    OURS_NAME,
    REFERENCE_NAME,
    add_tradeoff_metrics,
    build_algorithm_summary,
    build_budget_summary,
    build_head_to_head_detail,
    build_query_level_frame,
    df_markdown,
    load_task_frame,
    parse_csv_tokens,
    present_algorithm_summary,
    present_budget_summary,
    summarize_tradeoff_by_budget,
    summarize_tradeoff_counts,
)


plt.style.use("default")
sns.set_theme(style="whitegrid")
sns.set_context("paper", font_scale=1.15)


def _suffix(quick: bool) -> str:
    return "_quick" if quick else ""


def _save_markdown(path: Path, title: str, sections: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = [f"# {title}", ""] + sections
    path.write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")
    print(f"Saved: {path}")


def _save_figure(fig: plt.Figure, out_dir: Path, stem: str, *, suffix: str) -> None:
    png_out = out_dir / f"{stem}{suffix}.png"
    pdf_out = out_dir / f"{stem}{suffix}.pdf"
    fig.savefig(png_out, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_out, bbox_inches="tight")
    print(f"Saved: {png_out}")
    print(f"Saved: {pdf_out}")


def _plot_quality_speed_scatter(query_df: pd.DataFrame, out_dir: Path, *, suffix: str) -> None:
    if query_df.empty:
        return

    base = query_df.copy()
    base["algorithm"] = base["algorithm"].astype(str)
    summary = (
        base.groupby(["budget_minutes", "budget_label", "algorithm"], as_index=False, observed=True)
        .agg(
            stop_score_total=("stop_score_total", "mean"),
            elapsed_ms=("elapsed_ms", "mean"),
        )
        .sort_values(["budget_minutes", "algorithm"])
    )
    budgets = summary["budget_minutes"].dropna().unique().tolist()
    if not budgets:
        return

    fig, axes = plt.subplots(1, len(budgets), figsize=(6.5 * len(budgets), 5.4), squeeze=False)
    axes_flat = axes.flatten()

    for ax, budget in zip(axes_flat, budgets):
        part = summary[summary["budget_minutes"] == budget].copy()
        sns.scatterplot(
            data=part,
            x="elapsed_ms",
            y="stop_score_total",
            hue="algorithm",
            legend=False,
            ax=ax,
        )
        ax.set_xscale("log")
        ax.set_title(f"Budget {int(budget) // 60}h")
        ax.set_xlabel("Elapsed (ms, log scale)")
        ax.set_ylabel("Stop Score")
        for row in part.itertuples():
            ax.annotate(
                str(row.algorithm),
                (float(row.elapsed_ms), float(row.stop_score_total)),
                textcoords="offset points",
                xytext=(4, 4),
                fontsize=8,
            )
    for ax in axes_flat[len(budgets):]:
        ax.axis("off")

    plt.tight_layout()
    _save_figure(fig, out_dir, "exp3_quality_speed_scatter", suffix=suffix)
    plt.close(fig)

def _plot_ideal_distance(task_df: pd.DataFrame, out_dir: Path, *, suffix: str) -> None:
    if task_df.empty:
        return
    base = task_df.copy()
    base["algorithm"] = base["algorithm"].astype(str)
    summary = (
        base.groupby(["budget_minutes", "budget_label", "algorithm"], as_index=False, observed=True)
        .agg(avg_ideal_distance=("ideal_distance", "mean"))
        .sort_values(["budget_minutes", "algorithm"])
    )
    summary["budget_hours"] = summary["budget_minutes"] / 60.0
    fig = plt.figure(figsize=(10.8, 5.6))
    sns.lineplot(
        data=summary,
        x="budget_hours",
        y="avg_ideal_distance",
        hue="algorithm",
        style="algorithm",
        markers=True,
        dashes=False,
    )
    plt.xlabel("Budget (hours)")
    plt.ylabel("Average Ideal-Point Distance")
    plt.title("Exp3 Supplement to Exp1: Balance Trend by Budget")
    plt.xticks(sorted(summary["budget_hours"].dropna().unique().tolist()))
    plt.tight_layout()
    _save_figure(fig, out_dir, "exp3_ideal_distance", suffix=suffix)
    plt.close(fig)


def _write_tradeoff_summary(task_df: pd.DataFrame, query_df: pd.DataFrame, out_dir: Path, *, suffix: str) -> None:
    task_summary = present_algorithm_summary(build_algorithm_summary(task_df, count_label="task_count"), count_label="task_count")
    query_summary = present_algorithm_summary(build_algorithm_summary(query_df, count_label="query_count"), count_label="query_count")
    budget_summary = present_budget_summary(build_budget_summary(task_df, count_label="task_count"), count_label="task_count")

    sections = [
        "## Task-Level Summary",
        "",
        df_markdown(task_summary),
        "",
        "## Query-Level Summary",
        "",
        df_markdown(query_summary),
        "",
        "## Task-Level Summary by Budget",
        "",
        df_markdown(budget_summary),
        "",
    ]
    _save_markdown(out_dir / f"exp3_tradeoff_summary{suffix}.md", "Exp3 Balance Summary (Supplement to Exp1)", sections)


def _pick_reference(task_df: pd.DataFrame, *, left_algo: str, right_algo: str) -> str:
    if task_df.empty:
        return right_algo
    algos = [str(x) for x in task_df["algorithm"].dropna().astype(str).unique().tolist()]
    if right_algo in algos:
        return right_algo
    for candidate in algos:
        if candidate != left_algo:
            return candidate
    return right_algo


def _write_head_to_head(
    task_df: pd.DataFrame,
    query_df: pd.DataFrame,
    out_dir: Path,
    *,
    left_algo: str,
    right_algo: str,
    suffix: str,
) -> None:
    task_detail = build_head_to_head_detail(
        task_df,
        left_algo=left_algo,
        right_algo=right_algo,
        group_cols=["origin_name", "depart_time", "budget_minutes", "score_seed"],
    )
    query_detail = build_head_to_head_detail(
        query_df,
        left_algo=left_algo,
        right_algo=right_algo,
        group_cols=["origin_name", "depart_time", "budget_minutes"],
    )

    sections = [
        f"## {left_algo} vs {right_algo} Task-Level",
        "",
        df_markdown(summarize_tradeoff_counts(task_detail)),
        "",
        "### By Budget",
        "",
        df_markdown(summarize_tradeoff_by_budget(task_detail)),
        "",
        f"## {OURS_NAME} vs {REFERENCE_NAME} Query-Level",
        "",
        df_markdown(summarize_tradeoff_counts(query_detail)),
        "",
        "### By Budget",
        "",
        df_markdown(summarize_tradeoff_by_budget(query_detail)),
        "",
    ]
    _save_markdown(out_dir / f"exp3_head_to_head_tradeoff{suffix}.md", "Exp3 Head-to-Head Tradeoff", sections)
    if left_algo == OURS_NAME and right_algo == REFERENCE_NAME:
        _save_markdown(out_dir / f"exp3_ours_vs_nsga_tradeoff{suffix}.md", "Exp3 Ours vs NSGA-II Tradeoff", sections)


def _write_overview(
    task_df: pd.DataFrame,
    query_df: pd.DataFrame,
    out_dir: Path,
    *,
    left_algo: str,
    right_algo: str,
    suffix: str,
) -> None:
    task_summary = build_algorithm_summary(task_df, count_label="task_count")
    query_summary = build_algorithm_summary(query_df, count_label="query_count")
    task_detail = build_head_to_head_detail(
        task_df,
        left_algo=left_algo,
        right_algo=right_algo,
        group_cols=["origin_name", "depart_time", "budget_minutes", "score_seed"],
    )
    query_detail = build_head_to_head_detail(
        query_df,
        left_algo=left_algo,
        right_algo=right_algo,
        group_cols=["origin_name", "depart_time", "budget_minutes"],
    )
    task_counts = summarize_tradeoff_counts(task_detail).set_index("tradeoff_category") if not task_detail.empty else pd.DataFrame()
    query_counts = summarize_tradeoff_counts(query_detail).set_index("tradeoff_category") if not query_detail.empty else pd.DataFrame()

    sections: list[str] = []
    if not task_summary.empty:
        leader = task_summary.iloc[0]
        best_query_balance = query_summary.sort_values("avg_ideal_distance", ascending=True).iloc[0]
        sections.extend(
            [
                "## Key Findings",
                "",
                f"- Experiment 3 should be framed as a supplement to Experiment 1, focusing on whether the methods remain close to the score-time ideal point.",
                f"- Task-level balance leader: `{leader['algorithm']}` "
                f"(average ideal-point distance `{leader['avg_ideal_distance']:.3f}`).",
                f"- Query-level closest to the quality-speed ideal point: `{best_query_balance['algorithm']}` "
                f"(distance `{best_query_balance['avg_ideal_distance']:.3f}`).",
            ]
        )
        if not task_counts.empty:
            sections.append(
                f"- `{left_algo}` vs `{right_algo}` on task-level: "
                f"`{int(task_counts.loc['higher score + faster', 'count'])}` higher-score-and-faster tasks, "
                f"`{int(task_counts.loc['higher score + slower', 'count'])}` higher-score-but-slower tasks, "
                f"`{int(task_counts.loc['lower score + faster', 'count'])}` lower-score-but-faster tasks."
            )
        if not query_counts.empty:
            sections.append(
                f"- Query-level summary: `{left_algo}` has "
                f"`{int(query_counts.loc['higher score + faster', 'count'])}` higher-score-and-faster queries."
            )
        sections.append("")

    _save_markdown(out_dir / f"exp3_overview{suffix}.md", "Exp3 Overview (Supplement to Exp1)", sections)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot Exp3 quality-speed balance outputs.")
    parser.add_argument("--quick", action="store_true", help="Use exp3_results_quick.json.")
    parser.add_argument("--input", type=Path, default=None, help="Optional explicit task-level input path.")
    parser.add_argument("--figures-dir", type=Path, default=EXP3_FIGURES_DIR, help="Output directory.")
    parser.add_argument("--left-algo", type=str, default=OURS_NAME, help="Left algorithm for head-to-head tradeoff.")
    parser.add_argument("--right-algo", type=str, default=REFERENCE_NAME, help="Right algorithm for head-to-head tradeoff.")
    parser.add_argument(
        "--name-tag",
        type=str,
        default="",
        help="Optional output filename tag (e.g., recent2).",
    )
    args = parser.parse_args()

    input_path = args.input.resolve() if args.input else (DEFAULT_EXP3_RESULTS_QUICK if args.quick else DEFAULT_EXP3_RESULTS)
    _, task_df = load_task_frame(input_path)
    task_df = add_tradeoff_metrics(task_df, group_cols=["origin_name", "depart_time", "budget_minutes", "score_seed"])
    query_df = build_query_level_frame(task_df)

    out_dir = args.figures_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = _suffix(args.quick)
    tag = "_".join(parse_csv_tokens(args.name_tag.replace("-", "_").replace("|", "_")))
    if tag:
        suffix = f"{suffix}_{tag}"
    right_algo = _pick_reference(task_df, left_algo=args.left_algo, right_algo=args.right_algo)

    _plot_quality_speed_scatter(query_df, out_dir, suffix=suffix)
    _plot_ideal_distance(task_df, out_dir, suffix=suffix)
    _write_tradeoff_summary(task_df, query_df, out_dir, suffix=suffix)
    _write_head_to_head(task_df, query_df, out_dir, left_algo=args.left_algo, right_algo=right_algo, suffix=suffix)
    _write_overview(task_df, query_df, out_dir, left_algo=args.left_algo, right_algo=right_algo, suffix=suffix)


if __name__ == "__main__":
    main()
