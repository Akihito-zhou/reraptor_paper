"""
Pure RAPTOR: No pruning baseline.

Runs the underlying RAPTOR algorithm with no heuristic pruning, 
proving that without our optimizations (Beam, Dominance, Negative Score),
the state-space explosion prevents the algorithm from reaching an optimal
solution efficiently.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.base_algorithm import BaseAlgorithm
from algorithms.ours_full import OursFull

# Use the exact same wall-clock timeout as traditional Metaheuristics configs
from common.config import WALL_CLOCK_LIMIT_SEC


class PureRaptor(BaseAlgorithm):
    name = "Pure RAPTOR"
    category = "RAPTOR变体"

    def solve(self, planner, origin, depart_time, budget_minutes, *, seed=0):
        """
        Pure RAPTOR delegates to our core RAPTOR engine but with:
        - Beam Width: Infinite (No Beam Search)
        - Pareto Dominance: Off
        - Geometry Penalty: Off

        A strict 60s timeout is passed in because without pruning,
        pure RAPTOR will consume hundreds of gigabytes of RAM evaluating
        million-state trees.
        """
        self._set_query_context(origin=origin, depart_time=depart_time)
        engine = OursFull(
            use_beam=False,
            use_dominance=False,
            use_negative_score=False,
            timeout_seconds=WALL_CLOCK_LIMIT_SEC,
        )
        objective = getattr(self, "objective", None)
        if objective is not None:
            engine.objective = objective

        return engine.solve(
            planner=planner,
            origin=origin,
            depart_time=depart_time,
            budget_minutes=budget_minutes,
            seed=seed,
        )
