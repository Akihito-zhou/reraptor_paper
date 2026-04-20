"""
I/O utilities for experiment results.

Handles JSON serialisation of experiment results with timestamps and metadata.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def save_results(
    results: list[dict],
    output_path: Path,
    *,
    metadata: dict | None = None,
) -> Path:
    """
    Save experiment results to a JSON file.

    Adds a top-level metadata block with timestamp, python version, etc.
    """
    import platform
    import sys

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "platform": platform.platform(),
            "num_results": len(results),
            **(metadata or {}),
        },
        "results": results,
    }
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)
    tmp_path.replace(output_path)

    logger.info("Results saved to %s (%d entries)", output_path, len(results))
    return output_path


def load_results(path: Path) -> tuple[dict, list[dict]]:
    """
    Load results from a JSON file.

    Returns (metadata, results_list).
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {}, data
    return data.get("metadata", {}), data.get("results", [])


def format_result_row(
    algorithm: str,
    origin: str,
    depart_time: int,
    budget: int,
    seed: int,
    elapsed_ms: float,
    metrics: dict,
) -> dict:
    """
    Create a standardised result row dict.
    """
    return {
        "algorithm": algorithm,
        "origin": origin,
        "depart_time": depart_time,
        "budget_minutes": budget,
        "seed": seed,
        "elapsed_ms": round(elapsed_ms, 2),
        **metrics,
    }
