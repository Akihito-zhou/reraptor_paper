#!/usr/bin/env python3
"""
Plot supporting-study figures for Experiment 2.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper.experiments.common.config import FIGURES_BASE_DIR, RESULTS_BASE_DIR


plt.style.use("default")
sns.set_theme(style="whitegrid")
sns.set_context("paper", font_scale=1.1)

PRESSURE_LABELS = {
    "relaxed": "Relaxed",
    "default": "Default",
    "tight": "Tight",
    "very_tight": "Very Tight",
}
PRESSURE_ORDER = ["Relaxed", "Default", "Tight", "Very Tight"]


def load_rows(*, quick: bool, input_path: str | None) -> pd.DataFrame:
    if input_path:
        path = Path(input_path)
    else:
        name = "exp2_supporting_results_quick.json" if quick else "exp2_supporting_results.json"
        path = RESULTS_BASE_DIR / "exp2_ablation_study" / name
    if not path.exists():
        return pd.DataFrame()

    with open(path, "r", encoding="utf-8") as handle:
        rows = json.load(handle)
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    numeric_cols = [
        "depart_time",
        "budget_minutes",
        "seed",
        "score_seed",
        "beam_width",
        "candidate_cap_short",
        "candidate_cap_long",
        "elapsed_ms",
        "stop_score_total",
        "score_per_hour",
        "theme_score_total",
        "theme_hit_ratio",
        "theme_score_share",
        "off_theme_score_share",
        "labels",
        "theme_required_ratio",
        "theme_min_stops_apply",
        "theme_density",
        "theme_score_mass_share_all",
        "top20_theme_share",
        "top10_theme_score_mean",
        "top10_non_theme_score_mean",
        "score_conflict_gap",
        "theme_required_share_gap",
        "theme_top_share_gap",
        "theme_conflict_index",
        "budget_tightness",
        "effective_min_minutes",
        "effective_min_legs",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["feasible", "resource_cap_hit", "theme_satisfied"]:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)
    df["is_timeout"] = df.get("termination_reason", "").astype(str).eq("timeout")
    if "pressure_name" in df.columns:
        df["pressure_label"] = df["pressure_name"].astype(str).map(PRESSURE_LABELS).fillna(df["pressure_name"].astype(str))
    else:
        df["pressure_label"] = "Default"
    if "budget_minutes" in df.columns:
        df["budget_label"] = df["budget_minutes"].fillna(0).astype(int).floordiv(60).astype(str) + "h"
    else:
        df["budget_label"] = "0h"
    return df


def _format_pressure_series(series: pd.Series) -> pd.Categorical:
    ordered = [label for label in PRESSURE_ORDER if label in set(series.dropna().astype(str))]
    if not ordered:
        ordered = sorted(set(series.dropna().astype(str)))
    return pd.Categorical(series, categories=ordered, ordered=True)


def _quantile_labels(series: pd.Series, labels: list[str]) -> pd.Series:
    out = pd.Series(["N/A"] * len(series), index=series.index, dtype="object")
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.notna()
    if int(valid.sum()) == 0:
        return out
    unique_count = int(numeric[valid].nunique())
    if unique_count <= 1:
        out.loc[valid] = labels[min(len(labels) - 1, len(labels) // 2)]
        return out
    bucket_count = min(len(labels), unique_count)
    chosen_labels = labels[:bucket_count]
    ranked = numeric[valid].rank(method="first")
    out.loc[valid] = pd.qcut(ranked, q=bucket_count, labels=chosen_labels).astype(str)
    return out


def _existing_cols(df: pd.DataFrame, columns: list[str]) -> list[str]:
    return [col for col in columns if col in df.columns]


def _primary_metric_label(df: pd.DataFrame) -> str:
    if "primary_objective_name" not in df.columns:
        return "Primary"
    names = sorted({str(v) for v in df["primary_objective_name"].dropna().astype(str) if str(v)})
    if names == ["ride_minutes"]:
        return "RideMinutes"
    if len(names) == 1:
        return names[0]
    return "Primary"


def _theme_order(series: pd.Series) -> list[str]:
    preferred = ["single-digit", "odd-bus-tour", "century-ride", "random-subset", "rapid-transit"]
    present = [name for name in preferred if name in set(series.astype(str))]
    extras = sorted(set(series.astype(str)) - set(present))
    return present + extras


def build_negative_pair_frame(df: pd.DataFrame) -> pd.DataFrame:
    themed = df[df["experiment"].astype(str).str.startswith("negative_")].copy()
    themed = themed[themed["theme_name"].astype(str) != "none"].copy()
    if themed.empty:
        return pd.DataFrame()

    key_cols = _existing_cols(themed, [
        "experiment",
        "origin_code",
        "depart_time",
        "budget_minutes",
        "seed",
        "score_seed",
        "theme_name",
        "pressure_name",
    ]) or _existing_cols(themed, [
        "experiment",
        "origin",
        "depart_time",
        "budget_minutes",
        "seed",
        "score_seed",
        "theme_name",
        "pressure_name",
    ])
    carry_cols = _existing_cols(themed, [
        "origin",
        "origin_code",
        "pressure_label",
        "budget_label",
        "beam_width",
        "candidate_cap_short",
        "candidate_cap_long",
        "theme_density",
        "theme_conflict_index",
        "budget_tightness",
        "theme_kind",
        "project_scoring_type",
        "project_target",
        "start_mode",
        "primary_objective_name",
        "theme_target_size",
        "effective_min_minutes",
        "effective_min_legs",
    ])
    metric_cols = _existing_cols(themed, [
        "stop_score_total",
        "theme_score_total",
        "theme_hit_ratio",
        "theme_score_share",
        "theme_satisfied",
        "off_theme_score_share",
        "elapsed_ms",
        "labels",
        "theme_leg_count",
        "off_theme_leg_count",
        "theme_stop_count",
        "off_theme_stop_count",
        "feasible",
        "negative_total_hits",
        "beam_trim_events",
        "candidate_trim_events",
        "route_hash",
    ])

    carry_cols = [col for col in carry_cols if col not in key_cols]
    metric_cols = [col for col in metric_cols if col not in key_cols]

    full = themed[themed["algorithm"] == "Ours (Full)"][key_cols + carry_cols + metric_cols].copy()
    noneg = themed[themed["algorithm"] == "Ours (NoNeg)"][key_cols + metric_cols].copy()
    if full.empty or noneg.empty:
        return pd.DataFrame()

    pair = full.merge(noneg, on=key_cols, suffixes=("_full", "_noneg"))
    if pair.empty:
        return pair

    deltas = {
        "stop_score_total": "d_stop_score",
        "theme_score_total": "d_theme_score",
        "theme_hit_ratio": "d_theme_hit",
        "theme_score_share": "d_theme_share",
        "theme_satisfied": "d_theme_sat",
        "off_theme_score_share": "d_off_theme_share",
        "elapsed_ms": "d_elapsed_ms",
        "labels": "d_labels",
    }
    for base_col, delta_col in deltas.items():
        left = pair[f"{base_col}_full"]
        right = pair[f"{base_col}_noneg"]
        if str(base_col) == "theme_satisfied":
            pair[delta_col] = left.astype(float) - right.astype(float)
        else:
            pair[delta_col] = pd.to_numeric(left, errors="coerce") - pd.to_numeric(right, errors="coerce")

    pair["same_route"] = pair["route_hash_full"].astype(str).eq(pair["route_hash_noneg"].astype(str))
    pair["theme_advantage"] = (
        (pair["d_theme_hit"] > 1e-9)
        | (pair["d_theme_sat"] > 1e-9)
        | (pair["d_off_theme_share"] < -1e-9)
    )
    pair["no_theme_regression"] = pair["d_theme_hit"] >= -1e-9
    pair["pressure_label"] = _format_pressure_series(pair["pressure_label"].astype(str))
    pair["conflict_bin"] = _quantile_labels(
        pd.to_numeric(pair["theme_conflict_index"], errors="coerce"),
        ["Low conflict", "Medium conflict", "High conflict"],
    )
    pair["conflict_bin"] = pd.Categorical(
        pair["conflict_bin"],
        categories=["Low conflict", "Medium conflict", "High conflict"],
        ordered=True,
    )
    pair["density_bin"] = _quantile_labels(
        pd.to_numeric(pair["theme_density"], errors="coerce"),
        ["Sparse", "Medium", "Dense"],
    )
    pair["density_bin"] = pd.Categorical(
        pair["density_bin"],
        categories=["Sparse", "Medium", "Dense"],
        ordered=True,
    )
    return pair


def _markdown_table(df: pd.DataFrame, columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join(["---"] * len(columns)) + "|",
    ]
    for _, row in df.iterrows():
        vals = [str(row[col]) for col in columns]
        lines.append("| " + " | ".join(vals) + " |")
    return lines


def write_summary(df: pd.DataFrame, pair: pd.DataFrame, out_dir: Path, suffix: str) -> None:
    lines: list[str] = ["# Exp2 Supporting Summary", ""]
    if not pair.empty:
        primary_label = _primary_metric_label(pair.rename(columns={"primary_objective_name_full": "primary_objective_name"}))
        pair_count = int(len(pair))
        theme_improve = int((pair["d_theme_hit"] > 1e-9).sum())
        theme_tie = int((pair["d_theme_hit"].abs() <= 1e-9).sum())
        route_change = int((~pair["same_route"]).sum())
        best_theme = (
            pair.groupby("theme_name", as_index=False)["d_theme_hit"]
            .mean()
            .sort_values("d_theme_hit", ascending=False)
            .head(1)
        )
        strongest_theme = str(best_theme.iloc[0]["theme_name"]) if not best_theme.empty else "N/A"
        pressure_summary = (
            pair.groupby("pressure_label", as_index=False, observed=False)
            .agg(
                d_theme_hit=("d_theme_hit", "mean"),
                d_theme_sat=("d_theme_sat", "mean"),
            )
        )
        pressure_note = ""
        if len(pressure_summary) > 1:
            hit_span = float(pressure_summary["d_theme_hit"].max() - pressure_summary["d_theme_hit"].min())
            sat_span = float(pressure_summary["d_theme_sat"].max() - pressure_summary["d_theme_sat"].min())
            if hit_span <= 0.02 and sat_span <= 0.05:
                pressure_note = (
                    "- Tested pressure settings have very similar averages in this run, "
                    "so the main effect here is route-theme preservation rather than pressure sensitivity."
                )
        lines.extend(
            [
                "## Key Findings",
                "",
                f"- Paired tasks: `{pair_count}` route-theme cases.",
                f"- `Full` improves theme-hit ratio in `{theme_improve}/{pair_count}` pairs, with `{theme_tie}` ties and only `{pair_count - theme_improve - theme_tie}` regressions.",
                f"- Final routes change in `{route_change}/{pair_count}` pairs, so `neg` is changing selected routes rather than only search traces.",
                f"- Mean delta: `ThemeHit +{pair['d_theme_hit'].mean():.3f}`, `ThemeSat +{pair['d_theme_sat'].mean():.3f}`, `{primary_label} {pair['d_stop_score'].mean():+.3f}`, `Runtime +{pair['d_elapsed_ms'].mean() / 1000.0:.2f}s`.",
                f"- Strongest theme-level gain appears on `{strongest_theme}` in this run.",
            ]
        )
        if pressure_note:
            lines.append(pressure_note)
            lines.append("")
        else:
            lines.append("")

    for experiment in sorted(df["experiment"].dropna().unique().tolist()):
        part = df[df["experiment"] == experiment].copy()
        primary_label = _primary_metric_label(part)
        agg = (
            part.groupby("algorithm", as_index=False)
            .agg(
                primary=("stop_score_total", "mean"),
                rate=("score_per_hour", "mean"),
                theme_score=("theme_score_total", "mean"),
                theme_hit=("theme_hit_ratio", "mean"),
                theme_sat=("theme_satisfied", "mean"),
                elapsed_ms=("elapsed_ms", "mean"),
                labels=("labels", "mean"),
                success=("feasible", "mean"),
                cap_hit=("resource_cap_hit", "mean"),
                timeout=("is_timeout", "mean"),
            )
            .sort_values("algorithm")
        )
        lines.append(f"## {experiment}")
        lines.append("")
        lines.append(f"| Algorithm | {primary_label} | Rate | ThemeScore | ThemeHit | ThemeSat | Mean ms | Labels | Success | CapHit | Timeout |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for _, row in agg.iterrows():
            lines.append(
                f"| {row['algorithm']} | {row['primary']:.3f} | {row['rate']:.3f} | "
                f"{row['theme_score']:.3f} | {row['theme_hit']:.3f} | {row['theme_sat']:.3f} | "
                f"{row['elapsed_ms']:.3f} | {row['labels']:.1f} | {row['success']:.3f} | "
                f"{row['cap_hit']:.3f} | {row['timeout']:.3f} |"
            )
        lines.append("")

    if not pair.empty:
        primary_label = _primary_metric_label(pair.rename(columns={"primary_objective_name_full": "primary_objective_name"}))
        overall = pd.DataFrame(
            [
                {
                    "Metric": "ThemeHit delta",
                    "Mean": f"{pair['d_theme_hit'].mean():.4f}",
                    "FullBetter": int((pair["d_theme_hit"] > 1e-9).sum()),
                    "Tie": int((pair["d_theme_hit"].abs() <= 1e-9).sum()),
                    "NoNegBetter": int((pair["d_theme_hit"] < -1e-9).sum()),
                },
                {
                    "Metric": "ThemeSat delta",
                    "Mean": f"{pair['d_theme_sat'].mean():.4f}",
                    "FullBetter": int((pair["d_theme_sat"] > 1e-9).sum()),
                    "Tie": int((pair["d_theme_sat"].abs() <= 1e-9).sum()),
                    "NoNegBetter": int((pair["d_theme_sat"] < -1e-9).sum()),
                },
                {
                    "Metric": f"{primary_label} delta",
                    "Mean": f"{pair['d_stop_score'].mean():.3f}",
                    "FullBetter": int((pair["d_stop_score"] > 1e-9).sum()),
                    "Tie": int((pair["d_stop_score"].abs() <= 1e-9).sum()),
                    "NoNegBetter": int((pair["d_stop_score"] < -1e-9).sum()),
                },
                {
                    "Metric": "Runtime delta ms",
                    "Mean": f"{pair['d_elapsed_ms'].mean():.3f}",
                    "FullBetter": int((pair["d_elapsed_ms"] < -1e-9).sum()),
                    "Tie": int((pair["d_elapsed_ms"].abs() <= 1e-9).sum()),
                    "NoNegBetter": int((pair["d_elapsed_ms"] > 1e-9).sum()),
                },
                {
                    "Metric": "ThemeAdvantage rate",
                    "Mean": f"{pair['theme_advantage'].mean():.4f}",
                    "FullBetter": int(pair["theme_advantage"].sum()),
                    "Tie": int((~pair["theme_advantage"]).sum()),
                    "NoNegBetter": 0,
                },
            ]
        )
        lines.append("## negative_project_theme_alignment: Full vs NoNeg")
        lines.append("")
        lines.extend(_markdown_table(overall, list(overall.columns)))
        lines.append("")

        route_delta = pd.DataFrame(
            [
                {"Metric": "Paired cases", "Value": int(len(pair))},
                {"Metric": "Same-route cases", "Value": int(pair["same_route"].sum())},
                {"Metric": "Changed-route cases", "Value": int((~pair["same_route"]).sum())},
                {"Metric": "Changed-route rate", "Value": f"{float((~pair['same_route']).mean()):.4f}"},
            ]
        )
        lines.append("### Route Selection Difference")
        lines.append("")
        lines.extend(_markdown_table(route_delta, list(route_delta.columns)))
        lines.append("")

        pressure_num = (
            pair.groupby("pressure_label", as_index=False, observed=False)
            .agg(
                cases=("theme_name", "size"),
                d_theme_hit=("d_theme_hit", "mean"),
                d_theme_sat=("d_theme_sat", "mean"),
                d_stop_score=("d_stop_score", "mean"),
                d_elapsed_ms=("d_elapsed_ms", "mean"),
                theme_advantage_rate=("theme_advantage", "mean"),
                changed_route_rate=("same_route", lambda s: float((~s).mean())),
            )
            .sort_values("pressure_label")
        )
        pressure = pressure_num.copy()
        pressure["pressure_label"] = pressure["pressure_label"].astype(str)
        for col in ["d_theme_hit", "d_theme_sat", "d_stop_score", "d_elapsed_ms", "theme_advantage_rate", "changed_route_rate"]:
            pressure[col] = pressure[col].map(lambda v: f"{float(v):.4f}" if col != "d_stop_score" and col != "d_elapsed_ms" else f"{float(v):.3f}")
        lines.append("### By Pressure")
        lines.append("")
        lines.extend(_markdown_table(pressure.rename(columns={"pressure_label": "Pressure"}), list(pressure.rename(columns={"pressure_label": "Pressure"}).columns)))
        lines.append("")

        by_theme_num = (
            pair.groupby("theme_name", as_index=False)
            .agg(
                cases=("theme_name", "size"),
                d_theme_hit=("d_theme_hit", "mean"),
                d_theme_sat=("d_theme_sat", "mean"),
                d_stop_score=("d_stop_score", "mean"),
                d_elapsed_ms=("d_elapsed_ms", "mean"),
                theme_advantage_rate=("theme_advantage", "mean"),
            )
            .sort_values("theme_name")
        )
        by_theme = by_theme_num.copy()
        for col in ["d_theme_hit", "d_theme_sat", "d_stop_score", "d_elapsed_ms", "theme_advantage_rate"]:
            by_theme[col] = by_theme[col].map(lambda v: f"{float(v):.4f}" if col != "d_stop_score" and col != "d_elapsed_ms" else f"{float(v):.3f}")
        lines.append("### By Theme")
        lines.append("")
        lines.extend(_markdown_table(by_theme.rename(columns={"theme_name": "Theme"}), list(by_theme.rename(columns={"theme_name": "Theme"}).columns)))
        lines.append("")

        if "start_mode" in pair.columns:
            by_start = (
                pair.groupby("start_mode", as_index=False)
                .agg(
                    cases=("theme_name", "size"),
                    d_theme_hit=("d_theme_hit", "mean"),
                    d_theme_sat=("d_theme_sat", "mean"),
                    d_stop_score=("d_stop_score", "mean"),
                    d_elapsed_ms=("d_elapsed_ms", "mean"),
                    theme_advantage_rate=("theme_advantage", "mean"),
                )
                .sort_values("start_mode")
            )
            for col in ["d_theme_hit", "d_theme_sat", "d_stop_score", "d_elapsed_ms", "theme_advantage_rate"]:
                by_start[col] = by_start[col].map(lambda v: f"{float(v):.4f}" if col != "d_stop_score" and col != "d_elapsed_ms" else f"{float(v):.3f}")
            lines.append("### By Start Mode")
            lines.append("")
            lines.extend(_markdown_table(by_start.rename(columns={"start_mode": "StartMode"}), list(by_start.rename(columns={"start_mode": "StartMode"}).columns)))
        lines.append("")

    content = "\n".join(lines) + "\n"
    out_path = out_dir / f"exp2_supporting_summary{suffix}.md"
    out_path.write_text(content, encoding="utf-8")
    print(f"Saved: {out_path}")
    results_path = RESULTS_BASE_DIR / "exp2_ablation_study" / f"exp2_supporting_summary{suffix}.md"
    results_path.write_text(content, encoding="utf-8")
    print(f"Saved: {results_path}")


def plot_beam_overall(df: pd.DataFrame, out_dir: Path, suffix: str) -> None:
    beam = df[df["experiment"] == "beam_tail_risk"].copy()
    if beam.empty:
        return

    agg = (
        beam.groupby("algorithm", as_index=False)
        .agg(
            stop_score=("stop_score_total", "mean"),
            elapsed_ms=("elapsed_ms", "mean"),
            labels=("labels", "mean"),
            cap_hit_rate=("resource_cap_hit", "mean"),
            timeout_rate=("is_timeout", "mean"),
        )
        .sort_values("algorithm")
    )

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    palette = ["#1f6f8b", "#d1495b"]

    sns.barplot(data=agg, x="algorithm", y="stop_score", hue="algorithm", ax=axes[0, 0], palette=palette, legend=False)
    axes[0, 0].set_title("Beam Support: Stop Score")
    axes[0, 0].set_xlabel("")
    axes[0, 0].set_ylabel("Mean Stop Score")

    sns.barplot(data=agg, x="algorithm", y="elapsed_ms", hue="algorithm", ax=axes[0, 1], palette=palette, legend=False)
    axes[0, 1].set_title("Beam Support: Runtime")
    axes[0, 1].set_xlabel("")
    axes[0, 1].set_ylabel("Mean Elapsed ms")

    sns.barplot(data=agg, x="algorithm", y="labels", hue="algorithm", ax=axes[1, 0], palette=palette, legend=False)
    axes[1, 0].set_title("Beam Support: Search Size")
    axes[1, 0].set_xlabel("")
    axes[1, 0].set_ylabel("Mean Labels")

    rate_df = agg.melt(
        id_vars=["algorithm"],
        value_vars=["cap_hit_rate", "timeout_rate"],
        var_name="metric",
        value_name="rate",
    )
    sns.barplot(data=rate_df, x="algorithm", y="rate", hue="metric", ax=axes[1, 1], palette=["#f4a261", "#6d597a"])
    axes[1, 1].set_title("Beam Support: Failure Rates")
    axes[1, 1].set_xlabel("")
    axes[1, 1].set_ylabel("Rate")
    axes[1, 1].set_ylim(0.0, 1.0)
    axes[1, 1].legend(title="")

    for ax in axes.flat:
        ax.tick_params(axis="x", rotation=12)

    plt.tight_layout()
    out_path = out_dir / f"exp2_supporting_beam_overall{suffix}.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_negative_theme_dumbbell(pair: pd.DataFrame, out_dir: Path, suffix: str) -> None:
    if pair.empty:
        return
    agg = (
        pair.groupby(["theme_name", "budget_label"], as_index=False, observed=False)
        .agg(
            theme_hit_full=("theme_hit_ratio_full", "mean"),
            theme_hit_noneg=("theme_hit_ratio_noneg", "mean"),
            theme_sat_full=("theme_satisfied_full", lambda s: float(pd.to_numeric(s, errors="coerce").mean())),
            theme_sat_noneg=("theme_satisfied_noneg", lambda s: float(pd.to_numeric(s, errors="coerce").mean())),
        )
        .sort_values(["theme_name", "budget_label"])
    )
    if agg.empty:
        return

    order = _theme_order(agg["theme_name"])
    agg["theme_name"] = pd.Categorical(agg["theme_name"], categories=order, ordered=True)
    agg = agg.sort_values(["theme_name", "budget_label"]).reset_index(drop=True)
    agg["label"] = agg["theme_name"].astype(str) + " (" + agg["budget_label"].astype(str) + ")"
    y_pos = list(range(len(agg)))

    fig, axes = plt.subplots(1, 2, figsize=(13, max(4.8, 0.65 * len(agg) + 1.2)), sharey=True)
    colors = {"Ours (Full)": "#1f6f8b", "Ours (NoNeg)": "#d1495b"}
    panels = [
        ("theme_hit_noneg", "theme_hit_full", "Theme Hit Ratio", axes[0]),
        ("theme_sat_noneg", "theme_sat_full", "Theme Satisfaction Rate", axes[1]),
    ]
    for noneg_col, full_col, title, ax in panels:
        for idx, row in agg.iterrows():
            ax.plot(
                [float(row[noneg_col]), float(row[full_col])],
                [idx, idx],
                color="#9aa5b1",
                linewidth=1.5,
                zorder=1,
            )
            ax.scatter(float(row[noneg_col]), idx, color=colors["Ours (NoNeg)"], s=42, zorder=3)
            ax.scatter(float(row[full_col]), idx, color=colors["Ours (Full)"], s=42, zorder=3)
        ax.set_title(title)
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_xlim(-0.02, 1.02)
        ax.grid(axis="x", alpha=0.25)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(agg["label"].tolist())
    axes[0].legend(
        handles=[
            plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=colors["Ours (Full)"], markersize=7, label="Ours (Full)"),
            plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=colors["Ours (NoNeg)"], markersize=7, label="Ours (NoNeg)"),
        ],
        loc="lower right",
        frameon=True,
        title="Algorithm",
    )

    plt.tight_layout()
    out_path = out_dir / f"exp2_supporting_theme_dumbbell{suffix}.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_negative_conditions(pair: pd.DataFrame, out_dir: Path, suffix: str) -> None:
    if pair.empty:
        return

    heat_hit = (
        pair.pivot_table(
            index="theme_name",
            columns="pressure_label",
            values="d_theme_hit",
            aggfunc="mean",
            observed=False,
        )
        .sort_index()
    )
    heat_sat = (
        pair.pivot_table(
            index="theme_name",
            columns="pressure_label",
            values="d_theme_sat",
            aggfunc="mean",
            observed=False,
        )
        .sort_index()
    )
    if heat_hit.empty and heat_sat.empty:
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    sns.heatmap(heat_hit, cmap="vlag", center=0.0, annot=True, fmt=".3f", linewidths=0.5, ax=axes[0], cbar=False)
    axes[0].set_title("Full - NoNeg: Theme Hit Delta")
    axes[0].set_xlabel("Pressure")
    axes[0].set_ylabel("Theme")

    sns.heatmap(heat_sat, cmap="vlag", center=0.0, annot=True, fmt=".3f", linewidths=0.5, ax=axes[1], cbar=False)
    axes[1].set_title("Full - NoNeg: Theme Satisfaction Delta")
    axes[1].set_xlabel("Pressure")
    axes[1].set_ylabel("")

    plt.tight_layout()
    out_path = out_dir / f"exp2_supporting_negative_conditions{suffix}.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_negative_scatter(pair: pd.DataFrame, out_dir: Path, suffix: str) -> None:
    if pair.empty:
        return

    plt.figure(figsize=(8.5, 6))
    sns.scatterplot(
        data=pair,
        x=pair["d_elapsed_ms"] / 1000.0,
        y="d_theme_hit",
        hue="theme_name",
        style="budget_label",
        palette="deep",
        s=70,
        alpha=0.8,
    )
    plt.axvline(0.0, color="black", linewidth=1)
    plt.axhline(0.0, color="black", linewidth=1)
    plt.title("Theme Gain vs Runtime Cost")
    plt.xlabel("Runtime delta (Full - NoNeg, seconds)")
    plt.ylabel("Theme ratio delta (Full - NoNeg)")
    plt.tight_layout()
    out_path = out_dir / f"exp2_supporting_negative_tradeoff{suffix}.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot Exp2 supporting-study figures.")
    parser.add_argument("--quick", action="store_true", help="Use quick supporting results file.")
    parser.add_argument("--input", type=str, default="", help="Specific supporting results JSON file.")
    args = parser.parse_args()

    df = load_rows(quick=args.quick, input_path=args.input.strip() or None)
    if df.empty:
        expected = "run_exp2_supporting.py --quick" if args.quick else "run_exp2_supporting.py"
        print(f"No supporting results found. Please run {expected} first.")
        sys.exit(1)

    out_dir = FIGURES_BASE_DIR / "exp2"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "_quick" if args.quick else ""

    negative_pair = build_negative_pair_frame(df)
    write_summary(df, negative_pair, out_dir, suffix)
    plot_beam_overall(df, out_dir, suffix)
    plot_negative_theme_dumbbell(negative_pair, out_dir, suffix)
    plot_negative_conditions(negative_pair, out_dir, suffix)
    plot_negative_scatter(negative_pair, out_dir, suffix)
    print("All supporting figures generated.")


if __name__ == "__main__":
    main()
