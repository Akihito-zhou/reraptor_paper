"""
Adapted baseline inspired by Zhou & Wang (2025, FEM).

Original work studies demand-adaptive routing/request selection with ALNS.
This adapted variant applies a lightweight ALNS destroy/repair loop to the
timetable-feasible fixed-budget stop-reward setting.
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


class ZhouWang2025ALNSAdapted(BaseAlgorithm):
    name = "ZhouWang2025-ALNS (adapted)"
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
            exploration_rate=0.34,
            objective=objective,
        )
        if not current:
            return []

        best = list(current)
        best_score = self._score(best, budget_minutes=budget_minutes)
        current_score = best_score

        operators = ("shallow_tail", "medium_tail", "deep_tail", "restart_seeded")
        weights = {op: 1.0 for op in operators}
        scores = {op: 0.0 for op in operators}
        uses = {op: 0 for op in operators}
        temperature = 6.0

        iters = 0
        while time.perf_counter() < deadline and iters < 160:
            op = self._sample_operator(operators, weights, rng)
            candidate = self._apply_operator(
                op=op,
                planner=planner,
                route=current,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                objective=objective,
            )
            cand_score = self._score(candidate, budget_minutes=budget_minutes)

            accepted = False
            if cand_score >= current_score:
                accepted = True
                current = candidate
                current_score = cand_score
                if cand_score > best_score:
                    best = list(candidate)
                    best_score = cand_score
                    scores[op] += 5.0
                else:
                    scores[op] += 2.0
            else:
                delta = current_score - cand_score
                # SA-style acceptance for diversification.
                if rng.random() < (2.718281828 ** (-delta / max(1e-6, temperature))):
                    accepted = True
                    current = candidate
                    current_score = cand_score
                    scores[op] += 0.5

            uses[op] += 1
            if not accepted:
                scores[op] += 0.0

            iters += 1
            temperature = max(0.6, temperature * 0.985)
            if iters % 12 == 0:
                self._update_weights(weights, scores, uses)

        return best

    def _sample_operator(self, operators, weights, rng):
        total = sum(max(1e-6, float(weights[o])) for o in operators)
        target = rng.random() * total
        acc = 0.0
        for op in operators:
            acc += max(1e-6, float(weights[op]))
            if acc >= target:
                return op
        return operators[-1]

    def _apply_operator(
        self,
        *,
        op: str,
        planner,
        route,
        origin: str,
        depart_time: int,
        time_limit: int,
        rng,
        objective,
    ):
        n = len(route)
        if op == "shallow_tail":
            cut = rng.randint(max(0, n - max(3, n // 5)), n)
            return reroute_tail(
                planner,
                route=route,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                cut_index=cut,
                max_steps=44,
                exploration_rate=0.20,
                objective=objective,
            )
        if op == "medium_tail":
            cut = rng.randint(max(0, n // 3), max(1, n))
            return reroute_tail(
                planner,
                route=route,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                cut_index=cut,
                max_steps=44,
                exploration_rate=0.32,
                objective=objective,
            )
        if op == "deep_tail":
            cut = rng.randint(0, max(1, n // 2))
            return reroute_tail(
                planner,
                route=route,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                cut_index=cut,
                max_steps=44,
                exploration_rate=0.48,
                objective=objective,
            )

        # restart_seeded
        seed_len = 0 if n == 0 else rng.randint(0, max(1, n // 4))
        return build_route(
            planner,
            origin=origin,
            depart_time=depart_time,
            time_limit=time_limit,
            rng=rng,
            seed_edges=route[:seed_len],
            max_steps=44,
            exploration_rate=0.55,
            objective=objective,
        )

    def _update_weights(self, weights, scores, uses):
        reaction = 0.30
        for op in list(weights.keys()):
            if uses[op] <= 0:
                continue
            avg_reward = scores[op] / float(uses[op])
            weights[op] = (1.0 - reaction) * float(weights[op]) + reaction * max(0.2, avg_reward)
            scores[op] = 0.0
            uses[op] = 0

    def _score(self, edges, *, budget_minutes: int | None = None):
        return route_score(
            edges,
            objective=getattr(self, "objective", None),
            budget_minutes=budget_minutes,
        )

