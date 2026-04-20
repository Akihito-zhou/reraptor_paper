
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import replace
from typing import TYPE_CHECKING, Callable

from .planner_constants import (
    ALL_QUADRANTS_MASK,
    MAX_LABELS_PER_STOP,
    MAX_WALK_DISTANCE_KM,
    START_TIME_MINUTES,
)
from .planner_hubs import TRANSFER_HUBS, HUB_MAX_VISITS
from .planner_models import (
    ChallengeConfig,
    ChallengePlan,
    JourneyLeg,
    Label,
    LegPlan,
    RouteData,
    RouteTrip,
)
from .planner_utils import derive_quadrant_labels, distance_km as calc_distance_km, label_leg_to_plan, project_to_plane


if TYPE_CHECKING:
    from .planner import PlannerService


def run_raptor_challenge(
    planner: PlannerService,
    config: ChallengeConfig,
    start_stops: list[str] | None = None,
    end_stops: list[str] | None = None,
    start_time: int | None = None,
) -> ChallengePlan | None:
    """
    Runs a RAPTOR-based algorithm to find a journey that optimizes for a given challenge configuration.
    This is a label-setting algorithm that explores possible journeys round by round.
    
    Args:
        planner: The PlannerService instance with route data
        config: Challenge configuration with scoring functions
        start_stops: List of stop codes to start from (default: stations with routes near hakata)
        end_stops: List of stop codes to end at (default: same as start_stops for circular routes)
        start_time: Start time in minutes from midnight (default: START_TIME_MINUTES)
    """
    if not planner.routes:
        return None
    
    # Use provided start/end stops or find valid defaults
    actual_start_time = start_time if start_time is not None else START_TIME_MINUTES
    
    # Default: use stops with most route connections (best connectivity)
    if start_stops is None:
        # Sort stops by number of routes (most connected first)
        sorted_stops = sorted(
            planner.routes_by_stop.keys(),
            key=lambda s: len(planner.routes_by_stop.get(s, set())),
            reverse=True
        )
        # Take top 20 most connected stops
        start_stops = sorted_stops[:20]
    
    if end_stops is None:
        end_stops = start_stops  # Circular route: return to start
    
    if not start_stops:
        return None

    # Rounds store labels for each stop for each transfer round
    rounds: list[dict[str, list[Label]]] = [
        defaultdict(list) for _ in range(config.max_rounds + 1)
    ]
    metrics_cache: dict[tuple, dict[str, float]] = {}

    def metrics_key(label: Label) -> tuple:
        return _label_metrics_key(planner, label)

    def get_metrics(label: Label) -> dict[str, float]:
        key = metrics_key(label)
        metrics = metrics_cache.get(key)
        if metrics is None:
            metrics = _label_metrics(planner, label, config)
            metrics_cache[key] = metrics
        return metrics

    # Initialize with starting stops
    marked_stops: set[str] = set()
    end_stops_set = set(end_stops)  # For fast lookup
    for stop_code in start_stops:
        mask = planner.quadrant_map.get(stop_code, 0)
        base_label = Label(
            arrival=actual_start_time,
            ride_minutes=0,
            distance_km=0.0,
            visited=frozenset({stop_code}),
            quadrant_mask=mask,
            legs=(),
            score=0.0,
            stop_counts=((stop_code, 1),),
            line_counts=tuple(),
            transfers=0,
            min_transfer_gap=10**9,
        )
        metrics = get_metrics(base_label)
        scored = replace(base_label, score=config.scoring_fn(base_label, metrics))
        metrics_cache[metrics_key(scored)] = metrics
        rounds[0][stop_code].append(scored)
        marked_stops.add(stop_code)

    time_limit = actual_start_time + 24 * 60
    best_labels: list[Label] = []

    # Main RAPTOR loop
    for round_idx in range(config.max_rounds):
        # 1. Selection: Pick stops updated in previous round
        # If no stops updated, we are done
        if not marked_stops:
            break
        next_marked: set[str] = set()
        routes_to_scan: set[str] = set()
        for stop in marked_stops:
            routes_to_scan.update(planner.routes_by_stop.get(stop, ()))

        # Iterate through all routes serving the marked stops
        for route_id in routes_to_scan:
            route = planner.routes.get(route_id)
            if not route:
                continue

            # For each trip in the route
            for trip in route.trips:
                # Iterate through the segments of the trip
                for from_idx, stop_code in enumerate(route.stops[:-1]):
                    if stop_code not in rounds[round_idx]:
                        continue

                    # For each existing label at the stop
                    for label in rounds[round_idx][stop_code]:
                        earliest_depart = label.arrival + config.min_transfer_minutes
                        
                        onboard_label: Label | None = None
                        boarded = False
                        # Try to board and travel along the trip from the current stop
                        for seg_idx in range(from_idx, len(route.stops) - 1):
                            # ... (omitted for brevity, assuming context match works)
                            # Actually I need to match the whole block or be careful.
                            # I'll just replace the loop start and the inner usage.
                            pass

                        earliest_depart = label.arrival + config.min_transfer_minutes
                        
                        onboard_label: Label | None = None
                        boarded = False
                        # Try to board and travel along the trip from the current stop
                        for seg_idx in range(from_idx, len(route.stops) - 1):
                            depart = trip.departures[seg_idx]
                            arrive = trip.arrivals[seg_idx + 1]

                            if not boarded and depart < earliest_depart:
                                continue
                            
                            base_label = onboard_label if boarded else label
                            new_label = _extend_label(
                                planner,
                                base_label,
                                route,
                                trip,
                                seg_idx,
                                depart,
                                arrive,
                                config,
                            )

                            if new_label is None:
                                if boarded: break # Stop extending this path
                                continue
                            
                            if new_label.arrival > time_limit:
                                break

                            metrics = get_metrics(new_label)
                            scored_label = replace(
                                new_label,
                                score=config.scoring_fn(new_label, metrics),
                            )
                            metrics_cache[metrics_key(scored_label)] = metrics
                            to_stop = route.stops[seg_idx + 1]

                            inserted = _insert_label(
                                rounds[round_idx + 1][to_stop],
                                scored_label,
                                metrics,
                                config,
                                get_metrics,
                            )

                            if inserted:
                                next_marked.add(to_stop)
                                onboard_label = scored_label
                                boarded = True

                                # Check if this is a potential final solution
                                if (
                                    to_stop in end_stops_set
                                    and scored_label.arrival >= actual_start_time + 120
                                    and (
                                        not config.require_quadrants
                                        or scored_label.quadrant_mask
                                        == ALL_QUADRANTS_MASK
                                    )
                                    and config.accept_fn(scored_label, metrics)
                                ):
                                    best_labels.append(scored_label)
                            elif boarded:
                                # Dominated, stop exploring this path
                                break
        
        marked_stops = next_marked

    if not best_labels:
        return None

    best_labels.sort(key=lambda lbl: lbl.score, reverse=True)
    selected = best_labels[0]
    legs = [label_leg_to_plan(leg, planner.stations) for leg in selected.legs]
    
    # Get start station name from first leg (RAPTOR now supports any start point)
    start_name = (
        planner.stations.get(selected.legs[0].from_code).name
        if selected.legs and selected.legs[0].from_code in planner.stations
        else "博多駅"
    )
    
    return ChallengePlan(
        challenge_id=config.challenge_id,
        title=config.title,
        tagline=config.tagline,
        theme_tags=config.theme_tags,
        badge=config.badge,
        legs=legs,
        start_stop_name=start_name,
        wards=derive_quadrant_labels(legs, planner.quadrant_map),
        stations=planner.stations,
        # meal_breaks auto-injected by to_dict()
    )


