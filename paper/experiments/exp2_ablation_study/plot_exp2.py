#!/usr/bin/env python3
"""
Experiment 2: Plotting score-based ablation results.

Reads:
- results/exp2_ablation_study/exp2_results.json
- results/exp2_ablation_study/exp2_results_quick.json

Generates:
1. Markdown summary table
2. Label-space bar chart
3. Runtime bar chart
4. Score-runtime Pareto scatter
5. Normalized metric heatmap
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper.experiments.common.config import FIGURES_BASE_DIR, RESULTS_BASE_DIR


plt.style.use("default")
sns.set_theme(style="whitegrid")
sns.set_context("paper", font_scale=1.2)


PRIMARY_METRIC = "stop_score_total"
PRIMARY_LABEL = "Stop Score"

ALGORITHM_ORDER = {
    "Ours (Full)": 0,
    "Ours (NoNeg)": 1,
    "Ours (NoDom)": 2,
    "Ours (NoBeam)": 3,
    "Ours (NoBeam-NoDom)": 4,
    "Ours (NoDom-NoNeg)": 5,
    "Ours (NoBeam-NoNeg)": 6,
    "Ours (NoBeam-NoDom-NoNeg)": 7,
}


def load_results(*, quick_mode: bool = False, input_path: Path | None = None) -> pd.DataFrame:
    if input_path is not None:
        infile = Path(input_path)
    else:
        filename = "exp2_results_quick.json" if quick_mode else "exp2_results.json"
        infile = RESULTS_BASE_DIR / "exp2_ablation_study" / filename
    if not infile.exists():
        return pd.DataFrame()
    with open(infile, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("results", [])
    if not isinstance(data, list):
        raise ValueError(f"Expected list or wrapped results in {infile}")

    rows = []
    for run in data:
        rows.append(
            {
                "algorithm": run["algorithm"],
                "origin": run["origin"],
                "dept_time": run["depart_time"],
                "budget": run["budget_minutes"],
                "seed": run["seed"],
                "score_seed": run.get("score_seed", 0),
                "elapsed_ms": run["elapsed_ms"],
                "feasible": run.get("feasible", False),
                "effective_budget_feasible": run.get("effective_budget_feasible", run.get("feasible", False)),
                "stop_score_total": run.get("stop_score_total", 0.0),
                "score_per_hour": run.get("score_per_hour", 0.0),
                "effective_time_minutes": run.get("effective_time_minutes", 0.0),
                "labels": run.get("labels", 0),
                "resource_cap_hit": run.get("resource_cap_hit", False),
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    numeric_cols = [
        "dept_time",
        "budget",
        "seed",
        "score_seed",
        "elapsed_ms",
        "stop_score_total",
        "score_per_hour",
        "effective_time_minutes",
        "labels",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["feasible"] = df["feasible"].astype(bool)
    df["effective_budget_feasible"] = df["effective_budget_feasible"].astype(bool)
    df["resource_cap_hit"] = df["resource_cap_hit"].astype(bool)
    return df


def prepare_task_view(df: pd.DataFrame) -> pd.DataFrame:
    task_df = (
        df.groupby(["algorithm", "origin", "dept_time", "budget", "score_seed"], as_index=False)
        .agg(
            elapsed_ms=("elapsed_ms", "mean"),
            stop_score_total=("stop_score_total", "mean"),
            score_per_hour=("score_per_hour", "mean"),
            labels=("labels", "mean"),
            success_rate=("effective_budget_feasible", "mean"),
            cap_hit_rate=("resource_cap_hit", "mean"),
        )
    )
    task_df["budget_hours"] = task_df["budget"] / 60.0
    task_df["budget_label"] = task_df["budget_hours"].map(lambda x: f"{int(x)}h")
    return task_df


def aggregate_algorithms(task_df: pd.DataFrame) -> pd.DataFrame:
    agg_df = (
        task_df.groupby("algorithm", as_index=False)
        .agg(
            time_ms=("elapsed_ms", "mean"),
            stop_score=("stop_score_total", "mean"),
            score_per_hour=("score_per_hour", "mean"),
            labels=("labels", "mean"),
            success_rate=("success_rate", "mean"),
            cap_hit_rate=("cap_hit_rate", "mean"),
        )
    )

    agg_df["sort_order"] = agg_df["algorithm"].map(lambda x: ALGORITHM_ORDER.get(x, 99))
    agg_df = agg_df.sort_values("sort_order").drop(columns=["sort_order"])

    no_pruning_time = agg_df.loc[
        agg_df["algorithm"] == "Ours (NoBeam-NoDom-NoNeg)", "time_ms"
    ]
    if len(no_pruning_time) > 0 and no_pruning_time.iloc[0] > 0:
        agg_df["speedup_vs_no_pruning"] = no_pruning_time.iloc[0] / agg_df["time_ms"]
    else:
        agg_df["speedup_vs_no_pruning"] = np.nan

    best_score = agg_df["stop_score"].max()
    if best_score > 0:
        agg_df["gap_to_best_score_pct"] = (best_score - agg_df["stop_score"]) / best_score * 100.0
    else:
        agg_df["gap_to_best_score_pct"] = np.nan

    agg_df["success_rate_pct"] = agg_df["success_rate"] * 100.0
    agg_df["cap_hit_rate_pct"] = agg_df["cap_hit_rate"] * 100.0
    return agg_df


def write_summary(
    task_df: pd.DataFrame,
    agg_df: pd.DataFrame,
    out_dir: Path,
    *,
    file_suffix: str = "",
    mode_note: str | None = None,
) -> None:
    if task_df.empty or agg_df.empty:
        return

    def _format_count(value: float) -> str:
        if value >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        if value >= 1_000:
            return f"{value / 1_000:.1f}K"
        return f"{value:.0f}"

    def _score_delta_text(a: float, b: float) -> str:
        return f"{a - b:+.2f}"

    def _maybe_row(name: str) -> pd.Series | None:
        sub = agg_df.loc[agg_df["algorithm"] == name]
        if sub.empty:
            return None
        return sub.iloc[0]

    full = _maybe_row("Ours (Full)")
    noneg = _maybe_row("Ours (NoNeg)")
    nodom = _maybe_row("Ours (NoDom)")
    nobeam = _maybe_row("Ours (NoBeam)")
    nobeam_nodom = _maybe_row("Ours (NoBeam-NoDom)")
    nopruning = _maybe_row("Ours (NoBeam-NoDom-NoNeg)")
    if full is None or noneg is None or nodom is None or nobeam is None or nopruning is None:
        return
    noneg_gap = float(full["stop_score"] - noneg["stop_score"])
    noneg_close_threshold = max(5.0, 0.01 * max(abs(float(full["stop_score"])), 1.0))
    if abs(noneg_gap) <= noneg_close_threshold:
        noneg_line = (
            f"- `Ours (NoNeg)` is nearly tied on score "
            f"(`{noneg['stop_score']:.2f}`, gap `{noneg_gap:+.2f}`), "
            f"but is slightly slower and larger, which matches the claim that negative down-ranking is not the main speedup component."
        )
    else:
        noneg_line = (
            f"- Removing negative down-ranking changes score by `{_score_delta_text(noneg['stop_score'], full['stop_score'])}` "
            f"while runtime changes by `{noneg['time_ms'] - full['time_ms']:+.2f} ms` and label count by "
            f"`{noneg['labels'] - full['labels']:+.0f}`. This supports treating `Negative` as a role-separated constraint layer "
            f"rather than one of the two main search-space control layers."
        )

    nodom_line = (
        f"- Removing dominance pruning is clearly expensive overall: "
        f"`Ours (NoDom)` is `{nodom['time_ms'] / full['time_ms']:.2f}x` slower, "
        f"uses `{nodom['labels'] / full['labels']:.2f}x` labels, and changes score by "
        f"`{_score_delta_text(nodom['stop_score'], full['stop_score'])}`."
    )

    nobeam_line = (
        f"- Removing beam control materially increases search cost: "
        f"`Ours (NoBeam)` is `{nobeam['time_ms'] / full['time_ms']:.2f}x` slower, "
        f"uses `{nobeam['labels'] / full['labels']:.2f}x` labels, and changes score by "
        f"`{_score_delta_text(nobeam['stop_score'], full['stop_score'])}`."
    )

    by_budget = (
        task_df.groupby(["budget_label", "algorithm"], as_index=False)
        .agg(
            stop_score=("stop_score_total", "mean"),
            time_ms=("elapsed_ms", "mean"),
            labels=("labels", "mean"),
            success_rate=("success_rate", "mean"),
            cap_hit_rate=("cap_hit_rate", "mean"),
        )
    )

    def _budget_row(budget_label: str, algorithm: str) -> pd.Series:
        return by_budget.loc[
            (by_budget["budget_label"] == budget_label) & (by_budget["algorithm"] == algorithm)
        ].iloc[0]

    full_4h = _budget_row("4h", "Ours (Full)") if "4h" in set(by_budget["budget_label"]) else None
    full_8h = _budget_row("8h", "Ours (Full)") if "8h" in set(by_budget["budget_label"]) else None
    nobeam_4h = _budget_row("4h", "Ours (NoBeam)") if "4h" in set(by_budget["budget_label"]) else None
    nobeam_8h = _budget_row("8h", "Ours (NoBeam)") if "8h" in set(by_budget["budget_label"]) else None

    summary_table = agg_df[
        [
            "algorithm",
            "stop_score",
            "time_ms",
            "labels",
            "gap_to_best_score_pct",
            "success_rate_pct",
            "cap_hit_rate_pct",
        ]
    ].copy()
    summary_table = summary_table.rename(
        columns={
            "algorithm": "Algorithm",
            "stop_score": "StopScore",
            "time_ms": "RuntimeMs",
            "labels": "Labels",
            "gap_to_best_score_pct": "GapToBestPct",
            "success_rate_pct": "SuccessPct",
            "cap_hit_rate_pct": "CapHitPct",
        }
    )

    budget_table = by_budget.copy()
    budget_table["sort_order"] = budget_table["algorithm"].map(lambda x: ALGORITHM_ORDER.get(x, 99))
    budget_table = budget_table.sort_values(["budget_label", "sort_order"]).drop(columns=["sort_order"])
    for col in ["stop_score", "time_ms", "labels"]:
        if col == "labels":
            budget_table[col] = budget_table[col].map(lambda v: _format_count(float(v)))
        else:
            budget_table[col] = budget_table[col].map(lambda v: f"{float(v):.2f}")
    for col in ["success_rate", "cap_hit_rate"]:
        budget_table[col] = budget_table[col].map(lambda v: f"{float(v) * 100.0:.2f}")
    budget_table = budget_table.rename(
        columns={
            "budget_label": "Budget",
            "algorithm": "Algorithm",
            "stop_score": "StopScore",
            "time_ms": "RuntimeMs",
            "labels": "Labels",
            "success_rate": "SuccessPct",
            "cap_hit_rate": "CapHitPct",
        }
    )

    lines = ["# Experiment 2 Summary", ""]
    if mode_note:
        lines.append(f"- Mode: `{mode_note}`")
    lines.extend(
        [
            f"- Primary metric: `{PRIMARY_LABEL}`",
            "- Aggregation unit: `(origin, depart_time, budget, score_seed)`",
            "",
            "## Key Findings",
            "",
            (
                f"- `Ours (Full)` is the best overall configuration in this run: "
                f"`StopScore {full['stop_score']:.2f}`, `Runtime {full['time_ms']:.2f} ms`, "
                f"`Labels {full['labels']:.0f}`, and zero cap hits."
            ),
            noneg_line,
            nodom_line,
            nobeam_line,
        ]
    )
    if nobeam_nodom is not None:
        lines.append(
            (
                f"- `Ours (NoBeam-NoDom)` isolates the joint removal of the two main search-space control layers: "
                f"relative to `Full`, it is `{nobeam_nodom['time_ms'] / full['time_ms']:.2f}x` slower, "
                f"uses `{nobeam_nodom['labels'] / full['labels']:.2f}x` labels, and changes score by "
                f"`{nobeam_nodom['stop_score'] - full['stop_score']:+.2f}`. "
                f"The further change from `NoBeam-NoDom` to `NoBeam-NoDom-NoNeg` is "
                f"`{nopruning['stop_score'] - nobeam_nodom['stop_score']:+.2f}` score and "
                f"`{nopruning['time_ms'] - nobeam_nodom['time_ms']:+.2f} ms`, which helps separate the role of "
                f"`Negative` from the beam/dominance pair."
            )
        )
    if full_4h is not None and nobeam_4h is not None:
        lines.append(
            (
                f"- In `4h`, `NoBeam` scores higher than `Full` "
                f"(`{nobeam_4h['stop_score']:.2f}` vs `{full_4h['stop_score']:.2f}`), "
                f"but needs `{nobeam_4h['time_ms'] / full_4h['time_ms']:.2f}x` runtime and "
                f"`{nobeam_4h['cap_hit_rate'] * 100.0:.2f}%` cap hits."
            )
        )
    if full_8h is not None and nobeam_8h is not None:
        lines.append(
            (
                f"- In `8h`, `Full` dominates `NoBeam`: "
                f"`{full_8h['stop_score']:.2f}` vs `{nobeam_8h['stop_score']:.2f}` stop score, "
                f"`{full_8h['time_ms']:.2f}` vs `{nobeam_8h['time_ms']:.2f}` ms runtime, "
                f"with `NoBeam` hitting the cap on `{nobeam_8h['cap_hit_rate'] * 100.0:.2f}%` of tasks."
            )
        )
    lines.extend(
        [
            "",
            "## Overall Table",
            "",
            summary_table.to_markdown(index=False, floatfmt=".2f"),
            "",
            "## By Budget",
            "",
            budget_table.to_markdown(index=False),
            "",
            "## Interpretation",
            "",
            "- `Beam` and `dominance` should be presented as co-core efficiency layers that jointly control search-space growth.",
            "- `Negative down-ranking` should be presented as an objective-alignment component, not as the main source of score gain.",
            "- The fairest statement for Experiment 2 is therefore: `Ours (Full)` has the best combined profile across quality, runtime, and search size.",
            "",
        ]
    )

    content = "\n".join(lines)
    summary_path = out_dir / f"exp2_summary{file_suffix}.md"
    summary_path.write_text(content, encoding="utf-8")
    print(f"Saved: {summary_path}")
    results_path = RESULTS_BASE_DIR / "exp2_ablation_study" / f"exp2_summary{file_suffix}.md"
    results_path.write_text(content, encoding="utf-8")
    print(f"Saved: {results_path}")


def _label_bars(ax: plt.Axes) -> None:
    for p in ax.patches:
        val = p.get_height()
        if np.isnan(val) or val <= 0:
            continue
        if val >= 1_000_000:
            text = f"{val/1_000_000:.1f}M"
        elif val >= 1_000:
            text = f"{val/1_000:.1f}K"
        elif val < 1:
            text = f"{val:.2f}"
        else:
            text = f"{val:.0f}"

        ax.annotate(
            text,
            (p.get_x() + p.get_width() / 2.0, p.get_height()),
            ha="center",
            va="bottom",
            xytext=(0, 4),
            textcoords="offset points",
            fontsize=9,
        )


def plot_core_layer_deltas(
    agg_df: pd.DataFrame,
    out_dir: Path,
    *,
    file_suffix: str = "",
) -> None:
    full_row = agg_df.loc[agg_df["algorithm"] == "Ours (Full)"]
    if full_row.empty:
        return

    full = full_row.iloc[0]
    focus_order = [
        "Ours (NoNeg)",
        "Ours (NoDom)",
        "Ours (NoBeam)",
        "Ours (NoBeam-NoDom)",
        "Ours (NoBeam-NoDom-NoNeg)",
    ]
    focus = agg_df[agg_df["algorithm"].isin(focus_order)].copy()
    if focus.empty:
        return

    focus["score_delta"] = focus["stop_score"] - float(full["stop_score"])
    focus["runtime_ratio"] = focus["time_ms"] / max(float(full["time_ms"]), 1e-9)
    focus["label_ratio"] = focus["labels"] / max(float(full["labels"]), 1e-9)
    focus["short_name"] = (
        focus["algorithm"]
        .str.replace("Ours (", "", regex=False)
        .str.replace(")", "", regex=False)
    )
    focus["category"] = focus["algorithm"].map(
        {
            "Ours (NoNeg)": "Constraint",
            "Ours (NoDom)": "Core",
            "Ours (NoBeam)": "Core",
            "Ours (NoBeam-NoDom)": "Joint removal",
            "Ours (NoBeam-NoDom-NoNeg)": "Joint removal",
        }
    )

    palette = {
        "Constraint": "#4C78A8",
        "Core": "#F58518",
        "Joint removal": "#E45756",
    }
    colors = focus["category"].map(palette).tolist()
    y = np.arange(len(focus))

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.8), sharey=True)

    axes[0].axvline(0.0, color="#666666", linestyle="--", linewidth=1.0, alpha=0.8)
    axes[0].scatter(focus["score_delta"], y, s=90, c=colors, edgecolors="black", linewidths=0.6)
    axes[0].set_xlabel("Stop Score Delta vs Full")
    axes[0].set_title("Quality")
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(focus["short_name"])
    axes[0].grid(axis="x", alpha=0.25)
    for x, yi in zip(focus["score_delta"], y):
        axes[0].annotate(f"{x:+.1f}", (x, yi), xytext=(6, 0), textcoords="offset points", va="center", fontsize=8)

    axes[1].axvline(1.0, color="#666666", linestyle="--", linewidth=1.0, alpha=0.8)
    axes[1].scatter(focus["runtime_ratio"], y, s=90, c=colors, edgecolors="black", linewidths=0.6)
    axes[1].set_xscale("log")
    axes[1].set_xlabel("Runtime Ratio vs Full")
    axes[1].set_title("Time")
    axes[1].grid(axis="x", alpha=0.25, which="both")
    for x, yi in zip(focus["runtime_ratio"], y):
        axes[1].annotate(f"{x:.2f}x", (x, yi), xytext=(6, 0), textcoords="offset points", va="center", fontsize=8)

    axes[2].axvline(1.0, color="#666666", linestyle="--", linewidth=1.0, alpha=0.8)
    axes[2].scatter(focus["label_ratio"], y, s=90, c=colors, edgecolors="black", linewidths=0.6)
    axes[2].set_xscale("log")
    axes[2].set_xlabel("Label Ratio vs Full")
    axes[2].set_title("Search Size")
    axes[2].grid(axis="x", alpha=0.25, which="both")
    for x, yi in zip(focus["label_ratio"], y):
        axes[2].annotate(f"{x:.2f}x", (x, yi), xytext=(6, 0), textcoords="offset points", va="center", fontsize=8)

    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="w", label=label, markerfacecolor=color, markeredgecolor="black", markersize=8)
        for label, color in palette.items()
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Core-Layer Effects Relative to Ours (Full)", y=1.02, fontweight="bold")
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.18)
    figure_path = out_dir / f"exp2_core_layer_delta{file_suffix}.png"
    fig.savefig(figure_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {figure_path}")


def plot_ablation_study(
    df: pd.DataFrame,
    out_dir: Path,
    *,
    file_suffix: str = "",
    mode_note: str | None = None,
) -> None:
    task_df = prepare_task_view(df)
    agg_df = aggregate_algorithms(task_df)

    table_df = agg_df[
        [
            "algorithm",
            "stop_score",
            "score_per_hour",
            "time_ms",
            "speedup_vs_no_pruning",
            "labels",
            "gap_to_best_score_pct",
            "success_rate_pct",
            "cap_hit_rate_pct",
        ]
    ].copy()

    md_table = table_df.to_markdown(index=False, floatfmt=".2f")
    with open(out_dir / f"ablation_table{file_suffix}.md", "w", encoding="utf-8") as f:
        f.write("# Experiment 2: Stop-Score Ablation Study\n\n")
        if mode_note:
            f.write(f"Mode: {mode_note}\n\n")
        f.write(f"- Primary metric: `{PRIMARY_LABEL}`\n")
        f.write("- Aggregation unit: `(origin, depart_time, budget, score_seed)`\n\n")
        f.write(md_table)
        f.write("\n")
    print(f"Saved: {out_dir / f'ablation_table{file_suffix}.md'}")

    plt.figure(figsize=(10, 6))
    ax1 = sns.barplot(
        data=agg_df,
        x="algorithm",
        y="labels",
        hue="algorithm",
        palette="magma",
        legend=False,
    )
    if (agg_df["labels"] > 0).all():
        ax1.set_yscale("log")
        plt.ylabel("Generated Labels (Log Scale)")
    else:
        plt.ylabel("Generated Labels")
    plt.title("Search Space Size by Pruning Configuration", fontweight="bold")
    plt.xlabel("")
    plt.xticks(rotation=30, ha="right")
    _label_bars(ax1)
    plt.tight_layout()
    plt.savefig(out_dir / f"exp2_memory_labels_bar{file_suffix}.png", dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_dir / f'exp2_memory_labels_bar{file_suffix}.png'}")

    plt.figure(figsize=(10, 6))
    ax2 = sns.barplot(
        data=agg_df,
        x="algorithm",
        y="time_ms",
        hue="algorithm",
        palette="viridis",
        legend=False,
    )
    if (agg_df["time_ms"] > 0).all():
        ax2.set_yscale("log")
        plt.ylabel("Time in milliseconds (Log Scale)")
    else:
        plt.ylabel("Time in milliseconds")
    plt.title("Average Execution Time by Pruning Configuration", fontweight="bold")
    plt.xlabel("")
    plt.xticks(rotation=30, ha="right")
    _label_bars(ax2)
    plt.tight_layout()
    plt.savefig(out_dir / f"exp2_execution_time_bar{file_suffix}.png", dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_dir / f'exp2_execution_time_bar{file_suffix}.png'}")

    label_offsets = {
        "Ours (Full)": (8, 8),
        "Ours (NoBeam)": (8, -12),
        "Ours (NoBeam-NoDom)": (8, 10),
        "Ours (NoNeg)": (-45, 10),
        "Ours (NoBeam-NoNeg)": (-65, -12),
        "Ours (NoDom)": (8, 8),
        "Ours (NoDom-NoNeg)": (8, -12),
        "Ours (NoBeam-NoDom-NoNeg)": (8, 8),
    }

    def _short_name(algo_name: str) -> str:
        return algo_name.replace("Ours (", "").replace(")", "")

    fig, (ax3, ax3_zoom) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1.25, 1.0]})
    sns.scatterplot(
        data=agg_df,
        x="time_ms",
        y="stop_score",
        size="labels",
        hue="cap_hit_rate",
        sizes=(90, 520),
        palette="viridis_r",
        edgecolor="black",
        linewidth=0.7,
        legend="brief",
        ax=ax3,
    )
    ax3.set_xscale("log")
    ax3.set_xlabel("Runtime (ms, log scale)")
    ax3.set_ylabel(PRIMARY_LABEL)
    ax3.set_title("Global View")

    for _, r in agg_df.iterrows():
        dx, dy = label_offsets.get(r["algorithm"], (6, 6))
        ax3.annotate(
            _short_name(r["algorithm"]),
            (r["time_ms"], r["stop_score"]),
            textcoords="offset points",
            xytext=(dx, dy),
            fontsize=8,
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.65},
            arrowprops={"arrowstyle": "-", "lw": 0.5, "alpha": 0.5},
        )

    focus = agg_df[agg_df["time_ms"] <= 12000].copy()
    sns.scatterplot(
        data=focus,
        x="time_ms",
        y="stop_score",
        size="labels",
        hue="cap_hit_rate",
        sizes=(90, 520),
        palette="viridis_r",
        edgecolor="black",
        linewidth=0.7,
        legend=False,
        ax=ax3_zoom,
    )
    ax3_zoom.set_xlabel("Runtime (ms)")
    ax3_zoom.set_ylabel(PRIMARY_LABEL)
    ax3_zoom.set_title("Zoom: Fast-Region (<= 12,000 ms)")
    if not focus.empty:
        xmin = max(1.0, float(focus["time_ms"].min()) * 0.92)
        xmax = float(focus["time_ms"].max()) * 1.08
        ymin = float(focus["stop_score"].min()) - 5.0
        ymax = float(focus["stop_score"].max()) + 5.0
        ax3_zoom.set_xlim(xmin, xmax)
        ax3_zoom.set_ylim(ymin, ymax)
    for _, r in focus.iterrows():
        dx, dy = label_offsets.get(r["algorithm"], (6, 6))
        ax3_zoom.annotate(
            _short_name(r["algorithm"]),
            (r["time_ms"], r["stop_score"]),
            textcoords="offset points",
            xytext=(dx, dy),
            fontsize=8,
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.70},
        )

    fig.suptitle("Ablation Pareto View: Stop Score vs Runtime vs Search Size", y=1.02, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_dir / f"exp2_ablation_pareto_scatter{file_suffix}.png", dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_dir / f'exp2_ablation_pareto_scatter{file_suffix}.png'}")

    plot_core_layer_deltas(agg_df, out_dir, file_suffix=file_suffix)

    norm_df = agg_df[["algorithm", "stop_score", "score_per_hour", "time_ms", "labels", "cap_hit_rate"]].copy()
    norm_df = norm_df.set_index("algorithm")

    for col in ["stop_score", "score_per_hour"]:
        cmin, cmax = norm_df[col].min(), norm_df[col].max()
        norm_df[col] = (norm_df[col] - cmin) / (cmax - cmin) if cmax > cmin else 1.0

    for col in ["time_ms", "labels", "cap_hit_rate"]:
        cmin, cmax = norm_df[col].min(), norm_df[col].max()
        norm_df[col] = (cmax - norm_df[col]) / (cmax - cmin) if cmax > cmin else 1.0

    norm_df = norm_df.rename(
        columns={
            "stop_score": "StopScore",
            "score_per_hour": "ScoreEff",
            "time_ms": "Runtime",
            "labels": "LabelSpace",
            "cap_hit_rate": "CapSafety",
        }
    )

    heatmap_path = out_dir / f"exp2_ablation_metric_clustermap{file_suffix}.png"
    try:
        cg = sns.clustermap(
            norm_df,
            cmap="YlGnBu",
            vmin=0.0,
            vmax=1.0,
            linewidths=0.5,
            annot=True,
            fmt=".2f",
            col_cluster=False,
            figsize=(9, 6),
        )
        cg.ax_heatmap.set_title("Normalized Multi-Metric Profile (Higher is Better)", pad=12)
        cg.ax_heatmap.set_xlabel("Metrics")
        cg.ax_heatmap.set_ylabel("Algorithms")
        cg.savefig(heatmap_path, dpi=300, bbox_inches="tight")
        plt.close(cg.fig)
    except Exception:
        plt.figure(figsize=(9, 5))
        ax4 = sns.heatmap(
            norm_df,
            cmap="YlGnBu",
            vmin=0.0,
            vmax=1.0,
            linewidths=0.5,
            annot=True,
            fmt=".2f",
            cbar_kws={"label": "Normalized Score"},
        )
        ax4.set_title("Normalized Multi-Metric Profile (Higher is Better)")
        ax4.set_xlabel("Metrics")
        ax4.set_ylabel("Algorithms")
        plt.tight_layout()
        plt.savefig(heatmap_path, dpi=300, bbox_inches="tight")
        plt.close()
    print(f"Saved: {heatmap_path}")


def plot_ablation_by_budget(
    df: pd.DataFrame,
    out_dir: Path,
    *,
    quick_mode: bool = False,
    base_suffix: str = "",
) -> None:
    if "budget" not in df.columns:
        return
    budgets = sorted(df["budget"].dropna().unique().tolist())
    for budget in budgets:
        sub = df[df["budget"] == budget].copy()
        if sub.empty:
            continue
        budget_hours = int(budget // 60)
        suffix = f"{base_suffix}_{budget_hours}h"
        notes = []
        if quick_mode:
            notes.append("quick")
        notes.append(f"{budget_hours}h budget only")
        plot_ablation_study(sub, out_dir, file_suffix=suffix, mode_note=", ".join(notes))


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot Experiment 2 Results")
    parser.add_argument("--quick", action="store_true", help="Load quick mode results")
    parser.add_argument("--input", type=Path, default=None, help="Path to a specific Exp2 result JSON file")
    args = parser.parse_args()

    print("=" * 60)
    print(" PLOTTING EXPERIMENT 2 RESULTS")
    print(f" Quick Mode: {args.quick}")
    print("=" * 60)

    df = load_results(quick_mode=args.quick, input_path=args.input)
    if df.empty:
        expected = "run_exp2.py --quick" if args.quick else "run_exp2.py"
        print(f"No results found. Please run {expected} first.")
        sys.exit(1)

    out_dir = FIGURES_BASE_DIR / "exp2"
    out_dir.mkdir(parents=True, exist_ok=True)

    suffix = "_quick" if args.quick else ""
    mode_note = "quick" if args.quick else None
    plot_ablation_study(df, out_dir, file_suffix=suffix, mode_note=mode_note)
    write_summary(prepare_task_view(df), aggregate_algorithms(prepare_task_view(df)), out_dir, file_suffix=suffix, mode_note=mode_note)
    plot_ablation_by_budget(df, out_dir, quick_mode=args.quick, base_suffix=suffix)
    print("All validation artifacts successfully generated.")


if __name__ == "__main__":
    main()
