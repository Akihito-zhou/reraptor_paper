#!/usr/bin/env python3
"""
Pilot runner for 2024+ adapted baselines.

Purpose:
1) quickly verify runnability and comparability of adapted recent methods
2) produce a compact result file before committing to full-scale runs
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_exp1 import run_experiment


def main() -> None:
    run_experiment(
        quick_mode=False,
        resume=True,
        checkpoint_every=6,
        score_seed=20260323,
        score_seeds_override=[20260323],
        # Pilot slice: full origin set, 3 departure times, 2h/4h/6h/8h budgets, single seed.
        budgets_override=[2 * 60, 4 * 60, 6 * 60, 8 * 60],
        seeds_override=[0],
        output_tag="recent_adapted_pilot_2h4h6h8h",
        objective_mode="score_guided",
        include_recent_adapted_baselines=True,
        algorithms_override=[
            "Zhang2025-DynPref",
            "LiKim2024-RTA*",
            "ZhouWang2025-ALNS",
        ],
        # Keep deterministic methods single-seed during pilot.
        repeat_deterministic_seeds=False,
    )


if __name__ == "__main__":
    main()
