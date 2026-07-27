# Canonical Stop Score interpretability analysis

- Source: `paper/results/exp1_algorithm_comparison/exp1_results_canonical_final_10alg_manuscript_20260723.json`
- Paired unit: `(origin, departure, budget, reward seed)`.
- Uncertainty: 20,000-rep crossed block bootstrap (seed 20260723).

## Headline translation

Ours averages **872.438** Stop Score versus **802.539** for NSGA-II under the all-task failure policy. The difference is **69.899** or **8.710%** of the NSGA-II mean.

Because rewards are drawn from discrete `U{1,...,100}` with expectation 50.5, the mean score gap is numerically equivalent to **1.384** expected-reward stops (95% CI **[0.159, 2.592]**). This is an experimental-unit translation, not a count of real attractions or a utility/monetary quantity.

## Paired task metrics

| estimand                          | metric                              |   task_count |   mean |   median |   bootstrap_ci95_low |   bootstrap_ci95_high |
|:----------------------------------|:------------------------------------|-------------:|-------:|---------:|---------------------:|----------------------:|
| all_task_failure_zero             | Stop Score gap                      |          600 | 69.899 |   52.5   |                8.054 |               130.917 |
| all_task_failure_zero             | Scored-stop-count gap               |          600 |  1.32  |    1     |                0.535 |                 2.092 |
| all_task_failure_zero             | Selected reward per scored stop gap |          581 | -1.914 |   -0.791 |               -3.247 |                -0.654 |
| all_five_nsga_runs_feasible       | Stop Score gap                      |          452 |  4.708 |   15     |              -63.024 |                67.875 |
| all_five_nsga_runs_feasible       | Scored-stop-count gap               |          452 |  0.453 |    0.4   |               -0.39  |                 1.269 |
| all_five_nsga_runs_feasible       | Selected reward per scored stop gap |          452 | -1.608 |   -0.489 |               -2.89  |                -0.433 |
| mean_over_feasible_nsga_runs_only | Stop Score gap                      |          581 | -3.059 |   11     |              -71.301 |                62.44  |
| mean_over_feasible_nsga_runs_only | Scored-stop-count gap               |          581 |  0.37  |    0.4   |               -0.44  |                 1.152 |
| mean_over_feasible_nsga_runs_only | Selected reward per scored stop gap |          581 | -1.914 |   -0.791 |               -3.26  |                -0.653 |

## Exact symmetric decomposition

For the 581 tasks where NSGA-II returns at least one feasible route, the identity `Δscore = coverage association + reward-density association` holds exactly at task level. The terms describe an association, not a causal attribution:

| component                           |   task_count |    mean |   median |   bootstrap_ci95_low |   bootstrap_ci95_high |
|:------------------------------------|-------------:|--------:|---------:|---------------------:|----------------------:|
| Observed Stop Score gap             |          581 |  55.045 |   48.8   |               -7.976 |               113.036 |
| Scored-stop coverage association    |          581 |  81.357 |   73.246 |               26.165 |               135.139 |
| Selected reward-density association |          581 | -26.311 |   -9.983 |              -44.265 |                -9.575 |

The remaining **19** tasks have all five NSGA-II runs fail. Their NSGA-II reward density is undefined; their mean Ours score, and hence mean all-task score gap, is **524.105**. These tasks are reported as a reliability/no-feasible-return difference rather than forced into the coverage-density decomposition.

## Interpretation boundary

The primary all-task result is associated with more scored stops and a slightly lower selected reward per stop. However, the complete-case and feasible-seed-only score intervals cross zero. The paper should therefore distinguish overall performance (including reliability) from conditional solution quality and use `is associated with` rather than causal language.
