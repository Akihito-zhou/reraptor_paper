# Experiment 3 Balance Analysis (Supplement to Experiment 1)

Generated at: 2026-04-21T14:23:04

## 1. Positioning

Experiment 3 should be positioned as a supplementary balance analysis for Experiment 1. The goal is not to claim that Ours is best on every query, but to test whether it most often stays close to the score-time ideal point under the same task.

## 2. Data Overview

- Source results: `D:\reroute_fukuoka\paper\results\exp1_algorithm_comparison\exp1_results_merged_with_recent3_2h4h6h8h.json`
- Objective mode: `score_guided`
- Task-level rows: `1800`
- Query-level rows: `360`
- Origins: `['hakata', 'tenjin', 'nishijin', 'ohori-koen', 'yakuin', 'kashii', 'noke', 'meinohama', 'kaizuka', 'fukudaimae']`
- Budgets (minutes): `[120, 240, 360, 480]`
- Target budgets (minutes): `[120, 240, 360, 480]`
- Score seeds: `[20260323, 20260324, 20260325, 20260326, 20260327]`

## 3. Overall Quality-Speed Balance

- Task-level leader by balance summary: `ZhouWang2025-ALNS (adapted)` (ideal-point distance `0.571`).
- Query-level closest to the ideal point: `ZhouWang2025-ALNS (adapted)` (distance `0.491`).

### 3.1 Task-Level Summary

| algorithm                   |   task_count |   avg_stop_score |   avg_elapsed_ms |   avg_score_per_hour |   avg_ideal_distance |   avg_balance_rank |   best_score_rate |   fastest_rate |   avg_budget_feasible_rate |   avg_cap_hit_rate |
|:----------------------------|-------------:|-----------------:|-----------------:|---------------------:|---------------------:|-------------------:|------------------:|---------------:|---------------------------:|-------------------:|
| ZhouWang2025-ALNS (adapted) |          600 |         657.7627 |          62.8320 |             150.9588 |               0.5708 |             1.2267 |            0.2100 |         0.0000 |                     0.9383 |             0.0000 |
| Zhang2025-DynPref (adapted) |          600 |         443.7027 |          10.9136 |             111.1551 |               0.9478 |             1.8917 |            0.0100 |         0.9983 |                     0.9217 |             0.0000 |
| Ours (Full)                 |          600 |         826.9000 |        4165.6718 |             193.0188 |               1.0272 |             2.1517 |            0.7883 |         0.0017 |                     0.9783 |             0.0000 |

### 3.2 Query-Level Summary

| algorithm                   |   query_count |   avg_stop_score |   avg_elapsed_ms |   avg_score_per_hour |   avg_ideal_distance |   avg_balance_rank |   best_score_rate |   fastest_rate |   avg_budget_feasible_rate |   avg_cap_hit_rate |
|:----------------------------|--------------:|-----------------:|-----------------:|---------------------:|---------------------:|-------------------:|------------------:|---------------:|---------------------------:|-------------------:|
| ZhouWang2025-ALNS (adapted) |           120 |         657.7627 |          62.8320 |             150.9588 |               0.4913 |             1.0917 |            0.1417 |         0.0000 |                     0.9383 |             0.0000 |
| Zhang2025-DynPref (adapted) |           120 |         443.7027 |          10.9136 |             111.1551 |               0.9830 |             1.9750 |            0.0083 |         1.0000 |                     0.9217 |             0.0000 |
| Ours (Full)                 |           120 |         826.9000 |        4165.6718 |             193.0188 |               1.0044 |             2.1167 |            0.8500 |         0.0000 |                     0.9783 |             0.0000 |

### 3.3 Task-Level Summary by Budget

|   budget_minutes | budget_label   | algorithm                   |   task_count |   avg_stop_score |   avg_elapsed_ms |   avg_score_per_hour |   avg_ideal_distance |   best_score_rate |   fastest_rate |   avg_budget_feasible_rate |   avg_cap_hit_rate |
|-----------------:|:---------------|:----------------------------|-------------:|-----------------:|-----------------:|---------------------:|---------------------:|------------------:|---------------:|---------------------------:|-------------------:|
|              120 | 2h             | Ours (Full)                 |          150 |         350.3667 |          83.9545 |             215.3170 |               1.0140 |            0.6467 |         0.0067 |                     0.9667 |             0.0000 |
|              120 | 2h             | Zhang2025-DynPref (adapted) |          150 |         286.3400 |           7.5377 |             167.0437 |               0.8652 |            0.0400 |         0.9933 |                     0.9173 |             0.0000 |
|              120 | 2h             | ZhouWang2025-ALNS (adapted) |          150 |         328.2067 |          30.7383 |             189.5362 |               0.7180 |            0.3467 |         0.0000 |                     0.9360 |             0.0000 |
|              240 | 4h             | Ours (Full)                 |          150 |         725.7800 |        1329.0402 |             205.3327 |               1.0252 |            0.8600 |         0.0000 |                     0.9667 |             0.0000 |
|              240 | 4h             | Zhang2025-DynPref (adapted) |          150 |         425.8813 |          12.0520 |             115.9551 |               0.9628 |            0.0000 |         1.0000 |                     0.9173 |             0.0000 |
|              240 | 4h             | ZhouWang2025-ALNS (adapted) |          150 |         573.3973 |          54.9102 |             154.0374 |               0.5460 |            0.1400 |         0.0000 |                     0.9387 |             0.0000 |
|              360 | 6h             | Ours (Full)                 |          150 |         973.5667 |        2226.9183 |             180.6360 |               1.0384 |            0.7933 |         0.0000 |                     1.0000 |             0.0000 |
|              360 | 6h             | Zhang2025-DynPref (adapted) |          150 |         500.3347 |          12.1554 |              88.2065 |               0.9845 |            0.0000 |         1.0000 |                     0.9293 |             0.0000 |
|              360 | 6h             | ZhouWang2025-ALNS (adapted) |          150 |         787.1013 |          74.8861 |             137.6828 |               0.4941 |            0.2067 |         0.0000 |                     0.9480 |             0.0000 |
|              480 | 8h             | Ours (Full)                 |          150 |        1257.8867 |       13022.7741 |             170.7897 |               1.0313 |            0.8533 |         0.0000 |                     0.9800 |             0.0000 |
|              480 | 8h             | Zhang2025-DynPref (adapted) |          150 |         562.2547 |          11.9091 |              73.4151 |               0.9785 |            0.0000 |         1.0000 |                     0.9227 |             0.0000 |
|              480 | 8h             | ZhouWang2025-ALNS (adapted) |          150 |         942.3453 |          90.7934 |             122.5787 |               0.5252 |            0.1467 |         0.0000 |                     0.9307 |             0.0000 |

## 4. Ours (Full) vs NSGA-II


### 4.1 Task-Level Tradeoff Counts

_No data_

### 4.2 Task-Level Tradeoff by Budget

_No data_

### 4.3 Query-Level Tradeoff Counts

_No data_

## 5. Interpretation for Paper Writing

- The main claim should be that Ours provides the best overall quality-speed balance, not that it wins every single task.
- In the teacher-facing and paper-facing version, `ideal-point distance` should be the primary balance metric.
- The Ours-vs-NSGA-II tradeoff table should be used only as supplementary evidence for when Ours is simultaneously better and faster, and when it trades score for time or vice versa.
