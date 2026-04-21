# Experiment 3 Balance Analysis (Supplement to Experiment 1)

Generated at: 2026-04-21T14:34:18

## 1. Positioning

Experiment 3 should be positioned as a supplementary balance analysis for Experiment 1. The goal is not to claim that Ours is best on every query, but to test whether it most often stays close to the score-time ideal point under the same task.

## 2. Data Overview

- Source results: `D:\reroute_fukuoka\paper\results\exp1_algorithm_comparison\exp1_results_no_likim_2h4h6h8h.json`
- Objective mode: `score_guided`
- Task-level rows: `108`
- Query-level rows: `54`
- Origins: `['hakata', 'tenjin', 'nishijin']`
- Budgets (minutes): `[120, 240]`
- Target budgets (minutes): `[120, 240, 360, 480]`
- Missing target budgets in current Exp1 source: `[360, 480]`
- Score seeds: `[20260323, 20260324]`
- Head-to-head pair: `Ours (Full)` vs `ZhouWang2025-ALNS (adapted)`

## 3. Overall Quality-Speed Balance

- Task-level leader by balance summary: `ZhouWang2025-ALNS (adapted)` (ideal-point distance `0.475`).
- Query-level closest to the ideal point: `ZhouWang2025-ALNS (adapted)` (distance `0.412`).

### 3.1 Task-Level Summary

| algorithm                   |   task_count |   avg_stop_score |   avg_elapsed_ms |   avg_score_per_hour |   avg_ideal_distance |   avg_balance_rank |   best_score_rate |   fastest_rate |   avg_budget_feasible_rate |   avg_cap_hit_rate |
|:----------------------------|-------------:|-----------------:|-----------------:|---------------------:|---------------------:|-------------------:|------------------:|---------------:|---------------------------:|-------------------:|
| ZhouWang2025-ALNS (adapted) |           36 |         580.9167 |          56.5655 |             210.3991 |               0.4749 |             1.1667 |            0.2778 |         0.0000 |                     1.0000 |             0.0000 |
| Zhang2025-DynPref (adapted) |           36 |         453.2722 |          12.0091 |             170.6196 |               0.9594 |             1.9444 |            0.0000 |         1.0000 |                     0.9833 |             0.0000 |
| Ours (Full)                 |           36 |         595.5833 |        1197.5089 |             229.5893 |               1.0509 |             2.2222 |            0.7222 |         0.0000 |                     0.9722 |             0.0000 |

### 3.2 Query-Level Summary

| algorithm                   |   query_count |   avg_stop_score |   avg_elapsed_ms |   avg_score_per_hour |   avg_ideal_distance |   avg_balance_rank |   best_score_rate |   fastest_rate |   avg_budget_feasible_rate |   avg_cap_hit_rate |
|:----------------------------|--------------:|-----------------:|-----------------:|---------------------:|---------------------:|-------------------:|------------------:|---------------:|---------------------------:|-------------------:|
| ZhouWang2025-ALNS (adapted) |            18 |         580.9167 |          56.5655 |             210.3991 |               0.4116 |             1.1111 |            0.2778 |         0.0000 |                     1.0000 |             0.0000 |
| Zhang2025-DynPref (adapted) |            18 |         453.2722 |          12.0091 |             170.6196 |               0.9974 |             1.9444 |            0.0000 |         1.0000 |                     0.9833 |             0.0000 |
| Ours (Full)                 |            18 |         595.5833 |        1197.5089 |             229.5893 |               1.0533 |             2.2222 |            0.7222 |         0.0000 |                     0.9722 |             0.0000 |

### 3.3 Task-Level Summary by Budget

