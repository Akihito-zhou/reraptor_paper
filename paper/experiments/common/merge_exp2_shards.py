#!/usr/bin/env python3
"""Strictly merge the eight canonical Experiment 2 ablation shards."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from paper.experiments.common.merge_exp1_shards import merge_shards, write_json_atomic


EXPECTED_CONFIGS = (
    "Ours (Full)",
    "Ours (NoNeg)",
    "Ours (NoDom)",
    "Ours (NoBeam)",
    "Ours (NoBeam-NoDom)",
    "Ours (NoDom-NoNeg)",
    "Ours (NoBeam-NoNeg)",
    "Ours (NoBeam-NoDom-NoNeg)",
)
EXPECTED_ROWS_PER_CONFIG = 600


def merge_exp2_shards(input_paths: list[Path], output_tag: str) -> dict:
    """Merge, validate, and order the complete eight-configuration ablation."""

    payload = merge_shards(input_paths, output_tag)
    metadata = payload["metadata"]
    rows = payload["results"]

    if metadata.get("experiment") != "exp2_ablation_study":
        raise ValueError(
            "Experiment 2 merger requires experiment='exp2_ablation_study', "
            f"got {metadata.get('experiment')!r}"
        )

    counts = Counter(str(row.get("algorithm") or "") for row in rows)
    expected = set(EXPECTED_CONFIGS)
    actual = set(counts)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ValueError(
            "Experiment 2 configuration set mismatch: "
            f"missing={missing}, unexpected={unexpected}"
        )

    wrong_counts = {
        name: counts[name]
        for name in EXPECTED_CONFIGS
        if counts[name] != EXPECTED_ROWS_PER_CONFIG
    }
    if wrong_counts:
        raise ValueError(
            "Each Experiment 2 configuration must contain exactly "
            f"{EXPECTED_ROWS_PER_CONFIG} rows: {wrong_counts}"
        )

    config_order = {name: index for index, name in enumerate(EXPECTED_CONFIGS)}
    origin_order = {
        str(origin): index
        for index, origin in enumerate(metadata.get("origins") or [])
    }
    rows.sort(
        key=lambda row: (
            int(row.get("score_seed")),
            origin_order.get(
                str(row.get("origin_name") or row.get("origin") or ""),
                10**9,
            ),
            int(row.get("depart_time")),
            int(row.get("budget_minutes")),
            config_order[str(row.get("algorithm") or "")],
            int(row.get("seed")),
        )
    )

    metadata.pop("include_recent_adapted_baselines", None)
    metadata.pop("algorithms_override", None)
    metadata["ablation_config_count"] = len(EXPECTED_CONFIGS)
    metadata["ablation_config_order"] = list(EXPECTED_CONFIGS)
    metadata["merge_protocol"].update(
        {
            "experiment_scope": "exp2_ablation_study",
            "expected_configurations": list(EXPECTED_CONFIGS),
            "expected_rows_per_configuration": EXPECTED_ROWS_PER_CONFIG,
            "configuration_counts": {
                name: counts[name] for name in EXPECTED_CONFIGS
            },
        }
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge the eight canonical Experiment 2 ablation shards."
    )
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Input shard; repeat exactly once for each configuration.",
    )
    parser.add_argument("--output", required=True, help="Merged JSON output.")
    parser.add_argument(
        "--output-tag",
        default="canonical_exp2_final_8config",
        help="Metadata tag stored in the merged payload.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = merge_exp2_shards(
        [Path(value) for value in args.input],
        str(args.output_tag),
    )
    output = Path(args.output)
    write_json_atomic(output, payload)
    counts = payload["metadata"]["merge_protocol"]["configuration_counts"]
    print(f"Merged {len(args.input)} Experiment 2 shards -> {output.resolve()}")
    print(f"Rows: {len(payload['results'])}; configuration counts: {counts}")


if __name__ == "__main__":
    main()
