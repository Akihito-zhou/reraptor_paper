# Experiment 1 Multi-Seed Score-Guided Summary

- Source result file: `D:/reroute_fukuoka/paper/results/exp1_algorithm_comparison/exp1_results_full_score_guided_20260401.json`
- Score seeds: `[20260323, 20260324, 20260325, 20260326, 20260327]`
- Query x score-seed tasks: `300` per algorithm
- Base queries after averaging over score seeds: `60` per algorithm
- Primary metric: `stop_score_total`

## Key Findings

- `Ours` remains the top algorithm on the full multi-seed benchmark: average stop score `991.833` vs `NSGA-II` `909.698`.
- `Ours` is also faster: `7175.907` ms vs `NSGA-II` `31198.097` ms.
- On `query x score_seed` tasks, `Ours` beats `NSGA-II` in `209` of `300` comparisons.
- The Ours-NSGA score gap stays positive for every tested `score_seed`, but the weakest seed is `20260326` with only `5.537` average advantage.
- All Ours zero-score cases in this run are `effective_budget_feasible = False` edge cases, concentrated in `hakata, noke, yakuin` rather than valid-but-poor routes.

## Overall Task-Level Summary

| algorithm    |   task_count |   avg_stop_score |   avg_elapsed_ms |   avg_score_per_hour |   avg_feasible_rate |   wins |   avg_rank |
|:-------------|-------------:|-----------------:|-----------------:|---------------------:|--------------------:|-------:|-----------:|
| Ours (Full)  |          300 |          991.833 |         7175.91  |              188.061 |               0.973 |    179 |      1.983 |
| NSGA-II      |          300 |          909.698 |        31198.1   |              167.898 |               0.953 |     79 |      2.653 |
| ILS+2opt     |          300 |          809.446 |          645.488 |              145.402 |               0.957 |     15 |      3.637 |
| VNS          |          300 |          750.235 |          202.279 |              136.715 |               0.98  |      4 |      4.427 |
| SA           |          300 |          683.22  |          153.725 |              124.921 |               0.987 |      1 |      5.1   |
| McRAPTOR     |          300 |          629.053 |         3825.95  |              146.416 |               1     |     18 |      4.703 |
| Greedy (L=3) |          300 |          461.19  |            3.79  |               86.147 |               0.92  |      4 |      6.403 |
| Pure RAPTOR  |          300 |          318.91  |        61287     |              185.14  |               1     |      0 |      7.093 |

## Base-Query Summary

| algorithm    |   query_count |   avg_stop_score |   avg_elapsed_ms |   avg_score_per_hour |   avg_feasible_rate |   wins |   avg_rank |
|:-------------|--------------:|-----------------:|-----------------:|---------------------:|--------------------:|-------:|-----------:|
| Ours (Full)  |            60 |          991.833 |         7175.91  |              188.061 |               1     |     43 |      1.55  |
| NSGA-II      |            60 |          909.698 |        31198.1   |              167.898 |               0.983 |     12 |      2.283 |
| ILS+2opt     |            60 |          809.446 |          645.488 |              145.402 |               1     |      3 |      3.383 |
| VNS          |            60 |          750.235 |          202.279 |              136.715 |               1     |      1 |      4.3   |
| SA           |            60 |          683.22  |          153.725 |              124.921 |               1     |      0 |      5.283 |
| McRAPTOR     |            60 |          629.053 |         3825.95  |              146.416 |               1     |      1 |      4.683 |
| Greedy (L=3) |            60 |          461.19  |            3.79  |               86.147 |               1     |      0 |      7     |
| Pure RAPTOR  |            60 |          318.91  |        61287     |              185.14  |               1     |      0 |      7.517 |

## Ours vs NSGA-II by Budget

|   budget_minutes | budget_label   |   ours_better |   nsga_better |   ties |   avg_score_diff |   avg_ours_elapsed_ms |   avg_nsga_elapsed_ms |
|-----------------:|:---------------|--------------:|--------------:|-------:|-----------------:|----------------------:|----------------------:|
|              240 | 4h             |           113 |            37 |      0 |          100.841 |               1329.04 |               26629.9 |
|              480 | 8h             |            96 |            53 |      1 |           63.429 |              13022.8  |               35766.3 |

