from __future__ import annotations

from paper.experiments.common.stop_scoring import StopScoringProfile
from paper.experiments.exp3_parameter_sensitivity.sensitivity_protocol import (
    DEFAULT_SPEC,
    INTERACTION_CORNER_SPECS,
    OAT_SPECS,
    select_specs,
)
from paper.experiments.exp3_parameter_sensitivity.run_sensitivity import (
    CANONICAL_BUDGETS,
    DEFAULT_SCORE_SEEDS,
    INTERACTION_ORIGINS,
    INTERACTION_SCORE_SEEDS,
)


def test_oat_protocol_has_one_default_and_seventeen_new_configs() -> None:
    assert len(OAT_SPECS) == 18
    assert sum(spec.config_id == "default" for spec in OAT_SPECS) == 1
    assert len({spec.config_id for spec in OAT_SPECS}) == len(OAT_SPECS)
    assert len(select_specs(panel="oat", include_default=False)) == 17


def test_interaction_protocol_runs_only_four_new_corner_cells() -> None:
    assert len(INTERACTION_CORNER_SPECS) == 4
    assert {
        (spec.beam_width, spec.candidate_cap_short, spec.candidate_cap_long)
        for spec in INTERACTION_CORNER_SPECS
    } == {
        (25, 15, 10),
        (25, 60, 40),
        (100, 15, 10),
        (100, 60, 40),
    }


def test_default_sensitivity_spec_reproduces_current_algorithm_parameters() -> None:
    objective = DEFAULT_SPEC.objective(
        stop_scores={"A": 10},
        dwell_minutes=10,
        search_mode="score_guided",
    )
    algorithm = DEFAULT_SPEC.algorithm(
        objective=objective,
        timeout_seconds=60.0,
    )

    assert isinstance(objective, StopScoringProfile)
    assert objective.reward_coefficient == 10000.0
    assert objective.score_per_hour_coefficient == 5.0
    assert objective.effective_time_coefficient == 0.1
    assert objective.overrun_penalty == 50000.0
    assert algorithm.beam_width == 50
    assert algorithm.objective_candidate_cap_short == 30
    assert algorithm.objective_candidate_cap_long == 20
    assert algorithm.negative_repeat_penalty == 50000.0
    assert algorithm.negative_short_hop_penalty == 20000.0


def test_canonical_task_grids_have_expected_sizes() -> None:
    assert CANONICAL_BUDGETS == (120, 240, 360, 480)
    assert len(DEFAULT_SCORE_SEEDS) == 5
    assert len(INTERACTION_ORIGINS) == 3
    assert len(INTERACTION_SCORE_SEEDS) == 2
    assert 10 * 3 * len(CANONICAL_BUDGETS) * len(DEFAULT_SCORE_SEEDS) == 600
    assert (
        len(INTERACTION_ORIGINS)
        * 3
        * len(CANONICAL_BUDGETS)
        * len(INTERACTION_SCORE_SEEDS)
        == 72
    )
