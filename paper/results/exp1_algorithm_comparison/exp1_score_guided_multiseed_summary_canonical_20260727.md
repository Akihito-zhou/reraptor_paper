# Experiment 1 Multi-Seed Score-Guided Summary

- Source result file: `C:/Users/12730/Desktop/reroute_fukuoka/paper/results/exp1_algorithm_comparison/exp1_results_canonical_final_10alg_manuscript_20260723.json`
- Score seeds: `[20260323, 20260324, 20260325, 20260326, 20260327]`
- Query x score-seed tasks: `600` per algorithm
- Base queries after averaging over score seeds: `120` per algorithm
- Primary metric: `stop_score_total`

## Key Findings

- `Ours` remains the top algorithm on the full multi-seed benchmark: average stop score `872.438` vs `NSGA-II` `802.539`.
- `Ours` is also faster: `5171.181` ms vs `NSGA-II` `35634.781` ms.
- On `query x score_seed` tasks, `Ours` beats `NSGA-II` in `380` of `600` comparisons.
- The Ours-NSGA score gap stays positive for every tested `score_seed`, but the weakest seed is `20260326` with only `41.545` average advantage.

## Overall Task-Level Summary

| algorithm         |   task_count |   avg_stop_score |   avg_elapsed_ms |   avg_score_per_hour |   avg_feasible_rate |   wins |   avg_rank |
|:------------------|-------------:|-----------------:|-----------------:|---------------------:|--------------------:|-------:|-----------:|
| Ours (Full)       |          600 |          872.438 |         5171.18  |              185.473 |               1     |    373 |      1.985 |
| NSGA-II           |          600 |          802.539 |        35634.8   |              164.945 |               0.938 |    154 |      3.212 |
| ILS+2opt          |          600 |          758.733 |          638.398 |              162.296 |               1     |     25 |      3.473 |
| ALNS (adapted)    |          600 |          709.834 |          104.866 |              153.519 |               1     |      5 |      4.61  |
| VNS               |          600 |          700.271 |          224.575 |              151.637 |               1     |      2 |      4.887 |
| SA                |          600 |          622.115 |          168.314 |              134.631 |               1     |      0 |      6.25  |
| McRAPTOR          |          600 |          539.763 |         2994.83  |              146.18  |               0.975 |     16 |      6.728 |
| Greedy (L=3)      |          600 |          459.357 |            3.667 |              103.515 |               1     |     11 |      7.825 |
| DynPref (adapted) |          600 |          459.099 |           13.393 |              107.426 |               1     |      1 |      8.097 |
| Pure RAPTOR       |          600 |          316.733 |        56470.9   |              163.958 |               1     |     13 |      7.933 |

## Base-Query Summary

| algorithm         |   query_count |   avg_stop_score |   avg_elapsed_ms |   avg_score_per_hour |   avg_feasible_rate |   wins |   avg_rank |
|:------------------|--------------:|-----------------:|-----------------:|---------------------:|--------------------:|-------:|-----------:|
| Ours (Full)       |           120 |          872.438 |         5171.18  |              185.473 |               1     |     84 |      1.775 |
| NSGA-II           |           120 |          802.539 |        35634.8   |              164.945 |               1     |     25 |      3.2   |
| ILS+2opt          |           120 |          758.733 |          638.398 |              162.296 |               1     |      6 |      2.867 |
| ALNS (adapted)    |           120 |          709.834 |          104.866 |              153.519 |               1     |      0 |      4.442 |
| VNS               |           120 |          700.271 |          224.575 |              151.637 |               1     |      0 |      4.883 |
| SA                |           120 |          622.115 |          168.314 |              134.631 |               1     |      0 |      6.475 |
| McRAPTOR          |           120 |          539.763 |         2994.83  |              146.18  |               0.975 |      0 |      6.85  |
| Greedy (L=3)      |           120 |          459.357 |            3.667 |              103.515 |               1     |      0 |      8.4   |
| DynPref (adapted) |           120 |          459.099 |           13.393 |              107.426 |               1     |      0 |      8.067 |
| Pure RAPTOR       |           120 |          316.733 |        56470.9   |              163.958 |               1     |      5 |      8.042 |

