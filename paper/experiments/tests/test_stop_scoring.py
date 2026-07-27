from __future__ import annotations

from types import SimpleNamespace

import pytest

from paper.experiments.common.base_algorithm import BaseAlgorithm
from paper.experiments.common.stop_scoring import StopScoringProfile


ORIGIN = "O"
QUERY_DEPARTURE = 100


def make_edge(
    from_code: str,
    to_code: str,
    depart: int,
    arrive: int,
    *,
    trip_id: str = "T1",
) -> SimpleNamespace:
    return SimpleNamespace(
        from_code=from_code,
        to_code=to_code,
        depart=depart,
        arrive=arrive,
        trip_id=trip_id,
        line_id="L1",
        ride_minutes=arrive - depart,
        distance_km=1.0,
        from_lat=33.58,
        from_lon=130.40,
        to_lat=33.59,
        to_lon=130.41,
    )


@pytest.fixture
def profile() -> StopScoringProfile:
    # The origin deliberately has a large score so accidental inclusion is obvious.
    return StopScoringProfile(
        stop_scores={ORIGIN: 999, "A": 10, "B": 20},
        dwell_minutes=5,
        search_mode="score_guided",
    )


def score_edges(
    profile: StopScoringProfile,
    edges: list[SimpleNamespace],
    *,
    budget_minutes: int = 60,
) -> dict:
    return profile.metrics_from_edges(
        edges,
        origin_code=ORIGIN,
        query_depart_time=QUERY_DEPARTURE,
        budget_minutes=budget_minutes,
    )


def test_standard_origin_a_b_route(profile: StopScoringProfile) -> None:
    edges = [
        make_edge(ORIGIN, "A", 110, 120),
        make_edge("A", "B", 125, 140),
    ]

    metrics = score_edges(profile, edges, budget_minutes=50)

    assert metrics["stop_score_total"] == 30.0
    assert metrics["scored_stop_count"] == 2
    assert metrics["query_elapsed_minutes"] == 40.0
    assert metrics["dwell_minutes_total"] == 10
    assert metrics["effective_time_minutes"] == 50.0
    assert metrics["effective_budget_feasible"] is True


def test_unique_non_origin_stops_are_scored_once(profile: StopScoringProfile) -> None:
    edges = [
        make_edge(ORIGIN, "A", 110, 120),
        make_edge("A", "B", 125, 135),
        make_edge("B", "A", 140, 150),
    ]

    metrics = score_edges(profile, edges)

    assert metrics["stop_score_total"] == 30.0
    assert metrics["scored_stop_count"] == 2
    assert metrics["dwell_minutes_total"] == 10


def test_return_to_origin_never_scores_or_adds_dwell(profile: StopScoringProfile) -> None:
    edges = [
        make_edge(ORIGIN, "A", 105, 110),
        make_edge("A", ORIGIN, 115, 120),
    ]

    metrics = score_edges(profile, edges)

    assert metrics["stop_score_total"] == 10.0
    assert metrics["scored_stop_count"] == 1
    assert metrics["dwell_minutes_total"] == 5


def test_return_to_origin_reward_does_not_affect_search_priority(
    profile: StopScoringProfile,
) -> None:
    return_edge = make_edge("A", ORIGIN, 115, 120)
    zero_origin_profile = StopScoringProfile(
        stop_scores={ORIGIN: 0, "A": 10, "B": 20},
        dwell_minutes=5,
        search_mode="score_guided",
    )
    kwargs = {
        "edge": return_edge,
        "origin_code": ORIGIN,
        "visits": {ORIGIN: 1, "A": 1},
        "prev_edge": None,
    }

    assert profile.edge_priority(**kwargs) == zero_origin_profile.edge_priority(**kwargs)


def test_initial_waiting_is_included_in_effective_time(profile: StopScoringProfile) -> None:
    edges = [make_edge(ORIGIN, "A", 120, 130)]

    metrics = score_edges(profile, edges)

    assert metrics["query_elapsed_minutes"] == 30.0
    assert metrics["effective_time_minutes"] == 35.0
    assert metrics["score_per_hour"] == pytest.approx(10.0 * 60.0 / 35.0, abs=1e-6)


def test_budget_boundary_is_inclusive(profile: StopScoringProfile) -> None:
    at_limit = [make_edge(ORIGIN, "A", 120, 125)]
    over_limit = [make_edge(ORIGIN, "A", 120, 126)]

    feasible = score_edges(profile, at_limit, budget_minutes=30)
    infeasible = score_edges(profile, over_limit, budget_minutes=30)

    assert feasible["effective_time_minutes"] == 30.0
    assert feasible["effective_budget_feasible"] is True
    assert infeasible["effective_time_minutes"] == 31.0
    assert infeasible["effective_budget_overrun_minutes"] == 1.0
    assert infeasible["effective_budget_feasible"] is False

    assert profile.can_append(
        origin_code=ORIGIN,
        depart_time=QUERY_DEPARTURE,
        arrival_time=125,
        visits={ORIGIN: 1},
        next_stop_code="A",
        budget_minutes=30,
    )
    assert not profile.can_append(
        origin_code=ORIGIN,
        depart_time=QUERY_DEPARTURE,
        arrival_time=126,
        visits={ORIGIN: 1},
        next_stop_code="A",
        budget_minutes=30,
    )


