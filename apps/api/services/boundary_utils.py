"""
Utilities for loading and managing boundary override station data.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .planner import PlannerService

logger = logging.getLogger(__name__)

DEFAULT_BOUNDARY_FILE = Path(__file__).parent.parent / "data" / "generated" / "boundary_overrides.json"


def load_boundary_overrides(service: "PlannerService", overrides_path: Path | None = None) -> set[str]:
    """
    Load boundary station codes from boundary_overrides.json.
    
    Returns:
        Set of station codes that should be prioritized in City Loop planning.
    """
    path = overrides_path or DEFAULT_BOUNDARY_FILE
    
    if not path.exists():
        logger.warning(f"Boundary overrides file not found: {path}")
        return set()
    
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        include_list = data.get("include", [])
        boundary_codes = {station["code"] for station in include_list if "code" in station}
        
        # Filter to only include codes that exist in service.stations
        valid_codes = {code for code in boundary_codes if code in service.stations}
        
        logger.info(f"Loaded {len(valid_codes)} boundary override stations (out of {len(boundary_codes)} total)")
        return valid_codes
        
    except (json.JSONDecodeError, KeyError) as exc:
        logger.error(f"Failed to parse boundary overrides: {exc}")
        return set()


def calculate_boundary_coverage(legs, boundary_codes: set[str]) -> float:
    """
    Calculate what percentage of boundary stations are covered by the given legs.
    
    Args:
        legs: List of JourneyLeg or leg-like objects with from_code/to_code
        boundary_codes: Set of boundary station codes
    
    Returns:
        Coverage ratio from 0.0 to 1.0
    """
    if not boundary_codes:
        return 0.0
    
    visited_boundary = set()
    for leg in legs:
        if hasattr(leg, 'from_code') and leg.from_code in boundary_codes:
            visited_boundary.add(leg.from_code)
        if hasattr(leg, 'to_code') and leg.to_code in boundary_codes:
            visited_boundary.add(leg.to_code)
    
    coverage = len(visited_boundary) / len(boundary_codes)
    return coverage


__all__ = ["load_boundary_overrides", "calculate_boundary_coverage"]
