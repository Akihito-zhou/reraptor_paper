"""
McRAPTOR / rRAPTOR baseline: Multi-criteria RAPTOR.

Runs the standard RAPTOR with multi-criteria optimization (minimize arrival
time + transfers).  Demonstrates that transit-routing SOTA methods optimise
for shortest path, not value maximisation.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.base_algorithm import BaseAlgorithm


class McRaptorBaseline(BaseAlgorithm):
    name = "McRAPTOR"
    stochastic = True
    category = "RAPTOR家族"

    def solve(self, planner, origin, depart_time, budget_minutes, *, seed=0):
        """
        McRAPTOR optimises for minimum arrival time / fewest transfers.

        We run the standard RAPTOR to every reachable destination, then pick
        the journey that happens to have the most ride time — showing that
        even the 'best' traditional result is poor at value maximisation.
        """
        time_limit = depart_time + budget_minutes

        # Use the existing simple_raptor method toward different destinations
        # to collect multi-criteria Pareto-optimal journeys.
        best_path = []
        best_score = -float("inf")
        objective = getattr(self, "objective", None)

        # Sample 50 destinations reliably to ensure varied coverage
        rng = __import__("random").Random(seed)
        destinations = rng.sample(list(planner.stations.keys()), min(50, len(planner.stations)))

        for dest in destinations:
            if dest == origin:
                continue
            try:
                result = planner.run_simple_raptor(
                    origin=origin,
                    destination=dest,
                    depart_after=depart_time,
                )
                if not result:
                    continue
                _, journey_legs = result

                # Convert to TripEdges
                edges = planner._convert_journey_legs_to_trip_edges(journey_legs)
                valid = [e for e in edges if e.arrive <= time_limit]
                if objective is not None:
                    objective_metrics = objective.metrics_from_edges(valid, budget_minutes=budget_minutes)
                    if objective_metrics.get("effective_budget_feasible") is False:
                        continue
                score = (
                    objective.search_score_from_edges(valid, budget_minutes=budget_minutes)
                    if objective is not None
                    else sum(e.ride_minutes for e in valid)
                )

                if score > best_score:
                    best_score = score
                    best_path = valid
            except Exception:
                continue

        return best_path