def _extend_label(
    planner: PlannerService,
    base: Label,
    route: RouteData,
    trip: RouteTrip,
    segment_index: int,
    depart: int,
    arrive: int,
    config: ChallengeConfig,
) -> Label | None:
    from_code = route.stops[segment_index]
    to_code = route.stops[segment_index + 1]

    # Do not allow routes outside of Fukuoka city
    if to_code not in planner.fukuoka_station_codes:
        return None

    # Avoid immediate return trips on the same line
    if (
        base.legs
        and base.legs[-1].line_id == route.line_id
        and base.legs[-1].from_code == to_code
        and base.legs[-1].to_code == from_code
    ):
        return None

    if arrive <= depart:
        return None

    distance_inc = trip.segment_distances[segment_index]
    visited: set[str] = set(base.visited)
    visited.add(to_code)
    quadrant_mask = base.quadrant_mask | planner.quadrant_map.get(to_code, 0)

    # Calculate segment duration, handling midnight crossing
    segment_daily_depart = depart
    segment_daily_arrive = arrive
    segment_duration = segment_daily_arrive - segment_daily_depart
    if segment_duration < 0:
        segment_duration += 1440 # Add a day if it crosses midnight

    # Calculate the absolute departure time for the current segment
    # This is the earliest time we can depart, which is max(base.arrival, daily_depart_adjusted_for_day)
    # The daily_depart needs to be adjusted to the correct day relative to base.arrival
    absolute_depart_for_segment = segment_daily_depart
    # If the daily depart time is earlier than the daily part of base.arrival, it means it's on the next day
    if absolute_depart_for_segment < (base.arrival % 1440):
        absolute_depart_for_segment += (base.arrival // 1440 + 1) * 1440 # Add a full day
    else:
        absolute_depart_for_segment += (base.arrival // 1440) * 1440 # Add current day's offset

    # Ensure we depart no earlier than base.arrival (plus transfer buffer)
    absolute_depart_for_segment = max(absolute_depart_for_segment, base.arrival)

    # Calculate the absolute arrival time for the current segment
    absolute_arrive_for_segment = absolute_depart_for_segment + segment_duration

    ride_minutes = base.ride_minutes + segment_duration
    distance_km = base.distance_km + distance_inc

    legs = list(base.legs)
    prev_leg = legs[-1] if legs else None

    boarding_new_trip = (
        prev_leg is None
        or prev_leg.trip_id != trip.trip_id
        or prev_leg.line_id != route.line_id
    )
    gap = absolute_depart_for_segment - prev_leg.arrive if prev_leg else None

    if boarding_new_trip and prev_leg and gap is not None:
        if gap < config.min_transfer_minutes:
            return None

        # Enforce maximum walking distance for transfers
        prev_station = planner.stations.get(prev_leg.to_code)
        next_station = planner.stations.get(from_code)
        if prev_station and next_station:
            walk_dist = planner.get_station_distance(prev_leg.to_code, from_code)
            if walk_dist > MAX_WALK_DISTANCE_KM:
                return None

    new_transfers = base.transfers
    new_min_gap = base.min_transfer_gap
    if boarding_new_trip and prev_leg:
        new_transfers += 1
        gap_value = gap if gap is not None else 10**9
        new_min_gap = min(base.min_transfer_gap, gap_value)

    # Extend the last leg if it's the same trip
    if (
        legs
        and not boarding_new_trip
    ):
        last = legs[-1]
        legs[-1] = JourneyLeg(
            line_id=last.line_id,
            line_name=last.line_name,
            trip_id=last.trip_id,
            from_code=last.from_code,
            to_code=to_code,
            depart=last.depart, # This is already the absolute depart of the first segment of this extended leg
            arrive=absolute_arrive_for_segment, # Use absolute arrive of the current (last) segment
            distance_km=last.distance_km + distance_inc,
            stop_hops=last.stop_hops + 1,
        )
    else: # Board a new trip
        legs.append(
            JourneyLeg(
                line_id=route.line_id,
                line_name=route.line_name,
                trip_id=trip.trip_id,
                from_code=from_code,
                to_code=to_code,
                depart=absolute_depart_for_segment, # Use absolute depart
                arrive=absolute_arrive_for_segment,  # Use absolute arrive
                distance_km=distance_inc,
                stop_hops=1,
            )
        )

    stop_counts = dict(base.stop_counts)
    if not base.legs:
        stop_counts[from_code] = stop_counts.get(from_code, 0) + 1
    
    current_visits = stop_counts.get(to_code, 0)
    
    # 确定访问次数限制：换乘枢纽 > 博多站 > 普通站点
    # Determine visit limit: transfer hub > Hakata > regular stop
    limit = config.max_stop_visits
    station = planner.stations.get(to_code)
    is_hub = station and any(hub in station.name for hub in TRANSFER_HUBS)
    
    if is_hub:
        limit = HUB_MAX_VISITS
    elif to_code in planner.hakata_stops:
        limit = config.hakata_max_visits or config.max_stop_visits
    
    if limit is not None and current_visits >= limit:
        return None
    
    if (
        config.forbid_non_hakata_duplicates
        and to_code not in planner.hakata_stops
        and current_visits > 0
    ):
        return None
    stop_counts[to_code] = current_visits + 1

    line_counts = dict(base.line_counts)
    if boarding_new_trip:
        line_counts[route.line_id] = line_counts.get(route.line_id, 0) + 1
        if config.max_line_visits and line_counts[route.line_id] > config.max_line_visits:
            return None

    return Label(
        arrival=absolute_arrive_for_segment, # Corrected: Use the calculated absolute arrival
        ride_minutes=ride_minutes,
        distance_km=distance_km,
        visited=frozenset(visited),
        quadrant_mask=quadrant_mask,
        legs=tuple(legs),
        score=0.0,
        stop_counts=tuple(sorted(stop_counts.items())),
        line_counts=tuple(sorted(line_counts.items())),
        transfers=new_transfers,
        min_transfer_gap=new_min_gap,
    )


def _insert_label(
    bucket: list[Label],
    label: Label,
    label_metrics: dict[str, float],
    config: ChallengeConfig,
    get_metrics: Callable[[Label], dict[str, float]],
) -> bool:
    """
    Inserts a new label into a bucket if it's not dominated by any existing label.
    Removes any labels that are dominated by the new label.
    """
    # Check if the new label is dominated by any existing label in the bucket
    for existing in bucket:
        existing_metrics = get_metrics(existing)
        if config.dominance_fn(existing, existing_metrics, label, label_metrics):
            return False # New label is dominated, do not add it

    # Add the new label to the bucket
    bucket.append(label)

    # 1. Sort by score descending (Beam Search heuristic)
    # We want to keep high-scoring labels first.
    bucket.sort(key=lambda l: l.score, reverse=True)

    # 2. Beam Pruning: Keep only top K
    if len(bucket) > MAX_LABELS_PER_STOP:
        del bucket[MAX_LABELS_PER_STOP:]

    # 3. Score Dominance (Soft Pruning)
    # If the best label has score S, discard any label with score < S * 0.8
    # This assumes that a label with significantly lower score is unlikely to catch up.
    if bucket:
        best_score = bucket[0].score
        score_threshold = best_score * 0.8
        bucket[:] = [l for l in bucket if l.score >= score_threshold]

    # 4. Standard Dominance Check (Pareto efficiency within the beam)
    # We still want to remove strictly dominated labels to avoid redundancy.
    # This step is applied to the labels remaining after beam and score pruning.
    final_labels: list[Label] = []
    for candidate in bucket:
        is_dominated = False
        candidate_metrics = get_metrics(candidate) # Use get_metrics as passed to the function
        
        for existing in final_labels:
            existing_metrics = get_metrics(existing) # Use get_metrics
            if config.dominance_fn(existing, existing_metrics, candidate, candidate_metrics):
                is_dominated = True
                break
        
        if not is_dominated:
            final_labels.append(candidate)
    
    bucket[:] = final_labels # Update the original bucket with the filtered labels

    return True




# ---------- Metrics Calculation ----------

def _label_metrics_key(planner: PlannerService, label: Label) -> tuple:
    legs_key = tuple(
        (
            leg.line_id,
            leg.trip_id,
            leg.from_code,
            leg.to_code,
            leg.depart,
            leg.arrive,
        )
        for leg in label.legs
    )
    return (
        label.arrival,
        label.ride_minutes,
        round(label.distance_km, 6),
        label.visited,
        label.quadrant_mask,
        legs_key,
    )


def _label_metrics(planner: PlannerService, label: Label, config: ChallengeConfig | None = None) -> dict[str, float]:
    unique_lines = len({leg.line_id for leg in label.legs})
    unique_stops = len(label.visited)
    quadrants = bin(label.quadrant_mask).count("1")
    stop_counts_map = dict(label.stop_counts)
    stop_repeat_total = sum(max(0, cnt - 1) for cnt in stop_counts_map.values())
    stop_repeat_max = max(stop_counts_map.values()) if stop_counts_map else 0
    total_stops_passed = sum(leg.stop_hops for leg in label.legs)

    visited_coords: list[tuple[float, float]] = []
    distances: list[float] = []
    for code in label.visited:
        station = planner.stations.get(code)
        if not station:
            continue
        visited_coords.append((station.lat, station.lon))
        distances.append(
            calc_distance_km(station.lat, station.lon, *planner.hakata_coord)
        )

    avg_radius = sum(distances) / len(distances) if distances else 0.0
    max_radius = max(distances) if distances else 0.0
    center_visits = sum(1 for d in distances if d < planner.inner_radius_km)
    center_ratio = (center_visits / len(distances)) if distances else 0.0

    # Leg-based metrics
    leg_distances = [leg.distance_km for leg in label.legs]
    avg_leg_distance = sum(leg_distances) / len(leg_distances) if leg_distances else 0.0
    max_leg_distance = max(leg_distances) if leg_distances else 0.0
    
    leg_minutes = [leg.arrive - leg.depart for leg in label.legs]
    max_leg_minutes = max(leg_minutes) if leg_minutes else 0.0

    # Quadrant-based metrics
    max_radius_per_quadrant: dict[int, float] = defaultdict(float)
    for code in label.visited:
        station = planner.stations.get(code)
        quadrant = planner.quadrant_map.get(code)
        if not station or not quadrant:
            continue
        dist = calc_distance_km(station.lat, station.lon, *planner.hakata_coord)
        max_radius_per_quadrant[quadrant] = max(max_radius_per_quadrant[quadrant], dist)

    path_coords: list[tuple[float, float]] = []
    if label.legs:
        first_leg = label.legs[0]
        start_station = planner.stations.get(first_leg.from_code)
        if start_station:
            path_coords.append((start_station.lat, start_station.lon))
        for leg in label.legs:
            station = planner.stations.get(leg.to_code)
            if station:
                path_coords.append((station.lat, station.lon))
    else:
        path_coords.extend(visited_coords)

    hull_area = 0.0
    angle_span = 0.0
    turn_sum = 0.0
    
    # Only calculate expensive geometric metrics for Longest Distance
    if config is None or config.challenge_id == "longest-distance":
        hull_area = _polygon_area(planner, path_coords)
        angle_span, turn_sum = _angle_metrics(planner, path_coords)

    repeat_penalty = max(0, len(label.legs) - unique_lines)
    short_leg_count = sum(1 for leg in label.legs if leg.distance_km < 0.5)
    short_leg_ratio = (short_leg_count / len(label.legs)) if label.legs else 0.0
    
    boundary_hits = 0
    boundary_ratio = 0.0
    boundary_progress = 0.0
    boundary_set = set(planner.boundary_sequence)
    if boundary_set:
        boundary_hits = sum(1 for stop in label.visited if stop in boundary_set)
        boundary_ratio = boundary_hits / max(1, len(boundary_set))
        sequence_indices: list[int] = []
        seen_boundary: set[str] = set()
        for leg in label.legs:
            for code in (leg.from_code, leg.to_code):
                if code in boundary_set and code not in seen_boundary:
                    seen_boundary.add(code)
                    idx = planner.boundary_index.get(code)
                    if idx is not None:
                        sequence_indices.append(idx)
        if sequence_indices:
            sequence_indices.sort()
            coverage = sequence_indices[-1] - sequence_indices[0]
            total = max(1, len(planner.boundary_sequence))
            boundary_progress = min(1.0, coverage / total)

    return {
        "unique_lines": float(unique_lines),
        "unique_stops": float(unique_stops),
        "quadrants": float(quadrants),
        "avg_radius": avg_radius,
        "max_radius": max_radius,
        "center_ratio": center_ratio,
        "hull_area": hull_area,
        "angle_span": angle_span,
        "turn_sum": turn_sum,
        "repeat_penalty": float(repeat_penalty),
        "short_leg_ratio": short_leg_ratio,
        "boundary_hits": float(boundary_hits),
        "boundary_ratio": boundary_ratio,
        "boundary_progress": boundary_progress,
        "stop_repeat_total": float(stop_repeat_total),
        "stop_repeat_max": float(stop_repeat_max),
        "avg_leg_distance": avg_leg_distance,
        "max_leg_distance": max_leg_distance,
        "max_leg_distance": max_leg_distance,
        "max_leg_minutes": float(max_leg_minutes),
        "max_radius_per_quadrant": sum(max_radius_per_quadrant.values()),
        "total_stops_passed": float(total_stops_passed),
    }


def _convex_hull(
    points: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    unique_points = sorted(set(points))
    if len(unique_points) <= 1:
        return unique_points

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[tuple[float, float]] = []
    for p in unique_points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper: list[tuple[float, float]] = []
    for p in reversed(unique_points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


def _polygon_area(planner: PlannerService, coords: list[tuple[float, float]]) -> float:
    points = [
        project_to_plane(lat, lon, *planner.hakata_coord)
        for lat, lon in coords
        if lat and lon
    ]
    hull = _convex_hull(points)
    if len(hull) < 3:
        return 0.0
    area = 0.0
    for i in range(len(hull)):
        x1, y1 = hull[i]
        x2, y2 = hull[(i + 1) % len(hull)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def _angle_metrics(planner: PlannerService, coords: list[tuple[float, float]]) -> tuple[float, float]:
    if len(coords) < 2:
        return 0.0, 0.0
    angles: list[float] = []
    for lat, lon in coords:
        x, y = project_to_plane(lat, lon, *planner.hakata_coord)
        if x == 0.0 and y == 0.0:
            continue
        angle = (math.degrees(math.atan2(x, y)) + 360.0) % 360.0
        angles.append(angle)
    if len(angles) < 2:
        return 0.0, 0.0
    total_turn = 0.0
    for prev, nxt in zip(angles, angles[1:], strict=False):
        diff = (nxt - prev + 180.0) % 360.0 - 180.0
        total_turn += abs(diff)
    sorted_angles = sorted(angles)
    max_gap = 0.0
    for i in range(len(sorted_angles) - 1):
        gap = sorted_angles[i + 1] - sorted_angles[i]
        if gap > max_gap:
            max_gap = gap
    wrap_gap = sorted_angles[0] + 360.0 - sorted_angles[-1]
    if wrap_gap > max_gap:
        max_gap = wrap_gap
    span = 360.0 - max_gap
    return span, total_turn

