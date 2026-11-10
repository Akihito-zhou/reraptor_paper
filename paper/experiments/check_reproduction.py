"""Check a reader installation without downloading or uploading any data."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PLANNER_INPUTS = {
    "apps/api/data/base/stations_fukuoka.csv": (
        64_671,
        "85558a3753e16b129f387211f7dee6f5d82f8a190d5871152d3c390c4f31f7aa",
    ),
    "apps/api/data/base/freepass_lines.yml": (
        325_363,
        "485566f7fae122ede96acb4e592d9e464084fb033b74892bcf9491f74fc4462d",
    ),
    "apps/api/data/base/fukuoka_city.geojson": (
        818_877,
        "fb84a9bc2a804fa595a8e67cc2dba84133c242619463e4ec497c751b0957e1ea",
    ),
    "apps/api/data/base/line_stop_edges.csv": (
        171_283,
        "2de41bd64c0004f5d0ff452928da1b90ebccc3e846c5cd732f7a0bec59c3feb8",
    ),
    "apps/api/data/generated/boundary_overrides.json": (
        5_013,
        "5dfe3f10599178090e641480f370f84803ada6bdd132e135e34f732efab3ea80",
    ),
    "apps/api/data/timetables/segments_fukuoka_20251224.csv": (
        33_156_301,
        "319d443ac097f8964f8774d38fc63c6c8f7ef90e505eb167ffd38bc317727c82",
    ),
}

def check_inputs(root: Path = ROOT, *, require_data: bool = False) -> list[str]:
    errors = []
    present = [p for p in PLANNER_INPUTS if (root / p).is_file()]
    if not present and not require_data:
        print("INFO private inputs absent; public result auditing remains available")
        return errors
    for relative, (size, digest) in PLANNER_INPUTS.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"Missing authorized input: {relative}")
        else:
            with path.open("rb") as handle:
                actual = hashlib.file_digest(handle, "sha256").hexdigest()
            if path.stat().st_size != size or actual != digest:
                errors.append(f"Frozen input mismatch: {relative}")
    timetable_dir = root / "apps/api/data/timetables"
    candidates = list(timetable_dir.glob("segments_fukuoka_*.csv"))
    if len(candidates) > 1:
        errors.append("Keep only the frozen segments_fukuoka_20251224.csv snapshot in timetables; the loader selects by modification time")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-data", action="store_true", help="Require all six exact frozen inputs")
    args = parser.parse_args()
    from paper.experiments.common.planner_bridge import _ensure_app_path
    _ensure_app_path()
    from services.planner import PlannerService
    from paper.experiments.algorithms import build_all_algorithms
    algorithms = build_all_algorithms(include_recent_adapted=True)
    if len(algorithms) != 10:
        raise RuntimeError(f"Expected 10 manuscript algorithms, found {len(algorithms)}")
    print("PASS planner imports and all 10 manuscript algorithms")
    errors = check_inputs(require_data=args.require_data)
    if errors:
        for error in errors:
            print("FAIL", error)
        raise SystemExit(1)
    print("PASS reproduction preflight" + (" (exact private inputs verified)" if args.require_data else ""))


if __name__ == "__main__":
    main()
