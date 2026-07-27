from __future__ import annotations

import json
from pathlib import Path

import pytest

from paper.experiments.common.merge_exp1_shards import merge_shards


def make_payload(*, algorithm: str, seed: int, objective_mode: str = "score_guided") -> dict:
    row = {
        "algorithm": algorithm,
        "origin": "O",
        "origin_name": "origin",
        "depart_time": 420,
        "budget_minutes": 120,
        "seed": seed,
        "score_seed": 42,
    }
    return {
        "metadata": {
            "experiment": "exp1_algorithm_comparison",
            "quick_mode": False,
            "primary_metric": "stop_score_total",
            "primary_metric_label": "Stop Score",
            "score_seeds": [42],
            "score_seed_count": 1,
            "stop_score_min": 1,
            "stop_score_max": 100,
            "dwell_minutes": 10,
            "objective_mode": objective_mode,
            "origins": ["origin"],
            "depart_times": [420],
            "budgets": [120],
            "seeds": [0, 1],
            "shared_config": {"BEAM_WIDTH": 50},
            "scoring_semantics": {"version": "test"},
            "execution_protocol": {"parallel_execution": False},
            "python_version": "test",
            "platform": "test",
            "timestamp": "2026-07-21T00:00:00",
            "num_results": 1,
            "total_runs": 1,
            "algorithm_parameters": {algorithm: {"name": algorithm}},
            "seed_policy": {
                "repeat_deterministic_seeds": False,
                "deterministic_repeats": 1,
                "stochastic_repeats": 2,
                "algorithm_seed_counts": {algorithm: 1},
                "algorithm_seeds": {algorithm: [seed]},
            },
            "output_tag": algorithm,
            "include_recent_adapted_baselines": False,
            "algorithms_override": [algorithm],
        },
        "results": [row],
    }


def write_payload(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_merge_preserves_rows_and_combines_algorithm_metadata(tmp_path: Path) -> None:
    first = write_payload(tmp_path / "a.json", make_payload(algorithm="A", seed=0))
    second = write_payload(tmp_path / "b.json", make_payload(algorithm="B", seed=1))

    merged = merge_shards([first, second], "merged")

    assert len(merged["results"]) == 2
    assert merged["metadata"]["num_results"] == 2
    assert merged["metadata"]["total_runs"] == 2
    assert set(merged["metadata"]["algorithm_parameters"]) == {"A", "B"}
    assert merged["metadata"]["seed_policy"]["algorithm_seeds"] == {"A": [0], "B": [1]}
    assert len(merged["metadata"]["source_shards"]) == 2


def test_merge_rejects_algorithm_overlap(tmp_path: Path) -> None:
    first = write_payload(tmp_path / "a.json", make_payload(algorithm="A", seed=0))
    second = write_payload(tmp_path / "b.json", make_payload(algorithm="A", seed=0))

    with pytest.raises(ValueError, match="Algorithms occur in multiple shards"):
        merge_shards([first, second], "merged")


def test_merge_rejects_protocol_mismatch(tmp_path: Path) -> None:
    first = write_payload(tmp_path / "a.json", make_payload(algorithm="A", seed=0))
    second = write_payload(
        tmp_path / "b.json",
        make_payload(algorithm="B", seed=1, objective_mode="legacy_balanced"),
    )

    with pytest.raises(ValueError, match="objective_mode"):
        merge_shards([first, second], "merged")
