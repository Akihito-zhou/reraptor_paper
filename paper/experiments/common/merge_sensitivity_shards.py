#!/usr/bin/env python3
"""Strictly merge canonical Experiment 3 sensitivity shards.

The OAT and interaction panels use different frozen task grids and are
therefore merged into separate canonical payloads.  Every source shard is
validated against the preregistered configuration snapshot and exact Cartesian
task grid before any row is copied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from copy import deepcopy
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Any, Iterable

from paper.experiments.common.merge_exp1_shards import write_json_atomic
from paper.experiments.exp3_parameter_sensitivity.sensitivity_protocol import (
    INTERACTION_CORNER_SPECS,
    OAT_SPECS,
    SensitivitySpec,
)


EXPECTED_ROWS_PER_CONFIG = {"oat": 600, "interaction": 72}

COMMON_METADATA_FIELDS = (
    "experiment",
    "primary_metric",
    "primary_metric_label",
    "depart_times",
    "budgets",
    "seeds",
    "stop_score_min",
    "stop_score_max",
    "dwell_minutes",
    "objective_mode",
    "timeout_seconds",
    "shared_config",
    "scoring_semantics",
    "execution_protocol",
    "python_version",
    "platform",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_equal(left: Any, right: Any) -> bool:
    return json.dumps(left, ensure_ascii=False, sort_keys=True) == json.dumps(
        right,
        ensure_ascii=False,
        sort_keys=True,
    )


def _specs_for_panel(panel: str) -> tuple[SensitivitySpec, ...]:
    if panel == "oat":
        return OAT_SPECS
    if panel == "interaction":
        return INTERACTION_CORNER_SPECS
    raise ValueError(f"Unknown sensitivity panel: {panel}")


def _load(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Shard must contain a JSON object: {path}")
    metadata = payload.get("metadata")
    rows = payload.get("results")
    if not isinstance(metadata, dict) or not isinstance(rows, list):
        raise ValueError(f"Shard requires object metadata and list results: {path}")
    for count_field in ("num_results", "total_runs"):
        if int(metadata.get(count_field, -1)) != len(rows):
            raise ValueError(
                f"{count_field} mismatch in {path}: "
                f"declared={metadata.get(count_field)!r}, actual={len(rows)}"
            )
    return metadata, rows


def _row_key(row: dict[str, Any]) -> tuple[str, str, int, int, int, int]:
    return (
        str(row["sensitivity_config_id"]),
        str(row.get("origin_name") or row["origin"]),
        int(row["depart_time"]),
        int(row["budget_minutes"]),
        int(row["seed"]),
        int(row["score_seed"]),
    )


def _expected_keys(
    metadata: dict[str, Any],
    config_id: str,
) -> set[tuple[str, str, int, int, int, int]]:
    return {
        (
            config_id,
            str(origin),
            int(departure),
            int(budget),
            int(seed),
            int(score_seed),
        )
        for origin, departure, budget, seed, score_seed in product(
            metadata["origins"],
            metadata["depart_times"],
            metadata["budgets"],
            metadata["seeds"],
            metadata["score_seeds"],
        )
    }


def _assert_common_metadata(
    reference: dict[str, Any],
    candidate: dict[str, Any],
    path: Path,
) -> None:
    fields = (*COMMON_METADATA_FIELDS, "origins", "score_seeds", "score_seed_count")
    mismatches = [
        field
        for field in fields
        if not _json_equal(reference.get(field), candidate.get(field))
    ]
    if mismatches:
        raise ValueError(
            f"Incompatible sensitivity metadata in {path}: {', '.join(mismatches)}"
        )


def merge_sensitivity_shards(
    input_paths: Iterable[Path],
    *,
    panel: str,
    output_tag: str,
) -> dict[str, Any]:
    """Validate and merge every preregistered shard for one panel."""

    specs = _specs_for_panel(panel)
    spec_by_id = {spec.config_id: spec for spec in specs}
    paths = [Path(path).resolve() for path in input_paths]
    if not paths:
        raise ValueError("At least one input shard is required")
    if len(paths) != len(set(paths)):
        raise ValueError("The same sensitivity shard was provided more than once")

    loaded = [(path, *_load(path)) for path in paths]
    reference = loaded[0][1]
    for path, metadata, _ in loaded[1:]:
        _assert_common_metadata(reference, metadata, path)

    rows: list[dict[str, Any]] = []
    seen_keys: dict[tuple[str, str, int, int, int, int], Path] = {}
    seen_configs: set[str] = set()
    source_shards: list[dict[str, Any]] = []

    for path, metadata, shard_rows in loaded:
        if metadata.get("experiment") != "exp3_hyperparameter_sensitivity":
            raise ValueError(f"Wrong experiment in {path}: {metadata.get('experiment')!r}")
        if metadata.get("panel") != panel:
            raise ValueError(
                f"Wrong panel in {path}: expected {panel!r}, got {metadata.get('panel')!r}"
            )
        ids = metadata.get("sensitivity_config_ids")
        configurations = metadata.get("sensitivity_configurations")
        if (
            metadata.get("sensitivity_config_count") != 1
            or not isinstance(ids, list)
            or len(ids) != 1
            or not isinstance(configurations, dict)
            or set(configurations) != set(ids)
        ):
            raise ValueError(f"Each source must contain exactly one configuration: {path}")

        config_id = str(ids[0])
        if config_id not in spec_by_id:
            raise ValueError(f"Unexpected {panel} configuration {config_id!r} in {path}")
        if config_id in seen_configs:
            raise ValueError(f"Configuration occurs in multiple shards: {config_id}")
        seen_configs.add(config_id)
        spec = spec_by_id[config_id]

        if not _json_equal(configurations[config_id], spec.snapshot()):
            raise ValueError(f"Configuration snapshot mismatch for {config_id} in {path}")
        expected_count = EXPECTED_ROWS_PER_CONFIG[panel]
        if len(shard_rows) != expected_count:
            raise ValueError(
                f"{config_id} requires {expected_count} rows, got {len(shard_rows)}"
            )

        actual_keys: set[tuple[str, str, int, int, int, int]] = set()
        for row in shard_rows:
            key = _row_key(row)
            if key in actual_keys:
                raise ValueError(f"Duplicate task key within {path}: {key}")
            if key in seen_keys:
                raise ValueError(f"Duplicate task key across {seen_keys[key]} and {path}: {key}")
            actual_keys.add(key)
            seen_keys[key] = path

            expected_fields = {
                "algorithm": spec.algorithm_name,
                "sensitivity_config_id": spec.config_id,
                "sensitivity_panel": spec.panel,
                "sensitivity_factor": spec.factor,
                "sensitivity_factor_value": spec.factor_value,
            }
            mismatches = [
                field
                for field, expected_value in expected_fields.items()
                if row.get(field) != expected_value
            ]
            if mismatches or not _json_equal(
                row.get("sensitivity_parameters"),
                spec.snapshot(),
            ):
                raise ValueError(
                    f"Row/configuration mismatch for {config_id} in {path}: "
                    f"{mismatches or ['sensitivity_parameters']}"
                )
            rows.append(deepcopy(row))

        expected_keys = _expected_keys(metadata, config_id)
        if actual_keys != expected_keys:
            raise ValueError(
                f"Task grid mismatch for {config_id} in {path}: "
                f"missing={len(expected_keys - actual_keys)}, "
                f"unexpected={len(actual_keys - expected_keys)}"
            )
        source_shards.append(
            {
                "path": path.as_posix(),
                "sha256": _sha256(path),
                "rows": len(shard_rows),
                "config_id": config_id,
                "timestamp": metadata.get("timestamp"),
                "output_tag": metadata.get("output_tag"),
            }
        )

    expected_configs = set(spec_by_id)
    if seen_configs != expected_configs:
        raise ValueError(
            f"{panel} configuration set mismatch: "
            f"missing={sorted(expected_configs - seen_configs)}, "
            f"unexpected={sorted(seen_configs - expected_configs)}"
        )

    config_order = {spec.config_id: index for index, spec in enumerate(specs)}
    origin_order = {
        str(origin): index for index, origin in enumerate(reference["origins"])
    }
    rows.sort(
        key=lambda row: (
            int(row["score_seed"]),
            origin_order[str(row.get("origin_name") or row["origin"])],
            int(row["depart_time"]),
            int(row["budget_minutes"]),
            config_order[str(row["sensitivity_config_id"])],
            int(row["seed"]),
        )
    )

    counts = Counter(str(row["sensitivity_config_id"]) for row in rows)
    algorithms = {spec.algorithm_name: spec.snapshot() for spec in specs}
    algorithm_seeds = {
        spec.algorithm_name: [int(seed) for seed in reference["seeds"]]
        for spec in specs
    }
    metadata = {
        field: deepcopy(reference.get(field))
        for field in (*COMMON_METADATA_FIELDS, "origins", "score_seeds", "score_seed_count")
    }
    metadata.update(
        {
            "panel": panel,
            "timestamp": datetime.now().isoformat(),
            "num_results": len(rows),
            "total_runs": len(rows),
            "output_tag": output_tag,
            "sensitivity_config_count": len(specs),
            "sensitivity_config_ids": [spec.config_id for spec in specs],
            "sensitivity_configurations": {
                spec.config_id: spec.snapshot() for spec in specs
            },
            "algorithm_parameters": algorithms,
            "seed_policy": {
                "repeat_deterministic_seeds": False,
                "deterministic_repeats": 1,
                "stochastic_repeats": 1,
                "algorithm_seed_counts": {
                    name: len(seeds) for name, seeds in algorithm_seeds.items()
                },
                "algorithm_seeds": algorithm_seeds,
            },
            "baseline": deepcopy(reference.get("baseline")),
            "source_shards": sorted(
                source_shards,
                key=lambda item: config_order[item["config_id"]],
            ),
            "merge_protocol": {
                "raw_rows_preserved": True,
                "global_task_key_unique": True,
                "metadata_fields_checked": list(COMMON_METADATA_FIELDS),
                "panel_task_grid_checked": True,
                "configuration_snapshot_checked": True,
                "expected_configurations": [spec.config_id for spec in specs],
                "expected_rows_per_configuration": EXPECTED_ROWS_PER_CONFIG[panel],
                "configuration_counts": {
                    spec.config_id: counts[spec.config_id] for spec in specs
                },
            },
        }
    )
    return {"metadata": metadata, "results": rows}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge canonical Experiment 3 sensitivity shards."
    )
    parser.add_argument("--panel", choices=("oat", "interaction"), required=True)
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--output-tag", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = merge_sensitivity_shards(
        [Path(value) for value in args.input],
        panel=args.panel,
        output_tag=str(args.output_tag),
    )
    output = Path(args.output)
    write_json_atomic(output, payload)
    print(
        f"Merged {len(args.input)} {args.panel} shards -> {output.resolve()}\n"
        f"Rows: {len(payload['results'])}; "
        f"configs: {payload['metadata']['sensitivity_config_count']}"
    )


if __name__ == "__main__":
    main()