## Ours vs NSGA-II by Budget

|   budget_minutes | budget_label   |   ours_better |   nsga_better |   ties |   avg_score_diff |   avg_ours_elapsed_ms |   avg_nsga_elapsed_ms |
|-----------------:|:---------------|--------------:|--------------:|-------:|-----------------:|----------------------:|----------------------:|
|              120 | 2h             |            79 |            25 |     46 |           70.633 |                82.656 |               23221.8 |
|              240 | 4h             |           116 |            33 |      1 |          147.243 |              2042.99  |               33730.7 |
|              360 | 6h             |            87 |            63 |      0 |           22.967 |              3166.4   |               40131.4 |
|              480 | 8h             |            98 |            50 |      2 |           38.753 |             15392.7   |               45455.2 |

## Ours vs NSGA-II by Score Seed

|   score_seed |   ours_better |   nsga_better |   ties |   avg_score_diff |   avg_ours_elapsed_ms |   avg_nsga_elapsed_ms |
|-------------:|--------------:|--------------:|-------:|-----------------:|----------------------:|----------------------:|
|     20260323 |            80 |            34 |      6 |           61.66  |               4779.99 |               31180.3 |
|     20260324 |            74 |            38 |      8 |          117.615 |               6201.6  |               36097.7 |
|     20260325 |            70 |            37 |     13 |           80.475 |               5300.89 |               36961.2 |
|     20260326 |            83 |            26 |     11 |           41.545 |               4982.57 |               36515.1 |
|     20260327 |            73 |            36 |     11 |           48.2   |               4590.84 |               37419.6 |

## Largest Ours Losses

| origin_name   |   depart_time |   budget_minutes |   score_seed | best_algo   |   best_score |   ours_score |    gap |   ours_elapsed_ms |
|:--------------|--------------:|-----------------:|-------------:|:------------|-------------:|-------------:|-------:|------------------:|
| yakuin        |           420 |              480 |     20260323 | NSGA-II     |       1531.4 |          325 | 1206.4 |             81    |
| noke          |           600 |              480 |     20260327 | NSGA-II     |       1471.8 |          275 | 1196.8 |             87.75 |
| noke          |           420 |              480 |     20260325 | NSGA-II     |       1559.2 |          366 | 1193.2 |             94.12 |
| noke          |           600 |              480 |     20260326 | NSGA-II     |       1498   |          307 | 1191   |             90.82 |
| noke          |           420 |              480 |     20260326 | NSGA-II     |       1492.4 |          450 | 1042.4 |            153.27 |
| yakuin        |           840 |              480 |     20260323 | NSGA-II     |       1506.6 |          470 | 1036.6 |            153.44 |
| noke          |           420 |              480 |     20260327 | ILS+2opt    |       1308.8 |          339 |  969.8 |            109.09 |
| yakuin        |           600 |              480 |     20260323 | ILS+2opt    |       1288.4 |          332 |  956.4 |            190.09 |
| noke          |           420 |              480 |     20260323 | NSGA-II     |       1531.2 |          616 |  915.2 |            330.77 |
| yakuin        |           420 |              360 |     20260323 | NSGA-II     |       1286.4 |          405 |  881.4 |             76.73 |
| noke          |           600 |              360 |     20260326 | NSGA-II     |       1182.4 |          335 |  847.4 |            168.26 |
| noke          |           840 |              480 |     20260327 | NSGA-II     |       1507.8 |          665 |  842.8 |           1258.31 |

## Figure Outputs

- `C:/Users/12730/Desktop/reroute_fukuoka/tmp/exp1-canonical-audit/exp1_score_guided_multiseed_overview_canonical_20260727.png`
- `C:/Users/12730/Desktop/reroute_fukuoka/tmp/exp1-canonical-audit/exp1_score_guided_multiseed_budget_canonical_20260727.png`
- `C:/Users/12730/Desktop/reroute_fukuoka/tmp/exp1-canonical-audit/exp1_score_guided_multiseed_seed_stability_canonical_20260727.png`
