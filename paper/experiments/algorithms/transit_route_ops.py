"""
Transit-route operators for timetable-feasible metaheuristics.

This module provides reusable helpers so baseline algorithms always generate
routes that respect:
1) stop continuity
2) temporal monotonicity
3) transfer buffer (except same-trip continuation)
4) global time budget
"""
from __future__ import annotations

import math
from typing import Any

from common.config import TRANSFER_BUFFER_MINUTES


def edge_signature(edge: Any) -> tuple:
    """Build a stable edge signature for caching / deduplication."""
    return (
        edge.trip_id,
        edge.line_id,
        edge.from_code,
        edge.to_code,
        int(edge.depart),
        int(edge.arrive),
    )


def route_signature(edges: list[Any]) -> tuple:
    """Build a stable route signature from edge signatures."""
    return tuple(edge_signature(e) for e in edges)


def route_score(
    edges: list[Any],
    *,
    objective: Any | None = None,
    budget_minutes: int | None = None,
) -> float:
    """
    Lightweight scalar score for local search.

    Not used as the final paper metric; only for internal search guidance.
    """
    if objective is not None:
        return float(objective.search_score_from_edges(edges, budget_minutes=budget_minutes))
    if not edges:
        return 0.0
    ride = sum(max(0, e.arrive - e.depart) for e in edges)
    stops = {edges[0].from_code}
    for edge in edges:
        stops.add(edge.to_code)
    return float(ride + len(stops) * 6)


def is_feasible_route(
    edges: list[Any],
    *,
    origin: str,
    depart_time: int,
    time_limit: int,
) -> bool:
    """Strict feasibility check with transfer-buffer handling."""
    if not edges:
        return False
    if edges[0].from_code != origin:
        return False
    if edges[0].depart < depart_time:
        return False

    prev = None
    for edge in edges:
        if edge.arrive <= edge.depart:
            return False
        if edge.arrive > time_limit:
            return False

        if prev is not None:
            if prev.to_code != edge.from_code:
                return False
            same_trip = edge.trip_id == prev.trip_id and edge.line_id == prev.line_id
            earliest = prev.arrive if same_trip else prev.arrive + TRANSFER_BUFFER_MINUTES
            if edge.depart < earliest:
                return False
        prev = edge
    return True


def normalize_route(
    edges: list[Any],
    *,
    origin: str,
    depart_time: int,
    time_limit: int,
) -> list[Any]:
    """
    Keep the longest feasible subsequence while preserving order.

    This is used after perturbation/crossover to ensure every individual remains
    timetable-feasible before evaluation.
    """
    if not edges:
        return []

    cleaned: list[Any] = []
    current_stop = origin
    current_time = depart_time
    prev = None

    for edge in edges:
        if edge.from_code != current_stop:
            continue
        if edge.arrive <= edge.depart:
            continue

        same_trip = prev is not None and edge.trip_id == prev.trip_id and edge.line_id == prev.line_id
        earliest = current_time if (prev is None or same_trip) else current_time + TRANSFER_BUFFER_MINUTES
        if edge.depart < earliest:
            continue
        if edge.arrive > time_limit:
            continue

        cleaned.append(edge)
        prev = edge
        current_stop = edge.to_code
        current_time = edge.arrive

    return cleaned


def derive_route_state(
    edges: list[Any],
    *,
    origin: str,
    depart_time: int,
) -> tuple[str, int, Any | None, dict[str, int]]:
    """Return current stop/time/previous edge and stop-visit counts."""
    current_stop = origin
    current_time = depart_time
    prev = None
    visits: dict[str, int] = {origin: 1}

    for edge in edges:
        current_stop = edge.to_code
        current_time = edge.arrive
        prev = edge
        visits[edge.to_code] = visits.get(edge.to_code, 0) + 1

    return current_stop, current_time, prev, visits


def next_feasible_edges(
    planner: Any,
    *,
    origin_code: str,
    current_stop: str,
    current_time: int,
    prev_edge: Any | None,
    time_limit: int,
    lookahead_minutes: int = 90,
    max_candidates: int = 20,
    objective: Any | None = None,
    route_depart_time: int | None = None,
    visits: dict[str, int] | None = None,
) -> list[Any]:
    """Fetch feasible outgoing edges under transfer and budget constraints."""
    raw = planner._next_edges(current_stop, current_time, lookahead_minutes=lookahead_minutes)
    out: list[Any] = []
    for edge in raw:
        if edge.from_code != current_stop:
            continue
        if edge.arrive > time_limit:
            break
        same_trip = (
            prev_edge is not None
            and edge.trip_id == prev_edge.trip_id
            and edge.line_id == prev_edge.line_id
        )
        earliest = current_time if (prev_edge is None or same_trip) else current_time + TRANSFER_BUFFER_MINUTES
        if edge.depart < earliest:
            continue
        if (
            objective is not None
            and route_depart_time is not None
            and visits is not None
            and not objective.can_append(
                origin_code=origin_code,
                depart_time=route_depart_time,
                arrival_time=edge.arrive,
                visits=visits,
                next_stop_code=edge.to_code,
                budget_minutes=time_limit - route_depart_time,
            )
        ):
            continue
        out.append(edge)
        if len(out) >= max_candidates:
            break
    return out


