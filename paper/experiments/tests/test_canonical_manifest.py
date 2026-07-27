from __future__ import annotations

import json
from pathlib import Path

from paper.experiments.common.build_canonical_manifest import audit_result_file


def metadata(*, origins: list[str], total_runs: int) -> dict:
    return {
        "num_results": total_runs,
        "total_runs": total_runs,
        "score_seeds": [42],
        "origins": origins,
        "depart_times": [420],
        "budgets": [120],
        "seed_policy": {"algorithm_seeds": {"Greedy (L=3)": [0]}},
    }


def valid_row(*, origin_name: str = "hakata") -> dict:
    return {
        "algorithm": "Greedy (L=3)",
        "origin": "677805",
        "origin_name": origin_name,
        "depart_time": 420,
        "budget_minutes": 120,
        "seed": 0,
        "score_seed": 42,
        "feasible": True,
        "algorithm_failure": False,
        "query_infeasible_proven": False,
        "objective_metrics_valid": True,
        "stop_score_total": 304.0,
        "scored_stop_count": 4,
        "query_elapsed_minutes": 78.0,
        "dwell_minutes_total": 40,
        "effective_time_minutes": 118.0,
        "effective_budget_overrun_minutes": 0.0,
        "effective_budget_feasible": True,
        "score_per_hour": 154.576271,
        "violation_reason": "",
    }


def write_payload(path: Path, *, metadata_block: dict, rows: list[dict]) -> None:
    path.write_text(
        json.dumps({"metadata": metadata_block, "results": rows}),
        encoding="utf-8",
    )


def test_complete_result_file_passes_integrity_gate(tmp_path: Path) -> None:
    result_path = tmp_path / "complete.json"
    write_payload(
        result_path,
        metadata_block=metadata(origins=["hakata"], total_runs=1),
        rows=[valid_row()],
    )

    audit = audit_result_file(result_path)

    assert audit["integrity_gate_passed"] is True
    assert audit["counts"]["expected_task_keys"] == 1
    assert audit["missing_task_keys"] == []
    assert audit["duplicate_task_keys"] == []
    assert audit["semantic_errors"] == []


def test_missing_and_duplicate_task_keys_fail_integrity_gate(tmp_path: Path) -> None:
    result_path = tmp_path / "broken.json"
    row = valid_row()
    write_payload(
        result_path,
        metadata_block=metadata(origins=["hakata", "tenjin"], total_runs=2),
        rows=[row, dict(row)],
    )

    audit = audit_result_file(result_path)

    assert audit["integrity_gate_passed"] is False
    assert len(audit["duplicate_task_keys"]) == 1
    assert len(audit["missing_task_keys"]) == 1
    assert audit["missing_task_keys"][0]["origin_name"] == "tenjin"
