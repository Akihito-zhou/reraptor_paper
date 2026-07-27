from __future__ import annotations

from pathlib import Path

from paper.experiments.common.io_utils import save_results
from paper.experiments.common.json_list_store import load_json_rows
from paper.experiments.common.stop_scoring import StopScoringProfile
from paper.experiments.exp2_ablation_study.run_exp2 import (
    build_ablation_configs,
    build_experiment_metadata,
    filter_ablation_configs,
)


def test_json_list_resume_loader_accepts_wrapped_results(tmp_path: Path) -> None:
    path = tmp_path / "wrapped.json"
    rows = [{"algorithm": "x", "seed": 0}]
    save_results(rows, path, metadata={"experiment": "test", "total_runs": 1})
    assert load_json_rows(path) == rows


def test_exp2_metadata_declares_complete_expected_grid() -> None:
    objective = StopScoringProfile(
        stop_scores={},
        dwell_minutes=10,
        search_mode="score_guided",
    )
    configs = build_ablation_configs(
        timeout_seconds=60.0,
        no_pruning_label_cap=1_000_000,
        objective=objective,
    )
    metadata = build_experiment_metadata(
        quick_mode=False,
        score_seeds=[11, 12],
        score_min=1,
        score_max=100,
        dwell_minutes=10,
        objective_mode="score_guided",
        origins=["a", "b"],
        depart_times=[420],
        budgets=[120, 240],
        seeds=[0],
        configs=configs,
        total_runs=64,
        output_tag="canonical_test",
        timeout_seconds=60.0,
        no_pruning_max_labels=1_000_000,
    )
    assert metadata["total_runs"] == 64
    assert metadata["ablation_config_count"] == 8
    assert len(metadata["seed_policy"]["algorithm_seeds"]) == 8
    assert all(
        seeds == [0]
        for seeds in metadata["seed_policy"]["algorithm_seeds"].values()
    )
    assert metadata["execution_protocol"]["timeout_seconds_per_run"] == 60.0


def test_exp2_config_alias_filter_is_exact() -> None:
    objective = StopScoringProfile(
        stop_scores={},
        dwell_minutes=10,
        search_mode="score_guided",
    )
    configs = build_ablation_configs(
        timeout_seconds=60.0,
        no_pruning_label_cap=1_000_000,
        objective=objective,
    )
    assert [item.name for item in filter_ablation_configs(configs, ["full"])] == [
        "Ours (Full)"
    ]
    assert [item.name for item in filter_ablation_configs(configs, ["nobeam"])] == [
        "Ours (NoBeam)"
    ]
    assert [
        item.name
        for item in filter_ablation_configs(
            configs, ["nobeamnodom", "nobeamnodomnoneg"]
        )
    ] == [
        "Ours (NoBeam-NoDom)",
        "Ours (NoBeam-NoDom-NoNeg)",
    ]
