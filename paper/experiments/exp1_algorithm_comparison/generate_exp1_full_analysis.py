#!/usr/bin/env python3
"""
Generate full Experiment 1 analysis artifacts from exp1_results.json.

Outputs:
- paper/results/exp1_algorithm_comparison/exp1_analysis_stats.json
- paper/results/exp1_algorithm_comparison/exp1_full_text_analysis.md
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESULTS_FILE_DEFAULT = PROJECT_ROOT / "paper" / "results" / "exp1_algorithm_comparison" / "exp1_results.json"
STATS_OUT_DEFAULT = PROJECT_ROOT / "paper" / "results" / "exp1_algorithm_comparison" / "exp1_analysis_stats.json"
MD_OUT_DEFAULT = PROJECT_ROOT / "paper" / "results" / "exp1_algorithm_comparison" / "exp1_full_text_analysis.md"


def _load_results(path: Path) -> tuple[dict, list[dict]]:
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("metadata", {}), payload.get("results", [])


def _to_numeric(df: pd.DataFrame, cols: list[str]) -> None:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")


def _primary_metric(columns: list[str] | pd.Index) -> str:
    return "stop_score_total" if "stop_score_total" in set(columns) else "composite_score"


def _primary_label(metric: str) -> str:
    return "Stop Score" if metric == "stop_score_total" else "Composite Score"


def _prepare_frames(rows: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    run_df = pd.DataFrame(rows)
    _to_numeric(
        run_df,
        [
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
            "budget_minutes",
            "depart_time",
            "seed",
            "total_time_minutes",
        ],
    )
    run_df["feasible"] = run_df.get("feasible", True).fillna(False).astype(bool)
    run_df["algorithm"] = run_df["algorithm"].astype(str)

    agg_spec = {
        col: (col, "mean")
        for col in [
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
            "total_time_minutes",
        ]
        if col in run_df.columns
    }
    agg_spec["feasible_rate"] = ("feasible", "mean")
    query_df = run_df.groupby(["algorithm", "origin", "depart_time", "budget_minutes"], as_index=False).agg(**agg_spec)
    query_df["feasible"] = query_df["feasible_rate"].ge(0.5)
    return run_df, query_df


def _series_p95(s: pd.Series) -> float:
    arr = pd.to_numeric(s, errors="coerce").dropna().to_numpy()
    if len(arr) == 0:
        return 0.0
    return float(np.percentile(arr, 95))


def _algo_run_summary(run_df: pd.DataFrame) -> list[dict]:
    primary = _primary_metric(run_df.columns)
    grouped = run_df.groupby("algorithm", as_index=False)
    out = grouped.agg(
        n=("algorithm", "size"),
        feasible_rate=("feasible", "mean"),
        elapsed_mean=("elapsed_ms", "mean"),
        elapsed_median=("elapsed_ms", "median"),
        elapsed_std=("elapsed_ms", "std"),
        composite_mean=("composite_score", "mean"),
        primary_mean=(primary, "mean"),
        composite_std=("composite_score", "std"),
        ride_mean=("ride_minutes", "mean"),
        stops_mean=("unique_stops", "mean"),
        hull_mean=("hull_area", "mean"),
        score_per_hour_mean=("score_per_hour", "mean") if "score_per_hour" in run_df.columns else ("elapsed_ms", "mean"),
        total_time_mean=("total_time_minutes", "mean"),
    )
    p95 = (
        run_df.groupby("algorithm")["elapsed_ms"]
        .quantile(0.95)
        .rename("elapsed_p95")
        .reset_index()
    )
    out = out.merge(p95, on="algorithm", how="left")
    out = out.sort_values("primary_mean", ascending=False)
    return json.loads(out.to_json(orient="records"))


def _algo_query_summary(query_df: pd.DataFrame) -> list[dict]:
    primary = _primary_metric(query_df.columns)
    out = (
        query_df.groupby("algorithm", as_index=False)
        .agg(
            n_queries=("algorithm", "size"),
            feasible_rate=("feasible_rate", "mean"),
            elapsed_mean=("elapsed_ms", "mean"),
            composite_mean=("composite_score", "mean"),
            primary_mean=(primary, "mean"),
            ride_mean=("ride_minutes", "mean"),
            stops_mean=("unique_stops", "mean"),
            hull_mean=("hull_area", "mean"),
            score_per_hour_mean=("score_per_hour", "mean") if "score_per_hour" in query_df.columns else ("elapsed_ms", "mean"),
            total_time_mean=("total_time_minutes", "mean"),
        )
        .sort_values("primary_mean", ascending=False)
    )
    return json.loads(out.to_json(orient="records"))


def _summary_by_budget(run_df: pd.DataFrame, query_df: pd.DataFrame) -> tuple[dict, dict]:
    run_by_budget: dict[str, list[dict]] = {}
    query_by_budget: dict[str, list[dict]] = {}
    for budget in sorted(query_df["budget_minutes"].dropna().unique().tolist()):
        key = str(int(budget))
        run_by_budget[key] = _algo_run_summary(run_df[run_df["budget_minutes"] == budget].copy())
        query_by_budget[key] = _algo_query_summary(query_df[query_df["budget_minutes"] == budget].copy())
    return run_by_budget, query_by_budget


def _winner_counts(df: pd.DataFrame, group_cols: list[str], metric: str, higher_better: bool = True) -> dict[str, int]:
    if higher_better:
        idx = df.groupby(group_cols)[metric].idxmax()
    else:
        idx = df.groupby(group_cols)[metric].idxmin()
    winners = df.loc[idx, "algorithm"].value_counts()
    return {str(k): int(v) for k, v in winners.items()}


def _winner_counts_by_slice(
    df: pd.DataFrame,
    group_cols: list[str],
    slice_col: str,
    metric: str,
    higher_better: bool = True,
) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for slice_value in sorted(df[slice_col].dropna().unique().tolist()):
        sub = df[df[slice_col] == slice_value]
        out[str(int(slice_value))] = _winner_counts(sub, group_cols, metric, higher_better=higher_better)
    return out


def _wilcoxon_table(query_df: pd.DataFrame, metrics: list[tuple[str, bool]]) -> list[dict]:
    baseline = "Ours (Full)"
    key_cols = ["origin", "depart_time", "budget_minutes"]

    base = query_df[query_df["algorithm"] == baseline].copy()
    base["match_key"] = base[key_cols].astype(str).agg("|".join, axis=1)
    base = base.set_index("match_key")

    rows: list[dict] = []
    others = sorted(set(query_df["algorithm"].tolist()) - {baseline})
    for algo in others:
        other = query_df[query_df["algorithm"] == algo].copy()
        other["match_key"] = other[key_cols].astype(str).agg("|".join, axis=1)
        other = other.set_index("match_key")
        common = base.index.intersection(other.index)

        entry: dict[str, float | int | str | None] = {
            "algorithm": algo,
            "N": int(len(common)),
        }
        if len(common) < 5:
            rows.append(entry)
            continue

        for metric, _higher_better in metrics:
            x = pd.to_numeric(base.loc[common, metric], errors="coerce").fillna(0.0).to_numpy()
            y = pd.to_numeric(other.loc[common, metric], errors="coerce").fillna(0.0).to_numpy()
            diff = x - y
            entry[f"{metric}_mean_diff"] = float(np.mean(diff))
            if np.allclose(diff, 0):
                entry[f"{metric}_w"] = 0.0
                entry[f"{metric}_p"] = 1.0
            else:
                w, p = stats.wilcoxon(x, y, zero_method="wilcox", alternative="two-sided")
                entry[f"{metric}_w"] = float(w)
                entry[f"{metric}_p"] = float(p)
        rows.append(entry)
    return rows


def _wilcoxon_by_budget(query_df: pd.DataFrame, metrics: list[tuple[str, bool]]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for budget in sorted(query_df["budget_minutes"].dropna().unique().tolist()):
        key = str(int(budget))
        out[key] = _wilcoxon_table(query_df[query_df["budget_minutes"] == budget].copy(), metrics)
    return out


def _stability_stats(run_df: pd.DataFrame) -> tuple[dict[str, float], dict[str, int]]:
    primary = _primary_metric(run_df.columns)
    grp = (
        run_df.groupby(["algorithm", "origin", "depart_time", "budget_minutes"])[primary]
        .agg(["std", "nunique"])
        .reset_index()
    )
    stability = (
        grp.groupby("algorithm")["std"]
        .mean()
        .fillna(0.0)
        .sort_values()
    )
    ours = grp[grp["algorithm"] == "Ours (Full)"]["nunique"].value_counts().sort_index()
    stability_map = {str(k): float(v) for k, v in stability.to_dict().items()}
    ours_unique = {str(int(k)): int(v) for k, v in ours.to_dict().items()}
    return stability_map, ours_unique


def _relative_vs_nsga(query_df: pd.DataFrame) -> dict[str, float]:
    primary = _primary_metric(query_df.columns)
    base = query_df[query_df["algorithm"] == "Ours (Full)"]
    nsga = query_df[query_df["algorithm"] == "NSGA-II"]
    if base.empty or nsga.empty:
        return {}

    ours = base.mean(numeric_only=True)
    nsg = nsga.mean(numeric_only=True)

    def delta_pct(a: float, b: float) -> float:
        if b == 0:
            return 0.0
        return (a - b) / b * 100.0

    def ratio_pct(numer: float, denom: float) -> float:
        if denom == 0:
            return 0.0
        return numer / denom * 100.0

    return {
        "primary_pct": delta_pct(
            float(ours.get(primary, 0.0)),
            float(nsg.get(primary, 0.0)),
        ),
        "elapsed_delta_pct": delta_pct(
            float(ours.get("elapsed_ms", 0.0)),
            float(nsg.get("elapsed_ms", 0.0)),
        ),
        "stops_pct": delta_pct(float(ours.get("unique_stops", 0.0)), float(nsg.get("unique_stops", 0.0))),
        "hull_pct": delta_pct(float(ours.get("hull_area", 0.0)), float(nsg.get("hull_area", 0.0))),
        "score_rate_pct": delta_pct(float(ours.get("score_per_hour", 0.0)), float(nsg.get("score_per_hour", 0.0))),
    }


def _relative_vs_nsga_by_budget(query_df: pd.DataFrame) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for budget in sorted(query_df["budget_minutes"].dropna().unique().tolist()):
        out[str(int(budget))] = _relative_vs_nsga(query_df[query_df["budget_minutes"] == budget].copy())
    return out


def _elapsed_phrase(delta_pct_value: float) -> str:
    if delta_pct_value < 0:
        return f"elapsed {abs(delta_pct_value):+.2f}% faster".replace("+", "")
    return f"elapsed {delta_pct_value:+.2f}% slower"


def _planner_stats_from_rows(rows: list[dict]) -> dict:
    # Planner internals are not recorded in exp1_results.json.
    # Keep previous known fields when available in historical stats file by leaving placeholders.
    _ = rows
    return {}


def _df_to_markdown(df: pd.DataFrame, floatfmt: str = ".4f") -> str:
    if df.empty:
        return "_No data_"
    return df.to_markdown(index=False, floatfmt=floatfmt)


def _budget_label(budget_minutes: int) -> str:
    return f"{int(budget_minutes // 60)}h"


def _render_markdown(stats_payload: dict) -> str:
    meta = stats_payload["metadata"]
    algo_run = pd.DataFrame(stats_payload["algo_run_summary"])
    algo_query = pd.DataFrame(stats_payload["algo_query_summary"])
    run_by_budget = {k: pd.DataFrame(v) for k, v in stats_payload["algo_run_summary_by_budget"].items()}
    query_by_budget = {k: pd.DataFrame(v) for k, v in stats_payload["algo_query_summary_by_budget"].items()}

    wins_seed = pd.Series(stats_payload["seed_level_composite_wins"], name="wins").sort_values(ascending=False)
    wins_query = pd.Series(stats_payload["query_level_composite_wins"], name="wins").sort_values(ascending=False)
    wins_by_budget_seed = pd.DataFrame(stats_payload["seed_level_wins_by_budget"]).fillna(0).astype(int)
    wins_by_budget_query = pd.DataFrame(stats_payload["query_level_wins_by_budget"]).fillna(0).astype(int)

    wilcoxon_overall = pd.DataFrame(stats_payload["wilcoxon_query_level"])
    wilcoxon_by_budget = {
        k: pd.DataFrame(v) for k, v in stats_payload["wilcoxon_query_level_by_budget"].items()
    }

    primary = meta.get("primary_metric", "composite_score")
    primary_label = meta.get("primary_metric_label", _primary_label(str(primary)))
    top_overall = algo_query.sort_values("primary_mean", ascending=False).iloc[0]["algorithm"]
    rel = stats_payload.get("relative_vs_nsga", {})
    rel_by_budget = stats_payload.get("relative_vs_nsga_by_budget", {})

    lines: list[str] = []
    lines.append("# Experiment 1 Full-Scale Textual Analysis (Score-Based Revision)")
    lines.append("")
    lines.append(f"- Source result file: `{meta.get('results_file', 'paper/results/exp1_algorithm_comparison/exp1_results.json')}`")
    lines.append(f"- Analysis timestamp (result metadata): `{meta.get('timestamp', 'N/A')}`")
    lines.append(f"- Quick mode: `{meta.get('quick_mode', 'N/A')}`")
    lines.append(f"- Primary metric: `{primary_label}`")
    if "dwell_minutes" in meta:
        lines.append(f"- Uniform dwell time per scored stop: `{meta.get('dwell_minutes')}` minutes")
    lines.append("")
    lines.append("## 1. Protocol Clarification")
    lines.append("")
    lines.append("- This revised report provides **both** overall (4h+8h combined) and budget-sliced (4h / 8h separate) views.")
    lines.append("- Combined views are retained for global ranking; budget-sliced views avoid interpretation bias from truncation effects.")
    lines.append("")
    lines.append("## 2. Overall (Combined 4h+8h) Results")
    lines.append("")
    lines.append("### 2.1 Run-Level Summary")
    lines.append("")
    lines.append(_df_to_markdown(algo_run, floatfmt=".4f"))
    lines.append("")
    lines.append("### 2.2 Query-Level Summary")
    lines.append("")
    lines.append(_df_to_markdown(algo_query, floatfmt=".4f"))
    lines.append("")
    lines.append(f"- Top algorithm by {primary_label.lower()} (overall query-level): **{top_overall}**")
    if rel:
        lines.append(
            "- Ours vs NSGA-II (overall): "
            f"{primary_label.lower()} {rel.get('primary_pct', 0.0):+.2f}%, "
            f"{_elapsed_phrase(rel.get('elapsed_delta_pct', 0.0))}, "
            f"stops {rel.get('stops_pct', 0.0):+.2f}%, "
            f"score-rate {rel.get('score_rate_pct', 0.0):+.2f}%, "
            f"hull {rel.get('hull_pct', 0.0):+.2f}%."
        )
    lines.append("")
    lines.append("## 3. Budget-Sliced Results")
    lines.append("")
    for budget_key in sorted(query_by_budget.keys(), key=lambda x: int(x)):
        budget = int(budget_key)
        lines.append(f"### 3.{1 if budget == 240 else 2} Budget = {_budget_label(budget)}")
        lines.append("")
        lines.append("#### Query-Level Summary")
        lines.append("")
        lines.append(_df_to_markdown(query_by_budget[budget_key], floatfmt=".4f"))
        lines.append("")
        lines.append("#### Run-Level Summary")
        lines.append("")
        lines.append(_df_to_markdown(run_by_budget[budget_key], floatfmt=".4f"))
        if budget_key in rel_by_budget and rel_by_budget[budget_key]:
            r = rel_by_budget[budget_key]
            lines.append("")
            lines.append(
                "- Ours vs NSGA-II: "
                f"{primary_label.lower()} {r.get('primary_pct', 0.0):+.2f}%, "
                f"{_elapsed_phrase(r.get('elapsed_delta_pct', 0.0))}, "
                f"stops {r.get('stops_pct', 0.0):+.2f}%, "
                f"score-rate {r.get('score_rate_pct', 0.0):+.2f}%, "
                f"hull {r.get('hull_pct', 0.0):+.2f}%."
            )
        lines.append("")
    lines.append("## 4. Win Counts")
    lines.append("")
    lines.append(f"### 4.1 Seed-Level {primary_label} Wins (300 cases)")
    lines.append("")
    lines.append(wins_seed.to_frame().to_markdown())
    lines.append("")
    lines.append(f"### 4.2 Query-Level {primary_label} Wins (60 cases)")
    lines.append("")
    lines.append(wins_query.to_frame().to_markdown())
    lines.append("")
    lines.append("### 4.3 Seed-Level Wins by Budget")
    lines.append("")
    lines.append(wins_by_budget_seed.to_markdown())
    lines.append("")
    lines.append("### 4.4 Query-Level Wins by Budget")
    lines.append("")
    lines.append(wins_by_budget_query.to_markdown())
    lines.append("")
    lines.append("## 5. Statistical Tests")
    lines.append("")
    lines.append("### 5.1 Overall Wilcoxon (Query-Level)")
    lines.append("")
    lines.append(_df_to_markdown(wilcoxon_overall, floatfmt=".6g"))
    lines.append("")
    for budget_key in sorted(wilcoxon_by_budget.keys(), key=lambda x: int(x)):
        lines.append(f"### 5.{2 if budget_key == '240' else 3} Wilcoxon for {_budget_label(int(budget_key))} only")
        lines.append("")
        lines.append(_df_to_markdown(wilcoxon_by_budget[budget_key], floatfmt=".6g"))
        lines.append("")
    lines.append("## 6. Reproducibility Artifacts")
    lines.append("")
    lines.append("- Figures:")
    lines.append("  - `paper/figures/exp1/exp1_metric_panels.png` (combined)")
    lines.append("  - `paper/figures/exp1/exp1_metric_panels_4h.png`")
    lines.append("  - `paper/figures/exp1/exp1_metric_panels_8h.png`")
    lines.append("- Tables:")
    lines.append("  - `paper/figures/exp1/summary_table.md` (combined)")
    lines.append("  - `paper/figures/exp1/summary_table_4h.md`")
    lines.append("  - `paper/figures/exp1/summary_table_8h.md`")
    lines.append("  - `paper/figures/exp1/statistical_tests.md` (combined)")
    lines.append("  - `paper/figures/exp1/statistical_tests_4h.md`")
    lines.append("  - `paper/figures/exp1/statistical_tests_8h.md`")
    lines.append("- Machine-readable stats:")
    lines.append("  - `paper/results/exp1_algorithm_comparison/exp1_analysis_stats.json`")
    lines.append("")

    return "\n".join(lines) + "\n"


def build_analysis(results_path: Path, stats_out: Path, md_out: Path) -> None:
    metadata, rows = _load_results(results_path)
    run_df, query_df = _prepare_frames(rows)

    # Planner stats are not embedded in exp1_results.json. Preserve historical file fields if present.
    old_planner_stats: dict = {}
    if stats_out.exists():
        try:
            old_payload = json.loads(stats_out.read_text(encoding="utf-8"))
            old_planner_stats = old_payload.get("planner_stats", {})
        except Exception:
            old_planner_stats = {}

    primary = _primary_metric(query_df.columns)
    metrics_for_tests = [
        (primary, True),
        ("elapsed_ms", False),
        ("unique_stops", True),
        ("score_per_hour", True),
        ("hull_area", True),
    ]

    algo_run_summary = _algo_run_summary(run_df)
    algo_query_summary = _algo_query_summary(query_df)
    run_by_budget, query_by_budget = _summary_by_budget(run_df, query_df)

    seed_wins = _winner_counts(run_df, ["origin", "depart_time", "budget_minutes", "seed"], primary)
    query_wins = _winner_counts(query_df, ["origin", "depart_time", "budget_minutes"], primary)
    seed_wins_budget = _winner_counts_by_slice(
        run_df,
        ["origin", "depart_time", "budget_minutes", "seed"],
        "budget_minutes",
        primary,
    )
    seed_wins_depart = _winner_counts_by_slice(
        run_df,
        ["origin", "depart_time", "budget_minutes", "seed"],
        "depart_time",
        primary,
    )
    query_wins_budget = _winner_counts_by_slice(
        query_df,
        ["origin", "depart_time", "budget_minutes"],
        "budget_minutes",
        primary,
    )
    query_wins_depart = _winner_counts_by_slice(
        query_df,
        ["origin", "depart_time", "budget_minutes"],
        "depart_time",
        primary,
    )

    metric_wins_seed = {
        primary: _winner_counts(run_df, ["origin", "depart_time", "budget_minutes", "seed"], primary),
        "unique_stops": _winner_counts(run_df, ["origin", "depart_time", "budget_minutes", "seed"], "unique_stops"),
        "score_per_hour": _winner_counts(run_df, ["origin", "depart_time", "budget_minutes", "seed"], "score_per_hour"),
        "hull_area": _winner_counts(run_df, ["origin", "depart_time", "budget_minutes", "seed"], "hull_area"),
        "elapsed_ms": _winner_counts(
            run_df,
            ["origin", "depart_time", "budget_minutes", "seed"],
            "elapsed_ms",
            higher_better=False,
        ),
    }

    wilcoxon_overall = _wilcoxon_table(query_df, metrics_for_tests)
    wilcoxon_by_budget = _wilcoxon_by_budget(query_df, metrics_for_tests)
    stability, ours_unique = _stability_stats(run_df)
    infeasible_count = int((~run_df["feasible"]).sum())
    violation_counts = (
        run_df.loc[~run_df["feasible"], "violation_reason"]
        .fillna("")
        .value_counts()
        .to_dict()
    )
    violation_counts = {str(k): int(v) for k, v in violation_counts.items() if str(k)}

    payload = {
        "metadata": {
            **metadata,
            "results_file": str(results_path),
        },
        "planner_stats": old_planner_stats or _planner_stats_from_rows(rows),
        "config": {
            "origins": sorted(run_df["origin"].dropna().astype(str).unique().tolist()),
            "depart_times": sorted(int(x) for x in run_df["depart_time"].dropna().unique().tolist()),
            "budgets": sorted(int(x) for x in run_df["budget_minutes"].dropna().unique().tolist()),
            "num_repeats_max": int(run_df["seed"].nunique()),
            "random_seeds": sorted(int(x) for x in run_df["seed"].dropna().unique().tolist()),
            "total_expected_runs": int(metadata.get("total_runs", len(rows))),
        },
        "algorithms": sorted(run_df["algorithm"].dropna().astype(str).unique().tolist()),
        "algo_run_summary": algo_run_summary,
        "algo_query_summary": algo_query_summary,
        "algo_run_summary_by_budget": run_by_budget,
        "algo_query_summary_by_budget": query_by_budget,
        "seed_level_composite_wins": seed_wins,
        "query_level_composite_wins": query_wins,
        "seed_level_wins_by_budget": seed_wins_budget,
        "seed_level_wins_by_depart": seed_wins_depart,
        "query_level_wins_by_budget": query_wins_budget,
        "query_level_wins_by_depart": query_wins_depart,
        "metric_wins_seed_level": metric_wins_seed,
        "wilcoxon_query_level": wilcoxon_overall,
        "wilcoxon_query_level_by_budget": wilcoxon_by_budget,
        "stability_mean_std_by_seed": stability,
        "ours_unique_counts_across_runs_per_query": ours_unique,
        "ours_unique_counts_across_5_seeds": ours_unique,
        "infeasible_count": infeasible_count,
        "violation_counts": violation_counts,
        "relative_vs_nsga": _relative_vs_nsga(query_df),
        "relative_vs_nsga_by_budget": _relative_vs_nsga_by_budget(query_df),
    }

    stats_out.parent.mkdir(parents=True, exist_ok=True)
    stats_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_out.write_text(_render_markdown(payload), encoding="utf-8")

    print(f"Wrote {stats_out}")
    print(f"Wrote {md_out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate full Exp1 analysis stats + markdown.")
    parser.add_argument("--results", type=Path, default=RESULTS_FILE_DEFAULT)
    parser.add_argument("--stats-out", type=Path, default=STATS_OUT_DEFAULT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT_DEFAULT)
    args = parser.parse_args()
    build_analysis(args.results, args.stats_out, args.md_out)


if __name__ == "__main__":
    main()
