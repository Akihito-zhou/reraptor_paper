#!/usr/bin/env python3
"""Canonical Ours-vs-NSGA-II underperformance analysis.

The paired analysis unit is
``(origin, departure, budget, reward/score seed)``.  NSGA-II's five
algorithm-seed runs are averaged within each unit before comparison with the
single deterministic ReRAPTOR/Ours run.  Algorithm failures retain their
pre-registered zero score.

Confidence intervals use a crossed block bootstrap over reward seeds and
origin-departure scenarios.  Budgets remain fixed repeated design points
within each sampled scenario, so the 600 grid cells are not treated as 600
independent observations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import rankdata, wilcoxon


OURS_NAME = "Ours (Full)"
NSGA_NAME = "NSGA-II"
TASK_KEY = ["origin_name", "depart_time", "budget_minutes", "score_seed"]
SCENARIO_COLS = ["origin_name", "depart_time"]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULT = (
    PROJECT_ROOT
    / "paper"
    / "results"
    / "exp1_algorithm_comparison"
    / "exp1_results_canonical_final_10alg_manuscript_20260723.json"
)
DEFAULT_MANIFEST = (
    PROJECT_ROOT
    / "paper"
    / "results"
    / "manifests"
    / "phasea_exp1_final_10alg_manuscript_manifest_20260723.json"
)
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "paper" / "results" / "exp1_algorithm_comparison"
DEFAULT_FIGURES_DIR = PROJECT_ROOT / "paper" / "figures" / "exp1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def load_result_frame(path: Path) -> tuple[dict[str, Any], pd.DataFrame]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError(f"Unsupported result payload: {path}")
    metadata = dict(payload.get("metadata", {}) or {})
    frame = pd.DataFrame(payload["results"])
    required = {
        "algorithm",
        "origin_name",
        "depart_time",
        "budget_minutes",
        "seed",
        "score_seed",
        "stop_score_total",
        "elapsed_ms",
        "scored_stop_count",
        "feasible",
        "algorithm_failure",
        "violation_reason",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Result rows are missing required columns: {missing}")

    numeric = [
        "depart_time",
        "budget_minutes",
        "seed",
        "score_seed",
        "stop_score_total",
        "elapsed_ms",
        "scored_stop_count",
    ]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    for column in ["feasible", "algorithm_failure"]:
        frame[column] = frame[column].astype(bool)
    frame["algorithm"] = frame["algorithm"].astype(str)
    frame["origin_name"] = frame["origin_name"].astype(str)
    return metadata, frame


def _reward_density(score: pd.Series, stop_count: pd.Series) -> pd.Series:
    score_values = score.astype(float)
    stop_values = stop_count.astype(float)
    return pd.Series(
        np.where(stop_values > 0.0, score_values / stop_values, np.nan),
        index=score.index,
        dtype=float,
    )


def build_task_frame(
    run_frame: pd.DataFrame, *, expected_task_count: int | None = 600
) -> pd.DataFrame:
    """Aggregate raw Ours and NSGA-II runs into 600 paired task rows."""
    selected = run_frame[run_frame["algorithm"].isin([OURS_NAME, NSGA_NAME])].copy()
    algorithms = set(selected["algorithm"].unique())
    if algorithms != {OURS_NAME, NSGA_NAME}:
        raise ValueError(f"Expected Ours and NSGA-II, found {sorted(algorithms)}")

    selected["reward_per_scored_stop"] = _reward_density(
        selected["stop_score_total"], selected["scored_stop_count"]
    )
    selected["score_if_feasible"] = selected["stop_score_total"].where(
        selected["feasible"], np.nan
    )
    ours = selected[selected["algorithm"] == OURS_NAME].copy()
    nsga = selected[selected["algorithm"] == NSGA_NAME].copy()

    ours_counts = ours.groupby(TASK_KEY, sort=False).size()
    nsga_counts = nsga.groupby(TASK_KEY, sort=False).size()
    if not ours_counts.eq(1).all():
        bad = ours_counts[~ours_counts.eq(1)].head().to_dict()
        raise ValueError(f"Ours must have one run per paired task: {bad}")
    if not nsga_counts.eq(5).all():
        bad = nsga_counts[~nsga_counts.eq(5)].head().to_dict()
        raise ValueError(f"NSGA-II must have five runs per paired task: {bad}")
    if set(ours_counts.index) != set(nsga_counts.index):
        raise ValueError("Ours and NSGA-II paired task keys do not match")

    ours_seeds = ours.groupby(TASK_KEY, sort=False)["seed"].agg(lambda x: tuple(sorted(set(x))))
    nsga_seeds = nsga.groupby(TASK_KEY, sort=False)["seed"].agg(lambda x: tuple(sorted(set(x))))
    if not ours_seeds.map(lambda value: value == (0,)).all():
        raise ValueError("Ours seed policy differs from the expected deterministic seed 0")
    if not nsga_seeds.map(lambda value: value == (0, 1, 2, 3, 4)).all():
        raise ValueError("NSGA-II seed policy differs from seeds 0..4")

    ours_task = (
        ours.groupby(TASK_KEY, as_index=False, sort=False)
        .agg(
            ours_score=("stop_score_total", "first"),
            ours_elapsed_ms=("elapsed_ms", "first"),
            ours_scored_stop_count=("scored_stop_count", "first"),
            ours_reward_per_scored_stop=("reward_per_scored_stop", "first"),
            ours_feasible=("feasible", "first"),
            ours_algorithm_failure=("algorithm_failure", "first"),
        )
    )
    nsga_task = (
        nsga.groupby(TASK_KEY, as_index=False, sort=False)
        .agg(
            nsga_score=("stop_score_total", "mean"),
            nsga_score_feasible_only=("score_if_feasible", "mean"),
            nsga_score_sd=("stop_score_total", "std"),
            nsga_elapsed_ms=("elapsed_ms", "mean"),
            nsga_scored_stop_count=("scored_stop_count", "mean"),
            nsga_reward_per_scored_stop=("reward_per_scored_stop", "mean"),
            nsga_feasible_runs=("feasible", "sum"),
            nsga_failure_count=("algorithm_failure", "sum"),
            nsga_run_count=("algorithm", "size"),
        )
    )
    task = ours_task.merge(nsga_task, on=TASK_KEY, how="inner", validate="one_to_one")
    task["score_gap"] = task["ours_score"] - task["nsga_score"]
    task["score_gap_feasible_only"] = (
        task["ours_score"] - task["nsga_score_feasible_only"]
    )
    task["elapsed_ratio_nsga_over_ours"] = task["nsga_elapsed_ms"] / task[
        "ours_elapsed_ms"
    ].clip(lower=1e-9)
    task["nsga_failure_rate"] = task["nsga_failure_count"] / task["nsga_run_count"]
    task["nsga_any_failure"] = task["nsga_failure_count"] > 0
    task["nsga_all_failed"] = task["nsga_failure_count"] == task["nsga_run_count"]
    task["budget_hours"] = task["budget_minutes"] / 60.0
    task["departure_label"] = task["depart_time"].map(
        lambda value: f"{int(value) // 60:02d}:{int(value) % 60:02d}"
    )
    task["task_key"] = task[TASK_KEY].astype(str).agg("|".join, axis=1)
    if expected_task_count is not None and len(task) != expected_task_count:
        raise ValueError(
            f"Expected {expected_task_count} paired tasks, found {len(task)}"
        )
    if bool(task["ours_algorithm_failure"].any()) or not bool(task["ours_feasible"].all()):
        raise ValueError("Canonical Ours rows unexpectedly include an algorithm failure")
    return task.sort_values(TASK_KEY).reset_index(drop=True)


def classify_outcomes(gaps: pd.Series, tie_epsilon: float) -> pd.Series:
    values = gaps.astype(float).to_numpy()
    labels = np.where(
        values > tie_epsilon,
        "ours_win",
        np.where(values < -tie_epsilon, "ours_loss", "tie"),
    )
    return pd.Series(labels, index=gaps.index, dtype="object")


def crossed_block_bootstrap_ci(
    frame: pd.DataFrame,
    *,
    reps: int,
    seed: int,
) -> tuple[float, float]:
    """Bootstrap the mean gap over score-seed and scenario blocks."""
    if frame.empty:
        raise ValueError("Cannot bootstrap an empty frame")
    block = frame.copy()
    block["_scenario_block"] = block[SCENARIO_COLS].astype(str).agg("|".join, axis=1)
    seed_codes, seed_values = pd.factorize(block["score_seed"], sort=True)
    scenario_codes, scenario_values = pd.factorize(
        block["_scenario_block"], sort=True
    )
    values = block["score_gap"].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Crossed bootstrap received a non-finite score gap")

    rng = np.random.default_rng(seed)
    samples: list[np.ndarray] = []
    collected = 0
    chunk_size = min(2048, reps)
    while collected < reps:
        current = min(chunk_size, reps - collected)
        seed_draws = rng.integers(
            0, len(seed_values), size=(current, len(seed_values))
        )
        scenario_draws = rng.integers(
            0, len(scenario_values), size=(current, len(scenario_values))
        )
        seed_weights = np.zeros((current, len(seed_values)), dtype=np.int16)
        scenario_weights = np.zeros(
            (current, len(scenario_values)), dtype=np.int16
        )
        batch_rows = np.arange(current)
        for draw_index in range(seed_draws.shape[1]):
            seed_weights[batch_rows, seed_draws[:, draw_index]] += 1
        for draw_index in range(scenario_draws.shape[1]):
            scenario_weights[batch_rows, scenario_draws[:, draw_index]] += 1
        task_weights = (
            seed_weights[:, seed_codes] * scenario_weights[:, scenario_codes]
        )
        denominators = task_weights.sum(axis=1)
        valid = denominators > 0
        if bool(valid.any()):
            batch_samples = (task_weights[valid] @ values) / denominators[valid]
            samples.append(batch_samples)
            collected += int(valid.sum())
    sample_values = np.concatenate(samples)[:reps]
    low, high = np.quantile(sample_values, [0.025, 0.975])
    return float(low), float(high)


def _stable_bootstrap_seed(base_seed: int, label: str) -> int:
    offset = int(hashlib.sha256(label.encode("utf-8")).hexdigest()[:8], 16)
    return int((base_seed + offset) % (2**32 - 1))


def _python_scalar(value: Any) -> Any:
    return value.item() if isinstance(value, np.generic) else value


def summarize_subset(
    frame: pd.DataFrame,
    *,
    group_dimension: str,
    group_values: dict[str, Any],
    tie_epsilon: float,
    bootstrap_reps: int,
    bootstrap_seed: int,
) -> dict[str, Any]:
    gaps = frame["score_gap"].astype(float)
    outcomes = classify_outcomes(gaps, tie_epsilon)
    losses = gaps[gaps < -tie_epsilon]
    worst_count = max(1, math.ceil(len(gaps) * 0.10))
    label = json.dumps(
        {"group_dimension": group_dimension, **group_values},
        ensure_ascii=False,
        sort_keys=True,
    )
    ci_low, ci_high = crossed_block_bootstrap_ci(
        frame,
        reps=bootstrap_reps,
        seed=_stable_bootstrap_seed(bootstrap_seed, label),
    )
    summary: dict[str, Any] = {
        "group_dimension": group_dimension,
        **group_values,
        "task_count": int(len(frame)),
        "mean_gap": float(gaps.mean()),
        "median_gap": float(gaps.median()),
        "q1_gap": float(gaps.quantile(0.25)),
        "q3_gap": float(gaps.quantile(0.75)),
        "min_gap": float(gaps.min()),
        "max_gap": float(gaps.max()),
        "bootstrap_ci95_low": ci_low,
        "bootstrap_ci95_high": ci_high,
        "ours_wins": int((outcomes == "ours_win").sum()),
        "ties": int((outcomes == "tie").sum()),
        "ours_losses": int((outcomes == "ours_loss").sum()),
        "ours_win_rate": float((outcomes == "ours_win").mean()),
        "ours_loss_rate": float((outcomes == "ours_loss").mean()),
        "conditional_loss_magnitude_mean": (
            float((-losses).mean()) if not losses.empty else 0.0
        ),
        "conditional_loss_magnitude_median": (
            float((-losses).median()) if not losses.empty else 0.0
        ),
        "worst_decile_task_count": worst_count,
        "worst_decile_mean_gap": float(gaps.nsmallest(worst_count).mean()),
        "nsga_failure_rows": int(frame["nsga_failure_count"].sum()),
        "tasks_with_nsga_failure": int(frame["nsga_any_failure"].sum()),
        "tasks_with_all_nsga_runs_failed": int(frame["nsga_all_failed"].sum()),
    }
    return summary


def build_group_summaries(
    task: pd.DataFrame,
    *,
    tie_epsilon: float,
    bootstrap_reps: int,
    bootstrap_seed: int,
) -> dict[str, list[dict[str, Any]]]:
    definitions: list[tuple[str, list[str]]] = [
        ("budget", ["budget_minutes"]),
        ("origin", ["origin_name"]),
        ("departure", ["depart_time"]),
        ("origin_budget", ["origin_name", "budget_minutes"]),
        ("score_seed", ["score_seed"]),
    ]
    outputs: dict[str, list[dict[str, Any]]] = {}
    for dimension, columns in definitions:
        rows: list[dict[str, Any]] = []
        grouper: str | list[str] = columns[0] if len(columns) == 1 else columns
        for key, subset in task.groupby(grouper, sort=True):
            values = key if isinstance(key, tuple) else (key,)
            group_values = {
                column: _python_scalar(value)
                for column, value in zip(columns, values, strict=True)
            }
            rows.append(
                summarize_subset(
                    subset,
                    group_dimension=dimension,
                    group_values=group_values,
                    tie_epsilon=tie_epsilon,
                    bootstrap_reps=bootstrap_reps,
                    bootstrap_seed=bootstrap_seed,
                )
            )
        outputs[dimension] = rows
    return outputs


def paired_wilcoxon(gaps: Iterable[float], tie_epsilon: float) -> dict[str, Any]:
    values = np.asarray(list(gaps), dtype=float)
    nonzero = values[np.abs(values) > tie_epsilon]
    if nonzero.size == 0:
        return {
            "nonzero_pairs": 0,
            "statistic": 0.0,
            "p_value_two_sided": 1.0,
            "rank_biserial": 0.0,
        }
    statistic, p_value = wilcoxon(nonzero, alternative="two-sided", zero_method="wilcox")
    ranks = rankdata(np.abs(nonzero), method="average")
    positive = float(ranks[nonzero > 0].sum())
    negative = float(ranks[nonzero < 0].sum())
    rank_biserial = (positive - negative) / (positive + negative)
    return {
        "nonzero_pairs": int(nonzero.size),
        "statistic": float(statistic),
        "p_value_two_sided": float(p_value),
        "rank_biserial": float(rank_biserial),
        "role": "auxiliary_only; effect sizes and blocked bootstrap CI are primary",
    }


def failure_mode_table(
    task: pd.DataFrame, *, tie_epsilon: float
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for failure_count, subset in task.groupby("nsga_failure_count", sort=True):
        outcomes = classify_outcomes(subset["score_gap"], tie_epsilon)
        rows.append(
            {
                "nsga_failure_count": int(failure_count),
                "task_count": int(len(subset)),
                "task_share": float(len(subset) / len(task)),
                "mean_gap": float(subset["score_gap"].mean()),
                "median_gap": float(subset["score_gap"].median()),
                "ours_wins": int((outcomes == "ours_win").sum()),
                "ties": int((outcomes == "tie").sum()),
                "ours_losses": int((outcomes == "ours_loss").sum()),
            }
        )
    return pd.DataFrame(rows)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.where(pd.notna(frame), None)
    return clean.to_dict(orient="records")


def plot_origin_budget_heatmap(
    origin_budget: pd.DataFrame,
    *,
    origin_order: list[str],
    budget_order: list[int],
    png_path: Path,
    pdf_path: Path,
) -> None:
    sns.set_theme(style="white", context="paper", font_scale=1.05)
    plot_frame = origin_budget.copy()
    matrix = plot_frame.pivot(
        index="origin_name", columns="budget_minutes", values="mean_gap"
    )
    matrix = matrix.reindex(index=origin_order, columns=budget_order)
    matrix.columns = [f"{int(value) // 60} h" for value in matrix.columns]
    limit = float(np.nanmax(np.abs(matrix.to_numpy(dtype=float))))
    fig, ax = plt.subplots(figsize=(7.3, 4.7))
    sns.heatmap(
        matrix,
        cmap="RdBu_r",
        center=0.0,
        vmin=-limit,
        vmax=limit,
        annot=True,
        fmt=".1f",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Mean Stop Score gap (Ours − NSGA-II)"},
        ax=ax,
    )
    ax.set_xlabel("Time budget")
    ax.set_ylabel("Origin")
    ax.tick_params(axis="y", rotation=0)
    fig.tight_layout()
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)


def markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    selected = frame[columns].copy()
    for column in selected.columns:
        if pd.api.types.is_float_dtype(selected[column]):
            selected[column] = selected[column].round(3)
    return selected.to_markdown(index=False)


def write_markdown_report(
    *,
    path: Path,
    source_path: Path,
    overall: dict[str, Any],
    reliability_sensitivity: pd.DataFrame,
    wilcoxon_result: dict[str, Any],
    summaries: dict[str, pd.DataFrame],
    failures: pd.DataFrame,
    worst_losses: pd.DataFrame,
    task: pd.DataFrame,
    bootstrap_reps: int,
    bootstrap_seed: int,
) -> None:
    nsga_failure_rows = int(task["nsga_failure_count"].sum())
    lines = [
        "# Canonical Ours vs NSGA-II underperformance analysis",
        "",
        f"- Source: `{display_path(source_path)}`",
        "- Paired unit: `(origin, departure, budget, reward seed)`.",
        "- NSGA-II aggregation: arithmetic mean over five algorithm seeds; algorithm failures retain score 0.",
        f"- Uncertainty: {bootstrap_reps:,}-rep crossed block bootstrap over reward seeds and origin-departure scenarios (seed {bootstrap_seed}).",
        "- Tie rule: exact equality within the configured numerical epsilon.",
        "",
        "## Overall result",
        "",
        f"Ours leads by **{overall['mean_gap']:.3f} Stop Score** on average "
        f"(blocked-bootstrap 95% CI **[{overall['bootstrap_ci95_low']:.3f}, "
        f"{overall['bootstrap_ci95_high']:.3f}]**), with "
        f"**{overall['ours_wins']} wins / {overall['ties']} ties / "
        f"{overall['ours_losses']} losses** across {overall['task_count']} paired tasks.",
        f"When Ours loses, the conditional mean loss magnitude is "
        f"**{overall['conditional_loss_magnitude_mean']:.3f}**. The mean gap in "
        f"the worst 10% of tasks is **{overall['worst_decile_mean_gap']:.3f}**.",
        "",
        f"NSGA-II has **{nsga_failure_rows}/3000** algorithm-seed failures across "
        f"**{int(task['nsga_any_failure'].sum())}/600** paired tasks; these failures "
        "are recorded as `effective_budget_exceeded` and scored as zero under the "
        "pre-registered all-task policy.",
        "",
        "The auxiliary paired Wilcoxon test gives "
        f"`p={wilcoxon_result['p_value_two_sided']:.6g}` and paired rank-biserial "
        f"`r={wilcoxon_result['rank_biserial']:.3f}`. This test is secondary to "
        "the effect size and blocked-bootstrap interval.",
        "",
        "## Reliability sensitivity",
        "",
        "The primary all-task estimand keeps algorithm failures at score 0 because "
        "returning a budget-feasible route is part of algorithm performance. Two "
        "secondary estimands show how much the quality conclusion depends on this "
        "failure policy:",
        "",
        markdown_table(
            reliability_sensitivity,
            [
                "estimand",
                "task_count",
                "mean_gap",
                "bootstrap_ci95_low",
                "bootstrap_ci95_high",
                "ours_wins",
                "ties",
                "ours_losses",
            ],
        ),
        "",
        "## By budget",
        "",
        markdown_table(
            summaries["budget"],
            [
                "budget_minutes",
                "task_count",
                "mean_gap",
                "bootstrap_ci95_low",
                "bootstrap_ci95_high",
                "ours_wins",
                "ties",
                "ours_losses",
                "conditional_loss_magnitude_mean",
            ],
        ),
        "",
        "## By origin",
        "",
        markdown_table(
            summaries["origin"],
            [
                "origin_name",
                "task_count",
                "mean_gap",
                "bootstrap_ci95_low",
                "bootstrap_ci95_high",
                "ours_wins",
                "ties",
                "ours_losses",
            ],
        ),
        "",
        "## By departure",
        "",
        markdown_table(
            summaries["departure"],
            [
                "depart_time",
                "task_count",
                "mean_gap",
                "bootstrap_ci95_low",
                "bootstrap_ci95_high",
                "ours_wins",
                "ties",
                "ours_losses",
            ],
        ),
        "",
        "## Origin × budget",
        "",
        markdown_table(
            summaries["origin_budget"],
            [
                "origin_name",
                "budget_minutes",
                "mean_gap",
                "ours_wins",
                "ties",
                "ours_losses",
            ],
        ),
        "",
        "## Reliability by NSGA-II failure count",
        "",
        markdown_table(
            failures,
            [
                "nsga_failure_count",
                "task_count",
                "task_share",
                "mean_gap",
                "ours_wins",
                "ties",
                "ours_losses",
            ],
        ),
        "",
        "## Largest Ours losses",
        "",
        markdown_table(
            worst_losses,
            [
                "origin_name",
                "departure_label",
                "budget_minutes",
                "score_seed",
                "ours_score",
                "nsga_score",
                "score_gap",
                "nsga_failure_count",
            ],
        ),
        "",
        "Interpretation must remain conditional: the data identify where losses "
        "occur, but do not by themselves prove a causal search-mechanism explanation.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze canonical Ours-vs-NSGA-II underperformance"
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--source-manifest", type=Path, default=None,
                        help="Optional original manifest; an explicit missing path is an error.")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--figures-dir", type=Path, default=DEFAULT_FIGURES_DIR)
    parser.add_argument("--suffix", default="20260723")
    parser.add_argument("--bootstrap-reps", type=int, default=20_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260723)
    parser.add_argument("--tie-epsilon", type=float, default=1e-9)
    args = parser.parse_args()

    result_path = args.input.resolve()
    manifest_path = (args.source_manifest or DEFAULT_MANIFEST).resolve()
    if args.source_manifest is not None and not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    if not manifest_path.is_file():
        print("INFO original source manifest unavailable; provenance gates will be null")
    results_dir = args.results_dir.resolve()
    figures_dir = args.figures_dir.resolve()
    if args.bootstrap_reps < 1000:
        raise ValueError("--bootstrap-reps must be at least 1000 for a formal analysis")
    if not result_path.is_file():
        raise FileNotFoundError(result_path)
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    metadata, run_frame = load_result_frame(result_path)
    task = build_task_frame(run_frame)
    task["outcome"] = classify_outcomes(task["score_gap"], args.tie_epsilon)

    overall = summarize_subset(
        task,
        group_dimension="overall",
        group_values={},
        tie_epsilon=args.tie_epsilon,
        bootstrap_reps=args.bootstrap_reps,
        bootstrap_seed=args.bootstrap_seed,
    )
    grouped = build_group_summaries(
        task,
        tie_epsilon=args.tie_epsilon,
        bootstrap_reps=args.bootstrap_reps,
        bootstrap_seed=args.bootstrap_seed,
    )
    summary_frames = {key: pd.DataFrame(value) for key, value in grouped.items()}
    failures = failure_mode_table(task, tie_epsilon=args.tie_epsilon)
    worst_losses = task.nsmallest(20, "score_gap").copy()
    wilcoxon_result = paired_wilcoxon(task["score_gap"], args.tie_epsilon)

    complete_case = task[task["nsga_failure_count"] == 0].copy()
    complete_case_summary = summarize_subset(
        complete_case,
        group_dimension="reliability_sensitivity",
        group_values={"estimand": "all_five_nsga_runs_feasible"},
        tie_epsilon=args.tie_epsilon,
        bootstrap_reps=args.bootstrap_reps,
        bootstrap_seed=args.bootstrap_seed,
    )
    feasible_seed_only = task[task["nsga_feasible_runs"] > 0].copy()
    feasible_seed_only["score_gap"] = feasible_seed_only[
        "score_gap_feasible_only"
    ]
    feasible_seed_only_summary = summarize_subset(
        feasible_seed_only,
        group_dimension="reliability_sensitivity",
        group_values={"estimand": "mean_over_feasible_nsga_runs_only"},
        tie_epsilon=args.tie_epsilon,
        bootstrap_reps=args.bootstrap_reps,
        bootstrap_seed=args.bootstrap_seed,
    )
    reliability_sensitivity = pd.DataFrame(
        [complete_case_summary, feasible_seed_only_summary]
    )
    combined_summary = pd.concat(
        [
            pd.DataFrame([overall]),
            *summary_frames.values(),
            reliability_sensitivity,
        ],
        ignore_index=True,
        sort=False,
    )

    suffix = "".join(
        char if char.isalnum() or char in {"-", "_"} else "_"
        for char in str(args.suffix)
    )
    task_csv = results_dir / f"underperformance_task_level_{suffix}.csv"
    summary_csv = results_dir / f"underperformance_summary_{suffix}.csv"
    origin_budget_csv = results_dir / f"underperformance_origin_budget_{suffix}.csv"
    failure_csv = results_dir / f"underperformance_failure_modes_{suffix}.csv"
    report_json = results_dir / f"underperformance_analysis_{suffix}.json"
    report_md = results_dir / f"underperformance_analysis_{suffix}.md"
    heatmap_png = figures_dir / f"underperformance_heatmap_{suffix}.png"
    heatmap_pdf = figures_dir / f"underperformance_heatmap_{suffix}.pdf"

    task.to_csv(task_csv, index=False, encoding="utf-8", lineterminator="\n")
    combined_summary.to_csv(
        summary_csv, index=False, encoding="utf-8", lineterminator="\n"
    )
    summary_frames["origin_budget"].to_csv(
        origin_budget_csv, index=False, encoding="utf-8", lineterminator="\n"
    )
    failures.to_csv(failure_csv, index=False, encoding="utf-8", lineterminator="\n")

    origin_order = [str(value) for value in metadata.get("origins", [])]
    budget_order = [int(value) for value in metadata.get("budgets", [])]
    plot_origin_budget_heatmap(
        summary_frames["origin_budget"],
        origin_order=origin_order,
        budget_order=budget_order,
        png_path=heatmap_png,
        pdf_path=heatmap_pdf,
    )
    write_markdown_report(
        path=report_md,
        source_path=result_path,
        overall=overall,
        reliability_sensitivity=reliability_sensitivity,
        wilcoxon_result=wilcoxon_result,
        summaries=summary_frames,
        failures=failures,
        worst_losses=worst_losses,
        task=task,
        bootstrap_reps=args.bootstrap_reps,
        bootstrap_seed=args.bootstrap_seed,
    )

    source_manifest = (json.loads(manifest_path.read_text(encoding="utf-8"))
                       if manifest_path.is_file() else {})
    artifacts = [
        task_csv,
        summary_csv,
        origin_budget_csv,
        failure_csv,
        report_md,
        heatmap_png,
        heatmap_pdf,
    ]
    payload = {
        "schema_version": "reraptor-underperformance-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "result_path": display_path(result_path),
            "result_sha256": sha256_file(result_path),
            "manifest_path": display_path(manifest_path) if manifest_path.is_file() else None,
            "manifest_sha256": sha256_file(manifest_path) if manifest_path.is_file() else None,
            "canonical_result_commit": source_manifest.get("git", {}).get("commit"),
            "source_integrity_gate_passed": source_manifest.get(
                "integrity_gate_passed"
            ),
            "source_canonical_gate_passed": source_manifest.get(
                "canonical_gate_passed"
            ),
            "analysis_script": display_path(Path(__file__)),
            "analysis_script_sha256": sha256_file(Path(__file__)),
        },
        "analysis_policy": {
            "paired_unit": TASK_KEY,
            "nsga_algorithm_seed_aggregation": "arithmetic mean over seeds 0..4",
            "failure_policy": "algorithm failures retain stop score 0",
            "sensitivity_estimands": {
                "complete_case": "tasks where all five NSGA-II runs are feasible",
                "feasible_seed_only": "within-task NSGA-II mean excludes failed runs; all-failed tasks excluded",
            },
            "tie_epsilon": args.tie_epsilon,
            "bootstrap": {
                "method": "crossed block bootstrap over score_seed and origin-departure scenario",
                "repetitions": args.bootstrap_reps,
                "seed": args.bootstrap_seed,
                "budgets": "fixed repeated design points within scenario blocks",
            },
        },
        "invariants": {
            "paired_tasks": int(len(task)),
            "score_seed_count": int(task["score_seed"].nunique()),
            "origin_count": int(task["origin_name"].nunique()),
            "departure_count": int(task["depart_time"].nunique()),
            "budget_count": int(task["budget_minutes"].nunique()),
            "ours_algorithm_failures": int(task["ours_algorithm_failure"].sum()),
            "nsga_algorithm_seed_failures": int(task["nsga_failure_count"].sum()),
            "tasks_with_nsga_failure": int(task["nsga_any_failure"].sum()),
            "tasks_with_all_nsga_runs_failed": int(task["nsga_all_failed"].sum()),
        },
        "overall": overall,
        "reliability_sensitivity": _records(reliability_sensitivity),
        "wilcoxon_auxiliary": wilcoxon_result,
        "by_budget": _records(summary_frames["budget"]),
        "by_origin": _records(summary_frames["origin"]),
        "by_departure": _records(summary_frames["departure"]),
        "by_origin_budget": _records(summary_frames["origin_budget"]),
        "by_score_seed": _records(summary_frames["score_seed"]),
        "failure_modes": _records(failures),
        "largest_ours_losses": _records(worst_losses),
        "artifacts": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in artifacts
        ],
    }
    report_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"Paired tasks: {len(task)}")
    print(
        "Overall: "
        f"mean gap={overall['mean_gap']:.3f}, "
        f"95% CI=[{overall['bootstrap_ci95_low']:.3f}, "
        f"{overall['bootstrap_ci95_high']:.3f}], "
        f"W/T/L={overall['ours_wins']}/{overall['ties']}/{overall['ours_losses']}"
    )
    for path in [report_json, *artifacts]:
        print(f"Saved: {path}")


if __name__ == "__main__":
    main()
