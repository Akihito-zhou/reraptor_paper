"""
Adapted baseline inspired by Zhang et al. (2025, TRE).

Original paper context focuses on dynamic preference-based multimodal planning.
This adapted variant keeps the "rolling-horizon + preference adaptation" spirit
under this project's timetable-feasible stop-reward setting.
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.base_algorithm import BaseAlgorithm
from common.config import WALL_CLOCK_LIMIT_SEC
from algorithms.transit_route_ops import build_route, reroute_tail, route_score


class Zhang2025DynamicPrefAdapted(BaseAlgorithm):
    name = "Zhang2025-DynPref (adapted)"
    stochastic = True
    category = "Recent-2024+ (adapted)"

    def solve(self, planner, origin, depart_time, budget_minutes, *, seed=0):
        rng = random.Random(seed)
        time_limit = depart_time + budget_minutes
        deadline = time.perf_counter() + min(45.0, float(WALL_CLOCK_LIMIT_SEC))
        objective = getattr(self, "objective", None)

        current = build_route(
            planner,
            origin=origin,
            depart_time=depart_time,
            time_limit=time_limit,
            rng=rng,
            max_steps=44,
            exploration_rate=0.38,
            objective=objective,
        )
        if not current:
            return []

        best = list(current)
        best_score = self._dynamic_score(best, budget_minutes=budget_minutes)
        no_improve = 0

        while time.perf_counter() < deadline and no_improve < 24:
            utilization = self._utilization(best, budget_minutes=budget_minutes)
            # Early stage: deeper perturbation for exploration.
            # Late stage: shallower perturbation for exploitation.
            if utilization < 0.35:
                cut_low = 0
                cut_high = max(1, len(best) // 2)
                explore = 0.50
            elif utilization < 0.70:
                cut_low = max(0, len(best) // 4)
                cut_high = max(cut_low + 1, int(len(best) * 0.8))
                explore = 0.38
            else:
                cut_low = max(0, len(best) - max(3, len(best) // 4))
                cut_high = max(cut_low + 1, len(best))
                explore = 0.22

            cut = rng.randint(cut_low, cut_high)
            candidate = reroute_tail(
                planner,
                route=best,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                cut_index=cut,
                max_steps=44,
                exploration_rate=explore,
                objective=objective,
            )
            score = self._dynamic_score(candidate, budget_minutes=budget_minutes)

            if score > best_score:
                best = candidate
                best_score = score
                no_improve = 0
            else:
                no_improve += 1

        return best

    def _utilization(self, edges, *, budget_minutes: int) -> float:
        if not edges or budget_minutes <= 0:
            return 0.0
        route_minutes = max(0.0, float(edges[-1].arrive) - float(edges[0].depart))
        return max(0.0, min(1.0, route_minutes / float(budget_minutes)))

    def _dynamic_score(self, edges, *, budget_minutes: int) -> float:
        objective = getattr(self, "objective", None)
        if objective is None:
            return route_score(edges, budget_minutes=budget_minutes)

        metrics = objective.metrics_from_edges(edges, budget_minutes=budget_minutes)
        stop_score_total = float(metrics.get("stop_score_total", 0.0))
        scored_stop_count = float(metrics.get("scored_stop_count", 0.0))
        score_per_hour = float(metrics.get("score_per_hour", 0.0))
        effective_time = float(metrics.get("effective_time_minutes", 0.0))
        overrun = float(metrics.get("effective_budget_overrun_minutes", 0.0))

        utilization = 0.0 if budget_minutes <= 0 else max(0.0, min(1.0, effective_time / float(budget_minutes)))
        diversity_weight = 1.0 - utilization
        efficiency_weight = utilization

        return (
            stop_score_total * 10000.0
            + scored_stop_count * 16.0 * diversity_weight
            + score_per_hour * 8.0 * efficiency_weight
            - effective_time * 0.05
            - overrun * 50000.0
        )

