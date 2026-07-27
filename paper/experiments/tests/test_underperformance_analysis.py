from __future__ import annotations

import pandas as pd

from paper.experiments.exp1_algorithm_comparison.analyze_underperformance import (
    NSGA_NAME,
    OURS_NAME,
    build_task_frame,
    crossed_block_bootstrap_ci,
    summarize_subset,
)


def _row(
    *,
    algorithm: str,
    origin: str,
    departure: int,
    budget: int,
    score_seed: int,
    seed: int,
    score: float,
    failure: bool = False,
) -> dict:
    return {
        "algorithm": algorithm,
        "origin_name": origin,
        "depart_time": departure,
        "budget_minutes": budget,
        "score_seed": score_seed,
        "seed": seed,
        "stop_score_total": score,
        "elapsed_ms": 10.0 + seed,
        "scored_stop_count": 0 if failure else max(1, int(score // 10)),
        "feasible": not failure,
        "algorithm_failure": failure,
        "violation_reason": "effective_budget_exceeded" if failure else "",
    }


def _synthetic_runs() -> pd.DataFrame:
    rows: list[dict] = []
    for score_seed in [101, 102]:
        for origin in ["a", "b"]:
            for departure in [420, 600]:
                for budget in [120, 240]:
                    rows.append(
                        _row(
                            algorithm=OURS_NAME,
                            origin=origin,
                            departure=departure,
                            budget=budget,
                            score_seed=score_seed,
                            seed=0,
                            score=100.0,
                        )
                    )
                    for seed in range(5):
                        failure = (
                            score_seed == 101
                            and origin == "a"
                            and departure == 420
                            and budget == 120
                            and seed == 0
                        )
                        rows.append(
                            _row(
                                algorithm=NSGA_NAME,
                                origin=origin,
                                departure=departure,
                                budget=budget,
                                score_seed=score_seed,
                                seed=seed,
                                score=0.0 if failure else 80.0,
                                failure=failure,
                            )
                        )
    return pd.DataFrame(rows)


def test_task_aggregation_keeps_failure_as_zero() -> None:
    task = build_task_frame(_synthetic_runs(), expected_task_count=16)
    assert len(task) == 16
    failed_task = task[
        (task["score_seed"] == 101)
        & (task["origin_name"] == "a")
        & (task["depart_time"] == 420)
        & (task["budget_minutes"] == 120)
    ].iloc[0]
    assert failed_task["nsga_failure_count"] == 1
    assert failed_task["nsga_score"] == 64.0
    assert failed_task["nsga_score_feasible_only"] == 80.0
    assert failed_task["score_gap"] == 36.0
    assert failed_task["score_gap_feasible_only"] == 20.0


def test_crossed_bootstrap_is_deterministic_and_exact_for_constant_gap() -> None:
    task = build_task_frame(_synthetic_runs(), expected_task_count=16)
    constant = task.copy()
    constant["score_gap"] = 7.5
    first = crossed_block_bootstrap_ci(constant, reps=200, seed=42)
    second = crossed_block_bootstrap_ci(constant, reps=200, seed=42)
    assert first == second
    assert first == (7.5, 7.5)


def test_summary_reports_win_tie_loss_and_conditional_loss() -> None:
    task = build_task_frame(_synthetic_runs(), expected_task_count=16).iloc[:4].copy()
    task["score_gap"] = [10.0, 0.0, -20.0, -40.0]
    summary = summarize_subset(
        task,
        group_dimension="test",
        group_values={},
        tie_epsilon=1e-9,
        bootstrap_reps=200,
        bootstrap_seed=11,
    )
    assert summary["ours_wins"] == 1
    assert summary["ties"] == 1
    assert summary["ours_losses"] == 2
    assert summary["conditional_loss_magnitude_mean"] == 30.0


def test_crossed_bootstrap_accepts_an_unbalanced_failure_filtered_subset() -> None:
    task = build_task_frame(_synthetic_runs(), expected_task_count=16)
    subset = task.drop(index=task.index[[0, 3, 7]])
    low, high = crossed_block_bootstrap_ci(subset, reps=200, seed=7)
    assert low <= subset["score_gap"].mean() <= high
