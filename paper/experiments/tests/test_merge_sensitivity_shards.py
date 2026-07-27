from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import pytest

from paper.experiments.common.merge_sensitivity_shards import (
    EXPECTED_ROWS_PER_CONFIG,
    merge_sensitivity_shards,
)
from paper.experiments.exp3_parameter_sensitivity.sensitivity_protocol import OAT_SPECS


def _payload(config_id: str, *, rows_per_config: int) -> dict:
    spec = next(spec for spec in OAT_SPECS if spec.config_id == config_id)
    origins = [f"origin-{index}" for index in range(rows_per_config)]
    metadata = {
        "experiment": "exp3_hyperparameter_sensitivity",
        "panel": "oat",
        "primary_metric": "stop_score_total",
        "primary_metric_label": "Stop Score",
        "origins": origins,
        "depart_times": [420],
        "budgets": [120],
        "seeds": [0],
        "score_seeds": [42],
        "score_seed_count": 1,
        "stop_score_min": 1,
        "stop_score_max": 100,
        "dwell_minutes": 10,
        "objective_mode": "score_guided",
        "timeout_seconds": 60.0,
        "shared_config": {"label_cap": 3000000},
        "scoring_semantics": {"version": "test"},
        "execution_protocol": {"parallel_execution": False},
        "python_version": "3.10-test",
        "platform": "Windows-test",
        "sensitivity_config_count": 1,
        "sensitivity_config_ids": [config_id],
        "sensitivity_configurations": {config_id: spec.snapshot()},
        "num_results": rows_per_config,
        "total_runs": rows_per_config,
        "output_tag": config_id,
        "timestamp": "2026-07-27T00:00:00",
        "baseline": {"config_id": "default"},
    }
    rows = []
    for origin, departure, budget, seed, score_seed in product(
        origins,
        metadata["depart_times"],
        metadata["budgets"],
        metadata["seeds"],
        metadata["score_seeds"],
    ):
        rows.append(
            {
                "algorithm": spec.algorithm_name,
                "origin": origin,
                "origin_name": origin,
                "depart_time": departure,
                "budget_minutes": budget,
                "seed": seed,
                "score_seed": score_seed,
                "sensitivity_config_id": config_id,
                "sensitivity_panel": spec.panel,
                "sensitivity_factor": spec.factor,
                "sensitivity_factor_value": spec.factor_value,
                "sensitivity_parameters": spec.snapshot(),
            }
        )
    return {"metadata": metadata, "results": rows}


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_oat_merge_requires_all_configs_and_preserves_exact_counts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Keep the production expectation strict while using a small synthetic grid.
    monkeypatch.setitem(EXPECTED_ROWS_PER_CONFIG, "oat", 2)
    inputs = [
        _write(tmp_path / f"{spec.config_id}.json", _payload(spec.config_id, rows_per_config=2))
        for spec in reversed(OAT_SPECS)
    ]

    merged = merge_sensitivity_shards(inputs, panel="oat", output_tag="test")

    assert len(merged["results"]) == 2 * len(OAT_SPECS)
    assert merged["metadata"]["sensitivity_config_ids"] == [
        spec.config_id for spec in OAT_SPECS
    ]
    assert merged["metadata"]["merge_protocol"]["global_task_key_unique"] is True


def test_oat_merge_rejects_missing_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(EXPECTED_ROWS_PER_CONFIG, "oat", 2)
    inputs = [
        _write(tmp_path / f"{spec.config_id}.json", _payload(spec.config_id, rows_per_config=2))
        for spec in OAT_SPECS[:-1]
    ]

    with pytest.raises(ValueError, match="configuration set mismatch"):
        merge_sensitivity_shards(inputs, panel="oat", output_tag="test")


def test_oat_merge_rejects_row_parameter_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(EXPECTED_ROWS_PER_CONFIG, "oat", 2)
    inputs = []
    for spec in OAT_SPECS:
        payload = _payload(spec.config_id, rows_per_config=2)
        if spec.config_id == "w25":
            payload["results"][0]["sensitivity_parameters"]["beam_width"] = 26
        inputs.append(_write(tmp_path / f"{spec.config_id}.json", payload))

    with pytest.raises(ValueError, match="Row/configuration mismatch"):
        merge_sensitivity_shards(inputs, panel="oat", output_tag="test")
