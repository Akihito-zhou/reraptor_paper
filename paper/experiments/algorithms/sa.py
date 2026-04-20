"""
Simulated Annealing baseline with timetable-feasible neighbourhoods.
"""
from __future__ import annotations

import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.base_algorithm import BaseAlgorithm
from common.config import SA_COOLING_RATE, SA_INITIAL_TEMP, WALL_CLOCK_LIMIT_SEC
from algorithms.transit_route_ops import build_route, reroute_tail, route_score


class SimulatedAnnealing(BaseAlgorithm):
    name = "SA"
    stochastic = True
    category = "鍏冨晸鐧哄紡"

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
            exploration_rate=0.33,
            objective=objective,
        )
        if not current:
            return []

        best = list(current)
        best_score = self._score(best, budget_minutes=budget_minutes)
        current_score = best_score
        temp = SA_INITIAL_TEMP
        stagnant = 0

        while time.perf_counter() < deadline and temp > 1e-3 and stagnant < 600:
            neighbour = self._neighbour(
                current,
                planner=planner,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                temp=temp,
                objective=objective,
            )
            if not neighbour:
                temp *= SA_COOLING_RATE
                stagnant += 1
                continue

            n_score = self._score(neighbour, budget_minutes=budget_minutes)
            delta = n_score - current_score

            # Clamp exponent to avoid overflow at very small temperatures.
            accept_prob = math.exp(max(-60.0, min(60.0, delta / max(temp, 1e-9))))
            if delta >= 0 or rng.random() < accept_prob:
                current = neighbour
                current_score = n_score
                if current_score > best_score:
                    best = list(current)
                    best_score = current_score
                    stagnant = 0
                else:
                    stagnant += 1
            else:
                stagnant += 1

            temp *= SA_COOLING_RATE

        return best

    def _neighbour(
        self,
        edges,
        *,
        planner,
        origin: str,
        depart_time: int,
        time_limit: int,
        rng,
        temp: float,
        objective,
    ):
        if not edges:
            return []

        # Higher temperature -> larger edits (earlier cut), lower temperature -> fine-tuning.
        n = len(edges)
        if n == 0:
            return []

        ratio = max(0.0, min(1.0, temp / max(SA_INITIAL_TEMP, 1e-9)))
        max_early = max(1, int(n * ratio))
        low = max(0, n - max_early)
        cut = rng.randint(low, n)
        explore = 0.12 + 0.38 * ratio

        return reroute_tail(
            planner,
            route=edges,
            origin=origin,
            depart_time=depart_time,
            time_limit=time_limit,
            rng=rng,
            cut_index=cut,
            max_steps=40,
            exploration_rate=explore,
            objective=objective,
        )

    def _score(self, edges, *, budget_minutes: int | None = None):
        return route_score(
            edges,
            objective=getattr(self, "objective", None),
            budget_minutes=budget_minutes,
        )
