#!/usr/bin/env python3
"""
Generate detailed Exp2 analysis artifacts.

Outputs:
- paper/results/exp2_ablation_study/exp2_analysis_stats.json
- paper/results/exp2_ablation_study/exp2_full_text_analysis.md
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAIN_RESULTS_DEFAULT = PROJECT_ROOT / "paper" / "results" / "exp2_ablation_study" / "exp2_results.json"
SUPPORT_RESULTS_DEFAULT = PROJECT_ROOT / "paper" / "results" / "exp2_ablation_study" / "exp2_supporting_results.json"
STATS_OUT_DEFAULT = PROJECT_ROOT / "paper" / "results" / "exp2_ablation_study" / "exp2_analysis_stats.json"
MD_OUT_DEFAULT = PROJECT_ROOT / "paper" / "results" / "exp2_ablation_study" / "exp2_full_text_analysis.md"


def load_rows(path: Path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected list JSON at {path}, got {type(data)}")
    return data


def to_numeric(df: pd.DataFrame, cols: list[str]) -> None:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")


def q(s: pd.Series, p: float) -> float:
    arr = pd.to_numeric(s, errors="coerce").dropna().to_numpy()
    if len(arr) == 0:
        return 0.0
    return float(np.percentile(arr, p * 100.0))


def to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    return json.loads(df.replace({np.nan: None}).to_json(orient="records"))


def match_key(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    return df[cols].astype(str).agg("|".join, axis=1)


def paired_frames(df: pd.DataFrame, a: str, b: str, key_cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    da = df[df["algorithm"] == a].copy()
    db = df[df["algorithm"] == b].copy()
    if da.empty or db.empty:
        return pd.DataFrame(), pd.DataFrame()
    da["mk"] = match_key(da, key_cols)
    db["mk"] = match_key(db, key_cols)
    da = da.set_index("mk")
    db = db.set_index("mk")
    common = da.index.intersection(db.index)
    if len(common) == 0:
        return pd.DataFrame(), pd.DataFrame()
    return da.loc[common].copy(), db.loc[common].copy()


def wilcoxon_pair(x: np.ndarray, y: np.ndarray, higher_better: bool) -> dict[str, float]:
    diff = x - y
    if np.allclose(diff, 0):
        return {
            "mean_diff": float(np.mean(diff)),
            "median_diff": float(np.median(diff)),
            "w": 0.0,
            "p": 1.0,
            "better_rate": 0.0,
            "tie_rate": 1.0,
        }
    w, p = stats.wilcoxon(x, y, zero_method="wilcox", alternative="two-sided")
    if higher_better:
        better = np.mean(x > y)
    else:
        better = np.mean(x < y)
    tie = np.mean(np.isclose(x, y))
    return {
        "mean_diff": float(np.mean(diff)),
        "median_diff": float(np.median(diff)),
        "w": float(w),
        "p": float(p),
        "better_rate": float(better),
        "tie_rate": float(tie),
    }


def df_md(df: pd.DataFrame, floatfmt: str = ".4f") -> str:
    if df.empty:
        return "_No data_"
    return df.to_markdown(index=False, floatfmt=floatfmt)


def pct(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return (a - b) / b * 100.0


def infer_main(main_df: pd.DataFrame) -> dict[str, Any]:
    return {
        "algorithms": sorted(main_df["algorithm"].unique().tolist()),
        "num_origins": int(main_df["origin"].nunique()),
        "depart_times": sorted([int(x) for x in main_df["depart_time"].dropna().unique().tolist()]),
        "budgets": sorted([int(x) for x in main_df["budget_minutes"].dropna().unique().tolist()]),
        "seeds": sorted([int(x) for x in main_df["seed"].dropna().unique().tolist()]),
    }


def summarize_main_run(run_df: pd.DataFrame) -> pd.DataFrame:
    out = (
        run_df.groupby("algorithm", as_index=False)
        .agg(
            n=("algorithm", "size"),
            feasible_rate=("feasible", "mean"),
            cap_hit_rate=("resource_cap_hit", "mean"),
            timeout_rate=("is_timeout", "mean"),
            label_cap_rate=("is_label_cap", "mean"),
            elapsed_mean=("elapsed_ms", "mean"),
            elapsed_median=("elapsed_ms", "median"),
            elapsed_std=("elapsed_ms", "std"),
            elapsed_p95=("elapsed_ms", lambda s: q(s, 0.95)),
            labels_mean=("labels", "mean"),
            labels_p95=("labels", lambda s: q(s, 0.95)),
            composite_mean=("composite_score", "mean"),
            composite_std=("composite_score", "std"),
            ride_mean=("ride_minutes", "mean"),
            stops_mean=("unique_stops", "mean"),
            hull_mean=("hull_area", "mean"),
            quadrant_mean=("quadrant_coverage", "mean"),
            total_time_mean=("total_time_minutes", "mean"),
        )
        .sort_values("composite_mean", ascending=False)
    )
    return out


def summarize_main_query(query_df: pd.DataFrame) -> pd.DataFrame:
    out = (
        query_df.groupby("algorithm", as_index=False)
        .agg(
            n_queries=("algorithm", "size"),
            feasible_rate=("feasible_rate", "mean"),
            cap_hit_rate=("cap_hit_rate", "mean"),
            timeout_rate=("timeout_rate", "mean"),
            elapsed_mean=("elapsed_ms", "mean"),
            labels_mean=("labels", "mean"),
            composite_mean=("composite_score", "mean"),
            ride_mean=("ride_minutes", "mean"),
            stops_mean=("unique_stops", "mean"),
            hull_mean=("hull_area", "mean"),
            quadrant_mean=("quadrant_coverage", "mean"),
            total_time_mean=("total_time_minutes", "mean"),
        )
        .sort_values("composite_mean", ascending=False)
    )
    return out

def main_pairwise_vs_full(query_df: pd.DataFrame) -> pd.DataFrame:
    full = "Ours (Full)"
    key_cols = ["origin", "depart_time", "budget_minutes"]
    rows: list[dict[str, Any]] = []
    for algo in sorted(set(query_df["algorithm"].tolist()) - {full}):
        a, b = paired_frames(query_df, algo, full, key_cols)
        if a.empty:
            continue
        rows.append(
            {
                "algorithm": algo,
                "N": int(len(a)),
                "variant_minus_full_composite": float(a["composite_score"].mean() - b["composite_score"].mean()),
                "variant_minus_full_elapsed_ms": float(a["elapsed_ms"].mean() - b["elapsed_ms"].mean()),
                "variant_minus_full_labels": float(a["labels"].mean() - b["labels"].mean()),
                "variant_minus_full_ride": float(a["ride_minutes"].mean() - b["ride_minutes"].mean()),
                "variant_minus_full_stops": float(a["unique_stops"].mean() - b["unique_stops"].mean()),
                "variant_minus_full_hull": float(a["hull_area"].mean() - b["hull_area"].mean()),
                "variant_minus_full_cap_hit_rate": float(a["cap_hit_rate"].mean() - b["cap_hit_rate"].mean()),
                "variant_minus_full_timeout_rate": float(a["timeout_rate"].mean() - b["timeout_rate"].mean()),
                "variant_vs_full_composite_pct": pct(float(a["composite_score"].mean()), float(b["composite_score"].mean())),
                "variant_vs_full_elapsed_pct": pct(float(a["elapsed_ms"].mean()), float(b["elapsed_ms"].mean())),
            }
        )
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values("variant_minus_full_composite", ascending=False)
    return out


def main_wilcoxon_vs_full(query_df: pd.DataFrame) -> list[dict[str, Any]]:
    full = "Ours (Full)"
    key_cols = ["origin", "depart_time", "budget_minutes"]
    metrics = [
        ("composite_score", True),
        ("elapsed_ms", False),
        ("labels", False),
        ("ride_minutes", True),
        ("unique_stops", True),
        ("hull_area", True),
        ("cap_hit_rate", False),
        ("timeout_rate", False),
    ]
    rows: list[dict[str, Any]] = []
    for algo in sorted(set(query_df["algorithm"].tolist()) - {full}):
        a, b = paired_frames(query_df, full, algo, key_cols)
        entry: dict[str, Any] = {"algorithm": algo, "N": int(len(a))}
        if len(a) < 5:
            rows.append(entry)
            continue
        for metric, higher_better in metrics:
            x = pd.to_numeric(a[metric], errors="coerce").fillna(0.0).to_numpy()
            y = pd.to_numeric(b[metric], errors="coerce").fillna(0.0).to_numpy()
            r = wilcoxon_pair(x, y, higher_better)
            entry[f"{metric}_mean_diff_full_minus_other"] = r["mean_diff"]
            entry[f"{metric}_median_diff_full_minus_other"] = r["median_diff"]
            entry[f"{metric}_w"] = r["w"]
            entry[f"{metric}_p"] = r["p"]
            entry[f"{metric}_full_better_rate"] = r["better_rate"]
            entry[f"{metric}_tie_rate"] = r["tie_rate"]
        rows.append(entry)
    return rows


def winner_counts(df: pd.DataFrame, group_cols: list[str]) -> dict[str, int]:
    if df.empty:
        return {}
    idx = df.groupby(group_cols)["composite_score"].idxmax()
    w = df.loc[idx, "algorithm"].value_counts()
    return {str(k): int(v) for k, v in w.to_dict().items()}


def infer_support(sup_df: pd.DataFrame) -> dict[str, Any]:
    return {
        "experiments": sorted(sup_df["experiment"].unique().tolist()),
        "algorithms": sorted(sup_df["algorithm"].unique().tolist()),
        "num_origins": int(sup_df["origin"].nunique()),
        "depart_times": sorted([int(x) for x in sup_df["depart_time"].dropna().unique().tolist()]),
        "budgets": sorted([int(x) for x in sup_df["budget_minutes"].dropna().unique().tolist()]),
        "seeds": sorted([int(x) for x in sup_df["seed"].dropna().unique().tolist()]),
    }


def support_summary_by_exp(sup_df: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for exp in sorted(sup_df["experiment"].unique().tolist()):
        sub = sup_df[sup_df["experiment"] == exp].copy()
        agg = (
            sub.groupby("algorithm", as_index=False)
            .agg(
                runs=("algorithm", "size"),
                feasible_rate=("feasible", "mean"),
                cap_hit_rate=("resource_cap_hit", "mean"),
                timeout_rate=("is_timeout", "mean"),
                elapsed_mean=("elapsed_ms", "mean"),
                elapsed_p95=("elapsed_ms", lambda s: q(s, 0.95)),
                elapsed_p99=("elapsed_ms", lambda s: q(s, 0.99)),
                composite_mean=("composite_score", "mean"),
                theme_composite_mean=("theme_composite_score", "mean"),
                ride_mean=("ride_minutes", "mean"),
                stops_mean=("unique_stops", "mean"),
                hull_mean=("hull_area", "mean"),
                waiting_ratio_mean=("waiting_ratio", "mean"),
                revisit_ratio_mean=("revisit_ratio", "mean"),
                backtrack_mean=("backtrack_count", "mean"),
                beam_trim_run_rate=("beam_trim_events", lambda s: float(np.mean(pd.to_numeric(s, errors="coerce").fillna(0.0) > 0.0))),
                beam_trimmed_labels_mean=("beam_trimmed_labels", "mean"),
                negative_hit_run_rate=("negative_total_hits", lambda s: float(np.mean(pd.to_numeric(s, errors="coerce").fillna(0.0) > 0.0))),
                negative_hit_mean=("negative_total_hits", "mean"),
                negative_theme_hit_mean=("negative_theme_hits", "mean"),
                theme_hit_ratio_mean=("theme_hit_ratio", "mean"),
                theme_satisfied_rate=("theme_satisfied", "mean"),
            )
            .sort_values("theme_composite_mean", ascending=False)
        )
        out[str(exp)] = to_records(agg)
    return out


def beam_analysis(sup_df: pd.DataFrame) -> dict[str, Any]:
    sub = sup_df[sup_df["experiment"] == "beam_width_sweep_stress"].copy()
    if sub.empty:
        return {}
    sum_df = pd.DataFrame(support_summary_by_exp(sub).get("beam_width_sweep_stress", []))
    key_cols = ["origin", "depart_time", "budget_minutes", "seed"]
    baseline = "Ours (NoBeam)"
    algos = [a for a in sorted(sub["algorithm"].unique().tolist()) if a != baseline]

    delta_rows: list[dict[str, Any]] = []
    wil_rows: list[dict[str, Any]] = []
    for algo in algos:
        a, b = paired_frames(sub, algo, baseline, key_cols)
        if a.empty:
            continue
        delta_rows.append(
            {
                "algorithm": algo,
                "baseline": baseline,
                "N": int(len(a)),
                "delta_composite": float(a["composite_score"].mean() - b["composite_score"].mean()),
                "delta_elapsed_ms": float(a["elapsed_ms"].mean() - b["elapsed_ms"].mean()),
                "delta_labels": float(a["labels"].mean() - b["labels"].mean()),
                "delta_cap_hit_rate": float(a["resource_cap_hit"].mean() - b["resource_cap_hit"].mean()),
                "delta_timeout_rate": float(a["is_timeout"].mean() - b["is_timeout"].mean()),
            }
        )
        w1 = wilcoxon_pair(a["composite_score"].to_numpy(), b["composite_score"].to_numpy(), True)
        w2 = wilcoxon_pair(a["elapsed_ms"].to_numpy(), b["elapsed_ms"].to_numpy(), False)
        wil_rows.append(
            {
                "algorithm": algo,
                "baseline": baseline,
                "N": int(len(a)),
                "composite_mean_diff_algo_minus_nobeam": float(a["composite_score"].mean() - b["composite_score"].mean()),
                "composite_w": w1["w"],
                "composite_p": w1["p"],
                "composite_algo_better_rate": w1["better_rate"],
                "elapsed_mean_diff_algo_minus_nobeam": float(a["elapsed_ms"].mean() - b["elapsed_ms"].mean()),
                "elapsed_w": w2["w"],
                "elapsed_p": w2["p"],
                "elapsed_algo_better_rate": w2["better_rate"],
            }
        )

    by_budget: dict[str, list[dict[str, Any]]] = {}
    for bgt in sorted(sub["budget_minutes"].dropna().unique().tolist()):
        part = sub[sub["budget_minutes"] == bgt].copy()
        tmp: list[dict[str, Any]] = []
        for algo in algos:
            a, b = paired_frames(part, algo, baseline, key_cols)
            if a.empty:
                continue
            tmp.append(
                {
                    "algorithm": algo,
                    "baseline": baseline,
                    "N": int(len(a)),
                    "delta_composite": float(a["composite_score"].mean() - b["composite_score"].mean()),
                    "delta_elapsed_ms": float(a["elapsed_ms"].mean() - b["elapsed_ms"].mean()),
                    "delta_cap_hit_rate": float(a["resource_cap_hit"].mean() - b["resource_cap_hit"].mean()),
                    "delta_timeout_rate": float(a["is_timeout"].mean() - b["is_timeout"].mean()),
                }
            )
        by_budget[str(int(bgt))] = tmp

    return {
        "run_summary": to_records(sum_df),
        "deltas_vs_nobeam": delta_rows,
        "deltas_vs_nobeam_by_budget": by_budget,
        "wilcoxon_vs_nobeam": wil_rows,
    }

def theme_analysis(sup_df: pd.DataFrame) -> dict[str, Any]:
    sub = sup_df[sup_df["experiment"].str.startswith("theme_negative::")].copy()
    if sub.empty:
        return {}
    themes = sorted(sub["experiment"].unique().tolist())

    per_theme: list[dict[str, Any]] = []
    per_w: list[dict[str, Any]] = []
    key_small = ["origin", "depart_time", "budget_minutes", "seed"]

    for t in themes:
        part = sub[sub["experiment"] == t].copy()
        a, b = paired_frames(part, "Ours (Full)", "Ours (NoNeg)", key_small)
        if a.empty:
            continue
        per_theme.append(
            {
                "theme": t,
                "N": int(len(a)),
                "delta_composite_full_minus_noneg": float(a["composite_score"].mean() - b["composite_score"].mean()),
                "delta_theme_composite_full_minus_noneg": float(a["theme_composite_score"].mean() - b["theme_composite_score"].mean()),
                "delta_theme_hit_ratio_full_minus_noneg": float(a["theme_hit_ratio"].mean() - b["theme_hit_ratio"].mean()),
                "delta_theme_satisfied_rate_full_minus_noneg": float(a["theme_satisfied"].mean() - b["theme_satisfied"].mean()),
                "delta_elapsed_ms_full_minus_noneg": float(a["elapsed_ms"].mean() - b["elapsed_ms"].mean()),
                "delta_cap_hit_rate_full_minus_noneg": float(a["resource_cap_hit"].mean() - b["resource_cap_hit"].mean()),
                "delta_timeout_rate_full_minus_noneg": float(a["is_timeout"].mean() - b["is_timeout"].mean()),
                "full_negative_theme_hit_mean": float(a["negative_theme_hits"].mean()),
                "noneg_negative_theme_hit_mean": float(b["negative_theme_hits"].mean()),
            }
        )

        w_tc = wilcoxon_pair(a["theme_composite_score"].to_numpy(), b["theme_composite_score"].to_numpy(), True)
        w_c = wilcoxon_pair(a["composite_score"].to_numpy(), b["composite_score"].to_numpy(), True)
        w_h = wilcoxon_pair(a["theme_hit_ratio"].to_numpy(), b["theme_hit_ratio"].to_numpy(), True)
        w_t = wilcoxon_pair(a["elapsed_ms"].to_numpy(), b["elapsed_ms"].to_numpy(), False)
        per_w.append(
            {
                "theme": t,
                "N": int(len(a)),
                "theme_composite_w": w_tc["w"],
                "theme_composite_p": w_tc["p"],
                "composite_w": w_c["w"],
                "composite_p": w_c["p"],
                "theme_hit_ratio_w": w_h["w"],
                "theme_hit_ratio_p": w_h["p"],
                "elapsed_w": w_t["w"],
                "elapsed_p": w_t["p"],
            }
        )

    # pooled over all themes
    full, noneg = paired_frames(sub, "Ours (Full)", "Ours (NoNeg)", ["experiment", "origin", "depart_time", "budget_minutes", "seed"])
    pooled: dict[str, Any] = {}
    if not full.empty:
        pooled = {
            "N": int(len(full)),
            "delta_composite_full_minus_noneg": float(full["composite_score"].mean() - noneg["composite_score"].mean()),
            "delta_theme_composite_full_minus_noneg": float(full["theme_composite_score"].mean() - noneg["theme_composite_score"].mean()),
            "delta_theme_hit_ratio_full_minus_noneg": float(full["theme_hit_ratio"].mean() - noneg["theme_hit_ratio"].mean()),
            "delta_theme_satisfied_rate_full_minus_noneg": float(full["theme_satisfied"].mean() - noneg["theme_satisfied"].mean()),
            "delta_elapsed_ms_full_minus_noneg": float(full["elapsed_ms"].mean() - noneg["elapsed_ms"].mean()),
            "delta_cap_hit_rate_full_minus_noneg": float(full["resource_cap_hit"].mean() - noneg["resource_cap_hit"].mean()),
            "delta_timeout_rate_full_minus_noneg": float(full["is_timeout"].mean() - noneg["is_timeout"].mean()),
        }
        for metric, better in [
            ("theme_composite_score", True),
            ("composite_score", True),
            ("theme_hit_ratio", True),
            ("elapsed_ms", False),
        ]:
            r = wilcoxon_pair(full[metric].to_numpy(), noneg[metric].to_numpy(), better)
            pooled[f"{metric}_w"] = r["w"]
            pooled[f"{metric}_p"] = r["p"]
            pooled[f"{metric}_full_better_rate"] = r["better_rate"]

    theme_df = pd.DataFrame(per_theme)
    macro = {}
    if not theme_df.empty:
        macro = {
            "themes": int(len(theme_df)),
            "mean_delta_composite_full_minus_noneg": float(theme_df["delta_composite_full_minus_noneg"].mean()),
            "mean_delta_theme_composite_full_minus_noneg": float(theme_df["delta_theme_composite_full_minus_noneg"].mean()),
            "mean_delta_theme_hit_ratio_full_minus_noneg": float(theme_df["delta_theme_hit_ratio_full_minus_noneg"].mean()),
            "mean_delta_theme_satisfied_rate_full_minus_noneg": float(theme_df["delta_theme_satisfied_rate_full_minus_noneg"].mean()),
            "mean_delta_elapsed_ms_full_minus_noneg": float(theme_df["delta_elapsed_ms_full_minus_noneg"].mean()),
            "positive_theme_composite_count": int((theme_df["delta_theme_composite_full_minus_noneg"] > 0).sum()),
            "positive_composite_count": int((theme_df["delta_composite_full_minus_noneg"] > 0).sum()),
        }

    return {
        "per_theme_full_vs_noneg": per_theme,
        "per_theme_wilcoxon": per_w,
        "pooled_full_vs_noneg": pooled,
        "macro_aggregate_over_themes": macro,
    }


def render_md(payload: dict[str, Any]) -> str:
    m = payload["exp2_main"]
    s = payload["exp2_supporting"]
    num_main_algorithms = len(m["config_inferred"].get("algorithms", []))

    run_df = pd.DataFrame(m["algo_run_summary"])
    query_df = pd.DataFrame(m["algo_query_summary"])
    pair_df = pd.DataFrame(m["full_vs_variants_overall"])
    wil_df = pd.DataFrame(m["wilcoxon_query_level_overall"])

    run_budget = {k: pd.DataFrame(v) for k, v in m["algo_run_summary_by_budget"].items()}
    query_budget = {k: pd.DataFrame(v) for k, v in m["algo_query_summary_by_budget"].items()}
    pair_budget = {k: pd.DataFrame(v) for k, v in m["full_vs_variants_by_budget"].items()}
    wil_budget = {k: pd.DataFrame(v) for k, v in m["wilcoxon_query_level_by_budget"].items()}

    seed_w = pd.Series(m["seed_level_composite_wins"], name="wins").sort_values(ascending=False)
    query_w = pd.Series(m["query_level_composite_wins"], name="wins").sort_values(ascending=False)
    seed_w_b = pd.DataFrame(m["seed_level_wins_by_budget"]).fillna(0).astype(int)
    query_w_b = pd.DataFrame(m["query_level_wins_by_budget"]).fillna(0).astype(int)

    sum_by_exp = {k: pd.DataFrame(v) for k, v in s["summary_by_experiment"].items()}
    beam = s.get("beam_stress", {})
    beam_sum = pd.DataFrame(beam.get("run_summary", []))
    beam_delta = pd.DataFrame(beam.get("deltas_vs_nobeam", []))
    beam_w = pd.DataFrame(beam.get("wilcoxon_vs_nobeam", []))
    beam_budget = {k: pd.DataFrame(v) for k, v in beam.get("deltas_vs_nobeam_by_budget", {}).items()}

    theme = s.get("theme_negative", {})
    theme_df = pd.DataFrame(theme.get("per_theme_full_vs_noneg", []))
    theme_w = pd.DataFrame(theme.get("per_theme_wilcoxon", []))

    lines: list[str] = []
    lines.append("# Experiment 2 Full-Scale Analysis (Ablation + Supporting)")
    lines.append("")
    lines.append("## 0. 数据来源")
    lines.append("")
    lines.append(f"- 主消融: `paper/results/exp2_ablation_study/exp2_results.json`")
    lines.append(f"- 补充实验: `paper/results/exp2_ablation_study/exp2_supporting_results.json`")
    lines.append(f"- 主消融样本数: `{payload['metadata']['main_rows']}`")
    lines.append(f"- 补充实验样本数: `{payload['metadata']['support_rows']}`")
    lines.append("")
    lines.append(f"## 1. 主消融（{num_main_algorithms}配置）")
    lines.append("")
    lines.append("### 1.1 Run-Level 总体")
    lines.append("")
    lines.append(df_md(run_df))
    lines.append("")
    lines.append("### 1.2 Query-Level 总体")
    lines.append("")
    lines.append(df_md(query_df))
    lines.append("")
    lines.append("### 1.3 Full 对各消融配置差值（总体）")
    lines.append("")
    lines.append(df_md(pair_df))
    lines.append("")
    lines.append("### 1.4 Full vs 各配置配对检验（总体，Wilcoxon）")
    lines.append("")
    lines.append(df_md(wil_df))
    lines.append("")
    for b in sorted(run_budget.keys(), key=lambda x: int(x)):
        h = int(int(b) // 60)
        lines.append(f"### 1.{5 if h==4 else 6} Budget={h}h 切片")
        lines.append("")
        lines.append("Run-Level:")
        lines.append("")
        lines.append(df_md(run_budget[b]))
        lines.append("")
        lines.append("Query-Level:")
        lines.append("")
        lines.append(df_md(query_budget[b]))
        lines.append("")
        lines.append("Full 对各消融配置差值:")
        lines.append("")
        lines.append(df_md(pair_budget[b]))
        lines.append("")
        lines.append("Wilcoxon:")
        lines.append("")
        lines.append(df_md(wil_budget[b]))
        lines.append("")

    lines.append("### 1.7 胜场统计（Composite）")
    lines.append("")
    lines.append("Seed-Level:")
    lines.append("")
    lines.append(seed_w.to_frame().to_markdown())
    lines.append("")
    lines.append("Query-Level:")
    lines.append("")
    lines.append(query_w.to_frame().to_markdown())
    lines.append("")
    lines.append("Seed-Level by budget:")
    lines.append("")
    lines.append(seed_w_b.to_markdown())
    lines.append("")
    lines.append("Query-Level by budget:")
    lines.append("")
    lines.append(query_w_b.to_markdown())
    lines.append("")

    lines.append("## 2. 补充实验")
    lines.append("")
    for exp in sorted(sum_by_exp.keys()):
        lines.append(f"### 2.x {exp}")
        lines.append("")
        lines.append(df_md(sum_by_exp[exp]))
        lines.append("")

    lines.append("### 2.1 Beam 压力实验解读")
    lines.append("")
    lines.append(df_md(beam_sum))
    lines.append("")
    lines.append(df_md(beam_delta))
    lines.append("")
    lines.append(df_md(beam_w))
    lines.append("")
    for b in sorted(beam_budget.keys(), key=lambda x: int(x)):
        h = int(int(b) // 60)
        lines.append(f"Budget={h}h delta vs NoBeam:")
        lines.append("")
        lines.append(df_md(beam_budget[b]))
        lines.append("")

    lines.append("### 2.2 Theme Negative 解读")
    lines.append("")
    lines.append(df_md(theme_df))
    lines.append("")
    lines.append(df_md(theme_w))
    lines.append("")
    lines.append("Macro aggregate over themes:")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(theme.get("macro_aggregate_over_themes", {}), ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("Pooled full vs noneg:")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(theme.get("pooled_full_vs_noneg", {}), ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")

    lines.append("## 3. 总结（可写入论文）")
    lines.append("")
    lines.append("1. 主消融中 Beam 与 Dominance 都是中核层；单独去掉任一层都会明显放大搜索开销，而联合去掉二者时更能直接暴露搜索空间失控。")
    lines.append("2. `NoBeam-NoDom` 用于区分联合作用，避免把 `NoBeam-NoDom-NoNeg` 的退化全部归因于 Negative。")
    lines.append("3. Negative 在主题 supporting task 中主张更准确；它主要负责语义/主题对齐，而不是主 benchmark 里的核心提速。")
    lines.append("4. 因此实验二的职责划分应写成：Beam + Dominance = 搜索空间控制核心，Negative = 主题/语义约束层。")
    lines.append("")

    return "\n".join(lines) + "\n"

def build_payload(main_rows: list[dict[str, Any]], support_rows: list[dict[str, Any]], main_file: Path, support_file: Path) -> dict[str, Any]:
    # Main
    run_df = pd.DataFrame(main_rows)
    to_numeric(
        run_df,
        [
            "depart_time",
            "budget_minutes",
            "seed",
            "elapsed_ms",
            "ride_minutes",
            "distance_km",
            "unique_stops",
            "legs",
            "hull_area",
            "quadrant_coverage",
            "total_time_minutes",
            "composite_score",
            "labels",
            "timeout_seconds",
            "max_labels_cap",
        ],
    )
    run_df["algorithm"] = run_df["algorithm"].astype(str)
    run_df["origin"] = run_df["origin"].astype(str)
    run_df["feasible"] = run_df.get("feasible", True).fillna(False).astype(bool)
    run_df["resource_cap_hit"] = run_df.get("resource_cap_hit", False).fillna(False).astype(bool)
    run_df["termination_reason"] = run_df.get("termination_reason", "completed").fillna("completed").astype(str)
    run_df["is_timeout"] = run_df["termination_reason"].eq("timeout")
    run_df["is_label_cap"] = run_df["termination_reason"].eq("label_cap")

    query_df = (
        run_df.groupby(["algorithm", "origin", "depart_time", "budget_minutes"], as_index=False)
        .agg(
            elapsed_ms=("elapsed_ms", "mean"),
            ride_minutes=("ride_minutes", "mean"),
            distance_km=("distance_km", "mean"),
            unique_stops=("unique_stops", "mean"),
            legs=("legs", "mean"),
            hull_area=("hull_area", "mean"),
            quadrant_coverage=("quadrant_coverage", "mean"),
            total_time_minutes=("total_time_minutes", "mean"),
            composite_score=("composite_score", "mean"),
            labels=("labels", "mean"),
            feasible_rate=("feasible", "mean"),
            cap_hit_rate=("resource_cap_hit", "mean"),
            timeout_rate=("is_timeout", "mean"),
            label_cap_rate=("is_label_cap", "mean"),
        )
    )

    run_summary = summarize_main_run(run_df)
    query_summary = summarize_main_query(query_df)

    run_budget = {}
    query_budget = {}
    pair_budget = {}
    wil_budget = {}
    for b in sorted(query_df["budget_minutes"].dropna().unique().tolist()):
        k = str(int(b))
        run_budget[k] = summarize_main_run(run_df[run_df["budget_minutes"] == b].copy())
        query_budget[k] = summarize_main_query(query_df[query_df["budget_minutes"] == b].copy())
        pair_budget[k] = main_pairwise_vs_full(query_df[query_df["budget_minutes"] == b].copy())
        wil_budget[k] = main_wilcoxon_vs_full(query_df[query_df["budget_minutes"] == b].copy())

    pair_overall = main_pairwise_vs_full(query_df)
    wil_overall = main_wilcoxon_vs_full(query_df)

    seed_wins = winner_counts(run_df, ["origin", "depart_time", "budget_minutes", "seed"])
    query_wins = winner_counts(query_df, ["origin", "depart_time", "budget_minutes"])

    seed_wins_b = {}
    query_wins_b = {}
    for b in sorted(run_df["budget_minutes"].dropna().unique().tolist()):
        k = str(int(b))
        seed_wins_b[k] = winner_counts(run_df[run_df["budget_minutes"] == b].copy(), ["origin", "depart_time", "seed"])
        query_wins_b[k] = winner_counts(query_df[query_df["budget_minutes"] == b].copy(), ["origin", "depart_time"])

    term_dist = (
        run_df.groupby(["algorithm", "termination_reason"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )

    # Layer-effect compact summary
    qsum = query_summary.set_index("algorithm")
    def layer(a: str, b: str) -> dict[str, float]:
        if a not in qsum.index or b not in qsum.index:
            return {}
        qa, qb = qsum.loc[a], qsum.loc[b]
        return {
            "composite_delta": float(qb["composite_mean"] - qa["composite_mean"]),
            "elapsed_ms_delta": float(qb["elapsed_mean"] - qa["elapsed_mean"]),
            "labels_delta": float(qb["labels_mean"] - qa["labels_mean"]),
            "cap_hit_rate_delta": float(qb["cap_hit_rate"] - qa["cap_hit_rate"]),
            "timeout_rate_delta": float(qb["timeout_rate"] - qa["timeout_rate"]),
        }

    layer_summary = {
        "remove_beam_from_full__NoBeam_minus_Full": layer("Ours (Full)", "Ours (NoBeam)"),
        "remove_negative_from_full__NoNeg_minus_Full": layer("Ours (Full)", "Ours (NoNeg)"),
        "remove_dominance_from_full__NoDom_minus_Full": layer("Ours (Full)", "Ours (NoDom)"),
        "remove_dominance_when_no_beam__NoBeamNoDom_minus_NoBeam": layer("Ours (NoBeam)", "Ours (NoBeam-NoDom)"),
        "remove_beam_when_no_dominance__NoBeamNoDom_minus_NoDom": layer("Ours (NoDom)", "Ours (NoBeam-NoDom)"),
        "remove_negative_when_no_dom__NoDomNoNeg_minus_NoDom": layer("Ours (NoDom)", "Ours (NoDom-NoNeg)"),
        "remove_negative_when_no_beam_no_dom__NoPruning_minus_NoBeamNoDom": layer("Ours (NoBeam-NoDom)", "Ours (NoBeam-NoDom-NoNeg)"),
        "remove_all_from_no_dom_no_neg__NoPruning_minus_NoDomNoNeg": layer("Ours (NoDom-NoNeg)", "Ours (NoBeam-NoDom-NoNeg)"),
    }

    # Supporting
    sup_df = pd.DataFrame(support_rows)
    to_numeric(
        sup_df,
        [
            "depart_time", "budget_minutes", "seed", "elapsed_ms", "ride_minutes", "distance_km", "unique_stops", "legs",
            "hull_area", "quadrant_coverage", "total_time_minutes", "composite_score", "theme_composite_score", "theme_hit_ratio",
            "theme_target_size", "theme_hit_stops", "labels", "scored_labels", "negative_repeat_hits", "negative_ratio_hits",
            "negative_theme_hits", "negative_total_hits", "beam_trim_events", "beam_trimmed_labels", "waiting_ratio", "waiting_minutes",
            "revisit_ratio", "backtrack_count", "line_changes", "unique_lines", "edge_count", "timeout_seconds", "max_labels_cap",
        ],
    )
    for c in ["algorithm", "origin", "origin_code", "experiment", "theme_name", "termination_reason"]:
        if c in sup_df.columns:
            sup_df[c] = sup_df[c].fillna("").astype(str)
    for c in ["feasible", "resource_cap_hit", "theme_active", "theme_satisfied"]:
        if c in sup_df.columns:
            sup_df[c] = sup_df[c].fillna(False).astype(bool)
    sup_df["is_timeout"] = sup_df.get("termination_reason", "").eq("timeout")

    support_summary = support_summary_by_exp(sup_df)
    beam = beam_analysis(sup_df)
    theme = theme_analysis(sup_df)

    payload = {
        "metadata": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "main_results_file": str(main_file.as_posix()),
            "support_results_file": str(support_file.as_posix()),
            "main_rows": int(len(main_rows)),
            "support_rows": int(len(support_rows)),
            "main_results_mtime": datetime.fromtimestamp(main_file.stat().st_mtime).isoformat(timespec="seconds"),
            "support_results_mtime": datetime.fromtimestamp(support_file.stat().st_mtime).isoformat(timespec="seconds"),
        },
        "exp2_main": {
            "config_inferred": infer_main(run_df),
            "algo_run_summary": to_records(run_summary),
            "algo_query_summary": to_records(query_summary),
            "algo_run_summary_by_budget": {k: to_records(v) for k, v in run_budget.items()},
            "algo_query_summary_by_budget": {k: to_records(v) for k, v in query_budget.items()},
            "full_vs_variants_overall": to_records(pair_overall),
            "full_vs_variants_by_budget": {k: to_records(v) for k, v in pair_budget.items()},
            "wilcoxon_query_level_overall": wil_overall,
            "wilcoxon_query_level_by_budget": wil_budget,
            "seed_level_composite_wins": seed_wins,
            "query_level_composite_wins": query_wins,
            "seed_level_wins_by_budget": seed_wins_b,
            "query_level_wins_by_budget": query_wins_b,
            "termination_distribution_run_level": to_records(term_dist),
            "layer_effect_summary": layer_summary,
        },
        "exp2_supporting": {
            "config_inferred": infer_support(sup_df),
            "summary_by_experiment": support_summary,
            "beam_stress": beam,
            "theme_negative": theme,
        },
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate detailed Exp2 full analysis artifacts.")
    parser.add_argument("--main-results", type=Path, default=MAIN_RESULTS_DEFAULT)
    parser.add_argument("--support-results", type=Path, default=SUPPORT_RESULTS_DEFAULT)
    parser.add_argument("--out-json", type=Path, default=STATS_OUT_DEFAULT)
    parser.add_argument("--out-md", type=Path, default=MD_OUT_DEFAULT)
    args = parser.parse_args()

    main_rows = load_rows(args.main_results)
    support_rows = load_rows(args.support_results)
    payload = build_payload(main_rows, support_rows, args.main_results, args.support_results)
    md = render_md(payload)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    args.out_md.write_text(md, encoding="utf-8")

    print(f"[OK] stats json -> {args.out_json}")
    print(f"[OK] full text md -> {args.out_md}")


if __name__ == "__main__":
    main()
