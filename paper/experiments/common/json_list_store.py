"""
Helpers for raw-list experiment result files.

Several experiment runners store results as a plain JSON list instead of the
metadata-wrapped payload used by Exp1. These helpers centralize the common
resume/checkpoint logic so schema checks stay consistent across experiments.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Hashable


RowKeyFn = Callable[[dict[str, Any]], Hashable | None]
CompatibilityFn = Callable[[dict[str, Any]], bool]


def load_json_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    return data if isinstance(data, list) else []


def save_json_rows_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def build_resume_state(
    path: Path,
    *,
    row_to_key: RowKeyFn,
    is_compatible: CompatibilityFn | None = None,
) -> tuple[list[dict[str, Any]], set[Hashable], dict[str, int]]:
    existing = load_json_rows(path)
    cleaned: list[dict[str, Any]] = []
    completed: set[Hashable] = set()
    stats = {
        "loaded": len(existing),
        "kept": 0,
        "dropped_malformed": 0,
        "dropped_incompatible": 0,
        "dropped_duplicate": 0,
    }

    for row in existing:
        key = row_to_key(row)
        if key is None:
            stats["dropped_malformed"] += 1
            continue
        if is_compatible is not None and not is_compatible(row):
            stats["dropped_incompatible"] += 1
            continue
        if key in completed:
            stats["dropped_duplicate"] += 1
            continue
        cleaned.append(row)
        completed.add(key)

    stats["kept"] = len(cleaned)
    return cleaned, completed, stats
