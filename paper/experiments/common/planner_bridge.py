"""
Bridge module to load PlannerService from the app layer.

Adds the app package to sys.path so experiment scripts can import
the planner without installing the app as a package.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .config import PLANNER_DATA_DIR, PROJECT_ROOT

if TYPE_CHECKING:
    pass  # avoid circular at type-check time

_planner_instance = None


def _ensure_app_path() -> None:
    """Add the app services directory to sys.path if not already present."""
    services_dir = str(PROJECT_ROOT / "apps" / "api" / "services")
    app_dir = str(PROJECT_ROOT / "apps" / "api")
    for p in (services_dir, app_dir):
        if p not in sys.path:
            sys.path.insert(0, p)


def load_planner(*, force_reload: bool = False):
    """
    Returns a fully initialised PlannerService with GTFS data loaded.

    The instance is cached (singleton) unless *force_reload* is True.
    """
    global _planner_instance
    if _planner_instance is not None and not force_reload:
        return _planner_instance

    _ensure_app_path()

    from services.planner import PlannerService  # type: ignore

    planner = PlannerService(data_dir=PLANNER_DATA_DIR, enable_realtime=False)
    planner.ensure_data_loaded()
    if not planner.stations or not planner.static_edges:
        raise RuntimeError(
            "Planner inputs are missing or yielded an empty network. "
            "Install the six authorized files described in apps/api/data/README.md "
            "and run python -m paper.experiments.check_reproduction --require-data."
        )

    _planner_instance = planner
    return planner


def get_stop_codes(planner) -> dict[str, str]:
    """
    Returns a mapping from friendly origin names (used in config.ORIGINS)
    to actual GTFS stop codes.

    Override this if the mapping changes.
    """
    # Build lookup from station name fragments → code
    name_to_code: dict[str, str] = {}
    for code, station in planner.stations.items():
        name_lower = station.name.lower()
        name_to_code[name_lower] = code
        # Also map the code itself
        name_to_code[code.lower()] = code

    # Explicit mapping for config.ORIGINS
    manual_mapping = {
        "hakata": "677805",      # 博多駅
        "tenjin": "677793",      # 天神北
        "nishijin": "677846",    # 西新駅
        "ohori-koen": "676853",  # 大濠公園
        "yakuin": "676805",      # 薬院
        "kashii": "676527",      # 香椎
        "noke": "676736",        # 野芥駅前
        "meinohama": "675460",   # 姪浜
        "kaizuka": "676672",     # 貝塚
        "fukudaimae": "676008"   # 福大前
    }
    name_to_code.update(manual_mapping)

    return name_to_code


def resolve_origin(planner, friendly_name: str) -> str:
    """
    Resolve a friendly origin name from config.ORIGINS to a GTFS stop code.

    Falls back to using the name directly if it looks like a stop code.
    """
    mapping = get_stop_codes(planner)
    key = friendly_name.lower().strip()
    if key in mapping:
        return mapping[key]

    # Try partial match
    for name, code in mapping.items():
        if key in name or name in key:
            return code

    # If it's already a valid stop code, use it directly
    if friendly_name in planner.stations:
        return friendly_name

    raise ValueError(
        f"Cannot resolve origin '{friendly_name}'. "
        f"Available: {list(mapping.keys())[:20]}..."
    )
