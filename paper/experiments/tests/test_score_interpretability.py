from __future__ import annotations

import numpy as np
import pandas as pd

from paper.experiments.exp1_algorithm_comparison.analyze_score_interpretability import (
    _crossed_bootstrap_samples,
    build_interpretability_task_frame,
)
from paper.experiments.exp1_algorithm_comparison.analyze_underperformance import (
    NSGA_NAME,
    OURS_NAME,
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
    stops: float,
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
        "scored_stop_count": stops,
        "elapsed_ms": 10.0,
        "feasible": not failure,
        "algorithm_failure": failure,
        "violation_reason": "effective_budget_exceeded" if failure else "",
    }


def _canonical_shape_synthetic_runs() -> pd.DataFrame:
    rows: list[dict] = []
    origins = [f"o{i}" for i in range(10)]
    for score_seed in range(5):
        for origin in origins:
            for departure in [420, 600, 840]:
                for budget in [120, 240, 360, 480]:
                    rows.append(
                        _row(
                            algorithm=OURS_NAME,
                            origin=origin,
                            departure=departure,
                            budget=budget,
                            score_seed=score_seed,
                            seed=0,
                            score=120.0,
                            stops=2.0,
                        )
                    )
                    for seed in range(5):
                        failure = (
                            origin == "o0"
                            and departure == 420
                            and budget == 120
                            and score_seed == 0
                        )
                        rows.append(
                            _row(
                                algorithm=NSGA_NAME,
                                origin=origin,
                                departure=departure,
                                budget=budget,
                                score_seed=score_seed,
                                seed=seed,
                                score=0.0 if failure else 100.0,
                                stops=0.0 if failure else 2.0,
                                failure=failure,
                            )
                        )
    return pd.DataFrame(rows)


def test_exact_symmetric_decomposition_and_failed_density_boundary() -> None:
    task = build_interpretability_task_frame(_canonical_shape_synthetic_runs())
    assert len(task) == 600
    defined = task[~task["nsga_all_failed"]]
    reconstructed = defined["coverage_association"] + defined["density_association"]
    assert np.allclose(reconstructed, defined["score_gap"], atol=1e-9, rtol=0.0)
    failed = task[task["nsga_all_failed"]].iloc[0]
    assert np.isnan(failed["nsga_reward_per_scored_stop"])
    assert np.isnan(failed["coverage_association"])
    assert failed["score_gap"] == 120.0


def test_crossed_bootstrap_samples_are_deterministic_for_constant_values() -> None:
    task = build_interpretability_task_frame(_canonical_shape_synthetic_runs())
    task["constant"] = 3.25
    first = _crossed_bootstrap_samples(
        task, value_columns=["constant"], reps=200, seed=9
    )["constant"]
    second = _crossed_bootstrap_samples(
        task, value_columns=["constant"], reps=200, seed=9
    )["constant"]
    assert np.array_equal(first, second)
    assert np.allclose(first, 3.25)
