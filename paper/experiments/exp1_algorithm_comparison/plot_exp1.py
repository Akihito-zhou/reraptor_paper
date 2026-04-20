#!/usr/bin/env python3
"""
Experiment 1: publication-ready plotting & statistical validation.

Outputs are designed for the research plan:
1) Fig.3 style Pareto scatter (time vs quality) with clear grouping by budget.
2) Fig.4 style radar chart (multi-metric normalized comparison).
3) Clean metric panels and win-count heatmap (readable, non-cluttered).
4) Summary table + Wilcoxon tests on query-level means (60 independent queries).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# Add experiments root to PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.config import FIGURES_BASE_DIR, RESULTS_BASE_DIR
from common.io_utils import load_results
from common.utils import is_pareto_optimal


def _set_plot_style() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False


def _primary_metric(columns: list[str] | pd.Index) -> str:
    return "stop_score_total" if "stop_score_total" in set(columns) else "composite_score"


def _primary_label(metric: str) -> str:
    return "Stop Score" if metric == "stop_score_total" else "Composite Score"


def _prepare_views(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return query-level and algorithm-level views."""
    numeric_cols = [
        "elapsed_ms",
        "ride_minutes",
        "distance_km",
        "unique_stops",
        "legs",
        "hull_area",
        "composite_score",
        "stop_score_total",
        "scored_stop_count",
        "dwell_minutes_total",
        "effective_time_minutes",
        "score_per_hour",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    agg_spec: dict[str, tuple[str, str]] = {}
    for col in numeric_cols:
        if col in df.columns:
            agg_spec[col] = (col, "mean")
    agg_spec["feasible_rate"] = ("feasible", "mean")

    query_df = df.groupby(["algorithm", "origin", "depart_time", "budget_minutes"], as_index=False).agg(**agg_spec)

    algo_agg: dict[str, tuple[str, str]] = {}
    for col in query_df.columns:
        if col not in {"algorithm", "origin", "depart_time", "budget_minutes"}:
            algo_agg[col] = (col, "mean")
    algo_df = query_df.groupby("algorithm", as_index=False).agg(**algo_agg)
    algo_df = algo_df.sort_values(_primary_metric(algo_df.columns), ascending=False)
    return query_df, algo_df


def _algo_order(algo_df: pd.DataFrame) -> list[str]:
    primary = _primary_metric(algo_df.columns)
    return algo_df.sort_values(primary, ascending=False)["algorithm"].tolist()


def generate_summary_table(
    query_df: pd.DataFrame,
    output_dir: Path,
    *,
    suffix: str = "",
    note: str | None = None,
) -> None:
    """Generate markdown summary with query-level means."""
    summary = query_df.groupby("algorithm").agg(
        **{
            col: (col, "mean")
            for col in [
                _primary_metric(query_df.columns),
                "score_per_hour",
                "elapsed_ms",
                "unique_stops",
                "hull_area",
                "dwell_minutes_total",
                "feasible_rate",
            ]
            if col in query_df.columns
        }
    )
    primary = _primary_metric(summary.columns)
    summary = summary.sort_values(primary, ascending=False)
    summary["rank_primary"] = np.arange(1, len(summary) + 1)
    ordered_cols = [
        "rank_primary",
        primary,
        "score_per_hour",
        "elapsed_ms",
        "unique_stops",
        "hull_area",
        "dwell_minutes_total",
        "feasible_rate",
    ]
    summary = summary[[col for col in ordered_cols if col in summary.columns]].round(4)

    out_path = output_dir / f"summary_table{suffix}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Experiment 1: Score-Based Comparison Summary (Query-Level Means)\n\n")
        f.write("- Aggregation unit: `(origin, depart_time, budget_minutes)` after averaging over available runs/seeds for each algorithm.\n")
        query_count = query_df[["origin", "depart_time", "budget_minutes"]].drop_duplicates().shape[0]
        f.write(f"- Number of independent queries: {query_count}.\n")
        f.write(f"- Primary metric: `{_primary_label(primary)}`.\n")
        if note:
            f.write(f"- Scope: {note}.\n")
        f.write("\n")
        f.write(summary.to_markdown())
        f.write("\n")
    print(f"Saved summary table to {out_path}")


