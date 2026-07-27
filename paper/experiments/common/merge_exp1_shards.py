#!/usr/bin/env python3
"""Merge independently frozen Experiment 1 algorithm shards.

The merger is intentionally strict: all query/scoring/execution metadata must
match, algorithm names may occur in only one shard, and task keys must be
globally unique. The merged file retains every raw row and can be audited by
``build_canonical_manifest.py`` like a monolithic runner output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


COMMON_METADATA_FIELDS = (
    "experiment",
    "quick_mode",
    "primary_metric",
    "primary_metric_label",
    "score_seeds",
    "score_seed_count",
    "stop_score_min",
    "stop_score_max",
    "dwell_minutes",
    "objective_mode",
    "origins",
    "depart_times",
    "budgets",
    "seeds",
    "shared_config",
    "scoring_semantics",
    "execution_protocol",
    "python_version",
    "platform",
)

COMMON_SEED_POLICY_FIELDS = (
    "repeat_deterministic_seeds",
    "deterministic_repeats",
    "stochastic_repeats",
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def task_key(row: dict[str, Any]) -> tuple[str, str, int, int, int, int]:
    origin_name = str(row.get("origin_name") or row.get("origin") or "")
    return (
        str(row.get("algorithm") or ""),
        origin_name,
        int(row.get("depart_time")),
        int(row.get("budget_minutes")),
        int(row.get("seed")),
        int(row.get("score_seed")),
    )


def _json_equal(left: Any, right: Any) -> bool:
    return json.dumps(left, ensure_ascii=False, sort_keys=True) == json.dumps(
        right,
        ensure_ascii=False,
        sort_keys=True,
    )


def _assert_common_metadata(reference: dict[str, Any], candidate: dict[str, Any], path: Path) -> None:
    mismatches = [
        field
        for field in COMMON_METADATA_FIELDS
        if not _json_equal(reference.get(field), candidate.get(field))
    ]
    ref_policy = reference.get("seed_policy") or {}
    candidate_policy = candidate.get("seed_policy") or {}
    mismatches.extend(
        f"seed_policy.{field}"
        for field in COMMON_SEED_POLICY_FIELDS
        if not _json_equal(ref_policy.get(field), candidate_policy.get(field))
    )
    if mismatches:
        raise ValueError(f"Incompatible metadata in {path}: {', '.join(mismatches)}")


def _load_shard(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Shard must contain a JSON object: {path}")
    metadata = payload.get("metadata")
    rows = payload.get("results")
    if not isinstance(metadata, dict) or not isinstance(rows, list):
        raise ValueError(f"Shard requires object metadata and list results: {path}")
    declared = metadata.get("num_results")
    total_runs = metadata.get("total_runs")
    if declared is None or int(declared) != len(rows):
        raise ValueError(f"num_results mismatch in {path}: declared={declared}, actual={len(rows)}")
    if total_runs is None or int(total_runs) != len(rows):
        raise ValueError(f"total_runs mismatch in {path}: declared={total_runs}, actual={len(rows)}")
    parameters = metadata.get("algorithm_parameters")
    algorithm_seeds = (metadata.get("seed_policy") or {}).get("algorithm_seeds")
    if not isinstance(parameters, dict) or not parameters:
        raise ValueError(f"Missing algorithm_parameters in {path}")
    if not isinstance(algorithm_seeds, dict) or set(parameters) != set(algorithm_seeds):
        raise ValueError(f"Algorithm parameter/seed maps disagree in {path}")
    row_algorithms = {str(row.get("algorithm") or "") for row in rows}
    if row_algorithms != set(parameters):
        raise ValueError(
            f"Row algorithms disagree with metadata in {path}: "
            f"rows={sorted(row_algorithms)}, metadata={sorted(parameters)}"
        )
    return payload


def merge_shards(input_paths: Iterable[Path], output_tag: str) -> dict[str, Any]:
    paths = [Path(path).resolve() for path in input_paths]
    if not paths:
        raise ValueError("At least one input shard is required")
    if len(set(paths)) != len(paths):
        raise ValueError("The same input shard was provided more than once")

    loaded = [(path, _load_shard(path)) for path in paths]
    reference_metadata = loaded[0][1]["metadata"]
    for path, payload in loaded[1:]:
        _assert_common_metadata(reference_metadata, payload["metadata"], path)

    algorithms: dict[str, Any] = {}
    algorithm_seeds: dict[str, list[int]] = {}
    algorithm_seed_counts: dict[str, int] = {}
    overrides: list[str] = []
    rows: list[dict[str, Any]] = []
    seen_keys: dict[tuple[str, str, int, int, int, int], Path] = {}
    source_shards: list[dict[str, Any]] = []

    for path, payload in loaded:
        metadata = payload["metadata"]
        parameters = metadata["algorithm_parameters"]
        overlap = sorted(set(algorithms).intersection(parameters))
        if overlap:
            raise ValueError(f"Algorithms occur in multiple shards: {overlap}")
        algorithms.update(deepcopy(parameters))

        policy = metadata["seed_policy"]
        for name, seeds in policy["algorithm_seeds"].items():
            algorithm_seeds[name] = [int(seed) for seed in seeds]
            declared_count = int((policy.get("algorithm_seed_counts") or {}).get(name, len(seeds)))
            if declared_count != len(seeds):
                raise ValueError(f"Algorithm seed count mismatch for {name} in {path}")
            algorithm_seed_counts[name] = declared_count

        for token in metadata.get("algorithms_override") or []:
            token = str(token)
            if token not in overrides:
                overrides.append(token)

        for row in payload["results"]:
            key = task_key(row)
            if key in seen_keys:
                raise ValueError(f"Duplicate task key across {seen_keys[key]} and {path}: {key}")
            seen_keys[key] = path
            rows.append(deepcopy(row))

        source_shards.append(
            {
                "path": path.as_posix(),
                "sha256": file_sha256(path),
                "rows": len(payload["results"]),
                "algorithms": sorted(parameters),
                "timestamp": metadata.get("timestamp"),
                "output_tag": metadata.get("output_tag"),
            }
        )

    origin_order = {
        str(origin): index for index, origin in enumerate(reference_metadata.get("origins") or [])
    }
    rows.sort(
        key=lambda row: (
            int(row.get("score_seed")),
            origin_order.get(str(row.get("origin_name") or row.get("origin") or ""), 10**9),
            int(row.get("depart_time")),
            int(row.get("budget_minutes")),
            str(row.get("algorithm") or ""),
            int(row.get("seed")),
        )
    )

    metadata = {
        key: deepcopy(reference_metadata.get(key))
        for key in COMMON_METADATA_FIELDS
    }
    metadata.update(
        {
            "timestamp": datetime.now().isoformat(),
            "num_results": len(rows),
            "total_runs": len(rows),
            "algorithm_parameters": algorithms,
            "seed_policy": {
                **{
                    key: deepcopy((reference_metadata.get("seed_policy") or {}).get(key))
                    for key in COMMON_SEED_POLICY_FIELDS
                },
                "algorithm_seed_counts": algorithm_seed_counts,
                "algorithm_seeds": algorithm_seeds,
            },
            "output_tag": output_tag,
            "include_recent_adapted_baselines": any(
                bool(payload["metadata"].get("include_recent_adapted_baselines"))
                for _, payload in loaded
            ),
            "algorithms_override": overrides,
            "source_shards": source_shards,
            "merge_protocol": {
                "raw_rows_preserved": True,
                "global_task_key_unique": True,
                "metadata_fields_checked": list(COMMON_METADATA_FIELDS),
                "algorithm_overlap_allowed": False,
            },
        }
    )
    return {"metadata": metadata, "results": rows}


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge canonical Experiment 1 result shards")
    parser.add_argument("--input", action="append", required=True, help="Input shard; repeat per file")
    parser.add_argument("--output", required=True, help="Merged JSON output")
    parser.add_argument("--output-tag", default="canonical_exp1_merged")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    payload = merge_shards([Path(value) for value in args.input], str(args.output_tag))
    write_json_atomic(output, payload)
    algorithms = sorted(payload["metadata"]["algorithm_parameters"])
    print(f"Merged {len(args.input)} shards -> {output.resolve()}")
    print(f"Rows: {len(payload['results'])}; algorithms: {algorithms}")


if __name__ == "__main__":
    main()
