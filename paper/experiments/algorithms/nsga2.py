"""
NSGA-II baseline with timetable-feasible variation operators.

This implementation includes:
1) fast non-dominated sorting
2) crowding-distance assignment
3) binary tournament selection (rank, then crowding)
4) timetable-feasible crossover / mutation
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.base_algorithm import BaseAlgorithm
from common.config import (
    GA_GENERATIONS,
    GA_POPULATION_SIZE,
    TRANSFER_BUFFER_MINUTES,
    WALL_CLOCK_LIMIT_SEC,
)
from common.utils import compute_route_metrics
from algorithms.transit_route_ops import (
    build_route,
    derive_route_state,
    normalize_route,
    reroute_tail,
    route_score,
    route_signature,
)


class NSGA2(BaseAlgorithm):
    name = "NSGA-II"
    stochastic = True
    category = "鍏冨晸鐧哄紡"

    def solve(self, planner, origin, depart_time, budget_minutes, *, seed=0):
        rng = random.Random(seed)
        time_limit = depart_time + budget_minutes
        deadline = time.perf_counter() + WALL_CLOCK_LIMIT_SEC
        objective = getattr(self, "objective", None)

        self._metric_cache: dict[tuple, dict] = {}
        pop = self._seed_population(
            planner=planner,
            origin=origin,
            depart_time=depart_time,
            time_limit=time_limit,
            rng=rng,
            objective=objective,
        )
        if not pop:
            return []

        best = max(pop, key=lambda edges: self._score(edges, budget_minutes=budget_minutes))

        gen = 0
        while gen < GA_GENERATIONS and time.perf_counter() < deadline:
            objs = [self._objectives(ind, planner, budget_minutes=budget_minutes) for ind in pop]
            fronts, ranks = self._fast_non_dominated_sort(objs)
            crowding = self._crowding_for_fronts(fronts, objs)

            parents = [
                self._binary_tournament(pop, ranks, crowding, rng)
                for _ in range(len(pop))
            ]

            offspring = []
            for i in range(0, len(parents) - 1, 2):
                c1, c2 = self._crossover(
                    parents[i],
                    parents[i + 1],
                    planner=planner,
                    origin=origin,
                    depart_time=depart_time,
                    time_limit=time_limit,
                    rng=rng,
                    objective=objective,
                )
                c1 = self._mutate(
                    c1,
                    planner=planner,
                    origin=origin,
                    depart_time=depart_time,
                    time_limit=time_limit,
                    rng=rng,
                    objective=objective,
                )
                c2 = self._mutate(
                    c2,
                    planner=planner,
                    origin=origin,
                    depart_time=depart_time,
                    time_limit=time_limit,
                    rng=rng,
                    objective=objective,
                )
                if c1:
                    offspring.append(c1)
                if c2:
                    offspring.append(c2)

            if not offspring:
                break

            combined = pop + offspring
            pop = self._environmental_selection(
                combined,
                planner=planner,
                pop_size=GA_POPULATION_SIZE,
                budget_minutes=budget_minutes,
            )
            if not pop:
                break

            gen_best = max(pop, key=lambda edges: self._score(edges, budget_minutes=budget_minutes))
            if self._score(gen_best, budget_minutes=budget_minutes) > self._score(best, budget_minutes=budget_minutes):
                best = gen_best

            gen += 1

        return best

    def _seed_population(self, *, planner, origin: str, depart_time: int, time_limit: int, rng, objective=None):
        population: list[list] = []
        seen: set[tuple] = set()
        attempts = 0
        max_attempts = GA_POPULATION_SIZE * 8

        while len(population) < GA_POPULATION_SIZE and attempts < max_attempts:
            attempts += 1
            route = build_route(
                planner,
                origin=origin,
                depart_time=depart_time,
                time_limit=time_limit,
                rng=rng,
                max_steps=42,
                exploration_rate=0.12 + 0.55 * rng.random(),
                lookahead_minutes=70 + int(50 * rng.random()),
                objective=objective,
            )
            if not route:
                continue
            sig = route_signature(route)
            if sig in seen:
                continue
            seen.add(sig)
            population.append(route)

        return population

    def _crossover(
        self,
        p1,
        p2,
        *,
        planner,
        origin: str,
        depart_time: int,
        time_limit: int,
        rng,
        objective,
    ):
        child1 = self._build_child(
            primary=p1,
            donor=p2,
            planner=planner,
            origin=origin,
            depart_time=depart_time,
            time_limit=time_limit,
            rng=rng,
            objective=objective,
        )
        child2 = self._build_child(
            primary=p2,
            donor=p1,
            planner=planner,
            origin=origin,
            depart_time=depart_time,
            time_limit=time_limit,
            rng=rng,
            objective=objective,
        )
        return child1, child2

    def _build_child(
        self,
        *,
        primary,
        donor,
        planner,
        origin: str,
        depart_time: int,
        time_limit: int,
        rng,
        objective,
    ):
        if not primary:
            return []

        cut = rng.randint(0, len(primary))
        seed = normalize_route(
            primary[:cut],
            origin=origin,
            depart_time=depart_time,
            time_limit=time_limit,
        )

        # Donor-guided stitching: try one feasible donor edge from donor route.
        if donor:
            current_stop, current_time, prev_edge, _ = derive_route_state(
                seed, origin=origin, depart_time=depart_time
            )
            donor_candidates = []
            for edge in donor:
                if edge.from_code != current_stop:
                    continue
                same_trip = (
                    prev_edge is not None
                    and edge.trip_id == prev_edge.trip_id
                    and edge.line_id == prev_edge.line_id
                )
                earliest = (
                    current_time
                    if (prev_edge is None or same_trip)
                    else current_time + TRANSFER_BUFFER_MINUTES
                )
                if edge.depart < earliest or edge.arrive > time_limit:
                    continue
                donor_candidates.append(edge)
                if len(donor_candidates) >= 8:
                    break
            if donor_candidates:
                seed.append(rng.choice(donor_candidates))

        return build_route(
            planner,
            origin=origin,
            depart_time=depart_time,
            time_limit=time_limit,
            rng=rng,
            seed_edges=seed,
            max_steps=42,
            exploration_rate=0.30,
            objective=objective,
        )

    def _mutate(
        self,
        edges,
        *,
        planner,
        origin: str,
        depart_time: int,
        time_limit: int,
        rng,
        rate: float = 0.22,
        objective=None,
    ):
        if not edges or rng.random() > rate:
            return edges

        cut = rng.randint(0, len(edges))
        return reroute_tail(
            planner,
            route=edges,
            origin=origin,
            depart_time=depart_time,
            time_limit=time_limit,
            rng=rng,
            cut_index=cut,
            max_steps=42,
            exploration_rate=0.45,
            objective=objective,
        )

    def _objectives(self, edges, planner, *, budget_minutes: int | None = None):
        sig = route_signature(edges)
        cached = self._metric_cache.get(sig)
        if cached is None:
            objective = getattr(self, "objective", None)
            cached = compute_route_metrics(edges, planner)
            if objective is not None:
                cached.update(objective.metrics_from_edges(edges, budget_minutes=budget_minutes))
            self._metric_cache[sig] = cached
        objective = getattr(self, "objective", None)
        if objective is not None:
            return objective.objective_vector_from_edges(edges, budget_minutes=budget_minutes)
        return (
            float(cached.get("ride_minutes", 0.0)),
            float(cached.get("unique_stops", 0.0)),
            float(cached.get("hull_area", 0.0)),
        )

    def _score(self, edges, *, budget_minutes: int | None = None):
        return route_score(
            edges,
            objective=getattr(self, "objective", None),
            budget_minutes=budget_minutes,
        )

    @staticmethod
    def _dominates_obj(a, b) -> bool:
        return all(ai >= bi for ai, bi in zip(a, b, strict=False)) and any(
            ai > bi for ai, bi in zip(a, b, strict=False)
        )

    def _fast_non_dominated_sort(self, objs: list[tuple[float, float, float]]):
        n = len(objs)
        dominates: list[list[int]] = [[] for _ in range(n)]
        dominated_count = [0] * n
        ranks = [0] * n
        fronts: list[list[int]] = [[]]

        for p in range(n):
            for q in range(n):
                if p == q:
                    continue
                if self._dominates_obj(objs[p], objs[q]):
                    dominates[p].append(q)
                elif self._dominates_obj(objs[q], objs[p]):
                    dominated_count[p] += 1
            if dominated_count[p] == 0:
                ranks[p] = 0
                fronts[0].append(p)

        i = 0
        while i < len(fronts) and fronts[i]:
            next_front: list[int] = []
            for p in fronts[i]:
                for q in dominates[p]:
                    dominated_count[q] -= 1
                    if dominated_count[q] == 0:
                        ranks[q] = i + 1
                        next_front.append(q)
            if next_front:
                fronts.append(next_front)
            i += 1

        return fronts, ranks

    @staticmethod
    def _crowding_distance(front: list[int], objs: list[tuple[float, float, float]]) -> dict[int, float]:
        if not front:
            return {}
        if len(front) <= 2:
            return {idx: float("inf") for idx in front}

        distance = {idx: 0.0 for idx in front}
        dimensions = len(objs[0])
        for dim in range(dimensions):
            sorted_front = sorted(front, key=lambda idx: objs[idx][dim])
            distance[sorted_front[0]] = float("inf")
            distance[sorted_front[-1]] = float("inf")

            min_v = objs[sorted_front[0]][dim]
            max_v = objs[sorted_front[-1]][dim]
            if max_v <= min_v:
                continue

            for i in range(1, len(sorted_front) - 1):
                left = objs[sorted_front[i - 1]][dim]
                right = objs[sorted_front[i + 1]][dim]
                distance[sorted_front[i]] += (right - left) / (max_v - min_v)

        return distance

    def _crowding_for_fronts(self, fronts: list[list[int]], objs: list[tuple[float, float, float]]):
        crowding: dict[int, float] = {}
        for front in fronts:
            crowding.update(self._crowding_distance(front, objs))
        return crowding

    def _binary_tournament(self, pop, ranks, crowding, rng):
        i, j = rng.sample(range(len(pop)), 2)
        if ranks[i] < ranks[j]:
            return pop[i]
        if ranks[j] < ranks[i]:
            return pop[j]
        if crowding.get(i, 0.0) > crowding.get(j, 0.0):
            return pop[i]
        if crowding.get(j, 0.0) > crowding.get(i, 0.0):
            return pop[j]
        return pop[i] if rng.random() < 0.5 else pop[j]

    def _environmental_selection(self, combined, *, planner, pop_size: int, budget_minutes: int | None = None):
        # De-duplicate routes first to keep diversity.
        unique = {}
        for route in combined:
            unique[route_signature(route)] = route
        population = list(unique.values())
        if len(population) <= pop_size:
            return population

        objs = [self._objectives(ind, planner, budget_minutes=budget_minutes) for ind in population]
        fronts, _ = self._fast_non_dominated_sort(objs)

        selected_idx: list[int] = []
        for front in fronts:
            if len(selected_idx) + len(front) <= pop_size:
                selected_idx.extend(front)
            else:
                remain = pop_size - len(selected_idx)
                crowd = self._crowding_distance(front, objs)
                front_sorted = sorted(front, key=lambda idx: crowd.get(idx, 0.0), reverse=True)
                selected_idx.extend(front_sorted[:remain])
                break

        return [population[i] for i in selected_idx]
