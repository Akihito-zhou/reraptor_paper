"""
Adapted baseline inspired by Li & Kim (2024, CMC).

Original paper targets real-time demand-responsive transit with a heuristic
A*-style strategy. This adapted variant uses queue-based best-first expansion
on timetable-feasible edges for the paper's fixed-budget stop-reward setting.
"""
from __future__ import annotations

import heapq
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.base_algorithm import BaseAlgorithm
from common.config import WALL_CLOCK_LIMIT_SEC
from algorithms.transit_route_ops import next_feasible_edges, route_score


class LiKim2024HeuristicAStarAdapted(BaseAlgorithm):
    name = "LiKim2024-RTA* (adapted)"
    stochastic = True
    category = "Recent-2024+ (adapted)"

    def solve(self, planner, origin, depart_time, budget_minutes, *, seed=0):
        rng = random.Random(seed)
        time_limit = depart_time + budget_minutes
        deadline = time.perf_counter() + min(45.0, float(WALL_CLOCK_LIMIT_SEC))
        objective = getattr(self, "objective", None)

        # (priority, tie_breaker, stop, time, path, visits, prev_edge)
        pq: list[tuple[float, int, str, int, list, dict[str, int], object | None]] = []
        counter = 0
        start_visits = {str(origin): 1}
        heapq.heappush(
            pq,
            (
                -0.0,
                counter,
                str(origin),
                int(depart_time),
                [],
                start_visits,
                None,
            ),
        )

        best_path: list = []
        best_score = float("-inf")
        best_seen: dict[tuple[str, int, int], float] = {}
        expansions = 0
        max_expansions = 12000

        while pq and time.perf_counter() < deadline and expansions < max_expansions:
            _, _, current_stop, current_time, path, visits, prev_edge = heapq.heappop(pq)
            expansions += 1

            # Any non-empty route is a valid candidate; keep best-so-far.
            if path:
                score = self._terminal_score(path, budget_minutes=budget_minutes)
                if score > best_score:
                    best_score = score
                    best_path = path

            candidates = next_feasible_edges(
                planner,
                origin_code=str(origin),
                current_stop=str(current_stop),
                current_time=int(current_time),
                prev_edge=prev_edge,
                time_limit=int(time_limit),
                lookahead_minutes=90,
                max_candidates=16,
                objective=objective,
                route_depart_time=int(depart_time),
                visits=visits,
            )
            if not candidates:
                continue

            for edge in candidates:
                new_path = list(path)
                new_path.append(edge)
                new_visits = dict(visits)
                next_stop = str(edge.to_code)
                new_visits[next_stop] = new_visits.get(next_stop, 0) + 1

                g_score, f_score = self._astar_scores(new_path, budget_minutes=budget_minutes)
                key = (next_stop, int(edge.arrive) // 15, int(g_score // 20))
                if g_score <= best_seen.get(key, float("-inf")):
                    continue
                best_seen[key] = g_score

                counter += 1
                # Small randomized tie-breaking avoids deterministic queue bias.
                priority = -(f_score + rng.random() * 1e-6)
                heapq.heappush(
                    pq,
                    (
                        priority,
                        counter,
                        next_stop,
                        int(edge.arrive),
                        new_path,
                        new_visits,
                        edge,
                    ),
                )

        return best_path

    def _astar_scores(self, edges, *, budget_minutes: int) -> tuple[float, float]:
        objective = getattr(self, "objective", None)
        if objective is None:
            base = route_score(edges, budget_minutes=budget_minutes)
            return base, base

        metrics = objective.metrics_from_edges(edges, budget_minutes=budget_minutes)
        g_score = float(metrics.get("stop_score_total", 0.0))
        upper = objective.optimistic_total_upper_bound_from_metrics(
            metrics,
            budget_minutes=budget_minutes,
            min_leg_minutes=4.0,
        )
        # A*-like blend: current collected score + discounted optimistic remaining.
        h_score = max(0.0, upper - g_score)
        f_score = g_score + 0.35 * h_score
        return g_score, f_score

    def _terminal_score(self, edges, *, budget_minutes: int) -> float:
        objective = getattr(self, "objective", None)
        if objective is None:
            return route_score(edges, budget_minutes=budget_minutes)
        metrics = objective.metrics_from_edges(edges, budget_minutes=budget_minutes)
        return float(objective.search_score_from_metrics(metrics))

