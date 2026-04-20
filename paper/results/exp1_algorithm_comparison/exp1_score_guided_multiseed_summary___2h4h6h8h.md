# Experiment 1 Multi-Seed Score-Guided Summary

- Source result file: `D:/reroute_fukuoka/paper/results/exp1_algorithm_comparison/exp1_final_dataset_2h4h6h8h.json`
- Score seeds: `[20260323, 20260324, 20260325, 20260326, 20260327]`
- Query x score-seed tasks: `600` per algorithm
- Base queries after averaging over score seeds: `120` per algorithm
- Primary metric: `stop_score_total`

## Key Findings

- `Ours` remains the top algorithm on the full multi-seed benchmark: average stop score `826.900` vs `NSGA-II` `760.664`.
- `Ours` is also faster: `4165.672` ms vs `NSGA-II` `27351.183` ms.
- On `query x score_seed` tasks, `Ours` beats `NSGA-II` in `368` of `600` comparisons.
- The Ours-NSGA score gap stays positive for every tested `score_seed`, but the weakest seed is `20260326` with only `15.152` average advantage.
- All Ours zero-score cases in this run are `effective_budget_feasible = False` edge cases, concentrated in `hakata, noke, yakuin` rather than valid-but-poor routes.

## Overall Task-Level Summary

| algorithm    |   task_count |   avg_stop_score |   avg_elapsed_ms |   avg_score_per_hour |   avg_feasible_rate |   wins |   avg_rank |
|:-------------|-------------:|-----------------:|-----------------:|---------------------:|--------------------:|-------:|-----------:|
| Ours (Full)  |          600 |          826.9   |         4165.67  |              193.019 |               0.978 |    287 |      2.378 |
| NSGA-II      |          600 |          760.664 |        27351.2   |              170.403 |               0.923 |    170 |      2.83  |
| ILS+2opt     |          600 |          697.457 |          518.789 |              157.097 |               0.958 |     44 |      3.572 |
| VNS          |          600 |          644.998 |          169.309 |              148.131 |               0.977 |     10 |      4.393 |
| SA           |          600 |          589.457 |          130.796 |              137.254 |               0.983 |      3 |      5.255 |
| McRAPTOR     |          600 |          546.701 |         3684.86  |              149.332 |               1     |     31 |      5.052 |
| Greedy (L=3) |          600 |          416.985 |            3.046 |              101.266 |               0.932 |      8 |      6.335 |
| Pure RAPTOR  |          600 |          320.308 |        56483.3   |              192.363 |               0.995 |     47 |      6.185 |

## Base-Query Summary

| algorithm    |   query_count |   avg_stop_score |   avg_elapsed_ms |   avg_score_per_hour |   avg_feasible_rate |   wins |   avg_rank |
|:-------------|--------------:|-----------------:|-----------------:|---------------------:|--------------------:|-------:|-----------:|
| Ours (Full)  |           120 |          826.9   |         4165.67  |              193.019 |               1     |     67 |      1.942 |
| NSGA-II      |           120 |          760.664 |        27351.2   |              170.403 |               0.975 |     29 |      2.658 |
| ILS+2opt     |           120 |          697.457 |          518.789 |              157.097 |               1     |      8 |      3.333 |
| VNS          |           120 |          644.998 |          169.309 |              148.131 |               1     |      1 |      4.3   |
| SA           |           120 |          589.457 |          130.796 |              137.254 |               1     |      0 |      5.392 |
| McRAPTOR     |           120 |          546.701 |         3684.86  |              149.332 |               1     |      4 |      5.042 |
| Greedy (L=3) |           120 |          416.985 |            3.046 |              101.266 |               1     |      0 |      6.992 |
| Pure RAPTOR  |           120 |          320.308 |        56483.3   |              192.363 |               1     |     11 |      6.342 |

## Ours vs NSGA-II by Budget

|   budget_minutes | budget_label   |   ours_better |   nsga_better |   ties |   avg_score_diff |   avg_ours_elapsed_ms |   avg_nsga_elapsed_ms |
|-----------------:|:---------------|--------------:|--------------:|-------:|-----------------:|----------------------:|----------------------:|
|              120 | 2h             |            69 |            68 |     13 |           27.749 |                83.954 |               17026.8 |
|              240 | 4h             |           113 |            37 |      0 |          100.841 |              1329.04  |               26629.9 |
|              360 | 6h             |            90 |            60 |      0 |           72.925 |              2226.92  |               29981.8 |
|              480 | 8h             |            96 |            53 |      1 |           63.429 |             13022.8   |               35766.3 |

## Ours vs NSGA-II by Score Seed

|   score_seed |   ours_better |   nsga_better |   ties |   avg_score_diff |   avg_ours_elapsed_ms |   avg_nsga_elapsed_ms |
|-------------:|--------------:|--------------:|-------:|-----------------:|----------------------:|----------------------:|
|     20260323 |            75 |            45 |      0 |           90.285 |               4405.28 |               30728.1 |
|     20260324 |            73 |            43 |      4 |          107.433 |               5950.03 |               30706.8 |
|     20260325 |            72 |            46 |      2 |           86.315 |               5332.72 |               30245.8 |
|     20260326 |            78 |            37 |      5 |           15.152 |               2212.35 |               20114.6 |
|     20260327 |            70 |            47 |      3 |           31.997 |               2927.99 |               24960.7 |

## Ours Infeasible / Zero-Score Cases

| origin_name   |   depart_time |   budget_minutes |   score_seed |   stop_score_total |   elapsed_ms | effective_budget_feasible   |
|:--------------|--------------:|-----------------:|-------------:|-------------------:|-------------:|:----------------------------|
| noke          |           420 |              120 |     20260323 |                  0 |       140.79 | False                       |
| noke          |           600 |              120 |     20260324 |                  0 |       324.41 | False                       |
| noke          |           600 |              120 |     20260326 |                  0 |       158.3  | False                       |
| yakuin        |           420 |              120 |     20260325 |                  0 |       230.4  | False                       |
| yakuin        |           600 |              120 |     20260326 |                  0 |        86.25 | False                       |
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
| noke          |           600 |              360 |     20260327 | NSGA-II     |       1185.4 |          339 |  846.4 |            219.31 |
| yakuin        |           420 |              480 |     20260323 | NSGA-II     |       1240.6 |          409 |  831.6 |            203.26 |
| noke          |           600 |              360 |     20260326 | NSGA-II     |       1166   |          335 |  831   |            120.01 |
| yakuin        |           840 |              240 |     20260327 | NSGA-II     |        826   |            0 |  826   |            148.2  |

## Figure Outputs

- `D:/reroute_fukuoka/paper/figures/exp1/exp1_score_guided_multiseed_overview___2h4h6h8h.png`
- `D:/reroute_fukuoka/paper/figures/exp1/exp1_score_guided_multiseed_budget___2h4h6h8h.png`
- `D:/reroute_fukuoka/paper/figures/exp1/exp1_score_guided_multiseed_seed_stability___2h4h6h8h.png`
