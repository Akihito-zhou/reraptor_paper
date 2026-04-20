
from __future__ import annotations

from typing import TYPE_CHECKING

from ..planner_models import ChallengeConfig, ChallengePlan, Label
from ..raptor import run_raptor_challenge

if TYPE_CHECKING:
    from ..planner import PlannerService


def get_config(planner: PlannerService) -> ChallengeConfig:
    """Returns the configuration for the Most Unique Stops challenge."""
    transfer_buffer = 6
    transfer_penalty_weight = 1000

    def scoring_fn(label: Label, metrics: dict[str, float]) -> float:
        return (
            metrics["unique_stops"] * 10000  # Primary goal: visit new stops
            + metrics["total_stops_passed"] * 2000  # Secondary: pass many stops
            + metrics["quadrants"] * 1200
            + metrics["avg_radius"] * 180
            + label.distance_km * 40
            + metrics["boundary_ratio"] * 2500
            - metrics["center_ratio"] * 2500
            - metrics["repeat_penalty"] * 600
            - metrics["stop_repeat_total"] * 4000  # Penalty for repeats
            - label.transfers * transfer_penalty_weight
        )

    def dominance_fn(
        a: Label,
        metrics_a: dict[str, float],
        b: Label,
        metrics_b: dict[str, float],
    ) -> bool:
        if (
            metrics_a["unique_stops"] >= metrics_b["unique_stops"]
            and a.arrival <= b.arrival
        ):
            return a.score >= b.score
        return False

    def accept_fn(_: Label, __: dict[str, float]) -> bool:
        return True

    return ChallengeConfig(
        challenge_id="most-stops",
        title="ユニーク停留所コンプリート",
        tagline="24時間以内にできるだけ多くの停留所を踏破して博多へ戻るトレース。",
        theme_tags=["停留所制覇", "博多起終点"],
        badge="停留所ハンター",
        require_quadrants=False,
        max_rounds=150,  # Deep search
        scoring_fn=scoring_fn,
        dominance_fn=dominance_fn,
        accept_fn=accept_fn,
        min_transfer_minutes=transfer_buffer,
        max_stop_visits=4,
        forbid_non_hakata_duplicates=False,
    )


def plan(planner: "PlannerService") -> ChallengePlan | None:
    """Plans the Most Unique Stops challenge."""
    config = get_config(planner)
    
    # Use hakata stops as start/end for core challenges
    hakata = [s for s in planner.hakata_stops if s in planner.routes_by_stop]
    all_stops = list(planner.stations.keys())

    raptor_plan = run_raptor_challenge(
        planner, config,
        start_stops=hakata or None,
        end_stops=all_stops, # Open-ended for max collection
    )
    return raptor_plan