def _edge_priority(
    edge: Any,
    visits: dict[str, int],
    prev_edge: Any | None,
    *,
    objective: Any | None = None,
) -> float:
    """Heuristic for choosing expansion edges."""
    if objective is not None:
        return float(objective.edge_priority(edge=edge, visits=visits, prev_edge=prev_edge))
    score = float(max(0, edge.arrive - edge.depart))
    score += min(6.0, max(0.0, float(edge.distance_km)) * 0.8)

    seen = visits.get(edge.to_code, 0)
    if seen == 0:
        score += 12.0
    else:
        score -= min(10.0, 3.0 * seen)

    if prev_edge is not None and edge.trip_id == prev_edge.trip_id and edge.line_id == prev_edge.line_id:
        score += 3.0
    return score


def choose_edge(
    candidates: list[Any],
    *,
    visits: dict[str, int],
    prev_edge: Any | None,
    rng: Any,
    objective: Any | None = None,
    exploration_rate: float = 0.25,
    top_k: int = 6,
) -> Any:
    """Choose one edge from candidates with exploration/exploitation trade-off."""
    ranked = sorted(
        ((edge, _edge_priority(edge, visits, prev_edge, objective=objective)) for edge in candidates),
        key=lambda item: item[1],
        reverse=True,
    )
    pool = ranked[: max(1, min(top_k, len(ranked)))]
    if len(pool) == 1:
        return pool[0][0]

    if rng.random() < exploration_rate:
        return rng.choice([edge for edge, _ in pool])

    # Softmax over top candidates for stable but non-deterministic choice
    max_s = pool[0][1]
    weights = [math.exp((score - max_s) / 4.0) for _, score in pool]
    total = sum(weights)
    r = rng.random() * total
    acc = 0.0
    for (edge, _), w in zip(pool, weights, strict=False):
        acc += w
        if acc >= r:
            return edge
    return pool[-1][0]


def build_route(
    planner: Any,
    *,
    origin: str,
    depart_time: int,
    time_limit: int,
    rng: Any,
    seed_edges: list[Any] | None = None,
    max_steps: int = 40,
    lookahead_minutes: int = 90,
    max_candidates: int = 20,
    exploration_rate: float = 0.25,
    objective: Any | None = None,
) -> list[Any]:
    """Construct a feasible route by expanding from an optional feasible seed."""
    route = normalize_route(
        list(seed_edges or []),
        origin=origin,
        depart_time=depart_time,
        time_limit=time_limit,
    )
    current_stop, current_time, prev_edge, visits = derive_route_state(
        route,
        origin=origin,
        depart_time=depart_time,
    )

    while current_time < time_limit and len(route) < max_steps:
        candidates = next_feasible_edges(
            planner,
            origin_code=origin,
            current_stop=current_stop,
            current_time=current_time,
            prev_edge=prev_edge,
            time_limit=time_limit,
            lookahead_minutes=lookahead_minutes,
            max_candidates=max_candidates,
            objective=objective,
            route_depart_time=depart_time,
            visits=visits,
        )
        if not candidates:
            break
        chosen = choose_edge(
            candidates,
            visits=visits,
            prev_edge=prev_edge,
            rng=rng,
            objective=objective,
            exploration_rate=exploration_rate,
        )
        route.append(chosen)
        prev_edge = chosen
        current_stop = chosen.to_code
        current_time = chosen.arrive
        visits[current_stop] = visits.get(current_stop, 0) + 1

    return route


def reroute_tail(
    planner: Any,
    *,
    route: list[Any],
    origin: str,
    depart_time: int,
    time_limit: int,
    rng: Any,
    cut_index: int | None = None,
    max_steps: int = 40,
    lookahead_minutes: int = 90,
    max_candidates: int = 20,
    exploration_rate: float = 0.3,
    objective: Any | None = None,
) -> list[Any]:
    """
    Remove route tail at cut index and regrow a feasible continuation.

    This acts as a timetable-feasible neighbourhood operator.
    """
    cleaned = normalize_route(
        route,
        origin=origin,
        depart_time=depart_time,
        time_limit=time_limit,
    )
    n = len(cleaned)
    if cut_index is None:
        cut_index = 0 if n == 0 else rng.randint(0, n)
    cut_index = max(0, min(cut_index, n))
    seed = cleaned[:cut_index]

    return build_route(
        planner,
        origin=origin,
        depart_time=depart_time,
        time_limit=time_limit,
        rng=rng,
        seed_edges=seed,
        max_steps=max_steps,
        lookahead_minutes=lookahead_minutes,
        max_candidates=max_candidates,
        exploration_rate=exploration_rate,
        objective=objective,
    )
