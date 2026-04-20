"""
Ours (Full): Reverse-Objective RAPTOR + Three-Layer Hybrid Pruning + Geometry-Aware Scoring.

This algorithm directly implements the multi-objective label-setting approach
described in the paper. It decouples the core routing logic from the PlannerService's
`run_raptor_challenge` to ensure purely controlled experimentation.

Implementation note:
This experiment version expands labels on top of `stop_schedules` (`_next_edges`)
instead of `planner.routes`, because the underlying data uses non-unique `trip_id`
values and route-table reconstruction may drop valid services.
"""
from __future__ import annotations

import sys
import heapq
import math
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable
import time

# Allow importing from common
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.base_algorithm import BaseAlgorithm
from common.config import BEAM_WIDTH

# For types and geo calculations
# We import models directly from the app to reuse `Label` formats, but the algorithm is native.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
APP_API_DIR = PROJECT_ROOT / "apps" / "api"
if str(APP_API_DIR) not in sys.path:
    sys.path.insert(0, str(APP_API_DIR))

# Now import services
from services.planner_models import Label, JourneyLeg, TripEdge
from services.planner_utils import project_to_plane


class OursFull(BaseAlgorithm):
    name = "Ours (Full)"
    category = "本文"

    def __init__(
        self,
        use_beam: bool = True,
        use_dominance: bool = True,
        use_negative_score: bool = True,
        use_bound_dominance: bool = False,
        use_upper_bound_pruning: bool = False,
        use_potential_aware_beam: bool = False,
        beam_potential_weight: float = 0.5,
        beam_width: int = BEAM_WIDTH,
        timeout_seconds: float | None = None,
        max_labels: int | None = None,
        theme_name: str | None = None,
        theme_target_stops: frozenset[str] | set[str] | None = None,
        theme_min_ratio: float = 0.35,
        theme_penalty_weight: float = 100000.0,
        theme_bonus_per_hit: float = 20.0,
        theme_min_stops_apply: int = 4,
        theme_target_lines: frozenset[str] | set[str] | None = None,
        theme_line_min_ratio: float = 0.85,
        theme_line_penalty_weight: float = 120000.0,
        theme_line_bonus_per_hit: float = 25.0,
        theme_line_min_legs_apply: int = 3,
        search_score_weights: dict[str, float] | None = None,
        custom_metrics_fn: Callable[[Any, Label], dict[str, Any]] | None = None,
        custom_score_fn: Callable[[Label, dict[str, Any]], float] | None = None,
        custom_dominance_fn: Callable[[Label, dict[str, Any], Label, dict[str, Any]], bool] | None = None,
        custom_accept_fn: Callable[[Label, dict[str, Any]], bool] | None = None,
        custom_edge_filter_fn: Callable[[Label, TripEdge], bool] | None = None,
        min_transfer_minutes: int = 3,
        max_rounds_override: int | None = None,
        max_stop_visits: int | None = None,
        max_line_visits: int | None = None,
        objective_candidate_cap_short: int | None = 30,
        objective_candidate_cap_long: int | None = 20,
        objective_candidate_short_budget_max: int = 4 * 60,
    ):
        """
        Supports ablation studies by toggling pruning layers.
        """
        self.use_beam = use_beam
        self.use_dominance = use_dominance
        self.use_negative_score = use_negative_score
        self.use_bound_dominance = use_bound_dominance
        self.use_upper_bound_pruning = use_upper_bound_pruning
        self.use_potential_aware_beam = use_potential_aware_beam
        self.beam_potential_weight = float(max(0.0, beam_potential_weight))
        self.beam_width = beam_width
        self.timeout_seconds = timeout_seconds
        self.max_labels = max_labels
        self.theme_name = theme_name
        self.theme_target_stops = frozenset(theme_target_stops or [])
        self.theme_min_ratio = theme_min_ratio
        self.theme_penalty_weight = theme_penalty_weight
        self.theme_bonus_per_hit = theme_bonus_per_hit
        self.theme_min_stops_apply = theme_min_stops_apply
        self.theme_target_lines = frozenset(str(x) for x in (theme_target_lines or []))
        self.theme_line_min_ratio = theme_line_min_ratio
        self.theme_line_penalty_weight = theme_line_penalty_weight
        self.theme_line_bonus_per_hit = theme_line_bonus_per_hit
        self.theme_line_min_legs_apply = max(1, int(theme_line_min_legs_apply))
        self.custom_metrics_fn = custom_metrics_fn
        self.custom_score_fn = custom_score_fn
        self.custom_dominance_fn = custom_dominance_fn
        self.custom_accept_fn = custom_accept_fn
        self.custom_edge_filter_fn = custom_edge_filter_fn
        self.min_transfer_minutes = int(max(0, min_transfer_minutes))
        self.max_rounds_override = max_rounds_override
        self.max_stop_visits = max_stop_visits if max_stop_visits and max_stop_visits > 0 else None
        self.max_line_visits = max_line_visits if max_line_visits and max_line_visits > 0 else None
        self.objective_candidate_cap_short = (
            int(objective_candidate_cap_short)
            if objective_candidate_cap_short is not None and int(objective_candidate_cap_short) > 0
            else None
        )
        self.objective_candidate_cap_long = (
            int(objective_candidate_cap_long)
            if objective_candidate_cap_long is not None and int(objective_candidate_cap_long) > 0
            else None
        )
        self.objective_candidate_short_budget_max = int(max(0, objective_candidate_short_budget_max))

        # Optional objective-weight sensitivity for search scoring.
        # Defaults reproduce the historical coefficients exactly.
        # Keys: ride_minutes, unique_stops, hull_area, quadrant
        self._default_search_coef = {
            "ride_minutes": 1.5,
            "unique_stops": 10.0,
            "hull_area": 50.0,
            "quadrant": 100.0,
        }
        self._reference_weight_profile = {
            "ride_minutes": 0.40,
            "unique_stops": 0.25,
            "hull_area": 0.20,
            "quadrant": 0.15,
        }
        self.search_score_weights = dict(self._default_search_coef)
        if search_score_weights:
            for k, default_coef in self._default_search_coef.items():
                ref = self._reference_weight_profile.get(k, 0.0)
                raw = float(search_score_weights.get(k, ref))
                safe_raw = max(0.0, raw)
                if ref > 0:
                    self.search_score_weights[k] = default_coef * (safe_raw / ref)
                else:
                    self.search_score_weights[k] = default_coef

        self._last_labels_count = 0
        self._last_termination_reason = "completed"
        self._last_scored_labels = 0
        self._last_negative_repeat_hits = 0
        self._last_negative_ratio_hits = 0
        self._last_theme_negative_hits = 0
        self._last_theme_line_negative_hits = 0
        self._last_beam_trim_events = 0
        self._last_beam_trimmed_labels = 0
        self._last_upper_bound_pruned = 0
        self._last_global_trim_events = 0
        self._last_global_trimmed_labels = 0
        self._last_candidate_trim_events = 0
        self._last_candidate_trimmed_edges = 0
        
        # Name suffixes for ablation logging
        suffix = []
        if not use_beam: suffix.append("NoBeam")
        if not use_dominance: suffix.append("NoDom")
        if not use_negative_score: suffix.append("NoNeg")
        if use_potential_aware_beam: suffix.append("BeamPotential")
        if suffix:
            self.name = f"Ours ({'-'.join(suffix)})"

    def evaluate(
        self,
        planner,
        origin: str,
        depart_time: int,
        budget_minutes: int,
        *,
        seed: int = 0,
        score_weights: dict[str, float] | None = None,
    ) -> dict:
        self._last_labels_count = 0
        self._last_termination_reason = "completed"
        self._last_scored_labels = 0
        self._last_negative_repeat_hits = 0
        self._last_negative_ratio_hits = 0
        self._last_theme_negative_hits = 0
        self._last_theme_line_negative_hits = 0
        self._last_beam_trim_events = 0
        self._last_beam_trimmed_labels = 0
        self._last_upper_bound_pruned = 0
        self._last_global_trim_events = 0
        self._last_global_trimmed_labels = 0
        self._last_candidate_trim_events = 0
        self._last_candidate_trimmed_edges = 0
        result = super().evaluate(planner, origin, depart_time, budget_minutes, seed=seed, score_weights=score_weights)
        result["labels"] = self._last_labels_count
        result["termination_reason"] = self._last_termination_reason
        result["resource_cap_hit"] = self._last_termination_reason in {"timeout", "label_cap"}
        result["scored_labels"] = self._last_scored_labels
        result["negative_repeat_hits"] = self._last_negative_repeat_hits
        result["negative_ratio_hits"] = self._last_negative_ratio_hits
        result["negative_theme_hits"] = self._last_theme_negative_hits
        result["negative_theme_line_hits"] = self._last_theme_line_negative_hits
        result["negative_total_hits"] = (
            self._last_negative_repeat_hits
            + self._last_negative_ratio_hits
            + self._last_theme_negative_hits
            + self._last_theme_line_negative_hits
        )
        result["beam_trim_events"] = self._last_beam_trim_events
        result["beam_trimmed_labels"] = self._last_beam_trimmed_labels
        result["upper_bound_pruned"] = self._last_upper_bound_pruned
        result["global_trim_events"] = self._last_global_trim_events
        result["global_trimmed_labels"] = self._last_global_trimmed_labels
        result["candidate_trim_events"] = self._last_candidate_trim_events
        result["candidate_trimmed_edges"] = self._last_candidate_trimmed_edges
        return result

    def solve(self, planner, origin, depart_time, budget_minutes, *, seed=0):
        time_limit = depart_time + budget_minutes
        objective = getattr(self, "objective", None)
        self._last_termination_reason = "completed"
        self._last_scored_labels = 0
        self._last_negative_repeat_hits = 0
        self._last_negative_ratio_hits = 0
        self._last_theme_negative_hits = 0
        self._last_theme_line_negative_hits = 0
        self._last_beam_trim_events = 0
        self._last_beam_trimmed_labels = 0
        self._last_upper_bound_pruned = 0
        self._last_global_trim_events = 0
        self._last_global_trimmed_labels = 0
        self._last_candidate_trim_events = 0
        self._last_candidate_trimmed_edges = 0
        min_leg_minutes = (
            self._get_min_positive_ride_minutes(planner)
            if objective is not None and (self.use_bound_dominance or self.use_upper_bound_pruning or self.use_potential_aware_beam)
            else 0.0
        )
        incumbent_total = 0.0
        incumbent_effective_time = float("inf")
        
        # 1. Scoring Function (Geometry-Aware + Negative Penalty)
        def scoring_fn(label: Label, metrics: dict[str, float]) -> float:
            self._last_scored_labels += 1
            if self.custom_score_fn is not None:
                base_score = float(self.custom_score_fn(label, metrics))
            elif objective is not None:
                base_score = float(objective.search_score_from_metrics(metrics))
            else:
                base_score = (
                    label.ride_minutes * self.search_score_weights["ride_minutes"]
                    + metrics["unique_stops"] * self.search_score_weights["unique_stops"]
                )

                # Geometry-Aware Bonus
                base_score += metrics["hull_area"] * self.search_score_weights["hull_area"]
                base_score += metrics["quadrants"] * self.search_score_weights["quadrant"]

            # Optional theme-aware shaping for supporting experiments.
            theme_hits = 0
            if self.theme_target_stops:
                theme_hits = sum(1 for code in label.visited if code in self.theme_target_stops)
                base_score += theme_hits * self.theme_bonus_per_hit
            line_theme_hits = 0
            line_leg_count = 0
            if self.theme_target_lines and label.legs:
                line_ids = [str(leg.line_id) for leg in label.legs if getattr(leg, "line_id", None)]
                line_leg_count = len(line_ids)
                line_theme_hits = sum(1 for lid in line_ids if lid in self.theme_target_lines)
                base_score += line_theme_hits * self.theme_line_bonus_per_hit

            # Rule / Negative-Score Pruning
            penalty = 0
            if self.use_negative_score:
                if metrics["stop_repeat_max"] > 2:
                    penalty -= 50000
                    self._last_negative_repeat_hits += 1
                if metrics["unique_stops"] > 0 and (label.ride_minutes / metrics["unique_stops"]) < 2:
                    penalty -= 20000
                    self._last_negative_ratio_hits += 1
                if self.theme_target_stops and metrics["unique_stops"] >= self.theme_min_stops_apply:
                    hit_ratio = theme_hits / metrics["unique_stops"] if metrics["unique_stops"] > 0 else 0.0
                    if hit_ratio < self.theme_min_ratio:
                        penalty -= self.theme_penalty_weight * (self.theme_min_ratio - hit_ratio)
                        self._last_theme_negative_hits += 1
                if self.theme_target_lines and line_leg_count >= self.theme_line_min_legs_apply:
                    line_ratio = line_theme_hits / line_leg_count
                    if line_ratio < self.theme_line_min_ratio:
                        penalty -= self.theme_line_penalty_weight * (self.theme_line_min_ratio - line_ratio)
                        self._last_theme_line_negative_hits += 1

            return base_score + penalty

        def update_incumbent(metrics: dict[str, float]) -> None:
            nonlocal incumbent_total, incumbent_effective_time
            total = float(metrics.get("stop_score_total", 0.0))
            effective_time = float(metrics.get("effective_time_minutes", metrics.get("total_time_minutes", 0.0)))
            if total > incumbent_total + 1e-9:
                incumbent_total = total
                incumbent_effective_time = effective_time
                return
            if abs(total - incumbent_total) <= 1e-9 and effective_time < incumbent_effective_time:
                incumbent_effective_time = effective_time

        def should_prune_upper_bound(metrics: dict[str, float]) -> bool:
            if objective is None:
                return False
            upper = float(metrics.get("score_upper_bound_total", metrics.get("stop_score_total", 0.0)))
            effective_time = float(metrics.get("effective_time_minutes", metrics.get("total_time_minutes", 0.0)))
            if upper + 1e-9 < incumbent_total:
                self._last_upper_bound_pruned += 1
                return True
            if abs(upper - incumbent_total) <= 1e-9 and effective_time >= incumbent_effective_time - 1e-9:
                self._last_upper_bound_pruned += 1
                return True
            return False

        # 2. Dominance Function (Pareto Pruning)
        def dominance_fn(a: Label, ma: dict[str, float], b: Label, mb: dict[str, float]) -> bool:
            if not self.use_dominance:
                return False
            if self.custom_dominance_fn is not None:
                return bool(self.custom_dominance_fn(a, ma, b, mb))
            if objective is not None:
                if self.use_bound_dominance:
                    return bool(objective.dominates(score_a=a.score, metrics_a=ma, score_b=b.score, metrics_b=mb))
                ma_plain = dict(ma)
                mb_plain = dict(mb)
                ma_plain.pop("score_upper_bound_total", None)
                ma_plain.pop("score_upper_bound_gap", None)
                mb_plain.pop("score_upper_bound_total", None)
                mb_plain.pop("score_upper_bound_gap", None)
                return bool(objective.dominates(score_a=a.score, metrics_a=ma_plain, score_b=b.score, metrics_b=mb_plain))
            # a dominates b if:
            return (
                a.score >= b.score
                and a.ride_minutes >= b.ride_minutes * 0.95
                and ma["hull_area"] >= mb["hull_area"]
            )

        # Pre-compute metrics cache
        metrics_cache: dict[int, tuple[Label, dict[str, float]]] = {}

        def cache_metrics_for_label(label: Label, metrics: dict[str, float]) -> dict[str, float]:
            metrics_cache[id(label)] = (label, metrics)
            return metrics

        def compute_or_get_metrics(label: Label) -> dict[str, float]:
            entry = metrics_cache.get(id(label))
            if entry is not None and entry[0] is label:
                return entry[1]
            if entry is None or entry[0] is not label:
                if self.custom_metrics_fn is not None:
                    metrics = self.custom_metrics_fn(planner, label)
                else:
                    metrics = self._calculate_metrics(planner, label)
                    if objective is not None:
                        metrics.update(objective.metrics_from_label(label, budget_minutes=budget_minutes))
                        if self.use_bound_dominance or self.use_upper_bound_pruning or self.use_potential_aware_beam:
                            current_stop_code = label.legs[-1].to_code if label.legs else origin
                            metrics["score_upper_bound_total"] = objective.optimistic_total_upper_bound_from_metrics(
                                metrics,
                                budget_minutes=budget_minutes,
                                min_leg_minutes=min_leg_minutes,
                            )
                            metrics["score_upper_bound_total"] = min(
                                float(metrics["score_upper_bound_total"]),
                                self._state_aware_upper_bound(
                                    planner=planner,
                                    objective=objective,
                                    current_stop_code=current_stop_code,
                                    metrics=metrics,
                                    budget_minutes=budget_minutes,
                                    min_leg_minutes=min_leg_minutes,
                                ),
                            )
                            metrics["score_upper_bound_gap"] = round(
                                max(
                                    0.0,
                                    float(metrics["score_upper_bound_total"])
                                    - float(metrics.get("stop_score_total", 0.0)),
                                ),
                                6,
                            )
                return cache_metrics_for_label(label, metrics)
            return entry[1]

        # Config equivalents
        min_transfer_minutes = self.min_transfer_minutes
        max_rounds = self.max_rounds_override or min(220, max(40, budget_minutes // 2 + 20))
        lookahead_minutes = 120

        # Initialization
        rounds: list[dict[str, list[Label]]] = [defaultdict(list) for _ in range(max_rounds + 1)]
        marked_stops: set[str] = {origin}
        
        quadrant = planner.quadrant_map.get(origin, 0)
        base_label = Label(
            arrival=depart_time,
            ride_minutes=0,
            distance_km=0.0,
            visited=frozenset({origin}),
            quadrant_mask=quadrant,
            legs=(),
            score=0.0,
            stop_counts=((origin, 1),),
            line_counts=tuple(),
            transfers=0,
            min_transfer_gap=999999,
            objective_score_total=0.0,
            objective_scored_count=0,
        )
        base_metrics = compute_or_get_metrics(base_label)
        scored_base = replace(base_label, score=scoring_fn(base_label, base_metrics))
        cache_metrics_for_label(scored_base, base_metrics)
        rounds[0][origin].append(scored_base)
        self._last_labels_count += 1
        
        best_accepted: Label | None = None
        best_fallback: Label | None = None
        
        start_time = time.perf_counter()

        class RAPTORTimeout(Exception):
            pass

        class RAPTORLabelCap(Exception):
            pass

        def check_resource_caps(now: float | None = None) -> None:
            current = now if now is not None else time.perf_counter()
            if self.timeout_seconds and (current - start_time) > self.timeout_seconds:
                raise RAPTORTimeout()
            if self.max_labels is not None and self.max_labels > 0 and self._last_labels_count >= self.max_labels:
                raise RAPTORLabelCap()
        
        try:
            # 3. RAPTOR Core Search
            for round_idx in range(max_rounds):
                if not marked_stops:
                    break
                check_resource_caps()

                next_marked: set[str] = set()

                for stop_code in sorted(marked_stops):
                    labels_here = rounds[round_idx].get(stop_code, [])
                    if not labels_here:
                        continue

                    for label in labels_here:
                        check_resource_caps()

                        remaining = time_limit - label.arrival
                        if remaining <= 0:
                            continue

                        # Query departures from current stop; continuation on the same trip
                        # is handled by a relaxed depart-threshold check below.
                        candidates = planner._next_edges(
                            stop_code,
                            label.arrival,
                            lookahead_minutes=min(lookahead_minutes, remaining),
                        )
                        if not candidates:
                            continue

                        prev_leg = label.legs[-1] if label.legs else None
                        origin_code = origin if not label.legs else label.legs[0].from_code
                        base_visits = dict(label.stop_counts)
                        candidate_pool: list[TripEdge] = []
                        for edge in candidates:
                            check_resource_caps()
                            if edge.from_code != stop_code:
                                continue
                            if self.custom_edge_filter_fn is not None and not self.custom_edge_filter_fn(label, edge):
                                continue
                            if edge.arrive > time_limit:
                                break

                            same_trip = (
                                prev_leg is not None
                                and edge.trip_id == prev_leg.trip_id
                                and edge.line_id == prev_leg.line_id
                            )
                            earliest_depart = label.arrival if same_trip else (label.arrival + min_transfer_minutes)
                            if edge.depart < earliest_depart:
                                continue
                            if objective is not None and not objective.can_append(
                                origin_code=origin_code,
                                depart_time=depart_time,
                                arrival_time=edge.arrive,
                                visits=base_visits,
                                next_stop_code=edge.to_code,
                                budget_minutes=budget_minutes,
                            ):
                                continue
                            candidate_pool.append(edge)

                        candidates = self._trim_objective_candidates(
                            candidates=candidate_pool,
                            objective=objective,
                            visits=base_visits,
                            prev_leg=prev_leg,
                            budget_minutes=budget_minutes,
                        )
                        for edge in candidates:
                            check_resource_caps()
                            same_trip = (
                                prev_leg is not None
                                and edge.trip_id == prev_leg.trip_id
                                and edge.line_id == prev_leg.line_id
                            )
                            new_label = self._extend_edge(planner, label, edge, same_trip=same_trip)
                            if new_label is None:
                                continue

                            self._last_labels_count += 1
                            check_resource_caps()
                            metrics = compute_or_get_metrics(new_label)
                            if objective is not None and metrics.get("effective_budget_feasible") is False:
                                continue
                            if self.use_upper_bound_pruning and should_prune_upper_bound(metrics):
                                continue
                            scored_label = replace(new_label, score=scoring_fn(new_label, metrics))
                            cache_metrics_for_label(scored_label, metrics)
                            to_stop = edge.to_code

                            inserted = self._insert_label(
                                rounds[round_idx + 1][to_stop],
                                scored_label,
                                metrics,
                                dominance_fn,
                                compute_or_get_metrics,
                            )
                            if inserted:
                                next_marked.add(to_stop)
                                if len(new_label.legs) >= 2:
                                    update_incumbent(metrics)
                                    if best_fallback is None or scored_label.score > best_fallback.score:
                                        best_fallback = scored_label
                                    if self.custom_accept_fn is None or self.custom_accept_fn(scored_label, metrics):
                                        if best_accepted is None or scored_label.score > best_accepted.score:
                                            best_accepted = scored_label

                marked_stops = next_marked

        except RAPTORTimeout:
            self._last_termination_reason = "timeout"
        except RAPTORLabelCap:
            self._last_termination_reason = "label_cap"

        best = best_accepted or best_fallback
        if best is None:
            return []

        # 4. Final selection: Pick the highest scored journey
        # Convert JourneyLeg to TripEdge representation using app layer transformations
        return planner._convert_journey_legs_to_trip_edges(list(best.legs))
        
    def _extend_edge(self, planner, base: Label, edge: TripEdge, *, same_trip: bool) -> Label | None:
        if edge.arrive <= edge.depart:
            return None
        if edge.depart < base.arrival:
            return None

        duration = edge.arrive - edge.depart
        distance_inc = edge.distance_km
        visited = set(base.visited)
        visited.add(edge.to_code)
        q_mask = base.quadrant_mask | planner.quadrant_map.get(edge.to_code, 0)

        legs = list(base.legs)
        prev_leg = legs[-1] if legs else None
        boarding_new = not same_trip

        # Keep segment-level legs for fair metric computation in experiments.
        # If we collapse multiple hops into one leg, unique_stops gets undercounted.
        legs.append(JourneyLeg(
            line_id=edge.line_id,
            line_name=edge.line_name,
            trip_id=edge.trip_id,
            from_code=edge.from_code,
            to_code=edge.to_code,
            depart=edge.depart,
            arrive=edge.arrive,
            distance_km=distance_inc,
            stop_hops=1,
        ))

        stop_counts = dict(base.stop_counts)
        if not base.legs:
            stop_counts[edge.from_code] = stop_counts.get(edge.from_code, 0) + 1
        stop_counts[edge.to_code] = stop_counts.get(edge.to_code, 0) + 1
        if self.max_stop_visits is not None and stop_counts[edge.to_code] > self.max_stop_visits:
            return None

        line_counts = dict(base.line_counts)
        if boarding_new:
            line_counts[edge.line_id] = line_counts.get(edge.line_id, 0) + 1
            if self.max_line_visits is not None and line_counts[edge.line_id] > self.max_line_visits:
                return None

        objective_score_total = float(getattr(base, "objective_score_total", 0.0) or 0.0)
        objective_scored_count = int(getattr(base, "objective_scored_count", 0) or 0)
        if getattr(self, "objective", None) is not None:
            origin_code = edge.from_code if not base.legs else base.legs[0].from_code
            if edge.to_code != origin_code and edge.to_code not in base.visited:
                objective_score_total += float(self.objective.score_for_stop(edge.to_code))
                objective_scored_count += 1

        return Label(
            arrival=edge.arrive,
            ride_minutes=base.ride_minutes + duration,
            distance_km=base.distance_km + distance_inc,
            visited=frozenset(visited),
            quadrant_mask=q_mask,
            legs=tuple(legs),
            score=0.0,
            stop_counts=tuple(sorted(stop_counts.items())),
            line_counts=tuple(sorted(line_counts.items())),
            transfers=base.transfers + (1 if boarding_new and prev_leg else 0),
            min_transfer_gap=0,
            objective_score_total=objective_score_total,
            objective_scored_count=objective_scored_count,
        )

    def _insert_label(
        self,
        bucket: list[Label],
        candidate: Label,
        candidate_metrics: dict,
        dominance_fn: Callable,
        get_metrics: Callable,
    ) -> bool:
        if self.use_dominance:
            # Check if candidate is dominated
            for ex in bucket:
                if dominance_fn(ex, get_metrics(ex), candidate, candidate_metrics):
                    return False

        # Add candidate and remove those it dominates (if dominance is active)
        if self.use_dominance:
            bucket[:] = [ex for ex in bucket if not dominance_fn(candidate, candidate_metrics, ex, get_metrics(ex))]

        bucket.append(candidate)
        
        if self.use_beam:
            if self.use_potential_aware_beam and getattr(self, "objective", None) is not None:
                bucket.sort(
                    key=lambda l: self._beam_priority(l, get_metrics(l)),
                    reverse=True,
                )
            else:
                bucket.sort(key=lambda l: l.score, reverse=True)
            if len(bucket) > self.beam_width:
                trimmed = len(bucket) - self.beam_width
                del bucket[self.beam_width:]
                self._last_beam_trim_events += 1
                self._last_beam_trimmed_labels += trimmed
            
        return True

    def _calculate_metrics(self, planner, label: Label) -> dict[str, float]:
        if getattr(self, "objective", None) is not None:
            sc = dict(label.stop_counts)
            repeat_max = max(sc.values()) if sc else 0
            return {
                "unique_stops": float(max(0, len(label.visited) - 1)),
                "hull_area": 0.0,
                "quadrants": float(bin(label.quadrant_mask).count('1')),
                "stop_repeat_max": float(repeat_max),
            }
        coords = []
        for code in label.visited:
            station = planner.stations.get(code)
            if station: coords.append((station.lat, station.lon))
            
        hull_area = 0.0
        if len(coords) >= 3:
            pts = [project_to_plane(lat, lon, *planner.hakata_coord) for lat, lon in coords if lat and lon]
            pts = list(set(pts))
            if len(pts) >= 3:
                # naive centroid sorting shoelace
                cx = sum(p[0] for p in pts) / len(pts)
                cy = sum(p[1] for p in pts) / len(pts)
                pts.sort(key=lambda p: (math.atan2(p[1]-cy, p[0]-cx)))
                a = 0.0
                for i in range(len(pts)):
                    x1, y1 = pts[i]
                    x2, y2 = pts[(i+1)%len(pts)]
                    a += (x1*y2 - x2*y1)
                hull_area = abs(a) / 2.0
                
        sc = dict(label.stop_counts)
        repeat_max = max(sc.values()) if sc else 0
        quadrants = bin(label.quadrant_mask).count('1')
        
        return {
            "unique_stops": float(len(label.visited)),
            "hull_area": hull_area,
            "quadrants": float(quadrants),
            "stop_repeat_max": float(repeat_max)
        }

    def _get_min_positive_ride_minutes(self, planner) -> float:
        cached = getattr(planner, "_exp1_min_positive_ride_minutes", None)
        if cached is not None:
            return float(cached)

        min_positive: float | None = None
        for edge in getattr(planner, "static_edges", []) or []:
            ride = max(0, int(getattr(edge, "arrive", 0)) - int(getattr(edge, "depart", 0)))
            if ride <= 0:
                continue
            if min_positive is None or ride < min_positive:
                min_positive = float(ride)

        if min_positive is None:
            for schedule in getattr(planner, "stop_schedules", {}).values():
                for edge in getattr(schedule, "edges", []) or []:
                    ride = max(0, int(getattr(edge, "arrive", 0)) - int(getattr(edge, "depart", 0)))
                    if ride <= 0:
                        continue
                    if min_positive is None or ride < min_positive:
                        min_positive = float(ride)

        if min_positive is None:
            min_positive = 1.0
        setattr(planner, "_exp1_min_positive_ride_minutes", float(min_positive))
        return float(min_positive)

    def _beam_priority(self, label: Label, metrics: dict[str, float]) -> tuple[float, float, float, float]:
        total = float(metrics.get("stop_score_total", 0.0))
        upper = float(metrics.get("score_upper_bound_total", total))
        gap = max(0.0, upper - total)
        effective_time = float(metrics.get("effective_time_minutes", metrics.get("total_time_minutes", 0.0)))
        beam_score = total + self.beam_potential_weight * gap
        return (
            round(beam_score, 6),
            round(total, 6),
            -round(effective_time, 6),
            round(float(label.score), 6),
        )

    def _state_aware_upper_bound(
        self,
        *,
        planner,
        objective,
        current_stop_code: str,
        metrics: dict[str, float],
        budget_minutes: int,
        min_leg_minutes: float,
    ) -> float:
        current_total = float(metrics.get("stop_score_total", 0.0))
        current_count = int(metrics.get("scored_stop_count", metrics.get("unique_stops", 0)) or 0)
        effective_time = float(metrics.get("effective_time_minutes", metrics.get("total_time_minutes", 0.0)))
        extra_capacity = objective.optimistic_additional_stop_capacity(
            effective_time_minutes=effective_time,
            budget_minutes=budget_minutes,
            scored_stop_count=current_count,
            min_leg_minutes=min_leg_minutes,
        )
        if extra_capacity <= 0:
            return round(current_total, 6)

        remaining_effective = max(0, int(math.floor(float(budget_minutes) - effective_time)))
        if remaining_effective <= 0:
            return round(current_total, 6)

        reachable_additional = self._reachable_additional_score_upper_bound(
            planner=planner,
            objective=objective,
            current_stop_code=str(current_stop_code),
            remaining_effective_minutes=remaining_effective,
            extra_capacity=extra_capacity,
            min_leg_minutes=min_leg_minutes,
        )
        return round(current_total + reachable_additional, 6)

    def _reachable_additional_score_upper_bound(
        self,
        *,
        planner,
        objective,
        current_stop_code: str,
        remaining_effective_minutes: int,
        extra_capacity: int,
        min_leg_minutes: float,
    ) -> float:
        budget_key = max(0, int(remaining_effective_minutes))
        prefix_cache = getattr(planner, "_exp1_reachable_score_prefix_cache", None)
        if prefix_cache is None:
            prefix_cache = {}
            setattr(planner, "_exp1_reachable_score_prefix_cache", prefix_cache)

        cache_key = (
            id(objective),
            str(current_stop_code),
            int(budget_key),
            round(float(min_leg_minutes), 6),
        )
        if cache_key not in prefix_cache:
            min_ride = self._get_min_ride_lower_bounds(planner, str(current_stop_code))
            max_extra = objective.max_additional_stop_capacity(
                budget_minutes=budget_key,
                min_leg_minutes=min_leg_minutes,
            )
            feasible_budget = float(budget_key)
            selected_scores: list[float] = []
            if max_extra > 0 and feasible_budget > 0.0:
                for stop_code, stop_score in objective._score_ranked_stop_entries:
                    if stop_code == str(current_stop_code):
                        continue
                    ride_lb = min_ride.get(stop_code)
                    if ride_lb is None:
                        continue
                    if float(ride_lb) + float(objective.dwell_minutes) > feasible_budget + 1e-9:
                        continue
                    selected_scores.append(float(stop_score))
                    if len(selected_scores) >= max_extra:
                        break
            prefix = [0.0]
            running = 0.0
            for stop_score in selected_scores:
                running += float(stop_score)
                prefix.append(running)
            prefix_cache[cache_key] = tuple(prefix)

        prefix = prefix_cache[cache_key]
        safe = max(0, min(int(extra_capacity), len(prefix) - 1))
        return float(prefix[safe])

    def _get_min_ride_lower_bounds(self, planner, start_stop_code: str) -> dict[str, float]:
        cache = getattr(planner, "_exp1_min_ride_lower_bounds", None)
        if cache is None:
            cache = {}
            setattr(planner, "_exp1_min_ride_lower_bounds", cache)

        start_key = str(start_stop_code)
        if start_key in cache:
            return cache[start_key]

        adjacency = self._get_min_ride_graph(planner)
        dist: dict[str, float] = {start_key: 0.0}
        heap: list[tuple[float, str]] = [(0.0, start_key)]

        while heap:
            current_dist, stop_code = heapq.heappop(heap)
            if current_dist > dist.get(stop_code, float("inf")) + 1e-9:
                continue
            for next_code, ride_minutes in adjacency.get(stop_code, {}).items():
                candidate = current_dist + float(ride_minutes)
                if candidate + 1e-9 < dist.get(next_code, float("inf")):
                    dist[next_code] = candidate
                    heapq.heappush(heap, (candidate, next_code))

        cache[start_key] = dist
        return dist

    def _get_min_ride_graph(self, planner) -> dict[str, dict[str, float]]:
        cached = getattr(planner, "_exp1_min_ride_graph", None)
        if cached is not None:
            return cached

        adjacency: dict[str, dict[str, float]] = {}
        for edge in getattr(planner, "static_edges", []) or []:
            from_code = str(getattr(edge, "from_code", ""))
            to_code = str(getattr(edge, "to_code", ""))
            if not from_code or not to_code or from_code == to_code:
                continue
            ride = max(0, int(getattr(edge, "arrive", 0)) - int(getattr(edge, "depart", 0)))
            if ride <= 0:
                continue
            bucket = adjacency.setdefault(from_code, {})
            best = bucket.get(to_code)
            if best is None or ride < best:
                bucket[to_code] = float(ride)

        setattr(planner, "_exp1_min_ride_graph", adjacency)
        return adjacency

    def _trim_objective_candidates(
        self,
        *,
        candidates: list[TripEdge],
        objective,
        visits: dict[str, int],
        prev_leg: JourneyLeg | None,
        budget_minutes: int,
    ) -> list[TripEdge]:
        # Treat candidate capping as part of the beam-style width-control layer:
        # when Beam is disabled in ablations, pre-expansion candidate trimming
        # must also be disabled.
        if objective is None or not self.use_beam:
            return candidates

        cap = self._objective_candidate_cap(budget_minutes)
        if cap is None or cap <= 0 or len(candidates) <= cap:
            return candidates

        def rank_key(edge: TripEdge) -> tuple[int, float, int, int]:
            same_trip = int(
                prev_leg is not None
                and edge.trip_id == prev_leg.trip_id
                and edge.line_id == prev_leg.line_id
            )
            priority = float(objective.edge_priority(edge=edge, visits=visits, prev_edge=prev_leg))
            return (
                same_trip,
                round(priority, 6),
                -int(edge.depart),
                -int(edge.arrive),
            )

        ranked = sorted(candidates, key=rank_key, reverse=True)
        trimmed = len(ranked) - cap
        if trimmed > 0:
            self._last_candidate_trim_events += 1
            self._last_candidate_trimmed_edges += trimmed
        return ranked[:cap]

    def _objective_candidate_cap(self, budget_minutes: int) -> int | None:
        if budget_minutes <= self.objective_candidate_short_budget_max:
            return self.objective_candidate_cap_short
        return self.objective_candidate_cap_long
