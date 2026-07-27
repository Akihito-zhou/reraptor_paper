from __future__ import annotations

from apps.api.services.planner_models import StopSchedule, TripEdge


def make_edge(*, line_id: str, trip_id: str, arrive: int, to_code: str) -> TripEdge:
    return TripEdge(
        line_id=line_id,
        line_name=line_id,
        trip_id=trip_id,
        direction="outbound",
        service_date="2026-07-21",
        from_code="O",
        from_name="Origin",
        to_code=to_code,
        to_name=to_code,
        depart=420,
        arrive=arrive,
        distance_km=1.0,
        from_lat=33.58,
        from_lon=130.40,
        to_lat=33.59,
        to_lon=130.41,
    )


def finalized_signatures(edges: list[TripEdge]) -> list[tuple[str, str, int, str]]:
    schedule = StopSchedule()
    for edge in edges:
        schedule.add_edge(edge)
    schedule.finalize()
    return [
        (edge.line_id, edge.trip_id, edge.arrive, edge.to_code)
        for edge in schedule.edges
    ]


def test_equal_departure_edges_have_insertion_independent_order() -> None:
    edges = [
        make_edge(line_id="L2", trip_id="T2", arrive=435, to_code="B"),
        make_edge(line_id="L1", trip_id="T3", arrive=430, to_code="C"),
        make_edge(line_id="L1", trip_id="T1", arrive=430, to_code="A"),
    ]

    forward = finalized_signatures(edges)
    reverse = finalized_signatures(list(reversed(edges)))

    assert forward == reverse
    assert forward == [
        ("L1", "T1", 430, "A"),
        ("L1", "T3", 430, "C"),
        ("L2", "T2", 435, "B"),
    ]
