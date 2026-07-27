#!/usr/bin/env python3
"""Build a machine-readable reproducibility and integrity manifest.

The manifest does not make a result canonical by declaration. It records the
inputs, source tree, environment, task-key completeness, schema consistency,
and semantic validation needed to decide whether an output may be frozen.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = PROJECT_ROOT / "apps" / "api" / "data"
DEFAULT_MANIFEST_DIR = PROJECT_ROOT / "paper" / "results" / "manifests"

TASK_KEY_FIELDS = (
    "algorithm",
    "origin_name",
    "depart_time",
    "budget_minutes",
    "seed",
    "score_seed",
)
REQUIRED_RESULT_FIELDS = {
    *TASK_KEY_FIELDS,
    "feasible",
    "algorithm_failure",
    "query_infeasible_proven",
    "objective_metrics_valid",
    "stop_score_total",
    "scored_stop_count",
    "query_elapsed_minutes",
    "dwell_minutes_total",
    "effective_time_minutes",
    "effective_budget_feasible",
    "violation_reason",
}
ZERO_ON_FAILURE_FIELDS = (
    "stop_score_total",
    "scored_stop_count",
    "query_elapsed_minutes",
    "dwell_minutes_total",
    "effective_time_minutes",
    "effective_budget_overrun_minutes",
    "score_per_hour",
)


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
        return str(resolved)


def file_record(path: Path, *, role: str) -> dict[str, Any]:
    resolved = path.resolve()
    record: dict[str, Any] = {
        "path": display_path(resolved),
        "role": role,
        "exists": resolved.is_file(),
    }
    if resolved.is_file():
        stat = resolved.stat()
        record.update(
            {
                "bytes": int(stat.st_size),
                "modified_utc": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
                "sha256": sha256_file(resolved),
            }
        )
    return record


def run_command(args: list[str]) -> str:
    try:
        completed = subprocess.run(
            args,
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return completed.stdout.strip()


def git_snapshot() -> dict[str, Any]:
    status_lines = [
        line
        for line in run_command(["git", "status", "--porcelain=v1"]).splitlines()
        if line.strip()
    ]
    return {
        "commit": run_command(["git", "rev-parse", "HEAD"]),
        "branch": run_command(["git", "branch", "--show-current"]),
        "is_dirty": bool(status_lines),
        "status_porcelain": status_lines,
    }


def cpu_name() -> str:
    if sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            ) as key:
                return str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).strip()
        except OSError:
            pass
    return str(platform.processor() or platform.machine())


def total_memory_bytes() -> int | None:
    if sys.platform == "win32":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_physical", ctypes.c_ulonglong),
                ("available_physical", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("available_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("available_virtual", ctypes.c_ulonglong),
                ("available_extended_virtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.total_physical)
        return None
    try:
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, ValueError):
        return None


def package_snapshot() -> list[dict[str, str]]:
    packages = {
        str(dist.metadata.get("Name") or "unknown"): str(dist.version)
        for dist in importlib.metadata.distributions()
    }
    return [
        {"name": name, "version": packages[name]}
        for name in sorted(packages, key=str.casefold)
    ]


def environment_snapshot() -> dict[str, Any]:
    memory_bytes = total_memory_bytes()
    system_name = platform.system()
    release = platform.release()
    version = platform.version()
    windows_build: int | None = None
    operating_system_display = system_name
    if system_name == "Windows":
        try:
            windows_build = int(sys.getwindowsversion().build)
        except (AttributeError, TypeError, ValueError):
            try:
                windows_build = int(version.split(".")[-1])
            except (TypeError, ValueError):
                windows_build = None
        # Windows 11 intentionally retains the NT 10.0 kernel version. Older
        # Python releases may therefore report platform.release() == "10".
        operating_system_display = (
            "Windows 11"
            if windows_build is not None and windows_build >= 22000
            else f"Windows {release}"
        )
    thread_variables = {
        name: os.environ.get(name)
        for name in (
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
        )
    }
    return {
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "system": system_name,
        "release": release,
        "version": version,
        "operating_system_display": operating_system_display,
        "windows_build": windows_build,
        "machine": platform.machine(),
        "cpu_model": cpu_name(),
        "logical_cpu_count": os.cpu_count(),
        "total_memory_bytes": memory_bytes,
        "total_memory_gib": (
            round(memory_bytes / (1024**3), 3) if memory_bytes is not None else None
        ),
        "thread_environment": thread_variables,
        "installed_packages": package_snapshot(),
    }


def default_input_files(data_dir: Path) -> list[Path]:
    timetable_candidates = sorted(
        (data_dir / "timetables").glob("segments_fukuoka_*.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    inputs = [
        data_dir / "base" / "stations_fukuoka.csv",
        data_dir / "base" / "freepass_lines.yml",
        data_dir / "base" / "fukuoka_city.geojson",
        data_dir / "base" / "line_stop_edges.csv",
        data_dir / "generated" / "boundary_overrides.json",
    ]
    if timetable_candidates:
        inputs.append(timetable_candidates[0])
    return inputs


def default_source_files(generator_script: Path | None) -> list[Path]:
    sources = [
        PROJECT_ROOT / "paper" / "experiments" / "common" / "config.py",
        PROJECT_ROOT / "paper" / "experiments" / "common" / "base_algorithm.py",
        PROJECT_ROOT / "paper" / "experiments" / "common" / "stop_scoring.py",
        PROJECT_ROOT / "apps" / "api" / "poetry.lock",
    ]
    sources.extend(
        sorted((PROJECT_ROOT / "paper" / "experiments" / "algorithms").glob("*.py"))
    )
    if generator_script is not None:
        sources.append(generator_script)
    unique: dict[str, Path] = {}
    for path in sources:
        unique[str(path.resolve())] = path.resolve()
    return list(unique.values())


def load_result_payload(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return {}, [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        raise ValueError(f"Unsupported result payload in {path}")
    rows = payload.get("results", [])
    if not isinstance(rows, list):
        raise ValueError(f"results must be a list in {path}")
    return dict(payload.get("metadata", {}) or {}), [
        row for row in rows if isinstance(row, dict)
    ]


def task_key_from_row(row: dict[str, Any]) -> tuple[str, str, int, int, int, int] | None:
    try:
        origin = row.get("origin_name", row.get("origin"))
        return (
            str(row["algorithm"]),
            str(origin),
            int(row["depart_time"]),
            int(row["budget_minutes"]),
            int(row["seed"]),
            int(row["score_seed"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def expected_task_keys(metadata: dict[str, Any]) -> set[tuple[str, str, int, int, int, int]]:
    score_seeds = [int(value) for value in metadata.get("score_seeds", [])]
    origins = [str(value) for value in metadata.get("origins", [])]
    departures = [int(value) for value in metadata.get("depart_times", [])]
    budgets = [int(value) for value in metadata.get("budgets", [])]
    algorithm_seeds = (
        metadata.get("seed_policy", {}).get("algorithm_seeds", {})
        if isinstance(metadata.get("seed_policy"), dict)
        else {}
    )
    if not all((score_seeds, origins, departures, budgets, algorithm_seeds)):
        return set()
    return {
        (str(algorithm), origin, departure, budget, int(seed), score_seed)
        for score_seed in score_seeds
        for origin in origins
        for departure in departures
        for budget in budgets
        for algorithm, seeds in algorithm_seeds.items()
        for seed in seeds
    }


def serialize_key(key: tuple[str, str, int, int, int, int]) -> dict[str, Any]:
    return dict(zip(TASK_KEY_FIELDS, key, strict=True))


def result_semantic_errors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        key = task_key_from_row(row)
        prefix = {"row_index": index, "task_key": serialize_key(key) if key else None}
        feasible = bool(row.get("feasible", False))
        if feasible:
            if row.get("algorithm_failure") is not False:
                errors.append({**prefix, "error": "feasible_row_algorithm_failure_not_false"})
            if row.get("query_infeasible_proven") is not False:
                errors.append({**prefix, "error": "query_infeasible_proven_not_false"})
            if row.get("objective_metrics_valid") is not True:
                errors.append({**prefix, "error": "feasible_row_objective_metrics_invalid"})
            if row.get("effective_budget_feasible") is not True:
                errors.append({**prefix, "error": "feasible_row_effective_budget_invalid"})
            if str(row.get("violation_reason", "")):
                errors.append({**prefix, "error": "feasible_row_has_violation_reason"})
            try:
                expected_effective = float(row["query_elapsed_minutes"]) + float(
                    row["dwell_minutes_total"]
                )
                actual_effective = float(row["effective_time_minutes"])
                if abs(expected_effective - actual_effective) > 1e-6:
                    errors.append({**prefix, "error": "effective_time_identity_failed"})
                if actual_effective > float(row["budget_minutes"]) + 1e-9:
                    errors.append({**prefix, "error": "feasible_row_over_budget"})
            except (KeyError, TypeError, ValueError):
                errors.append({**prefix, "error": "invalid_effective_time_fields"})
        else:
            if row.get("algorithm_failure") is not True:
                errors.append({**prefix, "error": "invalid_row_algorithm_failure_not_true"})
            if row.get("query_infeasible_proven") is not False:
                errors.append({**prefix, "error": "invalid_row_claims_query_infeasibility"})
            for field in ZERO_ON_FAILURE_FIELDS:
                try:
                    if abs(float(row.get(field, 0.0))) > 1e-9:
                        errors.append({**prefix, "error": f"invalid_row_nonzero_{field}"})
                except (TypeError, ValueError):
                    errors.append({**prefix, "error": f"invalid_row_nonnumeric_{field}"})
    return errors


def audit_result_file(path: Path) -> dict[str, Any]:
    metadata, rows = load_result_payload(path)
    keys: list[tuple[str, str, int, int, int, int]] = []
    malformed: list[dict[str, Any]] = []
    schema_missing: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        key = task_key_from_row(row)
        if key is None:
            malformed.append({"row_index": index})
        else:
            keys.append(key)
        missing_fields = sorted(REQUIRED_RESULT_FIELDS - set(row))
        if missing_fields:
            schema_missing.append({"row_index": index, "missing_fields": missing_fields})

    counts = Counter(keys)
    duplicates = sorted(key for key, count in counts.items() if count > 1)
    actual = set(keys)
    expected = expected_task_keys(metadata)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected) if expected else []
    semantic_errors = result_semantic_errors(rows)
    violation_counts = Counter(
        str(row.get("violation_reason", "")) or "none" for row in rows
    )
    algorithms = Counter(str(row.get("algorithm", "missing")) for row in rows)

    declared_total = metadata.get("total_runs")
    declared_num_results = metadata.get("num_results")
    expected_count = len(expected) if expected else None
    count_consistent = (
        (declared_total is None or int(declared_total) == len(rows))
        and (declared_num_results is None or int(declared_num_results) == len(rows))
        and (expected_count is None or expected_count == len(rows))
    )
    passed = not any(
        (
            malformed,
            schema_missing,
            duplicates,
            missing,
            unexpected,
            semantic_errors,
        )
    ) and count_consistent
    return {
        "file": file_record(path, role="result"),
        "metadata": metadata,
        "counts": {
            "rows": len(rows),
            "unique_task_keys": len(actual),
            "expected_task_keys": expected_count,
            "declared_total_runs": declared_total,
            "declared_num_results": declared_num_results,
            "feasible_rows": sum(bool(row.get("feasible", False)) for row in rows),
            "algorithm_failure_rows": sum(
                bool(row.get("algorithm_failure", False)) for row in rows
            ),
        },
        "algorithms": dict(sorted(algorithms.items())),
        "violation_reasons": dict(sorted(violation_counts.items())),
        "malformed_rows": malformed,
        "rows_with_missing_schema_fields": schema_missing,
        "duplicate_task_keys": [serialize_key(key) for key in duplicates],
        "missing_task_keys": [serialize_key(key) for key in missing],
        "unexpected_task_keys": [serialize_key(key) for key in unexpected],
        "semantic_errors": semantic_errors,
        "count_consistent": count_consistent,
        "integrity_gate_passed": passed,
    }


def records_for_files(paths: Iterable[Path], *, role: str) -> list[dict[str, Any]]:
    return [file_record(path, role=role) for path in paths]


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(path)


def build_manifest(
    *,
    result_paths: list[Path],
    output_path: Path,
    status: str,
    data_dir: Path,
    input_paths: list[Path],
    artifact_paths: list[Path],
    generator_script: Path | None,
) -> dict[str, Any]:
    git = git_snapshot()
    result_audits = [audit_result_file(path) for path in result_paths]
    sources = default_source_files(generator_script)
    required_files = [*input_paths, *sources, *result_paths, *artifact_paths]
    missing_files = sorted(display_path(path) for path in required_files if not path.is_file())
    result_gates_passed = all(
        audit["integrity_gate_passed"] for audit in result_audits
    )
    integrity_gate_passed = not missing_files and result_gates_passed
    canonical_gate_passed = integrity_gate_passed and not git["is_dirty"]
    requested_status_gate_passed = (
        canonical_gate_passed if status == "canonical" else integrity_gate_passed
    )
    return {
        "schema_version": "reraptor-canonical-manifest-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "canonical_claim": bool(status == "canonical" and canonical_gate_passed),
        "integrity_gate_passed": integrity_gate_passed,
        "canonical_gate_passed": canonical_gate_passed,
        "requested_status_gate_passed": requested_status_gate_passed,
        "gate_policy": {
            "all_files_exist": True,
            "all_result_integrity_gates_pass": True,
            "clean_git_tree_required_for_canonical": True,
            "smoke_outputs_are_never_paper_evidence": True,
        },
        "git": git,
        "environment": environment_snapshot(),
        "data_directory": display_path(data_dir),
        "input_files": records_for_files(input_paths, role="planner_input"),
        "source_files": records_for_files(sources, role="source_or_lock"),
        "result_audits": result_audits,
        "additional_artifacts": records_for_files(artifact_paths, role="artifact"),
        "missing_files": missing_files,
        "manifest_output": display_path(output_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and validate a ReRAPTOR canonical/smoke manifest."
    )
    parser.add_argument("--result", action="append", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--status",
        choices=("smoke", "provisional", "canonical"),
        default="provisional",
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--input", action="append", type=Path, default=[])
    parser.add_argument("--artifact", action="append", type=Path, default=[])
    parser.add_argument("--generator-script", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    input_paths = (
        [path.resolve() for path in args.input]
        if args.input
        else default_input_files(data_dir)
    )
    generator_script = args.generator_script.resolve() if args.generator_script else None
    manifest = build_manifest(
        result_paths=[path.resolve() for path in args.result],
        output_path=args.output.resolve(),
        status=str(args.status),
        data_dir=data_dir,
        input_paths=input_paths,
        artifact_paths=[path.resolve() for path in args.artifact],
        generator_script=generator_script,
    )
    write_json_atomic(args.output.resolve(), manifest)
    print(f"Manifest saved: {args.output.resolve()}")
    print(f"Integrity gate passed: {manifest['integrity_gate_passed']}")
    print(f"Canonical gate passed: {manifest['canonical_gate_passed']}")
    for audit in manifest["result_audits"]:
        counts = audit["counts"]
        print(
            f"- {audit['file']['path']}: rows={counts['rows']}, "
            f"expected={counts['expected_task_keys']}, "
            f"integrity={audit['integrity_gate_passed']}"
        )
    if not manifest["requested_status_gate_passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
