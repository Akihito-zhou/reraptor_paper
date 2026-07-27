#!/usr/bin/env python3
"""Analyze the canonical Experiment 3 hyperparameter sensitivity panels.

All OAT comparisons are paired to the dedicated default shard on the exact
600-task grid. Confidence intervals use the same crossed block bootstrap
structure as the canonical Experiment 1 analyses: reward seeds and
origin-departure scenarios are resampled, while budgets remain repeated design
points within each sampled block.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESULT_DIR = PROJECT_ROOT / "paper" / "results" / "exp3_parameter_sensitivity"
DEFAULT_OAT = RESULT_DIR / "sensitivity_results_canonical_oat_18config_20260727.json"
DEFAULT_INTERACTION = (
    RESULT_DIR / "sensitivity_results_canonical_interaction_4corner_20260727.json"
)
TASK_KEY = ["origin_name", "depart_time", "budget_minutes", "seed", "score_seed"]
SCENARIO_COLS = ["origin_name", "depart_time"]
DATE_TAG = "20260727"


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


def load_panel(path: Path, *, panel: str, configs: int, rows: int) -> tuple[dict, pd.DataFrame]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    metadata = payload.get("metadata")
    raw = payload.get("results")
    if not isinstance(metadata, dict) or not isinstance(raw, list):
        raise ValueError(f"Invalid canonical payload: {path}")
    if metadata.get("experiment") != "exp3_hyperparameter_sensitivity":
        raise ValueError(f"Wrong experiment in {path}")
    if metadata.get("panel") != panel:
        raise ValueError(f"Expected panel {panel!r} in {path}")
    if int(metadata.get("sensitivity_config_count", -1)) != configs:
        raise ValueError(f"Expected {configs} configurations in {path}")
    if int(metadata.get("num_results", -1)) != rows or len(raw) != rows:
        raise ValueError(f"Expected {rows} rows in {path}")

    frame = pd.DataFrame(raw)
    required = {
        *TASK_KEY,
        "sensitivity_config_id",
        "sensitivity_factor",
        "sensitivity_factor_value",
        "sensitivity_parameters",
        "stop_score_total",
        "elapsed_ms",
        "labels",
        "resource_cap_hit",
        "candidate_trim_events",
        "beam_trim_events",
        "termination_reason",
    }
    missing = sorted(required - set(frame))
    if missing:
        raise ValueError(f"Missing columns in {path}: {missing}")
    for column in (
        "depart_time",
        "budget_minutes",
        "seed",
        "score_seed",
        "stop_score_total",
        "elapsed_ms",
        "labels",
        "candidate_trim_events",
        "beam_trim_events",
    ):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame["resource_cap_hit"] = frame["resource_cap_hit"].astype(bool)
    frame["origin_name"] = frame["origin_name"].astype(str)
    frame["sensitivity_config_id"] = frame["sensitivity_config_id"].astype(str)
    if frame.duplicated(["sensitivity_config_id", *TASK_KEY]).any():
        raise ValueError(f"Duplicate sensitivity task keys in {path}")
    return metadata, frame


def _stable_seed(base_seed: int, label: str) -> int:
    offset = int(hashlib.sha256(label.encode("utf-8")).hexdigest()[:8], 16)
    return int((base_seed + offset) % (2**32 - 1))


def crossed_block_bootstrap_ci(
    frame: pd.DataFrame,
    *,
    value_column: str,
    reps: int,
    seed: int,
) -> tuple[float, float]:
    if frame.empty:
        raise ValueError("Cannot bootstrap an empty frame")
    block = frame.copy()
    block["_scenario"] = block[SCENARIO_COLS].astype(str).agg("|".join, axis=1)
    seed_codes, seed_levels = pd.factorize(block["score_seed"], sort=True)
    scenario_codes, scenario_levels = pd.factorize(block["_scenario"], sort=True)
    values = block[value_column].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Bootstrap values must be finite")

    rng = np.random.default_rng(seed)
    samples: list[np.ndarray] = []
    collected = 0
    while collected < reps:
        current = min(2048, reps - collected)
        seed_draws = rng.integers(
            0, len(seed_levels), size=(current, len(seed_levels))
        )
        scenario_draws = rng.integers(
            0, len(scenario_levels), size=(current, len(scenario_levels))
        )
        seed_weights = np.zeros((current, len(seed_levels)), dtype=np.int16)
        scenario_weights = np.zeros(
            (current, len(scenario_levels)), dtype=np.int16
        )
        rows = np.arange(current)
        for column in range(seed_draws.shape[1]):
            seed_weights[rows, seed_draws[:, column]] += 1
        for column in range(scenario_draws.shape[1]):
            scenario_weights[rows, scenario_draws[:, column]] += 1
        weights = seed_weights[:, seed_codes] * scenario_weights[:, scenario_codes]
        denominators = weights.sum(axis=1)
        valid = denominators > 0
        if valid.any():
            samples.append((weights[valid] @ values) / denominators[valid])
            collected += int(valid.sum())
    values_boot = np.concatenate(samples)[:reps]
    low, high = np.quantile(values_boot, [0.025, 0.975])
    return float(low), float(high)


def _config_snapshot(metadata: dict, config_id: str) -> dict[str, Any]:
    configurations = metadata.get("sensitivity_configurations") or {}
    snapshot = configurations.get(config_id)
    if not isinstance(snapshot, dict):
        raise ValueError(f"Missing configuration snapshot: {config_id}")
    return snapshot


def build_oat_analysis(
    metadata: dict,
    frame: pd.DataFrame,
    *,
    bootstrap_reps: int,
    bootstrap_seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    config_order = list(metadata["sensitivity_config_ids"])
    counts = frame.groupby("sensitivity_config_id").size()
    if set(counts.index) != set(config_order) or not counts.eq(600).all():
        raise ValueError(f"OAT panel requires 600 rows for all 18 configurations: {counts}")

    default = (
        frame[frame["sensitivity_config_id"] == "default"]
        .set_index(TASK_KEY)
        .sort_index()
    )
    if len(default) != 600:
        raise ValueError("Default sensitivity configuration must contain 600 rows")

    overall_rows: list[dict[str, Any]] = []
    paired_rows: list[dict[str, Any]] = []
    budget_rows: list[dict[str, Any]] = []

    for order, config_id in enumerate(config_order):
        config = (
            frame[frame["sensitivity_config_id"] == config_id]
            .set_index(TASK_KEY)
            .sort_index()
        )
        if not config.index.equals(default.index):
            raise ValueError(f"Paired task keys differ from default: {config_id}")
        snapshot = _config_snapshot(metadata, config_id)
        factor = str(config["sensitivity_factor"].iloc[0])
        factor_value = str(config["sensitivity_factor_value"].iloc[0])
        score_delta = config["stop_score_total"] - default["stop_score_total"]
        pair = config.reset_index()[TASK_KEY].copy()
        pair["score_delta"] = score_delta.to_numpy(dtype=float)
        low, high = crossed_block_bootstrap_ci(
            pair,
            value_column="score_delta",
            reps=bootstrap_reps,
            seed=_stable_seed(bootstrap_seed, f"oat:{config_id}"),
        )

        overall_rows.append(
            {
                "config_order": order,
                "config_id": config_id,
                "factor": factor,
                "factor_value": factor_value,
                "beam_width": snapshot["beam_width"],
                "candidate_cap_short": snapshot["candidate_cap_short"],
                "candidate_cap_long": snapshot["candidate_cap_long"],
                "reward_coefficient": snapshot["reward_coefficient"],
                "score_per_hour_coefficient": snapshot[
                    "score_per_hour_coefficient"
                ],
                "effective_time_coefficient": snapshot[
                    "effective_time_coefficient"
                ],
                "negative_penalty_scale": snapshot["negative_penalty_scale"],
                "task_count": len(config),
                "mean_stop_score": float(config["stop_score_total"].mean()),
                "mean_elapsed_ms": float(config["elapsed_ms"].mean()),
                "mean_labels": float(config["labels"].mean()),
                "resource_cap_rate": float(config["resource_cap_hit"].mean()),
                "candidate_trim_activation_rate": float(
                    (config["candidate_trim_events"] > 0).mean()
                ),
                "beam_trim_activation_rate": float(
                    (config["beam_trim_events"] > 0).mean()
                ),
                "mean_candidate_trim_events": float(
                    config["candidate_trim_events"].mean()
                ),
                "mean_beam_trim_events": float(config["beam_trim_events"].mean()),
            }
        )
        paired_rows.append(
            {
                "config_order": order,
                "config_id": config_id,
                "factor": factor,
                "factor_value": factor_value,
                "paired_tasks": len(config),
                "mean_score_delta_vs_default": float(score_delta.mean()),
                "bootstrap_ci95_low": low,
                "bootstrap_ci95_high": high,
                "wins_vs_default": int((score_delta > 0).sum()),
                "ties_vs_default": int((score_delta == 0).sum()),
                "losses_vs_default": int((score_delta < 0).sum()),
                "mean_runtime_ratio_vs_default": float(
                    config["elapsed_ms"].mean() / default["elapsed_ms"].mean()
                ),
                "mean_label_ratio_vs_default": float(
                    config["labels"].mean() / default["labels"].mean()
                ),
                "resource_cap_rate_difference": float(
                    config["resource_cap_hit"].mean()
                    - default["resource_cap_hit"].mean()
                ),
                "identical_score_tasks": int((score_delta == 0).sum()),
                "identical_label_count_tasks": int(
                    (config["labels"] == default["labels"]).sum()
                ),
                "identical_termination_tasks": int(
                    (config["termination_reason"] == default["termination_reason"]).sum()
                ),
            }
        )

        for budget, budget_config in config.groupby("budget_minutes", sort=True):
            budget_default = default[
                default.index.get_level_values("budget_minutes") == budget
            ]
            budget_delta = (
                budget_config["stop_score_total"]
                - budget_default["stop_score_total"]
            )
            budget_rows.append(
                {
                    "config_order": order,
                    "config_id": config_id,
                    "factor": factor,
                    "factor_value": factor_value,
                    "budget_minutes": int(budget),
                    "task_count": len(budget_config),
                    "mean_stop_score": float(budget_config["stop_score_total"].mean()),
                    "mean_score_delta_vs_default": float(budget_delta.mean()),
                    "mean_elapsed_ms": float(budget_config["elapsed_ms"].mean()),
                    "mean_labels": float(budget_config["labels"].mean()),
                    "resource_cap_rate": float(
                        budget_config["resource_cap_hit"].mean()
                    ),
                }
            )

    overall = pd.DataFrame(overall_rows).sort_values("config_order")
    paired = pd.DataFrame(paired_rows).sort_values("config_order")
    by_budget = pd.DataFrame(budget_rows).sort_values(
        ["config_order", "budget_minutes"]
    )
    return overall, paired, by_budget


def build_interaction_analysis(
    oat_metadata: dict,
    oat: pd.DataFrame,
    interaction_metadata: dict,
    interaction: pd.DataFrame,
) -> pd.DataFrame:
    origins = list(interaction_metadata["origins"])
    score_seeds = [int(value) for value in interaction_metadata["score_seeds"]]
    center_specs = {
        "cap15_10": (50, "15/10"),
        "w25": (25, "30/20"),
        "default": (50, "30/20"),
        "w100": (100, "30/20"),
        "cap60_40": (50, "60/40"),
    }
    panels: list[pd.DataFrame] = []
    for config_id, (width, cap_label) in center_specs.items():
        selected = oat[
            (oat["sensitivity_config_id"] == config_id)
            & oat["origin_name"].isin(origins)
            & oat["score_seed"].isin(score_seeds)
        ].copy()
        if len(selected) != 72:
            raise ValueError(f"Interaction center {config_id} requires 72 tasks")
        selected["interaction_beam_width"] = width
        selected["interaction_cap"] = cap_label
        selected["interaction_source"] = "OAT center line"
        panels.append(selected)

    for config_id, selected_source in interaction.groupby(
        "sensitivity_config_id", sort=False
    ):
        selected = selected_source.copy()
        snapshot = _config_snapshot(interaction_metadata, str(config_id))
        selected["interaction_beam_width"] = int(snapshot["beam_width"])
        selected["interaction_cap"] = (
            f"{snapshot['candidate_cap_short']}/{snapshot['candidate_cap_long']}"
        )
        selected["interaction_source"] = "confirmatory corner run"
        panels.append(selected)

    combined = pd.concat(panels, ignore_index=True)
    cell_counts = combined.groupby(
        ["interaction_beam_width", "interaction_cap"]
    ).size()
    if len(cell_counts) != 9 or not cell_counts.eq(72).all():
        raise ValueError(f"Interaction grid must contain nine 72-task cells: {cell_counts}")

    default = (
        combined[
            (combined["interaction_beam_width"] == 50)
            & (combined["interaction_cap"] == "30/20")
        ]
        .set_index(TASK_KEY)
        .sort_index()
    )
    rows: list[dict[str, Any]] = []
    cap_order = {"15/10": 0, "30/20": 1, "60/40": 2}
    for (width, cap_label), cell_source in combined.groupby(
        ["interaction_beam_width", "interaction_cap"], sort=False
    ):
        cell = cell_source.set_index(TASK_KEY).sort_index()
        if not cell.index.equals(default.index):
            raise ValueError(f"Interaction task keys differ at W={width}, cap={cap_label}")
        delta = cell["stop_score_total"] - default["stop_score_total"]
        rows.append(
            {
                "beam_width": int(width),
                "candidate_cap": cap_label,
                "candidate_cap_order": cap_order[cap_label],
                "source": str(cell["interaction_source"].iloc[0]),
                "task_count": len(cell),
                "mean_stop_score": float(cell["stop_score_total"].mean()),
                "mean_score_delta_vs_default_subset": float(delta.mean()),
                "wins_vs_default_subset": int((delta > 0).sum()),
                "ties_vs_default_subset": int((delta == 0).sum()),
                "losses_vs_default_subset": int((delta < 0).sum()),
                "mean_elapsed_ms": float(cell["elapsed_ms"].mean()),
                "mean_labels": float(cell["labels"].mean()),
                "resource_cap_rate": float(cell["resource_cap_hit"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["candidate_cap_order", "beam_width"])


def write_outputs(
    *,
    oat_path: Path,
    interaction_path: Path,
    overall: pd.DataFrame,
    paired: pd.DataFrame,
    by_budget: pd.DataFrame,
    interaction: pd.DataFrame,
    bootstrap_reps: int,
    bootstrap_seed: int,
) -> None:
    paths = {
        "overall": RESULT_DIR / f"sensitivity_canonical_summary_{DATE_TAG}.csv",
        "paired": RESULT_DIR / f"sensitivity_canonical_paired_vs_default_{DATE_TAG}.csv",
        "by_budget": RESULT_DIR / f"sensitivity_canonical_by_budget_{DATE_TAG}.csv",
        "interaction": RESULT_DIR / f"sensitivity_canonical_interaction_{DATE_TAG}.csv",
    }
    for name, frame in (
        ("overall", overall),
        ("paired", paired),
        ("by_budget", by_budget),
        ("interaction", interaction),
    ):
        frame.to_csv(paths[name], index=False, float_format="%.10g")

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": [
            {
                "path": display_path(oat_path),
                "sha256": sha256_file(oat_path),
            },
            {
                "path": display_path(interaction_path),
                "sha256": sha256_file(interaction_path),
            },
        ],
        "analysis_protocol": {
            "oat_pairing": "exact origin-departure-budget-seed-score_seed task key",
            "default_config_id": "default",
            "bootstrap": {
                "method": (
                    "crossed block bootstrap over score_seed and "
                    "origin-departure scenario; budgets retained as repeated "
                    "design points"
                ),
                "repetitions": bootstrap_reps,
                "seed": bootstrap_seed,
            },
            "runtime_interpretation": (
                "descriptive only because configurations ran sequentially; "
                "quality and search-resource metrics are the primary "
                "sensitivity evidence"
            ),
            "interaction_subset": (
                "3 origins x 3 departures x 4 budgets x 2 reward seeds; "
                "five center-line cells filtered from OAT and four corners "
                "run separately"
            ),
        },
        "overall": overall.to_dict(orient="records"),
        "paired_vs_default": paired.to_dict(orient="records"),
        "by_budget": by_budget.to_dict(orient="records"),
        "interaction": interaction.to_dict(orient="records"),
        "csv_outputs": {name: display_path(path) for name, path in paths.items()},
    }
    output = RESULT_DIR / f"sensitivity_canonical_analysis_{DATE_TAG}.json"
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze canonical sensitivity results")
    parser.add_argument("--oat", type=Path, default=DEFAULT_OAT)
    parser.add_argument("--interaction", type=Path, default=DEFAULT_INTERACTION)
    parser.add_argument("--bootstrap-reps", type=int, default=20_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260727)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.bootstrap_reps < 1000:
        raise ValueError("--bootstrap-reps must be at least 1000")
    oat_path = args.oat.resolve()
    interaction_path = args.interaction.resolve()
    oat_metadata, oat = load_panel(oat_path, panel="oat", configs=18, rows=10_800)
    interaction_metadata, interaction = load_panel(
        interaction_path,
        panel="interaction",
        configs=4,
        rows=288,
    )
    overall, paired, by_budget = build_oat_analysis(
        oat_metadata,
        oat,
        bootstrap_reps=args.bootstrap_reps,
        bootstrap_seed=args.bootstrap_seed,
    )
    interaction_summary = build_interaction_analysis(
        oat_metadata,
        oat,
        interaction_metadata,
        interaction,
    )
    write_outputs(
        oat_path=oat_path,
        interaction_path=interaction_path,
        overall=overall,
        paired=paired,
        by_budget=by_budget,
        interaction=interaction_summary,
        bootstrap_reps=args.bootstrap_reps,
        bootstrap_seed=args.bootstrap_seed,
    )
    default = overall.loc[overall["config_id"] == "default"].iloc[0]
    print(
        f"Analyzed 18 OAT configurations and 9 interaction cells. "
        f"Default score={default['mean_stop_score']:.3f}, "
        f"runtime={default['mean_elapsed_ms']:.1f} ms."
    )


if __name__ == "__main__":
    main()
