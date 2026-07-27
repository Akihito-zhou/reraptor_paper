"""
Abstract base class for all baseline algorithms.

Every algorithm module in algorithms/ must subclass BaseAlgorithm and
implement the `solve()` method.  The `evaluate()` method is inherited and
provides standardised timing + metric computation.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .config import TRANSFER_BUFFER_MINUTES
from .utils import compute_route_metrics, composite_score
from .io_utils import format_result_row

if TYPE_CHECKING:
    from .config import SCORE_WEIGHTS


class BaseAlgorithm(ABC):
    """
    Interface that all algorithms must implement.

    Subclasses define:
        - name (str): Identifier e.g. "ILS+2opt"
        - category (str): Grouping e.g. "PC-TSP主流"
        - solve(): Returns a list of TripEdge

    The inherited evaluate() method calls solve(), measures wall-clock
    time, computes metrics, and returns a standardised result dict.
    """

    name: str = "unnamed"
    category: str = "unknown"
    stochastic: bool = False

    @abstractmethod
    def solve(
        self,
        planner,
        origin: str,
        depart_time: int,
        budget_minutes: int,
        *,
        seed: int = 0,
    ) -> list:
        """
        Run the algorithm and return a route.

        Parameters
        ----------
        planner : PlannerService
            Fully initialised planner with GTFS data loaded.
        origin : str
            GTFS stop code for the starting point.
        depart_time : int
            Departure time in minutes since midnight.
        budget_minutes : int
            Maximum time budget in minutes.
        seed : int
            Random seed for reproducibility (relevant for stochastic methods).

        Returns
        -------
        list[TripEdge]
            Ordered list of trip edges forming the route.
            Return an empty list if the algorithm fails to construct a route.
            This does not establish that the query itself is infeasible.
        """
        ...

    def evaluate(
        self,
        planner,
        origin: str,
        depart_time: int,
        budget_minutes: int,
        *,
        seed: int = 0,
        score_weights: dict[str, float] | None = None,
    ) -> dict:
        """
        Run solve() with timing and compute all metrics.

        Returns a standardised result dict ready for JSON serialisation.
        """
        self._set_query_context(origin=origin, depart_time=depart_time)
        t0 = time.perf_counter()
        path_edges = self.solve(
            planner, origin, depart_time, budget_minutes, seed=seed,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000

        is_feasible, violation_reason = self._validate_path_edges(
            path_edges=path_edges,
            planner=planner,
            origin=origin,
            depart_time=depart_time,
            budget_minutes=budget_minutes,
        )

        if not is_feasible:
            metrics = self._invalid_result_metrics(
                violation_reason=violation_reason,
                origin=origin,
                depart_time=depart_time,
                budget_minutes=budget_minutes,
            )
            metrics["raw_route_edge_count"] = int(len(path_edges))
        else:
            metrics = compute_route_metrics(path_edges, planner)
            metrics["composite_score"] = composite_score(metrics, score_weights)
            metrics["feasible"] = True
            metrics["violation_reason"] = ""
            metrics["raw_violation_reason"] = ""
            metrics["algorithm_failure"] = False
            metrics["query_infeasible_proven"] = False
            metrics["objective_metrics_valid"] = True
            metrics.update(self._objective_metrics(
                path_edges,
                origin=origin,
                depart_time=depart_time,
                budget_minutes=budget_minutes,
            ))
            if metrics.get("effective_budget_feasible") is False:
                raw_metrics = {
                    f"raw_{key}": value
                    for key, value in metrics.items()
                    if key not in {
                        "feasible",
                        "violation_reason",
                        "raw_violation_reason",
                        "algorithm_failure",
                        "query_infeasible_proven",
                        "objective_metrics_valid",
                    }
                }
                metrics = self._invalid_result_metrics(
                    violation_reason="effective_budget_exceeded",
                    origin=origin,
                    depart_time=depart_time,
                    budget_minutes=budget_minutes,
                )
                metrics.update(raw_metrics)

        return format_result_row(
            algorithm=self.name,
            origin=origin,
            depart_time=depart_time,
            budget=budget_minutes,
            seed=seed,
            elapsed_ms=elapsed_ms,
            metrics=metrics,
        )

    def _objective_metrics(
        self,
        path_edges: list,
        *,
        origin: str,
        depart_time: int,
        budget_minutes: int,
    ) -> dict:
        objective = getattr(self, "objective", None)
        if objective is None:
            return {}
        return objective.metrics_from_edges(
            path_edges,
            origin_code=origin,
            query_depart_time=depart_time,
            budget_minutes=budget_minutes,
        )

    def _set_query_context(self, *, origin: str, depart_time: int) -> None:
        """Store the active query for internal scoring during solve()."""
        self._active_origin_code = str(origin)
        self._active_query_depart_time = int(depart_time)

    def _query_context(self) -> tuple[str, int]:
        try:
            return self._active_origin_code, self._active_query_depart_time
        except AttributeError as exc:
            raise RuntimeError(
                "Scoring requires an active query context; call solve() or evaluate() first."
            ) from exc

    def _invalid_result_metrics(
        self,
        *,
        violation_reason: str,
        origin: str,
        depart_time: int,
        budget_minutes: int,
    ) -> dict:
        """Return clean zero metrics for an invalid algorithm output."""
        metrics = {
            "ride_minutes": 0,
            "distance_km": 0.0,
            "unique_stops": 0,
            "legs": 0,
            "hull_area": 0.0,
            "quadrant_coverage": 0,
            "total_time_minutes": 0,
            "composite_score": 0.0,
            "feasible": False,
            "violation_reason": str(violation_reason),
            "raw_violation_reason": str(violation_reason),
            "algorithm_failure": True,
            "query_infeasible_proven": False,
            "objective_metrics_valid": False,
        }
        objective_metrics = self._objective_metrics(
            [],
            origin=origin,
            depart_time=depart_time,
            budget_minutes=budget_minutes,
        )
        if objective_metrics:
            objective_metrics["effective_budget_feasible"] = False
        metrics.update(objective_metrics)
        return metrics

    def _validate_path_edges(
        self,
        *,
        path_edges: list,
        planner,
        origin: str,
        depart_time: int,
        budget_minutes: int,
    ) -> tuple[bool, str]:
        """
        Validate hard constraints for experiment fairness.

        Constraints:
        1. Non-empty route.
        2. Route starts from requested origin and not before requested departure.
        3. Temporal monotonicity and stop continuity for every adjacent edge.
        4. Transfer buffer for trip changes is respected.
        5. Route end time does not exceed query budget.
        6. Edge endpoints exist in loaded station data.
        """
        if not path_edges:
            return False, "empty_route"

        first_edge = path_edges[0]
        if first_edge.from_code != origin:
            return False, "origin_mismatch"
        if first_edge.depart < depart_time:
            return False, "depart_before_query"

        for idx, edge in enumerate(path_edges):
            if edge.arrive <= edge.depart:
                return False, "non_positive_edge_duration"
            if edge.from_code not in planner.stations or edge.to_code not in planner.stations:
                return False, "unknown_stop_code"

            if idx == 0:
                continue

            prev_edge = path_edges[idx - 1]
            if prev_edge.to_code != edge.from_code:
                return False, "teleportation"
            same_trip = (
                edge.trip_id == prev_edge.trip_id
                and edge.line_id == prev_edge.line_id
            )
            earliest_depart = (
                prev_edge.arrive
                if same_trip
                else prev_edge.arrive + TRANSFER_BUFFER_MINUTES
            )
            if edge.depart < earliest_depart:
                if same_trip:
                    return False, "time_travel"
                return False, "transfer_buffer_violation"

        if path_edges[-1].arrive > depart_time + budget_minutes:
            return False, "budget_exceeded"

        return True, ""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} category={self.category!r}>"
