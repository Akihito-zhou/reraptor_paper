
from __future__ import annotations

from typing import TYPE_CHECKING

from ..planner_models import ChallengeConfig, ChallengePlan, Label
from ..raptor import run_raptor_challenge

if TYPE_CHECKING:
    from ..planner import PlannerService


def get_config(planner: PlannerService) -> ChallengeConfig:
    """Returns the configuration for the Longest Duration challenge."""
    transfer_buffer = 5
    transfer_penalty_weight = 800

    def scoring_fn(label: Label, metrics: dict[str, float]) -> float:
        stop_counts = dict(label.stop_counts)
        for stop, count in stop_counts.items():
            limit = challenge_config.max_stop_visits
            if stop in planner.hakata_stops:
                limit = challenge_config.hakata_max_visits or limit
        # Calculate average speed (km/h)
        # avg_speed = label.distance_km / (label.ride_minutes / 60) if label.ride_minutes > 0 else 0
        # speed_penalty = max(0, avg_speed - 25) * 200 

        return (
            label.ride_minutes * 40000  # High weight
            + metrics["max_leg_minutes"] * 500
            + metrics["unique_lines"] * 800
            + metrics["quadrants"] * 2000
            + metrics["avg_radius"] * 250
            + metrics["boundary_ratio"] * 3000
            + metrics["hull_area"] * 100
            - metrics["center_ratio"] * 4000
            - metrics["short_leg_ratio"] * 1000
            - metrics["repeat_penalty"] * 500      # Restored to 500
            - metrics["stop_repeat_total"] * 900   # Restored to 900
            # - speed_penalty * 100
            - label.transfers * 100
        )

    def dominance_fn(
        a: Label,
        metrics_a: dict[str, float],
        b: Label,
        metrics_b: dict[str, float],
    ) -> bool:
        # Standard RAPTOR: a dominates b if a is faster (min time) and effectively better 
        # But for Longest Duration, we WANT later arrival if it means more duration.
        # So we only prune if 'a' has MORE duration AND arrives EARLIER.
        # If 'a' has more duration but arrives LATER, we keep both (since 'b' might be useful for catching a specific connecting bus).
        if (
            a.ride_minutes >= b.ride_minutes
            and metrics_a["unique_lines"] >= metrics_b["unique_lines"]
            and a.arrival <= b.arrival
        ):
            return a.score >= b.score
        return False

    def accept_fn(_: Label, __: dict[str, float]) -> bool:
        return True

    challenge_config = ChallengeConfig(
        challenge_id="longest-duration",
        title="24時間ロングライド",
        tagline="博多から出発し24時間ひたすら乗り継ぎ続ける耐久チャレンジ。",
        theme_tags=["時間最大化", "耐久"],
        badge="最長乗車",
        require_quadrants=False,
        max_rounds=150,  # Deep search
        scoring_fn=scoring_fn,
        dominance_fn=dominance_fn,
        accept_fn=accept_fn,
        min_transfer_minutes=5, 
        max_stop_visits=20,     
        max_line_visits=10,     
        hakata_max_visits=20,   
    )
    return challenge_config


def plan(planner: "PlannerService") -> ChallengePlan | None:
    """Plans the Longest Duration challenge."""
    config = get_config(planner)
    
    # Use hakata stops as start/end for core challenges
    hakata = [s for s in planner.hakata_stops if s in planner.routes_by_stop]
    
    # RAPTOR defaults end_stops=None to start_stops (circular). 
    # We want open-ended, so we must explicitly pass ALL stops.
    all_stops = list(planner.stations.keys())
    
    raptor_plan = run_raptor_challenge(
        planner, config,
        start_stops=hakata or None,
        end_stops=all_stops, 
    )
    return raptor_plan