## Ours vs NSGA-II by Score Seed

|   score_seed |   ours_better |   nsga_better |   ties |   avg_score_diff |   avg_ours_elapsed_ms |   avg_nsga_elapsed_ms |
|-------------:|--------------:|--------------:|-------:|-----------------:|----------------------:|----------------------:|
|     20260323 |            41 |            19 |      0 |          123.453 |               7697.3  |               36109.9 |
|     20260324 |            43 |            17 |      0 |          138.103 |              10414.1  |               36603.2 |
|     20260325 |            43 |            17 |      0 |           94.23  |               9501.07 |               37834.3 |
|     20260326 |            42 |            17 |      1 |            5.537 |               3813.43 |               22675.9 |
|     20260327 |            40 |            20 |      0 |           49.353 |               4453.66 |               22767.3 |

## Ours Infeasible / Zero-Score Cases

| origin_name   |   depart_time |   budget_minutes |   score_seed |   stop_score_total |   elapsed_ms | effective_budget_feasible   |
|:--------------|--------------:|-----------------:|-------------:|-------------------:|-------------:|:----------------------------|
| hakata        |           420 |              240 |     20260324 |                  0 |       972.52 | False                       |
| noke          |           600 |              240 |     20260326 |                  0 |      3175.09 | False                       |
| noke          |           840 |              240 |     20260324 |                  0 |      1680.06 | False                       |
| yakuin        |           600 |              240 |     20260326 |                  0 |       938.84 | False                       |
| yakuin        |           840 |              240 |     20260327 |                  0 |       148.2  | False                       |
| noke          |           600 |              480 |     20260325 |                  0 |      9116.29 | False                       |
| noke          |           840 |              480 |     20260325 |                  0 |      1548.72 | False                       |
| yakuin        |           420 |              480 |     20260326 |                  0 |      1014.85 | False                       |

## Largest Ours Losses

| origin_name   |   depart_time |   budget_minutes |   score_seed | best_algo   |   best_score |   ours_score |    gap |   ours_elapsed_ms |
|:--------------|--------------:|-----------------:|-------------:|:------------|-------------:|-------------:|-------:|------------------:|
| yakuin        |           420 |              480 |     20260326 | VNS         |       1411   |            0 | 1411   |           1014.85 |
| noke          |           840 |              480 |     20260325 | NSGA-II     |       1233.6 |            0 | 1233.6 |           1548.72 |
| noke          |           420 |              480 |     20260327 | NSGA-II     |       1553   |          339 | 1214   |             94.26 |
| noke          |           600 |              480 |     20260326 | NSGA-II     |       1477.4 |          316 | 1161.4 |             82.51 |
| noke          |           600 |              480 |     20260327 | ILS+2opt    |       1403.2 |          275 | 1128.2 |             78.18 |
| noke          |           420 |              480 |     20260326 | NSGA-II     |       1455.4 |          357 | 1098.4 |             98.86 |
| noke          |           600 |              480 |     20260325 | ILS+2opt    |       1080.4 |            0 | 1080.4 |           9116.29 |
| yakuin        |           840 |              480 |     20260323 | NSGA-II     |       1529.4 |          519 | 1010.4 |            235.14 |
| yakuin        |           420 |              480 |     20260323 | NSGA-II     |       1240.6 |          409 |  831.6 |            203.26 |
| yakuin        |           840 |              240 |     20260327 | NSGA-II     |        826   |            0 |  826   |            148.2  |
| yakuin        |           600 |              480 |     20260323 | NSGA-II     |       1212.6 |          409 |  803.6 |            159.24 |
| noke          |           840 |              480 |     20260327 | NSGA-II     |       1476.6 |          674 |  802.6 |            947.93 |

## Figure Outputs

- `D:/reroute_fukuoka/paper/figures/exp1/exp1_score_guided_multiseed_overview_20260403.png`
- `D:/reroute_fukuoka/paper/figures/exp1/exp1_score_guided_multiseed_budget_20260403.png`
- `D:/reroute_fukuoka/paper/figures/exp1/exp1_score_guided_multiseed_seed_stability_20260403.png`