def plot_pareto_front(query_df: pd.DataFrame, output_dir: Path) -> None:
    """
    Fig.3 style:
    - X: execution time (ms, log scale; lower is better)
    - Y: composite score (higher is better)
    - grouped by budget to avoid point overlap
    """
    primary = _primary_metric(query_df.columns)
    plot_df = (
        query_df.groupby(["algorithm", "budget_minutes"], as_index=False)
        .agg(elapsed_ms=("elapsed_ms", "mean"), primary_metric=(primary, "mean"))
    )

    fig, ax = plt.subplots(figsize=(13, 8))
    sns.scatterplot(
        data=plot_df,
        x="elapsed_ms",
        y="primary_metric",
        hue="algorithm",
        style="budget_minutes",
        s=180,
        palette="tab10",
        ax=ax,
    )

    # Draw Pareto fronts per budget for readability.
    for budget in sorted(plot_df["budget_minutes"].unique()):
        sub = plot_df[plot_df["budget_minutes"] == budget].copy()
        points = [[-row.elapsed_ms, row.primary_metric] for _, row in sub.iterrows()]
        mask = is_pareto_optimal(points, maximize=True)
        front = sub.iloc[mask].sort_values("elapsed_ms")
        if len(front) > 1:
            ax.plot(
                front["elapsed_ms"],
                front["primary_metric"],
                linestyle="--",
                linewidth=2,
                alpha=0.8,
                label=f"Pareto Front ({budget // 60}h)",
            )

    alias = {
        "Ours (Full)": "Ours",
        "Greedy (L=3)": "Greedy",
        "Pure RAPTOR": "Pure",
    }
    for _, row in plot_df.iterrows():
        short_name = alias.get(row["algorithm"], row["algorithm"])
        label = f"{short_name}-{int(row['budget_minutes']//60)}h"
        ax.annotate(
            label,
            (row["elapsed_ms"], row["primary_metric"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=9,
            alpha=0.9,
        )

    ax.set_xscale("log")
    ax.set_xlabel("Execution Time (ms, log scale)")
    ax.set_ylabel(f"{_primary_label(primary)} (higher is better)")
    ax.set_title("Experiment 1: Score-Runtime Pareto Comparison")
    ax.grid(True, which="both", linestyle="--", alpha=0.3)

    # Keep legend outside to preserve data area clarity.
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0)
    plt.tight_layout()

    out_path = output_dir / "exp1_pareto_front.png"
    plt.savefig(out_path, dpi=320, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved Pareto front plot to {out_path}")


def plot_radar_chart(algo_df: pd.DataFrame, output_dir: Path, *, top_k: int = 5) -> None:
    """Fig.4 style radar chart on normalized metrics for top algorithms."""
    primary = _primary_metric(algo_df.columns)
    metrics = {
        primary: "Score",
        "score_per_hour": "ScoreEff",
        "unique_stops": "Stops",
        "hull_area": "Hull",
        "time_eff": "TimeEff",
    }

    full = algo_df.copy()
    full["time_eff"] = 1.0 / (full["elapsed_ms"] + 1e-9)
    top_algos = full.sort_values(primary, ascending=False)["algorithm"].head(top_k).tolist()

    # Min-max normalization over all algorithms, then plot top-k only.
    norm = full.set_index("algorithm")
    for col in metrics:
        cmin = float(norm[col].min())
        cmax = float(norm[col].max())
        if cmax > cmin:
            norm[col] = (norm[col] - cmin) / (cmax - cmin)
        else:
            norm[col] = 1.0

    categories = list(metrics.values())
    cols = list(metrics.keys())
    angles = np.linspace(0, 2 * np.pi, len(cols), endpoint=False).tolist()
    angles += angles[:1]

    fig = plt.figure(figsize=(10, 10))
    ax = plt.subplot(111, polar=True)

    palette = sns.color_palette("tab10", n_colors=len(top_algos))
    for color, algo in zip(palette, top_algos):
        values = norm.loc[algo, cols].tolist()
        values += values[:1]
        ax.plot(angles, values, linewidth=2.5, label=algo, color=color)
        ax.fill(angles, values, alpha=0.12, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=9)
    ax.set_ylim(0, 1.0)
    ax.set_title("Experiment 1: Multi-Metric Radar (Top Algorithms)", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.30, 1.15))

    out_path = output_dir / "exp1_radar_chart.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=320, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved radar chart to {out_path}")


