#!/usr/bin/env python3
"""Interpret the canonical Ours-vs-NSGA-II Stop Score difference.

This analysis reports paired differences in score, scored-stop
count, and selected reward per scored stop.  For tasks where both algorithms
have a defined reward density, the exact symmetric identity

    n_o d_o - n_n d_n
      = (n_o - n_n)(d_o + d_n)/2 + (d_o - d_n)(n_o + n_n)/2

separates a stop-coverage association from a reward-density association
without claiming a causal mechanism.  All-five-failed NSGA-II tasks are
reported separately because their selected reward density is undefined.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from paper.experiments.exp1_algorithm_comparison.analyze_underperformance import (
    DEFAULT_MANIFEST,
    DEFAULT_RESULT,
    NSGA_NAME,
    OURS_NAME,
    PROJECT_ROOT,
    SCENARIO_COLS,
    TASK_KEY,
    _stable_bootstrap_seed,
    display_path,
    load_result_frame,
    sha256_file,
)


DEFAULT_RESULTS_DIR = PROJECT_ROOT / "paper" / "results" / "exp1_algorithm_comparison"
UNIFORM_REWARD_MIN = 1
UNIFORM_REWARD_MAX = 100
UNIFORM_EXPECTED_REWARD = (UNIFORM_REWARD_MIN + UNIFORM_REWARD_MAX) / 2


def build_interpretability_task_frame(run_frame: pd.DataFrame) -> pd.DataFrame:
    selected = run_frame[run_frame["algorithm"].isin([OURS_NAME, NSGA_NAME])].copy()
    selected["score_if_feasible"] = selected["stop_score_total"].where(
        selected["feasible"], np.nan
    )
    selected["stops_if_feasible"] = selected["scored_stop_count"].where(
        selected["feasible"], np.nan
    )
    ours = selected[selected["algorithm"] == OURS_NAME].copy()
    nsga = selected[selected["algorithm"] == NSGA_NAME].copy()

    ours_counts = ours.groupby(TASK_KEY, sort=False).size()
    nsga_counts = nsga.groupby(TASK_KEY, sort=False).size()
    if len(ours_counts) != 600 or not ours_counts.eq(1).all():
        raise ValueError("Expected 600 deterministic Ours task rows")
    if len(nsga_counts) != 600 or not nsga_counts.eq(5).all():
        raise ValueError("Expected five NSGA-II seed rows for each of 600 tasks")
    if set(ours_counts.index) != set(nsga_counts.index):
        raise ValueError("Ours and NSGA-II task keys do not match")

    ours_task = (
        ours.groupby(TASK_KEY, as_index=False, sort=False)
        .agg(
            ours_score=("stop_score_total", "first"),
            ours_scored_stops=("scored_stop_count", "first"),
            ours_failure=("algorithm_failure", "first"),
        )
    )
    nsga_task = (
        nsga.groupby(TASK_KEY, as_index=False, sort=False)
        .agg(
            nsga_score=("stop_score_total", "mean"),
            nsga_scored_stops=("scored_stop_count", "mean"),
            nsga_score_feasible_only=("score_if_feasible", "mean"),
            nsga_scored_stops_feasible_only=("stops_if_feasible", "mean"),
            nsga_failure_count=("algorithm_failure", "sum"),
            nsga_feasible_runs=("feasible", "sum"),
        )
    )
    task = ours_task.merge(nsga_task, on=TASK_KEY, how="inner", validate="one_to_one")
    if bool(task["ours_failure"].any()):
        raise ValueError("Canonical Ours unexpectedly contains failures")

    task["score_gap"] = task["ours_score"] - task["nsga_score"]
    task["scored_stop_gap"] = (
        task["ours_scored_stops"] - task["nsga_scored_stops"]
    )
    task["ours_reward_per_scored_stop"] = task["ours_score"] / task[
        "ours_scored_stops"
    ].replace(0, np.nan)
    task["nsga_reward_per_scored_stop"] = task["nsga_score"] / task[
        "nsga_scored_stops"
    ].replace(0, np.nan)
    task["reward_per_scored_stop_gap"] = (
        task["ours_reward_per_scored_stop"]
        - task["nsga_reward_per_scored_stop"]
    )

    task["score_gap_feasible_only"] = (
        task["ours_score"] - task["nsga_score_feasible_only"]
    )
    task["scored_stop_gap_feasible_only"] = (
        task["ours_scored_stops"] - task["nsga_scored_stops_feasible_only"]
    )
    task["nsga_reward_per_scored_stop_feasible_only"] = (
        task["nsga_score_feasible_only"]
        / task["nsga_scored_stops_feasible_only"].replace(0, np.nan)
    )
    task["reward_per_scored_stop_gap_feasible_only"] = (
        task["ours_reward_per_scored_stop"]
        - task["nsga_reward_per_scored_stop_feasible_only"]
    )

    density_defined = task["nsga_reward_per_scored_stop"].notna()
    task["coverage_association"] = np.nan
    task["density_association"] = np.nan
    task.loc[density_defined, "coverage_association"] = (
        task.loc[density_defined, "scored_stop_gap"]
        * (
            task.loc[density_defined, "ours_reward_per_scored_stop"]
            + task.loc[density_defined, "nsga_reward_per_scored_stop"]
        )
        / 2.0
    )
    task.loc[density_defined, "density_association"] = (
        task.loc[density_defined, "reward_per_scored_stop_gap"]
        * (
            task.loc[density_defined, "ours_scored_stops"]
            + task.loc[density_defined, "nsga_scored_stops"]
        )
        / 2.0
    )
    reconstructed = (
        task.loc[density_defined, "coverage_association"]
        + task.loc[density_defined, "density_association"]
    )
    if not np.allclose(
        reconstructed,
        task.loc[density_defined, "score_gap"],
        rtol=0.0,
        atol=1e-9,
    ):
        raise ValueError("Exact score decomposition identity failed")

    task["nsga_all_failed"] = task["nsga_failure_count"] == 5
    task["budget_hours"] = task["budget_minutes"] / 60.0
    task["departure_label"] = task["depart_time"].map(
        lambda value: f"{int(value) // 60:02d}:{int(value) % 60:02d}"
    )
    task["task_key"] = task[TASK_KEY].astype(str).agg("|".join, axis=1)
    return task.sort_values(TASK_KEY).reset_index(drop=True)


def _crossed_bootstrap_samples(
    frame: pd.DataFrame,
    *,
    value_columns: list[str],
    reps: int,
    seed: int,
) -> dict[str, np.ndarray]:
    selected = frame.dropna(subset=value_columns).copy()
    if selected.empty:
        raise ValueError("No finite rows available for bootstrap")
    selected["_scenario_block"] = selected[SCENARIO_COLS].astype(str).agg(
        "|".join, axis=1
    )
    seed_codes, seed_values = pd.factorize(selected["score_seed"], sort=True)
    scenario_codes, scenario_values = pd.factorize(
        selected["_scenario_block"], sort=True
    )
    values = selected[value_columns].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Bootstrap values must be finite")

    rng = np.random.default_rng(seed)
    output = {column: [] for column in value_columns}
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
        weights = seed_weights[:, seed_codes] * scenario_weights[:, scenario_codes]
        denominators = weights.sum(axis=1)
        valid = denominators > 0
        if not bool(valid.any()):
            continue
        means = (weights[valid] @ values) / denominators[valid, None]
        for index, column in enumerate(value_columns):
            output[column].append(means[:, index])
        collected += int(valid.sum())
    return {
        column: np.concatenate(chunks)[:reps]
        for column, chunks in output.items()
    }


def _metric_summary(
    frame: pd.DataFrame,
    *,
    metric: str,
    label: str,
    reps: int,
    seed: int,
) -> dict[str, Any]:
    values = frame[metric].dropna().astype(float)
    bootstrap = _crossed_bootstrap_samples(
        frame,
        value_columns=[metric],
        reps=reps,
        seed=seed,
    )[metric]
    low, high = np.quantile(bootstrap, [0.025, 0.975])
    return {
        "metric": label,
        "column": metric,
        "task_count": int(len(values)),
        "mean": float(values.mean()),
        "median": float(values.median()),
        "q1": float(values.quantile(0.25)),
        "q3": float(values.quantile(0.75)),
        "bootstrap_ci95_low": float(low),
        "bootstrap_ci95_high": float(high),
    }


def _estimand_summary(
    frame: pd.DataFrame,
    *,
    estimand: str,
    score_gap: str,
    stop_gap: str,
    density_gap: str,
    reps: int,
    seed: int,
) -> list[dict[str, Any]]:
    definitions = [
        (score_gap, "Stop Score gap"),
        (stop_gap, "Scored-stop-count gap"),
        (density_gap, "Selected reward per scored stop gap"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (column, label) in enumerate(definitions):
        summary = _metric_summary(
            frame,
            metric=column,
            label=label,
            reps=reps,
            seed=seed + index * 997,
        )
        summary["estimand"] = estimand
        rows.append(summary)
    return rows


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in frame.to_dict(orient="records"):
        records.append(
            {
                key: (
                    None
                    if isinstance(value, float) and not np.isfinite(value)
                    else value.item()
                    if isinstance(value, np.generic)
                    else value
                )
                for key, value in row.items()
            }
        )
    return records


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    selected = frame[columns].copy()
    for column in selected.columns:
        if pd.api.types.is_float_dtype(selected[column]):
            selected[column] = selected[column].round(3)
    return selected.to_markdown(index=False)


def write_markdown(
    *,
    path: Path,
    source: Path,
    headline: dict[str, Any],
    metrics: pd.DataFrame,
    decomposition: pd.DataFrame,
    all_failed: dict[str, Any],
    reps: int,
    seed: int,
) -> None:
    lines = [
        "# Canonical Stop Score interpretability analysis",
        "",
        f"- Source: `{display_path(source)}`",
        "- Paired unit: `(origin, departure, budget, reward seed)`.",
        f"- Uncertainty: {reps:,}-rep crossed block bootstrap (seed {seed}).",
        "",
        "## Headline translation",
        "",
        f"Ours averages **{headline['ours_mean_score']:.3f}** Stop Score versus "
        f"**{headline['nsga_mean_score']:.3f}** for NSGA-II under the all-task "
        f"failure policy. The difference is **{headline['mean_score_gap']:.3f}** "
        f"or **{headline['relative_improvement_percent']:.3f}%** of the NSGA-II "
        "mean.",
        "",
        f"Because rewards are drawn from discrete `U{{1,...,100}}` with expectation "
        f"{UNIFORM_EXPECTED_REWARD:.1f}, the mean score gap is numerically equivalent "
        f"to **{headline['equivalent_uniform_reward_stops']:.3f}** expected-reward "
        f"stops (95% CI **[{headline['equivalent_uniform_reward_stops_ci95_low']:.3f}, "
        f"{headline['equivalent_uniform_reward_stops_ci95_high']:.3f}]**). This is "
        "an experimental-unit translation, not a count of real attractions or a "
        "utility/monetary quantity.",
        "",
        "## Paired task metrics",
        "",
        _markdown_table(
            metrics,
            [
                "estimand",
                "metric",
                "task_count",
                "mean",
                "median",
                "bootstrap_ci95_low",
                "bootstrap_ci95_high",
            ],
        ),
        "",
        "## Exact symmetric decomposition",
        "",
        "For the 581 tasks where NSGA-II returns at least one feasible route, the "
        "identity `Δscore = coverage association + reward-density association` "
        "holds exactly at task level. The terms describe an association, not a "
        "causal attribution:",
        "",
        _markdown_table(
            decomposition,
            [
                "component",
                "task_count",
                "mean",
                "median",
                "bootstrap_ci95_low",
                "bootstrap_ci95_high",
            ],
        ),
        "",
        f"The remaining **{all_failed['task_count']}** tasks have all five NSGA-II "
        f"runs fail. Their NSGA-II reward density is undefined; their mean Ours "
        f"score, and hence mean all-task score gap, is "
        f"**{all_failed['mean_score_gap']:.3f}**. These tasks are reported as a "
        "reliability/no-feasible-return difference rather than forced into the "
        "coverage-density decomposition.",
        "",
        "## Interpretation boundary",
        "",
        "The primary all-task result is associated with more scored stops and a "
        "slightly lower selected reward per stop. However, the complete-case and "
        "feasible-seed-only score intervals cross zero. The paper should therefore "
        "distinguish overall performance (including reliability) from conditional "
        "solution quality and use `is associated with` rather than causal language.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interpret the canonical Ours-vs-NSGA-II Stop Score gap"
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--suffix", default="20260723")
    parser.add_argument("--bootstrap-reps", type=int, default=20_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260723)
    args = parser.parse_args()
    if args.bootstrap_reps < 1000:
        raise ValueError("--bootstrap-reps must be at least 1000")

    input_path = args.input.resolve()
    manifest_path = args.source_manifest.resolve()
    results_dir = args.results_dir.resolve()
    results_dir.mkdir(parents=True, exist_ok=True)
    metadata, run_frame = load_result_frame(input_path)
    task = build_interpretability_task_frame(run_frame)

    overall_bootstrap_seed = _stable_bootstrap_seed(
        args.bootstrap_seed,
        json.dumps(
            {"group_dimension": "overall"},
            ensure_ascii=False,
            sort_keys=True,
        ),
    )
    primary_metrics = _estimand_summary(
        task,
        estimand="all_task_failure_zero",
        score_gap="score_gap",
        stop_gap="scored_stop_gap",
        density_gap="reward_per_scored_stop_gap",
        reps=args.bootstrap_reps,
        seed=overall_bootstrap_seed,
    )
    complete_case = task[task["nsga_failure_count"] == 0].copy()
    complete_case_seed = _stable_bootstrap_seed(
        args.bootstrap_seed,
        json.dumps(
            {
                "estimand": "all_five_nsga_runs_feasible",
                "group_dimension": "reliability_sensitivity",
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
    )
    complete_metrics = _estimand_summary(
        complete_case,
        estimand="all_five_nsga_runs_feasible",
        score_gap="score_gap",
        stop_gap="scored_stop_gap",
        density_gap="reward_per_scored_stop_gap",
        reps=args.bootstrap_reps,
        seed=complete_case_seed,
    )
    feasible_seed_only = task[task["nsga_feasible_runs"] > 0].copy()
    feasible_seed_only_seed = _stable_bootstrap_seed(
        args.bootstrap_seed,
        json.dumps(
            {
                "estimand": "mean_over_feasible_nsga_runs_only",
                "group_dimension": "reliability_sensitivity",
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
    )
    feasible_metrics = _estimand_summary(
        feasible_seed_only,
        estimand="mean_over_feasible_nsga_runs_only",
        score_gap="score_gap_feasible_only",
        stop_gap="scored_stop_gap_feasible_only",
        density_gap="reward_per_scored_stop_gap_feasible_only",
        reps=args.bootstrap_reps,
        seed=feasible_seed_only_seed,
    )
    metrics = pd.DataFrame(primary_metrics + complete_metrics + feasible_metrics)

    decomposable = task[~task["nsga_all_failed"]].copy()
    decomposition_rows = []
    for index, (column, label) in enumerate(
        [
            ("score_gap", "Observed Stop Score gap"),
            ("coverage_association", "Scored-stop coverage association"),
            ("density_association", "Selected reward-density association"),
        ]
    ):
        summary = _metric_summary(
            decomposable,
            metric=column,
            label=label,
            reps=args.bootstrap_reps,
            seed=args.bootstrap_seed + 30_000 + index * 997,
        )
        summary["component"] = label
        decomposition_rows.append(summary)
    decomposition = pd.DataFrame(decomposition_rows)

    score_samples = _crossed_bootstrap_samples(
        task,
        value_columns=["ours_score", "nsga_score", "score_gap"],
        reps=args.bootstrap_reps,
        seed=overall_bootstrap_seed,
    )
    percent_samples = (
        100.0
        * score_samples["score_gap"]
        / np.maximum(score_samples["nsga_score"], 1e-12)
    )
    equivalent_samples = score_samples["score_gap"] / UNIFORM_EXPECTED_REWARD
    score_ci = np.quantile(score_samples["score_gap"], [0.025, 0.975])
    percent_ci = np.quantile(percent_samples, [0.025, 0.975])
    equivalent_ci = np.quantile(equivalent_samples, [0.025, 0.975])
    mean_ours = float(task["ours_score"].mean())
    mean_nsga = float(task["nsga_score"].mean())
    mean_gap = float(task["score_gap"].mean())
    headline = {
        "ours_mean_score": mean_ours,
        "nsga_mean_score": mean_nsga,
        "mean_score_gap": mean_gap,
        "mean_score_gap_ci95_low": float(score_ci[0]),
        "mean_score_gap_ci95_high": float(score_ci[1]),
        "relative_improvement_percent": float(100.0 * mean_gap / mean_nsga),
        "relative_improvement_ci95_low": float(percent_ci[0]),
        "relative_improvement_ci95_high": float(percent_ci[1]),
        "uniform_reward_min": UNIFORM_REWARD_MIN,
        "uniform_reward_max": UNIFORM_REWARD_MAX,
        "uniform_expected_reward": UNIFORM_EXPECTED_REWARD,
        "equivalent_uniform_reward_stops": float(
            mean_gap / UNIFORM_EXPECTED_REWARD
        ),
        "equivalent_uniform_reward_stops_ci95_low": float(equivalent_ci[0]),
        "equivalent_uniform_reward_stops_ci95_high": float(equivalent_ci[1]),
    }
    all_failed_frame = task[task["nsga_all_failed"]]
    all_failed = {
        "task_count": int(len(all_failed_frame)),
        "mean_score_gap": float(all_failed_frame["score_gap"].mean()),
        "mean_ours_score": float(all_failed_frame["ours_score"].mean()),
        "nsga_reward_density": None,
        "classification": "reliability/no-feasible-return difference",
    }

    suffix = "".join(
        char if char.isalnum() or char in {"-", "_"} else "_"
        for char in str(args.suffix)
    )
    task_csv = results_dir / f"score_interpretability_task_level_{suffix}.csv"
    summary_csv = results_dir / f"score_interpretability_summary_{suffix}.csv"
    report_md = results_dir / f"score_interpretability_analysis_{suffix}.md"
    report_json = results_dir / f"score_interpretability_analysis_{suffix}.json"
    task.to_csv(task_csv, index=False, encoding="utf-8", lineterminator="\n")
    pd.concat(
        [
            metrics,
            decomposition.assign(estimand="decomposable_tasks"),
        ],
        ignore_index=True,
        sort=False,
    ).to_csv(summary_csv, index=False, encoding="utf-8", lineterminator="\n")
    write_markdown(
        path=report_md,
        source=input_path,
        headline=headline,
        metrics=metrics,
        decomposition=decomposition,
        all_failed=all_failed,
        reps=args.bootstrap_reps,
        seed=args.bootstrap_seed,
    )

    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = [task_csv, summary_csv, report_md]
    payload = {
        "schema_version": "reraptor-score-interpretability-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "result_path": display_path(input_path),
            "result_sha256": sha256_file(input_path),
            "manifest_path": display_path(manifest_path),
            "manifest_sha256": sha256_file(manifest_path),
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
            "primary_estimand": "all-task; NSGA-II failures retain zero score and zero stops",
            "density_definition": "ratio of task-level aggregate score to aggregate scored-stop count",
            "decomposition": "exact symmetric two-factor identity on tasks with defined densities",
            "bootstrap": {
                "method": "crossed block bootstrap over score_seed and origin-departure scenario",
                "repetitions": args.bootstrap_reps,
                "seed": args.bootstrap_seed,
            },
            "language_boundary": "association, not causal attribution",
        },
        "invariants": {
            "paired_tasks": int(len(task)),
            "decomposable_tasks": int(len(decomposable)),
            "all_five_nsga_runs_failed_tasks": int(task["nsga_all_failed"].sum()),
            "decomposition_max_abs_error": float(
                np.max(
                    np.abs(
                        decomposable["score_gap"]
                        - decomposable["coverage_association"]
                        - decomposable["density_association"]
                    )
                )
            ),
            "score_seed_count": int(task["score_seed"].nunique()),
            "origin_count": int(task["origin_name"].nunique()),
            "departure_count": int(task["depart_time"].nunique()),
            "budget_count": int(task["budget_minutes"].nunique()),
        },
        "headline": headline,
        "paired_metric_summaries": _records(metrics),
        "decomposition": _records(decomposition),
        "all_nsga_runs_failed": all_failed,
        "artifacts": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in artifacts
        ],
        "metadata_snapshot": {
            "score_seeds": metadata.get("score_seeds"),
            "stop_score_min": metadata.get("stop_score_min"),
            "stop_score_max": metadata.get("stop_score_max"),
            "scoring_semantics": metadata.get("scoring_semantics"),
        },
    }
    report_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"Score gap: {mean_gap:.3f} ({headline['relative_improvement_percent']:.3f}%), "
        f"equivalent uniform-reward stops: "
        f"{headline['equivalent_uniform_reward_stops']:.3f}"
    )
    for path in [report_json, *artifacts]:
        print(f"Saved: {path}")


if __name__ == "__main__":
    main()
