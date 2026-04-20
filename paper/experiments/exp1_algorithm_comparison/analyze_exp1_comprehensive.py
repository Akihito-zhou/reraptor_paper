#!/usr/bin/env python3
"""
Experiment 1 comprehensive-performance analysis.

Goal:
1. Show quality, stability, and efficiency together (not single-point wins).
2. Provide query-level comprehensive ranking to support "overall best" claims.
3. Serve as supplementary evidence only; it does not replace core metrics in the research plan.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add experiments root to PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.config import FIGURES_BASE_DIR, RESULTS_BASE_DIR
from common.io_utils import load_results


def _minmax(series: pd.Series, higher_better: bool = True) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float)
    lo = float(s.min())
    hi = float(s.max())
    if hi <= lo:
        return pd.Series([1.0] * len(s), index=s.index)
    norm = (s - lo) / (hi - lo)
    return norm if higher_better else (1.0 - norm)


def _query_key_columns(df: pd.DataFrame) -> list[str]:
    cols = []
    for col in ("origin", "depart_time"):
        if col in df.columns:
            cols.append(col)

    if "budget_minutes" in df.columns:
        cols.append("budget_minutes")
    elif "budget" in df.columns:
        cols.append("budget")

    if "seed" in df.columns:
        cols.append("seed")

    return cols


def _algorithm_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("algorithm", as_index=False)
        .agg(
            runs=("algorithm", "size"),
            feasible_rate=("feasible", "mean"),
            mean_composite=("composite_score", "mean"),
            mean_elapsed_ms=("elapsed_ms", "mean"),
            median_elapsed_ms=("elapsed_ms", "median"),
        )
    )

    feasible_only = (
        df[df["feasible"] == True]
        .groupby("algorithm")["composite_score"]
        .mean()
    )
    summary["mean_composite_feasible_only"] = (
        summary["algorithm"].map(feasible_only).fillna(0.0)
    )

    summary["norm_quality"] = _minmax(summary["mean_composite"], higher_better=True)
    summary["norm_stability"] = _minmax(summary["feasible_rate"], higher_better=True)
    summary["norm_efficiency"] = _minmax(summary["median_elapsed_ms"], higher_better=False)
    summary["balanced_index"] = (
        summary["norm_quality"] + summary["norm_stability"] + summary["norm_efficiency"]
    ) / 3.0
    summary["balanced_rank"] = summary["balanced_index"].rank(ascending=False, method="min").astype(int)

    summary = summary.sort_values(
        by=["balanced_index", "mean_composite", "feasible_rate"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    return summary


def _query_level_borda(
    df: pd.DataFrame,
    key_cols: list[str],
    *,
    w_quality: float,
    w_stability: float,
    w_efficiency: float,
) -> pd.DataFrame:
    if not key_cols:
        raise ValueError("Cannot build query-level ranking: no query-key columns found.")

    ranked = df.copy()
    ranked["query_key"] = ranked[key_cols].astype(str).agg("|".join, axis=1)
    ranked["feasible_int"] = ranked["feasible"].astype(int)

    ranked["rank_quality"] = ranked.groupby("query_key")["composite_score"].rank(
        ascending=False, method="average"
    )
    ranked["rank_stability"] = ranked.groupby("query_key")["feasible_int"].rank(
        ascending=False, method="average"
    )
    ranked["rank_efficiency"] = ranked.groupby("query_key")["elapsed_ms"].rank(
        ascending=True, method="average"
    )
    ranked["equal_rank_sum"] = (
        ranked["rank_quality"] + ranked["rank_stability"] + ranked["rank_efficiency"]
    )
    ranked["weighted_rank_sum"] = (
        ranked["rank_quality"] * w_quality
        + ranked["rank_stability"] * w_stability
        + ranked["rank_efficiency"] * w_efficiency
    )

    best_per_query = ranked.groupby("query_key")["weighted_rank_sum"].transform("min")
    ranked["is_query_winner"] = (ranked["weighted_rank_sum"] == best_per_query).astype(int)

    out = (
        ranked.groupby("algorithm", as_index=False)
        .agg(
            queries=("query_key", "count"),
            wins=("is_query_winner", "sum"),
            win_rate=("is_query_winner", "mean"),
            avg_rank_quality=("rank_quality", "mean"),
            avg_rank_stability=("rank_stability", "mean"),
            avg_rank_efficiency=("rank_efficiency", "mean"),
            avg_equal_rank_sum=("equal_rank_sum", "mean"),
            avg_weighted_rank_sum=("weighted_rank_sum", "mean"),
        )
        .sort_values(
            by=["avg_weighted_rank_sum", "avg_rank_quality", "win_rate"],
            ascending=[True, True, False],
        )
        .reset_index(drop=True)
    )
    return out


def _write_report(
    metadata: dict,
    summary: pd.DataFrame,
    borda: pd.DataFrame,
    output_md: Path,
    *,
    w_quality: float,
    w_stability: float,
    w_efficiency: float,
) -> None:
    top_balanced = summary.iloc[0]["algorithm"] if not summary.empty else "N/A"
    top_borda = borda.iloc[0]["algorithm"] if not borda.empty else "N/A"

    with open(output_md, "w", encoding="utf-8") as f:
        f.write("# Experiment 1: Comprehensive Performance Report (Supplementary)\n\n")
        f.write("## Metadata\n")
        f.write(f"- timestamp: {metadata.get('timestamp', 'N/A')}\n")
        f.write(f"- experiment: {metadata.get('experiment', 'N/A')}\n")
        f.write(f"- num_results: {metadata.get('num_results', 'N/A')}\n\n")

        f.write("## Key Findings\n")
        f.write(
            f"- Top algorithm by balanced index (quality + stability + efficiency): **{top_balanced}**\n"
        )
        f.write(
            f"- Top algorithm by query-level weighted ranking: **{top_borda}**\n\n"
        )
        f.write(
            "- This report is supplementary and should be interpreted together with the primary Exp1 protocol metrics.\n\n"
        )

        f.write("## Algorithm-Level Balanced Index\n")
        f.write(summary.to_markdown(index=False, floatfmt=".4f"))
        f.write("\n\n")

        f.write("## Query-Level Comprehensive Ranking\n")
        f.write(
            f"- weighted rank formula: `rank_quality*{w_quality:.2f} + rank_stability*{w_stability:.2f} + rank_efficiency*{w_efficiency:.2f}`\n"
        )
        f.write(borda.to_markdown(index=False, floatfmt=".4f"))
        f.write("\n")


def main(
    input_path: Path | None,
    output_dir: Path | None,
    *,
    w_quality: float,
    w_stability: float,
    w_efficiency: float,
) -> None:
    results_path = input_path or (RESULTS_BASE_DIR / "exp1_algorithm_comparison" / "exp1_results.json")
    out_dir = output_dir or (FIGURES_BASE_DIR / "exp1_algorithm_comparison")
    out_dir.mkdir(parents=True, exist_ok=True)

    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    metadata, rows = load_results(results_path)
    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError(f"No rows in results file: {results_path}")

    required = ["algorithm", "elapsed_ms", "composite_score", "feasible"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    for col in ["elapsed_ms", "composite_score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["feasible"] = df["feasible"].fillna(False).astype(bool)

    key_cols = _query_key_columns(df)
    summary = _algorithm_summary(df)
    borda = _query_level_borda(
        df,
        key_cols,
        w_quality=w_quality,
        w_stability=w_stability,
        w_efficiency=w_efficiency,
    )

    summary_csv = out_dir / "comprehensive_algorithm_summary.csv"
    borda_csv = out_dir / "comprehensive_borda_summary.csv"
    report_md = out_dir / "comprehensive_performance.md"

    summary.to_csv(summary_csv, index=False)
    borda.to_csv(borda_csv, index=False)
    _write_report(
        metadata,
        summary,
        borda,
        report_md,
        w_quality=w_quality,
        w_stability=w_stability,
        w_efficiency=w_efficiency,
    )

    print(f"Input: {results_path}")
    print(f"Wrote: {summary_csv}")
    print(f"Wrote: {borda_csv}")
    print(f"Wrote: {report_md}")
    if not summary.empty:
        print(
            "Balanced-index winner:",
            summary.iloc[0]["algorithm"],
            f"(score={summary.iloc[0]['balanced_index']:.4f})",
        )
    if not borda.empty:
        print(
            "Weighted-rank winner:",
            borda.iloc[0]["algorithm"],
            f"(avg_rank_sum={borda.iloc[0]['avg_weighted_rank_sum']:.4f})",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze comprehensive performance for Experiment 1.")
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to exp1 results JSON. Default: paper/results/exp1_algorithm_comparison/exp1_results.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for markdown/csv artifacts. Default: paper/figures/exp1_algorithm_comparison",
    )
    parser.add_argument("--w-quality", type=float, default=0.60, help="Weight for quality rank.")
    parser.add_argument("--w-stability", type=float, default=0.25, help="Weight for feasibility rank.")
    parser.add_argument("--w-efficiency", type=float, default=0.15, help="Weight for time rank.")
    args = parser.parse_args()
    weight_sum = args.w_quality + args.w_stability + args.w_efficiency
    if abs(weight_sum - 1.0) > 1e-9:
        raise ValueError(
            f"Ranking weights must sum to 1.0, got {weight_sum:.6f} "
            f"({args.w_quality}, {args.w_stability}, {args.w_efficiency})"
        )

    main(
        args.input,
        args.output_dir,
        w_quality=args.w_quality,
        w_stability=args.w_stability,
        w_efficiency=args.w_efficiency,
    )