def test_edge_and_label_metrics_use_identical_semantics(profile: StopScoringProfile) -> None:
    edges = [
        make_edge(ORIGIN, "A", 110, 120),
        make_edge("A", ORIGIN, 125, 135),
        make_edge(ORIGIN, "B", 140, 150),
    ]
    label = SimpleNamespace(
        legs=tuple(edges),
        visited=frozenset({ORIGIN, "A", "B"}),
        objective_score_total=30.0,
        objective_scored_count=2,
    )

    edge_metrics = score_edges(profile, edges)
    label_metrics = profile.metrics_from_label(
        label,
        origin_code=ORIGIN,
        query_depart_time=QUERY_DEPARTURE,
        budget_minutes=60,
    )

    assert label_metrics == edge_metrics


def test_reward_time_dominance_is_only_a_heuristic() -> None:
    # Both labels are at the same stop and round. Label A is currently better,
    # but it has already collected H; label B can still collect H next.
    profile_with_future_stop = StopScoringProfile(
        stop_scores={ORIGIN: 0, "H": 100, "L": 1},
        dwell_minutes=0,
        search_mode="score_guided",
    )
    metrics_a = {"stop_score_total": 100.0, "effective_time_minutes": 10.0}
    metrics_b = {"stop_score_total": 1.0, "effective_time_minutes": 20.0}

    assert profile_with_future_stop.dominates(
        score_a=1_000_000.0,
        metrics_a=metrics_a,
        score_b=10_000.0,
        metrics_b=metrics_b,
    )

    final_a = metrics_a["stop_score_total"]  # H is already visited: no new reward.
    final_b = metrics_b["stop_score_total"] + profile_with_future_stop.score_for_stop("H")
    assert final_b > final_a


def test_parameterized_score_guided_defaults_are_exactly_equivalent() -> None:
    metrics = {
        "stop_score_total": 123.0,
        "scored_stop_count": 4,
        "effective_time_minutes": 217.0,
        "effective_budget_overrun_minutes": 3.0,
        "score_per_hour": 34.009,
    }
    default_profile = StopScoringProfile(
        stop_scores={},
        search_mode="score_guided",
    )
    explicit_profile = StopScoringProfile(
        stop_scores={},
        search_mode="score_guided",
        reward_coefficient=10000.0,
        score_per_hour_coefficient=5.0,
        effective_time_coefficient=0.1,
        overrun_penalty=50000.0,
    )

    expected = round(123.0 * 10000.0 + 34.009 * 5.0 - 217.0 * 0.1 - 3.0 * 50000.0, 6)
    assert default_profile.search_score_from_metrics(metrics) == expected
    assert explicit_profile.search_score_from_metrics(metrics) == expected


def test_parameterized_score_guided_coefficients_change_only_declared_terms() -> None:
    metrics = {
        "stop_score_total": 10.0,
        "effective_time_minutes": 20.0,
        "effective_budget_overrun_minutes": 2.0,
        "score_per_hour": 30.0,
    }
    profile = StopScoringProfile(
        stop_scores={},
        search_mode="score_guided",
        reward_coefficient=5000.0,
        score_per_hour_coefficient=2.5,
        effective_time_coefficient=0.2,
        overrun_penalty=25000.0,
    )

    assert profile.search_score_from_metrics(metrics) == round(
        10.0 * 5000.0 + 30.0 * 2.5 - 20.0 * 0.2 - 2.0 * 25000.0,
        6,
    )


class FixedRouteAlgorithm(BaseAlgorithm):
    name = "fixed-route-test"

    def __init__(self, route: list[SimpleNamespace], objective: StopScoringProfile):
        self.route = route
        self.objective = objective

    def solve(
        self,
        planner,
        origin: str,
        depart_time: int,
        budget_minutes: int,
        *,
        seed: int = 0,
    ) -> list[SimpleNamespace]:
        self._set_query_context(origin=origin, depart_time=depart_time)
        return list(self.route)


def make_planner() -> SimpleNamespace:
    return SimpleNamespace(stations={ORIGIN: object(), "A": object(), "B": object()})


def test_empty_route_is_an_algorithm_failure_not_query_infeasibility(
    profile: StopScoringProfile,
) -> None:
    row = FixedRouteAlgorithm([], profile).evaluate(
        make_planner(),
        ORIGIN,
        QUERY_DEPARTURE,
        30,
    )

    assert row["feasible"] is False
    assert row["violation_reason"] == "empty_route"
    assert row["raw_violation_reason"] == "empty_route"
    assert row["algorithm_failure"] is True
    assert row["query_infeasible_proven"] is False
    assert row["objective_metrics_valid"] is False
    assert row["effective_budget_feasible"] is False
    assert row["stop_score_total"] == 0.0
    assert row["effective_time_minutes"] == 0.0


def test_post_check_failure_clears_metrics_and_keeps_raw_diagnostics(
    profile: StopScoringProfile,
) -> None:
    # Structurally within 30 minutes, but 29 elapsed + 5 dwell exceeds the budget.
    route = [make_edge(ORIGIN, "A", 100, 129)]
    row = FixedRouteAlgorithm(route, profile).evaluate(
        make_planner(),
        ORIGIN,
        QUERY_DEPARTURE,
        30,
    )

    assert row["feasible"] is False
    assert row["violation_reason"] == "effective_budget_exceeded"
    assert row["raw_violation_reason"] == "effective_budget_exceeded"
    assert row["algorithm_failure"] is True
    assert row["objective_metrics_valid"] is False
    assert row["stop_score_total"] == 0.0
    assert row["scored_stop_count"] == 0
    assert row["dwell_minutes_total"] == 0
    assert row["effective_time_minutes"] == 0.0
    assert row["effective_budget_overrun_minutes"] == 0.0
    assert row["raw_stop_score_total"] == 10.0
    assert row["raw_dwell_minutes_total"] == 5
    assert row["raw_effective_time_minutes"] == 34.0
    assert row["raw_effective_budget_overrun_minutes"] == 4.0