def _mean_ci95(series: pd.Series) -> tuple[float, float]:
    arr = pd.to_numeric(series, errors="coerce").dropna().to_numpy()
    if len(arr) == 0:
        return 0.0, 0.0
    mean = float(arr.mean())
    if len(arr) == 1:
        return mean, 0.0
    ci = 1.96 * float(arr.std(ddof=1)) / np.sqrt(len(arr))
    return mean, ci


def _plot_metric_panels_core(
    query_df: pd.DataFrame,
    algo_order: list[str],
    out_path: Path,
    *,
    title: str,
    n_queries: int,
) -> None:
    """Render four horizontal bar panels with 95% CI for a given query slice."""
    metric_cfg = [
        (_primary_metric(query_df.columns), _primary_label(_primary_metric(query_df.columns)), False, "viridis"),
        ("elapsed_ms", "Execution Time (ms)", True, "mako"),
        ("unique_stops", "Visited Stops", False, "crest"),
        ("hull_area", "Convex Hull Area", False, "rocket"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    axes = axes.flatten()

    for ax, (metric, title, log_scale, cmap_name) in zip(axes, metric_cfg):
        rows = []
        for algo in algo_order:
            sub = query_df[query_df["algorithm"] == algo][metric]
            mean, ci = _mean_ci95(sub)
            rows.append((algo, mean, ci))
        stats_df = pd.DataFrame(rows, columns=["algorithm", "mean", "ci"])
        ascending = metric == "elapsed_ms"
        stats_df = stats_df.sort_values("mean", ascending=ascending)

        colors = sns.color_palette(cmap_name, n_colors=len(stats_df))
        ax.barh(
            y=stats_df["algorithm"],
            width=stats_df["mean"],
            xerr=stats_df["ci"],
            color=colors,
            edgecolor="black",
            linewidth=0.3,
            alpha=0.9,
            capsize=3,
        )
        ax.set_title(title)
        ax.set_xlabel(f"Mean over {n_queries} queries (95% CI)")
        if log_scale:
            ax.set_xscale("log")
        ax.grid(axis="x", linestyle="--", alpha=0.3)

    fig.suptitle(title, fontsize=18, y=1.02)
    fig.tight_layout()
    fig.savefig(out_path, dpi=320, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved metric panels to {out_path}")


def plot_metric_panels(query_df: pd.DataFrame, algo_order: list[str], output_dir: Path) -> None:
    """
    Overall metric panels across all query settings.

    Note: this intentionally mixes 4h/8h budgets into a global overview.
    For budget-specific views, see `plot_metric_panels_by_budget`.
    """
    n_queries = query_df[["origin", "depart_time", "budget_minutes"]].drop_duplicates().shape[0]
    _plot_metric_panels_core(
        query_df,
        algo_order,
        output_dir / "exp1_metric_panels.png",
        title="Experiment 1: Algorithm Metric Panels (All Budgets)",
        n_queries=n_queries,
    )


def plot_metric_panels_by_budget(query_df: pd.DataFrame, algo_order: list[str], output_dir: Path) -> None:
    """Generate separate metric panels for each budget bucket (e.g., 4h vs 8h)."""
    if "budget_minutes" not in query_df.columns:
        return

    budgets = sorted(query_df["budget_minutes"].dropna().unique().tolist())
    for budget in budgets:
        sub = query_df[query_df["budget_minutes"] == budget].copy()
        if sub.empty:
            continue
        n_queries = sub[["origin", "depart_time", "budget_minutes"]].drop_duplicates().shape[0]
        budget_hours = int(budget // 60)
        _plot_metric_panels_core(
            sub,
            algo_order,
            output_dir / f"exp1_metric_panels_{budget_hours}h.png",
            title=f"Experiment 1: Algorithm Metric Panels ({budget_hours}h Budget)",
            n_queries=n_queries,
        )


def plot_win_heatmap(query_df: pd.DataFrame, output_dir: Path) -> None:
    """Heatmap: primary-metric winners across (depart_time, budget) buckets."""
    primary = _primary_metric(query_df.columns)
    key_cols = ["origin", "depart_time", "budget_minutes"]
    idx = query_df.groupby(key_cols)[primary].idxmax()
    winners = query_df.loc[idx].copy()
    winners["slot"] = winners.apply(
        lambda r: f"{int(r['depart_time']//60):02d}:00 | {int(r['budget_minutes']//60)}h",
        axis=1,
    )

    table = winners.pivot_table(
        index="algorithm",
        columns="slot",
        values="origin",
        aggfunc="count",
        fill_value=0,
    ).sort_index(axis=1)

    algorithm_order = (
        winners["algorithm"].value_counts().index.tolist()
        if not winners.empty
        else table.index.tolist()
    )
    table = table.reindex(algorithm_order)

    plt.figure(figsize=(11, 6))
    sns.heatmap(
        table,
        annot=True,
        fmt="d",
        cmap="YlGnBu",
        linewidths=0.5,
        cbar_kws={"label": "Winner Count"},
    )
    plt.title(f"{_primary_label(primary)} Winner Count by Time-Budget Slot (60 Queries)")
    plt.xlabel("Departure Time | Budget")
    plt.ylabel("Algorithm")
    plt.tight_layout()

    out_path = output_dir / "exp1_win_heatmap.png"
    plt.savefig(out_path, dpi=320, bbox_inches="tight")
    plt.close()
    print(f"Saved win heatmap to {out_path}")


def run_statistical_tests(
    query_df: pd.DataFrame,
    output_dir: Path,
    *,
    suffix: str = "",
    note: str | None = None,
) -> None:
    """
    Wilcoxon tests on query-level means (N=60 independent queries),
    pairing by (origin, depart_time, budget_minutes).
    """
    out_path = output_dir / f"statistical_tests{suffix}.md"
    baseline = "Ours (Full)"
    if baseline not in set(query_df["algorithm"]):
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("Baseline model not found. Could not run statistical differences.\n")
        return

    primary = _primary_metric(query_df.columns)
    test_metrics = [primary, "unique_stops", "hull_area", "elapsed_ms"]
    key_cols = ["origin", "depart_time", "budget_minutes"]

    base = query_df[query_df["algorithm"] == baseline].copy()
    base["match_key"] = base[key_cols].astype(str).agg("_".join, axis=1)
    base = base.set_index("match_key")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Wilcoxon Signed-Rank Test Results (Query-Level Means)\n\n")
        f.write(f"**Baseline:** `{baseline}`\n")
        pair_count = query_df[["origin", "depart_time", "budget_minutes"]].drop_duplicates().shape[0]
        f.write(f"Paired by `(origin, depart_time, budget_minutes)`, N={pair_count}.\n")
        f.write(f"Primary metric: `{_primary_label(primary)}`.\n")
        if note:
            f.write(f"Scope: {note}.\n")
        f.write("\n")

        for metric in test_metrics:
            f.write(f"## Metric: `{metric}`\n")
            f.write("| Algorithm | Pairs (N) | Mean Diff (Ours-Other) | W-Statistic | p-value | Significant (p<0.05) |\n")
            f.write("|---|---:|---:|---:|---:|---|\n")

            for algo in sorted(set(query_df["algorithm"]) - {baseline}):
                other = query_df[query_df["algorithm"] == algo].copy()
                other["match_key"] = other[key_cols].astype(str).agg("_".join, axis=1)
                other = other.set_index("match_key")

                common = base.index.intersection(other.index)
                if len(common) < 5:
                    f.write(f"| {algo} | {len(common)} | N/A | N/A | N/A | N/A |\n")
                    continue

                x = base.loc[common, metric].to_numpy()
                y = other.loc[common, metric].to_numpy()
                diff = x - y
                mean_diff = float(diff.mean())
                if np.allclose(diff, 0):
                    f.write(f"| {algo} | {len(common)} | {mean_diff:+.6f} | 0.0 | 1.000000 | No |\n")
                    continue

                w, pval = stats.wilcoxon(x, y, zero_method="wilcox", alternative="two-sided")
                sig = "Yes" if pval < 0.05 else "No"
                f.write(f"| {algo} | {len(common)} | {mean_diff:+.6f} | {w:.1f} | {pval:.6g} | {sig} |\n")
            f.write("\n")
    print(f"Saved statistical tests to {out_path}")


def generate_budget_sliced_reports(query_df: pd.DataFrame, output_dir: Path) -> None:
    """Generate summary/statistical markdown files per budget."""
    if "budget_minutes" not in query_df.columns:
        return

    budgets = sorted(query_df["budget_minutes"].dropna().unique().tolist())
    for budget in budgets:
        sub = query_df[query_df["budget_minutes"] == budget].copy()
        if sub.empty:
            continue
        hours = int(budget // 60)
        suffix = f"_{hours}h"
        note = f"{hours}h budget only"
        generate_summary_table(sub, output_dir, suffix=suffix, note=note)
        run_statistical_tests(sub, output_dir, suffix=suffix, note=note)


def main(quick_mode: bool = False) -> None:
    _set_plot_style()

    filename = "exp1_results_quick.json" if quick_mode else "exp1_results.json"
    results_path = RESULTS_BASE_DIR / "exp1_algorithm_comparison" / filename
    if not results_path.exists():
        print(f"Results file not found: {results_path}")
        print("Please run run_exp1.py first.")
        sys.exit(1)

    metadata, results = load_results(results_path)
    df = pd.DataFrame(results)
    if df.empty:
        print("No results found in the file.")
        sys.exit(1)

    out_dir = FIGURES_BASE_DIR / ("exp1_quick" if quick_mode else "exp1")
    out_dir.mkdir(parents=True, exist_ok=True)

    query_df, algo_df = _prepare_views(df)
    order = _algo_order(algo_df)
    budget_hours = sorted(int(x // 60) for x in query_df["budget_minutes"].dropna().unique().tolist())
    if len(budget_hours) > 1:
        scope_note = "all budgets combined (4h + 8h)"
    elif budget_hours:
        scope_note = f"{budget_hours[0]}h budget only"
    else:
        scope_note = "combined"

    generate_summary_table(query_df, out_dir, note=scope_note)
    run_statistical_tests(query_df, out_dir, note=scope_note)
    generate_budget_sliced_reports(query_df, out_dir)
    plot_pareto_front(query_df, out_dir)
    plot_radar_chart(algo_df, out_dir, top_k=5)
    plot_metric_panels(query_df, order, out_dir)
    plot_metric_panels_by_budget(query_df, order, out_dir)
    plot_win_heatmap(query_df, out_dir)

    print(f"All Exp1 artifacts generated in: {out_dir}")
    print(f"Using results timestamp: {metadata.get('timestamp', 'unknown')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot Experiment 1 Results")
    parser.add_argument("--quick", action="store_true", help="Load quick mode results")
    args = parser.parse_args()
    main(quick_mode=args.quick)
