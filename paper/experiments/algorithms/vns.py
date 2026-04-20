"""
VNS baseline adapted to timetable-feasible transit routing.

Neighbourhood moves are implemented via feasible tail rerouting with
different cut-depth patterns.
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


class VNS(BaseAlgorithm):
    name = "VNS"
    stochastic = True
    category = "TSP-TB涓绘祦"

    def __init__(self, k_max: int = 4):
        self.k_max = k_max

    def solve(self, planner, origin, depart_time, budget_minutes, *, seed=0):
        rng = random.Random(seed)
        time_limit = depart_time + budget_minutes
        deadline = time.perf_counter() + WALL_CLOCK_LIMIT_SEC
        objective = getattr(self, "objective", None)

        current = build_route(
            planner,
            origin=origin,
            depart_time=depart_time,
            time_limit=time_limit,
            rng=rng,
            max_steps=40,
            exploration_rate=0.30,
            objective=objective,
        )
        if not current:
            return []

        best = list(current)
        best_score = self._score(current, budget_minutes=budget_minutes)
        k = 1
        stagnant = 0

        while time.perf_counter() < deadline and stagnant < 32:
            shaken = self._shake(
                current,
                k=k,
                planner=planner,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                objective=objective,
            )

            improved = self._local_search(
                shaken,
                planner=planner,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                objective=objective,
            )
            score = self._score(improved, budget_minutes=budget_minutes)

            if score > best_score:
                best = list(improved)
                best_score = score
                current = list(improved)
                k = 1
                stagnant = 0
            else:
                k += 1
                stagnant += 1
                if k > self.k_max:
                    k = 1
                    current = list(best)

        return best

    def _shake(
        self,
        edges,
        *,
        k: int,
        planner,
        origin: str,
        depart_time: int,
        time_limit: int,
        rng,
        objective,
    ):
        """
        VNS shaking:
        k controls perturbation strength by increasing reroute depth / count.
        """
        if not edges:
            return []

        candidate = list(edges)
        repeats = max(1, min(4, k))
        for _ in range(repeats):
            n = max(1, len(candidate))
            if k == 1:
                cut = rng.randint(max(0, n - max(2, n // 4)), n)
                explore = 0.34
            elif k == 2:
                cut = rng.randint(max(0, n // 3), n)
                explore = 0.40
            elif k == 3:
                cut = rng.randint(0, n)
                explore = 0.46
            else:
                cut = rng.randint(0, max(1, n // 2))
                explore = 0.52

            candidate = reroute_tail(
                planner,
                route=candidate,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                cut_index=cut,
                max_steps=40,
                exploration_rate=explore,
                objective=objective,
            )
        return candidate

    def _local_search(
        self,
        edges,
        *,
        planner,
        origin: str,
        depart_time: int,
        time_limit: int,
        rng,
        objective,
    ):
        """First-improvement local search using conservative reroute moves."""
        if not edges:
            return []

        best = list(edges)
        best_score = self._score(best, budget_minutes=time_limit - depart_time)

        trials = max(6, min(18, len(edges) + 4))
        for _ in range(trials):
            cut = rng.randint(max(0, len(best) - max(3, len(best) // 3)), len(best))
            candidate = reroute_tail(
                planner,
                route=best,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                cut_index=cut,
                max_steps=40,
                exploration_rate=0.18,
                objective=objective,
            )
            score = self._score(candidate, budget_minutes=time_limit - depart_time)
            if score > best_score:
                return candidate

        return best

    def _score(self, edges, *, budget_minutes: int | None = None):
        return route_score(
            edges,
            objective=getattr(self, "objective", None),
            budget_minutes=budget_minutes,
        )
