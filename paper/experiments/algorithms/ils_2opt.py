"""
ILS + 2-opt baseline adapted to timetable-feasible transit routing.

The neighbourhood keeps strict timetable feasibility by using
"cut + feasible-regrowth" operators instead of edge-order permutations.
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


class ILS2Opt(BaseAlgorithm):
    name = "ILS+2opt"
    stochastic = True
    category = "PC-TSP涓绘祦"

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
            max_steps=42,
            exploration_rate=0.32,
            objective=objective,
        )
        if not current:
            return []

        best = list(current)
        best_score = self._score(current, budget_minutes=budget_minutes)
        no_improve_rounds = 0

        while time.perf_counter() < deadline:
            improved = self._two_opt_like(
                current,
                planner=planner,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                objective=objective,
            )
            imp_score = self._score(improved, budget_minutes=budget_minutes)

            if imp_score > best_score:
                best = list(improved)
                best_score = imp_score
                no_improve_rounds = 0
            else:
                no_improve_rounds += 1

            current = self._perturb(
                improved,
                planner=planner,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                objective=objective,
            )

            # Early stop to avoid burning the entire wall-clock when search stagnates.
            if no_improve_rounds >= 28:
                break

        return best

    def _two_opt_like(
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
        """
        2-opt style local improvement:
        try multiple cut points and regrow a feasible tail, keep best candidate.
        """
        if not edges:
            return []

        best = list(edges)
        best_score = self._score(best, budget_minutes=time_limit - depart_time)

        trials = max(8, min(26, len(edges) * 2))
        for _ in range(trials):
            cut = rng.randint(0, len(best))
            candidate = reroute_tail(
                planner,
                route=best,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                cut_index=cut,
                max_steps=42,
                exploration_rate=0.20,
                objective=objective,
            )
            score = self._score(candidate, budget_minutes=time_limit - depart_time)
            if score > best_score:
                best = candidate
                best_score = score

        return best

    def _perturb(
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
        """
        ILS perturbation:
        apply one stronger reroute around an early random cut to escape local optima.
        """
        if not edges:
            return []

        upper = max(1, min(len(edges), len(edges) // 2 + 1))
        cut = rng.randint(0, upper)
        return reroute_tail(
            planner,
            route=edges,
            origin=origin,
            depart_time=depart_time,
            time_limit=time_limit,
            rng=rng,
            cut_index=cut,
            max_steps=42,
            exploration_rate=0.42,
            objective=objective,
        )

    def _score(self, edges, *, budget_minutes: int | None = None):
        return route_score(
            edges,
            objective=getattr(self, "objective", None),
            budget_minutes=budget_minutes,
        )
