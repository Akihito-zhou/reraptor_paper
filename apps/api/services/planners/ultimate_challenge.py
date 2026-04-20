"""
Ultimate Challenge Planner - The most extreme route covering all of Fukuoka's boundaries.

究極チャレンジプランナー - 福岡市の端から端まで制覇する究極のルート。

Uses the same RAPTOR greedy algorithm as longest-duration but with enhanced scoring
that prioritizes maximum ride time AND maximum boundary coverage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..planner_models import ChallengeConfig, ChallengePlan, Label
from ..raptor import run_raptor_challenge

if TYPE_CHECKING:
    from ..planner import PlannerService


# Famous boundary stations that earn bonus points when visited
BOUNDARY_LANDMARKS = {
    "675186",  # 福岡空港国際線
    "676574",  # マリンワールド海の中道
    "676585",  # 志賀島
    "675529",  # 九大ビッグオレンジ
    "675530",  # 九大工学部
    "678064",  # 九大センターゾーン入口
    "675460",  # 姪浜
    "676882",  # 福岡タワー
    "675382",  # 油山
    "675628",  # 西鉄大橋駅
    "678086",  # こども病院
    "676873",  # PayPayドーム
    "675988",  # 香椎宮
}


def get_config(planner: PlannerService) -> ChallengeConfig:
    """Returns the configuration for the Ultimate Challenge."""
    
    def scoring_fn(label: Label, metrics: dict[str, float]) -> float:
        # Calculate boundary landmark bonus
        stop_counts = dict(label.stop_counts)  # Convert tuple to dict
        visited_stops = set(stop_counts.keys())
        landmark_bonus = len(visited_stops & BOUNDARY_LANDMARKS) * 8000
        
        return (
            # PRIMARY: Maximize ride time (HIGHEST weight - must beat longest-duration)
            label.ride_minutes * 80000  # Very high weight for duration
            # SECONDARY: Maximize distance
            + label.distance_km * 800
            # TERTIARY: Maximize boundary coverage
            + metrics["quadrants"] * 8000  # 4 quadrants = 32000 bonus
            + metrics["boundary_ratio"] * 10000  # Favor boundary routes
            + metrics["hull_area"] * 500  # Encourage geographical spread
            + metrics["max_radius"] * 1500  # Encourage reaching far points
            + metrics["avg_radius"] * 400  # Encourage staying away from center
            # Route quality
            + metrics["unique_lines"] * 1000
            + metrics["max_leg_minutes"] * 300  # Favor long individual legs
            # Add landmark bonus (visiting famous boundary spots)
            + landmark_bonus
            # PENALTIES (reduced to allow longer routes)
            - metrics["center_ratio"] * 5000  # Reduced penalty
            - metrics["short_leg_ratio"] * 400
            - metrics["repeat_penalty"] * 200
            - metrics["stop_repeat_total"] * 300
            - label.transfers * 20  # Minimal transfer penalty
        )

    def dominance_fn(
        a: Label,
        metrics_a: dict[str, float],
        b: Label,
        metrics_b: dict[str, float],
    ) -> bool:
        # Looser dominance to explore more boundary routes
        if (
            a.ride_minutes >= b.ride_minutes
            and metrics_a["quadrants"] >= metrics_b["quadrants"]
            and metrics_a["boundary_ratio"] >= metrics_b["boundary_ratio"]
            and a.arrival <= b.arrival
        ):
            return a.score >= b.score
        return False

    def accept_fn(_: Label, __: dict[str, float]) -> bool:
        return True

    config = ChallengeConfig(
        challenge_id="ultimate-challenge",
        title="究極の福岡バス制覇",
        tagline="福岡市の全境界を巡り、12時間以上乗り続ける究極のチャレンジ。九大から志賀島、油山まで制覇せよ。",
        theme_tags=["究極", "境界制覇", "最長乗車", "全区制覇"],
        badge="究極制覇者",
        require_quadrants=True,  # Must cover all 4 quadrants
        max_rounds=70,  # More rounds for comprehensive exploration
        scoring_fn=scoring_fn,
        dominance_fn=dominance_fn,
        accept_fn=accept_fn,
        min_transfer_minutes=5,
        max_stop_visits=6,  # Allow more revisits for longer routes
        max_line_visits=4,  # Allow more line revisits
        hakata_max_visits=8,  # Allow returning to hub multiple times
    )
    return config


def plan(planner: "PlannerService") -> ChallengePlan | None:
    """Plans the Ultimate Challenge using RAPTOR greedy algorithm."""
    config = get_config(planner)
    
    # Use hakata stops as start/end for core challenges
    hakata = [s for s in planner.hakata_stops if s in planner.routes_by_stop]
    
    # Use RAPTOR challenge with enhanced boundary scoring
    raptor_plan = run_raptor_challenge(
        planner, config,
        start_stops=hakata or None,
        end_stops=hakata or None,
    )
    if raptor_plan:
        return raptor_plan

    # Fallback to beam search with boundary focus
    result = planner.run_beam_search(
        score_key="ride",  # Maximize ride time
        require_unique=False,
        require_quadrants=True,  # Must cover all quadrants
        max_queue=4000,  # Larger queue for more exploration
        max_expansions=200000,  # More expansions for comprehensive search
        max_stop_visits=5,
        max_line_visits=3,
        min_transfer_minutes=5,
        transfer_penalty_minutes=2,  # Lower penalty
        hakata_max_visits=5,
        stop_repeat_penalty_weight=400,
    )
    if result:
        from ..planner_utils import collapse_edges, derive_quadrant_labels
        legs = collapse_edges(result.path, planner.stations)
        
        return ChallengePlan(
            challenge_id="ultimate-challenge",
            title="究極の福岡バス制覇",
            tagline="福岡市の全境界を巡り、12時間以上乗り続ける究極のチャレンジ。",
            theme_tags=["究極", "境界制覇", "最長乗車"],
            badge="究極制覇者",
            legs=legs,
            start_stop_name=planner.stations[planner.hakata_stops[0]].name,
            wards=derive_quadrant_labels(legs, planner.quadrant_map),
            stations=planner.stations,
        )

    return None
