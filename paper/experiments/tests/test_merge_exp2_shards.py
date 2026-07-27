from __future__ import annotations

from pathlib import Path

import pytest

from paper.experiments.common.merge_exp2_shards import (
    EXPECTED_CONFIGS,
    EXPECTED_ROWS_PER_CONFIG,
    merge_exp2_shards,
)
from paper.experiments.tests.test_merge_exp1_shards import (
    make_payload,
    write_payload,
)


def make_exp2_payload(algorithm: str, seed: int) -> dict:
    payload = make_payload(algorithm=algorithm, seed=seed)
    payload["metadata"]["experiment"] = "exp2_ablation_study"
    rows = []
    for index in range(EXPECTED_ROWS_PER_CONFIG):
        row = dict(payload["results"][0])
        row["origin"] = f"O{index}"
        row["origin_name"] = f"origin-{index}"
        rows.append(row)
    payload["results"] = rows
    payload["metadata"]["num_results"] = len(rows)
    payload["metadata"]["total_runs"] = len(rows)
    return payload


def test_exp2_merge_requires_and_orders_all_eight_configs(tmp_path: Path) -> None:
    inputs = [
        write_payload(
            tmp_path / f"{index}.json",
            make_exp2_payload(algorithm=name, seed=0),
        )
        for index, name in enumerate(reversed(EXPECTED_CONFIGS))
    ]

    merged = merge_exp2_shards(inputs, "final")

    assert len(merged["results"]) == len(EXPECTED_CONFIGS) * EXPECTED_ROWS_PER_CONFIG
    assert merged["metadata"]["ablation_config_count"] == len(EXPECTED_CONFIGS)
    assert merged["metadata"]["ablation_config_order"] == list(EXPECTED_CONFIGS)
    assert list(merged["metadata"]["merge_protocol"]["configuration_counts"]) == list(
        EXPECTED_CONFIGS
    )


def test_exp2_merge_rejects_missing_config(tmp_path: Path) -> None:
    inputs = [
        write_payload(
            tmp_path / f"{index}.json",
            make_exp2_payload(algorithm=name, seed=0),
        )
        for index, name in enumerate(EXPECTED_CONFIGS[:-1])
    ]

    with pytest.raises(ValueError, match="configuration set mismatch"):
        merge_exp2_shards(inputs, "missing")
