"""
Stop-score objective helpers for Experiment 1.

The new main task is to maximize the total score collected from visited stops
within a fixed time budget. Scores are assigned once per unique stop.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Iterable


def build_random_stop_score_map(
    planner: Any,
    *,
    seed: int,
    score_min: int,
    score_max: int,
) -> dict[str, int]:
    rng = random.Random(seed)
    codes = sorted(str(code) for code in getattr(planner, "stations", {}).keys())
    return {
        code: int(rng.randint(int(score_min), int(score_max)))
        for code in codes
    }


def _unique_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        key = str(item)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    return ordered


@dataclass(frozen=True)
class StopScoringProfile:
    stop_scores: dict[str, int]
    dwell_minutes: int = 0
    search_mode: str = "score_guided"
    reward_coefficient: float = 10000.0
    score_per_hour_coefficient: float = 5.0
    effective_time_coefficient: float = 0.1
    overrun_penalty: float = 50000.0

    @cached_property
    def _sorted_scores_desc(self) -> tuple[float, ...]:
        return tuple(sorted((float(v) for v in self.stop_scores.values()), reverse=True))

    @cached_property
    def _score_ranked_stop_entries(self) -> tuple[tuple[str, float], ...]:
        return tuple(
            sorted(
                ((str(code), float(score)) for code, score in self.stop_scores.items()),
                key=lambda item: item[1],
                reverse=True,
            )
        )

    @cached_property
    def _prefix_score_sums(self) -> tuple[float, ...]:
        prefix = [0.0]
        running = 0.0
        for score in self._sorted_scores_desc:
            running += float(score)
            prefix.append(running)
        return tuple(prefix)

    def zero_metrics(self) -> dict[str, float | int | bool]:
        return {
            "stop_score_total": 0.0,
            "scored_stop_count": 0,
            "dwell_minutes_total": 0,
            "query_elapsed_minutes": 0.0,
            "effective_time_minutes": 0.0,
            "effective_budget_overrun_minutes": 0.0,
            "effective_budget_feasible": True,
            "score_per_hour": 0.0,
        }

    def score_for_stop(self, stop_code: Any) -> float:
        return float(self.stop_scores.get(str(stop_code), 0))

    def _prefix_sum_top_scores(self, count: int) -> float:
        safe = max(0, min(int(count), len(self._sorted_scores_desc)))
        return float(self._prefix_score_sums[safe])

    def max_additional_stop_capacity(
        self,
        *,
        budget_minutes: int,
        min_leg_minutes: float = 0.0,
    ) -> int:
        return self.optimistic_additional_stop_capacity(
            effective_time_minutes=0.0,
            budget_minutes=budget_minutes,
            scored_stop_count=0,
            min_leg_minutes=min_leg_minutes,
        )

    def _metrics_from_stop_codes(
        self,
        stop_codes: Iterable[Any],
        *,
        origin_code: str,
        query_elapsed_minutes: float,
        budget_minutes: int | None = None,
    ) -> dict[str, float | int | bool]:
        origin = str(origin_code)
        unique_stops = _unique_preserve_order(
            str(code) for code in stop_codes if str(code) != origin
        )
        stop_score_total = float(sum(self.score_for_stop(code) for code in unique_stops))
        scored_stop_count = int(len(unique_stops))
        dwell_total = int(self.dwell_minutes * scored_stop_count)
        elapsed = float(max(0.0, query_elapsed_minutes))
        effective_time = float(elapsed + dwell_total)
        overrun = float(max(0.0, effective_time - float(budget_minutes))) if budget_minutes is not None else 0.0
        feasible = overrun <= 1e-9
        score_per_hour = (stop_score_total * 60.0 / effective_time) if effective_time > 0 else 0.0
        return {
            "stop_score_total": round(stop_score_total, 6),
            "scored_stop_count": scored_stop_count,
            "dwell_minutes_total": dwell_total,
            "query_elapsed_minutes": round(elapsed, 6),
            "effective_time_minutes": round(effective_time, 6),
            "effective_budget_overrun_minutes": round(overrun, 6),
            "effective_budget_feasible": feasible,
            "score_per_hour": round(score_per_hour, 6),
        }

    def metrics_from_edges(
        self,
        path_edges: list[Any],
        *,
        origin_code: str,
        query_depart_time: int,
        budget_minutes: int | None = None,
    ) -> dict[str, float | int | bool]:
        if not path_edges:
            return self.zero_metrics()
        stop_codes = [str(edge.to_code) for edge in path_edges]
        query_elapsed_minutes = float(
            max(0, int(path_edges[-1].arrive) - int(query_depart_time))
        )
        return self._metrics_from_stop_codes(
            stop_codes,
            origin_code=origin_code,
            query_elapsed_minutes=query_elapsed_minutes,
            budget_minutes=budget_minutes,
        )

    def metrics_from_label(
        self,
        label: Any,
        *,
        origin_code: str,
        query_depart_time: int,
        budget_minutes: int | None = None,
    ) -> dict[str, float | int | bool]:
        legs = list(getattr(label, "legs", ()) or ())
        if not legs:
            return self.zero_metrics()
        query_elapsed_minutes = float(
            max(0, int(legs[-1].arrive) - int(query_depart_time))
        )
        return self._metrics_from_stop_codes(
            (str(leg.to_code) for leg in legs),
            origin_code=origin_code,
            query_elapsed_minutes=query_elapsed_minutes,
            budget_minutes=budget_minutes,
        )

    def can_append(
        self,
        *,
        origin_code: str,
        depart_time: int,
        arrival_time: int,
        visits: dict[str, int],
        next_stop_code: str,
        budget_minutes: int,
    ) -> bool:
        scored_stop_count = len(visits) - (1 if origin_code in visits else 0)
        if next_stop_code != origin_code and next_stop_code not in visits:
            scored_stop_count += 1
        dwell_total = int(self.dwell_minutes * max(0, scored_stop_count))
        total_time_minutes = float(max(0, int(arrival_time) - int(depart_time)))
        effective_time = total_time_minutes + dwell_total
        return effective_time <= float(budget_minutes)

    def optimistic_additional_stop_capacity(
        self,
        *,
        effective_time_minutes: float,
        budget_minutes: int,
        scored_stop_count: int,
        min_leg_minutes: float = 0.0,
    ) -> int:
        remaining = max(0.0, float(budget_minutes) - float(effective_time_minutes))
        per_new_stop = max(0.0, float(self.dwell_minutes)) + max(0.0, float(min_leg_minutes))
        if per_new_stop <= 1e-9:
            capacity = len(self._sorted_scores_desc)
        else:
            capacity = int(remaining // per_new_stop)
        remaining_unvisited = max(0, len(self._sorted_scores_desc) - max(0, int(scored_stop_count)))
        return max(0, min(capacity, remaining_unvisited))

    def optimistic_total_upper_bound(
        self,
        *,
        stop_score_total: float,
        scored_stop_count: int,
        effective_time_minutes: float,
        budget_minutes: int,
        min_leg_minutes: float = 0.0,
    ) -> float:
        current_total = float(stop_score_total)
        current_count = max(0, int(scored_stop_count))
        extra_capacity = self.optimistic_additional_stop_capacity(
            effective_time_minutes=effective_time_minutes,
            budget_minutes=budget_minutes,
            scored_stop_count=current_count,
            min_leg_minutes=min_leg_minutes,
        )
        total_by_extra = current_total + self._prefix_sum_top_scores(extra_capacity)
        total_by_count = self._prefix_sum_top_scores(current_count + extra_capacity)
        return round(min(total_by_extra, total_by_count), 6)

    def optimistic_total_upper_bound_from_metrics(
        self,
        metrics: dict[str, Any],
        *,
        budget_minutes: int,
        min_leg_minutes: float = 0.0,
    ) -> float:
        return self.optimistic_total_upper_bound(
            stop_score_total=float(metrics.get("stop_score_total", 0.0)),
            scored_stop_count=int(metrics.get("scored_stop_count", metrics.get("unique_stops", 0)) or 0),
            effective_time_minutes=float(metrics.get("effective_time_minutes", metrics.get("total_time_minutes", 0.0))),
            budget_minutes=budget_minutes,
            min_leg_minutes=min_leg_minutes,
        )

    def search_score_from_metrics(self, metrics: dict[str, Any]) -> float:
        stop_score_total = float(metrics.get("stop_score_total", 0.0))
        scored_stop_count = float(metrics.get("scored_stop_count", metrics.get("unique_stops", 0.0)))
        effective_time = float(metrics.get("effective_time_minutes", metrics.get("total_time_minutes", 0.0)))
        overrun = float(metrics.get("effective_budget_overrun_minutes", 0.0))
        score_per_hour = float(metrics.get("score_per_hour", 0.0))
        if self.search_mode == "score_guided":
            # Primary objective: maximize collected stop score under the budget.
            # Time-related terms are only tie-breakers so they never outweigh
            # even a small gain in total collected score.
            return round(
                stop_score_total * float(self.reward_coefficient)
                + score_per_hour * float(self.score_per_hour_coefficient)
                - effective_time * float(self.effective_time_coefficient)
                - overrun * float(self.overrun_penalty),
                6,
            )
        return round(
            stop_score_total * 70.0
            + score_per_hour * 120.0
            + scored_stop_count * 6.0
            - effective_time * 2.0
            - overrun * 5000.0,
            6,
        )

    def search_score_from_edges(
        self,
        path_edges: list[Any],
        *,
        origin_code: str,
        query_depart_time: int,
        budget_minutes: int | None = None,
    ) -> float:
        metrics = self.metrics_from_edges(
            path_edges,
            origin_code=origin_code,
            query_depart_time=query_depart_time,
            budget_minutes=budget_minutes,
        )
        return self.search_score_from_metrics(metrics)

    def objective_vector_from_edges(
        self,
        path_edges: list[Any],
        *,
        origin_code: str,
        query_depart_time: int,
        budget_minutes: int | None = None,
    ) -> tuple[float, float, float]:
        metrics = self.metrics_from_edges(
            path_edges,
            origin_code=origin_code,
            query_depart_time=query_depart_time,
            budget_minutes=budget_minutes,
        )
        if self.search_mode == "score_guided":
            return (
                float(metrics.get("stop_score_total", 0.0)),
                -float(metrics.get("effective_time_minutes", metrics.get("total_time_minutes", 0.0))),
                float(metrics.get("score_per_hour", 0.0)),
            )
        return (
            float(metrics.get("stop_score_total", 0.0)),
            float(metrics.get("score_per_hour", 0.0)),
            float(metrics.get("scored_stop_count", 0.0)),
        )

    def edge_priority(
        self,
        *,
        edge: Any,
        origin_code: str,
        visits: dict[str, int],
        prev_edge: Any | None,
    ) -> float:
        if self.search_mode == "score_guided":
            destination = str(getattr(edge, "to_code", ""))
            raw_score = 0.0 if destination == str(origin_code) else self.score_for_stop(destination)
            seen = int(visits.get(str(getattr(edge, "to_code", "")), 0))
            ride_minutes = float(max(0, int(edge.arrive) - int(edge.depart)))
            effective_cost = max(1.0, ride_minutes + float(self.dwell_minutes))
            score = raw_score * (0.15 if seen > 0 else 1.0)
            score += (raw_score / effective_cost) * 25.0
            score -= effective_cost * 0.05
            if prev_edge is not None and edge.trip_id == prev_edge.trip_id and edge.line_id == prev_edge.line_id:
                score += 2.0
            return float(score)
        destination = str(getattr(edge, "to_code", ""))
        score = 0.0 if destination == str(origin_code) else self.score_for_stop(destination)
        seen = int(visits.get(str(getattr(edge, "to_code", "")), 0))
        if seen > 0:
            score *= 0.25
        score += float(max(0, int(edge.arrive) - int(edge.depart))) * 0.1
        score += min(4.0, max(0.0, float(getattr(edge, "distance_km", 0.0))) * 0.4)
        if prev_edge is not None and edge.trip_id == prev_edge.trip_id and edge.line_id == prev_edge.line_id:
            score += 2.0
        return float(score)

    def dominates(
        self,
        *,
        score_a: float,
        metrics_a: dict[str, Any],
        score_b: float,
        metrics_b: dict[str, Any],
    ) -> bool:
        """Heuristic reward-time reduction predicate.

        This is intentionally not described as exact Pareto dominance: the
        scalar metrics do not encode the visited-stop set or the previous-trip
        continuation state, both of which can change future feasible rewards.
        Optional upper-bound fields make the predicate more selective but do
        not turn it into a proof-safe dominance rule.
        """
        a_total = float(metrics_a.get("stop_score_total", 0.0))
        b_total = float(metrics_b.get("stop_score_total", 0.0))
        a_time = float(metrics_a.get("effective_time_minutes", metrics_a.get("total_time_minutes", 0.0)))
        b_time = float(metrics_b.get("effective_time_minutes", metrics_b.get("total_time_minutes", 0.0)))
        a_upper = float(metrics_a.get("score_upper_bound_total", a_total))
        b_upper = float(metrics_b.get("score_upper_bound_total", b_total))
        better_or_equal = a_total >= b_total and a_time <= b_time and a_upper >= b_upper
        strictly_better = (
            a_total > b_total
            or a_time < b_time
            or a_upper > b_upper
            or score_a > score_b
        )
        return bool(better_or_equal and strictly_better)