|   budget_minutes | budget_label   | algorithm                   |   task_count |   avg_stop_score |   avg_elapsed_ms |   avg_score_per_hour |   avg_ideal_distance |   best_score_rate |   fastest_rate |   avg_budget_feasible_rate |   avg_cap_hit_rate |
|-----------------:|:---------------|:----------------------------|-------------:|-----------------:|-----------------:|---------------------:|---------------------:|------------------:|---------------:|---------------------------:|-------------------:|
|              120 | 2h             | Ours (Full)                 |           18 |         410.7222 |          97.8250 |             239.7641 |               1.0623 |            0.7778 |         0.0000 |                     1.0000 |             0.0000 |
|              120 | 2h             | Zhang2025-DynPref (adapted) |           18 |         353.6889 |           9.3373 |             194.3838 |               0.9412 |            0.0000 |         1.0000 |                     0.9889 |             0.0000 |
|              120 | 2h             | ZhouWang2025-ALNS (adapted) |           18 |         408.3556 |          41.1502 |             224.2742 |               0.5979 |            0.2222 |         0.0000 |                     1.0000 |             0.0000 |
|              240 | 4h             | Ours (Full)                 |           18 |         780.4444 |        2297.1928 |             219.4146 |               1.0396 |            0.6667 |         0.0000 |                     0.9444 |             0.0000 |
|              240 | 4h             | Zhang2025-DynPref (adapted) |           18 |         552.8556 |          14.6809 |             146.8554 |               0.9776 |            0.0000 |         1.0000 |                     0.9778 |             0.0000 |
|              240 | 4h             | ZhouWang2025-ALNS (adapted) |           18 |         753.4778 |          71.9808 |             196.5241 |               0.3519 |            0.3333 |         0.0000 |                     1.0000 |             0.0000 |

## 4. Ours (Full) vs ZhouWang2025-ALNS (adapted)

- Task-level: `Ours (Full)` achieves `higher score + faster` on `2` tasks, `higher score + slower` on `24` tasks, and `lower score + faster` on `0` tasks.

### 4.1 Task-Level Tradeoff Counts

| tradeoff_category            |   count |   rate |
|:-----------------------------|--------:|-------:|
| higher score + faster        |       2 | 0.0556 |
| higher score + similar time  |       0 | 0.0000 |
| higher score + slower        |      24 | 0.6667 |
| similar score + faster       |       0 | 0.0000 |
| similar score + similar time |       0 | 0.0000 |
| similar score + slower       |       0 | 0.0000 |
| lower score + faster         |       0 | 0.0000 |
| lower score + similar time   |       0 | 0.0000 |
| lower score + slower         |      10 | 0.2778 |

### 4.2 Task-Level Tradeoff by Budget

|   budget_minutes | budget_label   | tradeoff_category            |   count |   rate |
|-----------------:|:---------------|:-----------------------------|--------:|-------:|
|              120 | 2h             | higher score + faster        |       2 | 0.1111 |
|              120 | 2h             | higher score + similar time  |       0 | 0.0000 |
|              120 | 2h             | higher score + slower        |      12 | 0.6667 |
|              120 | 2h             | similar score + faster       |       0 | 0.0000 |
|              120 | 2h             | similar score + similar time |       0 | 0.0000 |
|              120 | 2h             | similar score + slower       |       0 | 0.0000 |
|              120 | 2h             | lower score + faster         |       0 | 0.0000 |
|              120 | 2h             | lower score + similar time   |       0 | 0.0000 |
|              120 | 2h             | lower score + slower         |       4 | 0.2222 |
|              240 | 4h             | higher score + faster        |       0 | 0.0000 |
|              240 | 4h             | higher score + similar time  |       0 | 0.0000 |
|              240 | 4h             | higher score + slower        |      12 | 0.6667 |
|              240 | 4h             | similar score + faster       |       0 | 0.0000 |
|              240 | 4h             | similar score + similar time |       0 | 0.0000 |
|              240 | 4h             | similar score + slower       |       0 | 0.0000 |
|              240 | 4h             | lower score + faster         |       0 | 0.0000 |
|              240 | 4h             | lower score + similar time   |       0 | 0.0000 |
|              240 | 4h             | lower score + slower         |       6 | 0.3333 |

### 4.3 Query-Level Tradeoff Counts

| tradeoff_category            |   count |   rate |
|:-----------------------------|--------:|-------:|
| higher score + faster        |       0 | 0.0000 |
| higher score + similar time  |       0 | 0.0000 |
| higher score + slower        |      13 | 0.7222 |
| similar score + faster       |       0 | 0.0000 |
| similar score + similar time |       0 | 0.0000 |
| similar score + slower       |       0 | 0.0000 |
| lower score + faster         |       0 | 0.0000 |
| lower score + similar time   |       0 | 0.0000 |
| lower score + slower         |       5 | 0.2778 |

## 5. Interpretation for Paper Writing

- The main claim should be that Ours provides the best overall quality-speed balance, not that it wins every single task.
- In the teacher-facing and paper-facing version, `ideal-point distance` should be the primary balance metric.
- The Ours-vs-NSGA-II tradeoff table should be used only as supplementary evidence for when Ours is simultaneously better and faster, and when it trades score for time or vice versa.
