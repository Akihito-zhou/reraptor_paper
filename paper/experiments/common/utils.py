"""
Shared metric computation utilities.

All experiment scripts use these functions to compute route quality metrics,
ensuring consistent evaluation across experiments.
"""
from __future__ import annotations

import math
from typing import Sequence


# ─── Convex Hull ──────────────────────────────────────────────────────────────

def convex_hull_area(coords: Sequence[tuple[float, float]]) -> float:
    """
    Compute the area of the convex hull of 2-D points (km²).

    *coords* are (lat, lon) pairs. They are projected to a local plane
    (km units) before the hull is computed via the Monotone Chain algorithm.
    Returns 0.0 when fewer than 3 unique points are given.
    """
    if len(coords) < 3:
        return 0.0

    # Project to flat (km) plane centred on centroid
    clat = sum(c[0] for c in coords) / len(coords)
    clon = sum(c[1] for c in coords) / len(coords)
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(clat))
    pts = [
        ((lon - clon) * km_per_deg_lon, (lat - clat) * km_per_deg_lat)
        for lat, lon in coords
    ]

    # Remove duplicates
    pts = list(set(pts))
    if len(pts) < 3:
        return 0.0

    # Monotone chain convex hull
    pts.sort()

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    if len(hull) < 3:
        return 0.0

    # Shoelace area
    n = len(hull)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += hull[i][0] * hull[j][1]
        area -= hull[j][0] * hull[i][1]
    return abs(area) / 2.0


# ─── Quadrant Coverage ───────────────────────────────────────────────────────

def quadrant_coverage(coords: Sequence[tuple[float, float]]) -> int:
    """
    Count how many quadrants (NE, NW, SE, SW) are covered by the coordinates,
    relative to their centroid.  Returns 0-4.
    """
    if len(coords) < 2:
        return 0
    clat = sum(c[0] for c in coords) / len(coords)
    clon = sum(c[1] for c in coords) / len(coords)
    quadrants = set()
    for lat, lon in coords:
        q = ("N" if lat >= clat else "S") + ("E" if lon >= clon else "W")
        quadrants.add(q)
    return len(quadrants)


# ─── Route Metrics ────────────────────────────────────────────────────────────

def compute_route_metrics(path_edges, planner=None) -> dict:
    """
    Compute a standardised metrics dictionary from a list of TripEdge objects.

    Returns dict with keys:
        ride_minutes, distance_km, unique_stops, legs, hull_area,
        quadrant_coverage, total_time_minutes
    """
    if not path_edges:
        return {
            "ride_minutes": 0,
            "distance_km": 0.0,
            "unique_stops": 0,
            "legs": 0,
            "hull_area": 0.0,
            "quadrant_coverage": 0,
            "total_time_minutes": 0,
        }

    ride_min = sum(max(0, e.arrive - e.depart) for e in path_edges)
    distance = sum(e.distance_km for e in path_edges)

    stops = set()
    coords = []
    for e in path_edges:
        stops.add(e.from_code)
        stops.add(e.to_code)
        coords.append((e.from_lat, e.from_lon))
        coords.append((e.to_lat, e.to_lon))

    # Count legs (distinct trips)
    legs = 1
    for i in range(1, len(path_edges)):
        if path_edges[i].trip_id != path_edges[i - 1].trip_id:
            legs += 1

    total_time = path_edges[-1].arrive - path_edges[0].depart if path_edges else 0

    return {
        "ride_minutes": ride_min,
        "distance_km": round(distance, 2),
        "unique_stops": len(stops),
        "legs": legs,
        "hull_area": round(convex_hull_area(coords), 4),
        "quadrant_coverage": quadrant_coverage(coords),
        "total_time_minutes": total_time,
    }


# ─── Pareto / Hypervolume ─────────────────────────────────────────────────────

def is_pareto_optimal(
    points: list[list[float]],
    maximize: bool = True,
) -> list[bool]:
    """
    Determine which points are Pareto-optimal.

    *points* is a list of objective vectors.
    When *maximize* is True, a point dominates another if it is >= on all
    objectives and > on at least one.
    """
    n = len(points)
    optimal = [True] * n
    for i in range(n):
        if not optimal[i]:
            continue
        for j in range(n):
            if i == j or not optimal[j]:
                continue
            if _dominates(points[j], points[i], maximize):
                optimal[i] = False
                break
    return optimal


def _dominates(a: list[float], b: list[float], maximize: bool) -> bool:
    """Return True if *a* dominates *b*."""
    all_geq = True
    any_gt = False
    for ai, bi in zip(a, b):
        if maximize:
            if ai < bi:
                all_geq = False
                break
            if ai > bi:
                any_gt = True
        else:
            if ai > bi:
                all_geq = False
                break
            if ai < bi:
                any_gt = True
    return all_geq and any_gt


def compute_hypervolume_2d(
    points: list[tuple[float, float]],
    ref: tuple[float, float],
) -> float:
    """
    Compute exact Hypervolume for 2-D maximisation objectives.

    *points* are (obj1, obj2) tuples.  *ref* is the reference (worst) point.
    """
    # Filter dominated points
    filtered = [(x, y) for x, y in points if x > ref[0] and y > ref[1]]
    if not filtered:
        return 0.0
    # Sort by first objective descending
    filtered.sort(key=lambda p: -p[0])
    hv = 0.0
    prev_y = ref[1]
    for x, y in filtered:
        if y > prev_y:
            hv += (x - ref[0]) * (y - prev_y)
            prev_y = y
    return hv


# ─── Composite Score ──────────────────────────────────────────────────────────

def composite_score(
    metrics: dict,
    weights: dict[str, float] | None = None,
    normalizers: dict[str, float] | None = None,
) -> float:
    """
    Compute a weighted composite score from metrics.

    *normalizers* maps metric keys to their expected max values for [0, 1]
    scaling.  If not provided, raw values are used.
    """
    from .config import SCORE_WEIGHTS

    w = weights or SCORE_WEIGHTS
    norm = normalizers or {
        "ride_minutes": 480,
        "unique_stops": 50,
        "hull_area": 100,
        "quadrant": 4,
    }

    score = 0.0
    for key, weight in w.items():
        raw = metrics.get(key, metrics.get("quadrant_coverage", 0) if key == "quadrant" else 0)
        n = norm.get(key, 1.0)
        score += weight * (raw / n if n else 0)
    return round(score, 6)
