"""
Greedy with Lookahead: Simple heuristic baseline.

At each stop, evaluates the next N departing edges, picks the one with
the best immediate score, and repeats until the time budget is exhausted.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.base_algorithm import BaseAlgorithm


class GreedyLookahead(BaseAlgorithm):
    name = "Greedy (L=3)"
    category = "簡単啓発式"

    def __init__(self, lookahead: int = 3):
        self.lookahead = lookahead

    def solve(self, planner, origin, depart_time, budget_minutes, *, seed=0):
        self._set_query_context(origin=origin, depart_time=depart_time)
        time_limit = depart_time + budget_minutes
        current_stop = origin
        current_time = depart_time
        path_edges = []
        visited = {origin}
        objective = getattr(self, "objective", None)

        while current_time < time_limit:
            candidates = planner._next_edges(
                current_stop, current_time + 3, lookahead_minutes=60
            )
            if not candidates:
                break

            # Filter by budget
            candidates = [e for e in candidates if e.arrive <= time_limit]
            if objective is not None:
                visits = {str(code): 1 for code in visited}
                candidates = [
                    e
                    for e in candidates
                    if objective.can_append(
                        origin_code=str(origin),
                        depart_time=depart_time,
                        arrival_time=e.arrive,
                        visits=visits,
                        next_stop_code=str(e.to_code),
                        budget_minutes=budget_minutes,
                    )
                ]
            if not candidates:
                break

            # Score each candidate with lookahead
            best_edge = None
            best_score = -float("inf")

            for edge in candidates[: self.lookahead * 3]:
                if objective is not None:
                    visits = {str(code): 1 for code in visited}
                    score = objective.edge_priority(
                        edge=edge,
                        origin_code=origin,
                        visits=visits,
                        prev_edge=path_edges[-1] if path_edges else None,
                    )
                else:
                    score = edge.ride_minutes
                    if edge.to_code not in visited:
                        score += 10

                # Lookahead: check what's available from this edge's destination
                if self.lookahead > 0:
                    next_edges = planner._next_edges(
                        edge.to_code, edge.arrive + 3, lookahead_minutes=30
                    )
                    for ne in next_edges[: self.lookahead]:
                        if ne.arrive <= time_limit:
                            if objective is not None:
                                visits = {str(code): 1 for code in visited}
                                visits[str(edge.to_code)] = visits.get(str(edge.to_code), 0) + 1
                                la_score = objective.edge_priority(
                                    edge=ne,
                                    origin_code=origin,
                                    visits=visits,
                                    prev_edge=edge,
                                )
                            else:
                                la_score = ne.ride_minutes
                                if ne.to_code not in visited:
                                    la_score += 5
                            score += la_score * 0.3  # Discounted future value

                if score > best_score:
                    best_score = score
                    best_edge = edge

            if best_edge is None:
                break

            path_edges.append(best_edge)
            visited.add(best_edge.to_code)
            current_stop = best_edge.to_code
            current_time = best_edge.arrive

        return path_edges
