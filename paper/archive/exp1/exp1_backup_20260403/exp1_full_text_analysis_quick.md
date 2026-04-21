# Experiment 1 Full-Scale Textual Analysis (Score-Based Revision)

- Source result file: `paper\results\exp1_algorithm_comparison\exp1_results_quick.json`
- Analysis timestamp (result metadata): `2026-03-23T18:36:09.120721`
- Quick mode: `True`
- Primary metric: `Stop Score`
- Uniform dwell time per scored stop: `10` minutes

## 1. Protocol Clarification

- This revised report provides **both** overall (4h+8h combined) and budget-sliced (4h / 8h separate) views.
- Combined views are retained for global ranking; budget-sliced views avoid interpretation bias from truncation effects.

## 2. Overall (Combined 4h+8h) Results

### 2.1 Run-Level Summary

| algorithm    |   n |   feasible_rate |   elapsed_mean |   elapsed_median | elapsed_std   |   composite_mean |   primary_mean | composite_std   |   ride_mean |   stops_mean |   hull_mean |   score_per_hour_mean |   total_time_mean |   elapsed_p95 |
|:-------------|----:|----------------:|---------------:|-----------------:|:--------------|-----------------:|---------------:|:----------------|------------:|-------------:|------------:|----------------------:|------------------:|--------------:|
| NSGA-II      |   1 |          1.0000 |     45091.9000 |       45091.9000 |               |           0.3725 |      1668.0000 |                 |    109.0000 |      21.0000 |     13.3451 |              236.0377 |          224.0000 |    45091.9000 |
| Ours (Full)  |   1 |          1.0000 |     17369.5300 |       17369.5300 |               |           0.2978 |      1440.0000 |                 |     67.0000 |      20.0000 |     14.7184 |              251.8950 |          153.0000 |    17369.5300 |
| ILS+2opt     |   1 |          1.0000 |       251.6800 |         251.6800 |               |           0.3558 |      1285.0000 |                 |    111.0000 |      17.0000 |     14.1719 |              200.7812 |          224.0000 |      251.6800 |
| SA           |   1 |          1.0000 |       143.3300 |         143.3300 |               |           0.3235 |      1214.0000 |                 |     93.0000 |      18.0000 |     21.7564 |              183.9394 |          226.0000 |      143.3300 |
| Greedy (L=3) |   1 |          1.0000 |         5.0500 |           5.0500 |               |           0.3070 |      1162.0000 |                 |     94.0000 |      15.0000 |     20.5927 |              187.9245 |          231.0000 |        5.0500 |
| VNS          |   1 |          1.0000 |        45.6000 |          45.6000 |               |           0.2977 |      1091.0000 |                 |    103.0000 |      15.0000 |     12.1819 |              179.8352 |          224.0000 |       45.6000 |
| McRAPTOR     |   1 |          1.0000 |      8938.8100 |        8938.8100 |               |           0.2283 |       792.0000 |                 |     47.0000 |      13.0000 |      5.8330 |              146.2154 |          205.0000 |     8938.8100 |
| Pure RAPTOR  |   1 |          1.0000 |     61751.4300 |       61751.4300 |               |           0.1953 |       274.0000 |                 |     26.0000 |       4.0000 |      1.8009 |              260.9524 |           33.0000 |    61751.4300 |

### 2.2 Query-Level Summary

| algorithm    |   n_queries |   feasible_rate |   elapsed_mean |   composite_mean |   primary_mean |   ride_mean |   stops_mean |   hull_mean |   score_per_hour_mean |   total_time_mean |
|:-------------|------------:|----------------:|---------------:|-----------------:|---------------:|------------:|-------------:|------------:|----------------------:|------------------:|
| NSGA-II      |           1 |          1.0000 |     45091.9000 |           0.3725 |      1668.0000 |    109.0000 |      21.0000 |     13.3451 |              236.0377 |          224.0000 |
| Ours (Full)  |           1 |          1.0000 |     17369.5300 |           0.2978 |      1440.0000 |     67.0000 |      20.0000 |     14.7184 |              251.8950 |          153.0000 |
| ILS+2opt     |           1 |          1.0000 |       251.6800 |           0.3558 |      1285.0000 |    111.0000 |      17.0000 |     14.1719 |              200.7812 |          224.0000 |
| SA           |           1 |          1.0000 |       143.3300 |           0.3235 |      1214.0000 |     93.0000 |      18.0000 |     21.7564 |              183.9394 |          226.0000 |
| Greedy (L=3) |           1 |          1.0000 |         5.0500 |           0.3070 |      1162.0000 |     94.0000 |      15.0000 |     20.5927 |              187.9245 |          231.0000 |
| VNS          |           1 |          1.0000 |        45.6000 |           0.2977 |      1091.0000 |    103.0000 |      15.0000 |     12.1819 |              179.8352 |          224.0000 |
| McRAPTOR     |           1 |          1.0000 |      8938.8100 |           0.2283 |       792.0000 |     47.0000 |      13.0000 |      5.8330 |              146.2154 |          205.0000 |
| Pure RAPTOR  |           1 |          1.0000 |     61751.4300 |           0.1953 |       274.0000 |     26.0000 |       4.0000 |      1.8009 |              260.9524 |           33.0000 |

- Top algorithm by stop score (overall query-level): **NSGA-II**
- Ours vs NSGA-II (overall): stop score -13.67%, elapsed +61.48% faster, stops -4.76%, score-rate +6.72%, hull +10.29%.

## 3. Budget-Sliced Results

### 3.1 Budget = 4h

#### Query-Level Summary

| algorithm    |   n_queries |   feasible_rate |   elapsed_mean |   composite_mean |   primary_mean |   ride_mean |   stops_mean |   hull_mean |   score_per_hour_mean |   total_time_mean |
|:-------------|------------:|----------------:|---------------:|-----------------:|---------------:|------------:|-------------:|------------:|----------------------:|------------------:|
| NSGA-II      |           1 |          1.0000 |     45091.9000 |           0.3725 |      1668.0000 |    109.0000 |      21.0000 |     13.3451 |              236.0377 |          224.0000 |
| Ours (Full)  |           1 |          1.0000 |     17369.5300 |           0.2978 |      1440.0000 |     67.0000 |      20.0000 |     14.7184 |              251.8950 |          153.0000 |
| ILS+2opt     |           1 |          1.0000 |       251.6800 |           0.3558 |      1285.0000 |    111.0000 |      17.0000 |     14.1719 |              200.7812 |          224.0000 |
| SA           |           1 |          1.0000 |       143.3300 |           0.3235 |      1214.0000 |     93.0000 |      18.0000 |     21.7564 |              183.9394 |          226.0000 |
| Greedy (L=3) |           1 |          1.0000 |         5.0500 |           0.3070 |      1162.0000 |     94.0000 |      15.0000 |     20.5927 |              187.9245 |          231.0000 |
| VNS          |           1 |          1.0000 |        45.6000 |           0.2977 |      1091.0000 |    103.0000 |      15.0000 |     12.1819 |              179.8352 |          224.0000 |
| McRAPTOR     |           1 |          1.0000 |      8938.8100 |           0.2283 |       792.0000 |     47.0000 |      13.0000 |      5.8330 |              146.2154 |          205.0000 |
| Pure RAPTOR  |           1 |          1.0000 |     61751.4300 |           0.1953 |       274.0000 |     26.0000 |       4.0000 |      1.8009 |              260.9524 |           33.0000 |

#### Run-Level Summary

| algorithm    |   n |   feasible_rate |   elapsed_mean |   elapsed_median | elapsed_std   |   composite_mean |   primary_mean | composite_std   |   ride_mean |   stops_mean |   hull_mean |   score_per_hour_mean |   total_time_mean |   elapsed_p95 |
|:-------------|----:|----------------:|---------------:|-----------------:|:--------------|-----------------:|---------------:|:----------------|------------:|-------------:|------------:|----------------------:|------------------:|--------------:|
| NSGA-II      |   1 |          1.0000 |     45091.9000 |       45091.9000 |               |           0.3725 |      1668.0000 |                 |    109.0000 |      21.0000 |     13.3451 |              236.0377 |          224.0000 |    45091.9000 |
| Ours (Full)  |   1 |          1.0000 |     17369.5300 |       17369.5300 |               |           0.2978 |      1440.0000 |                 |     67.0000 |      20.0000 |     14.7184 |              251.8950 |          153.0000 |    17369.5300 |
| ILS+2opt     |   1 |          1.0000 |       251.6800 |         251.6800 |               |           0.3558 |      1285.0000 |                 |    111.0000 |      17.0000 |     14.1719 |              200.7812 |          224.0000 |      251.6800 |
| SA           |   1 |          1.0000 |       143.3300 |         143.3300 |               |           0.3235 |      1214.0000 |                 |     93.0000 |      18.0000 |     21.7564 |              183.9394 |          226.0000 |      143.3300 |
| Greedy (L=3) |   1 |          1.0000 |         5.0500 |           5.0500 |               |           0.3070 |      1162.0000 |                 |     94.0000 |      15.0000 |     20.5927 |              187.9245 |          231.0000 |        5.0500 |
| VNS          |   1 |          1.0000 |        45.6000 |          45.6000 |               |           0.2977 |      1091.0000 |                 |    103.0000 |      15.0000 |     12.1819 |              179.8352 |          224.0000 |       45.6000 |
| McRAPTOR     |   1 |          1.0000 |      8938.8100 |        8938.8100 |               |           0.2283 |       792.0000 |                 |     47.0000 |      13.0000 |      5.8330 |              146.2154 |          205.0000 |     8938.8100 |
| Pure RAPTOR  |   1 |          1.0000 |     61751.4300 |       61751.4300 |               |           0.1953 |       274.0000 |                 |     26.0000 |       4.0000 |      1.8009 |              260.9524 |           33.0000 |    61751.4300 |

- Ours vs NSGA-II: stop score -13.67%, elapsed +61.48% faster, stops -4.76%, score-rate +6.72%, hull +10.29%.

## 4. Win Counts

### 4.1 Seed-Level Stop Score Wins (300 cases)

|         |   wins |
|:--------|-------:|
| NSGA-II |      1 |

### 4.2 Query-Level Stop Score Wins (60 cases)

|         |   wins |
|:--------|-------:|
| NSGA-II |      1 |

### 4.3 Seed-Level Wins by Budget

|         |   240 |
|:--------|------:|
| NSGA-II |     1 |

### 4.4 Query-Level Wins by Budget

|         |   240 |
|:--------|------:|
| NSGA-II |     1 |

## 5. Statistical Tests

### 5.1 Overall Wilcoxon (Query-Level)

| algorithm    |   N |
|:-------------|----:|
| Greedy (L=3) |   1 |
| ILS+2opt     |   1 |
| McRAPTOR     |   1 |
| NSGA-II      |   1 |
| Pure RAPTOR  |   1 |
| SA           |   1 |
| VNS          |   1 |

### 5.2 Wilcoxon for 4h only

| algorithm    |   N |
|:-------------|----:|
| Greedy (L=3) |   1 |
| ILS+2opt     |   1 |
| McRAPTOR     |   1 |
| NSGA-II      |   1 |
| Pure RAPTOR  |   1 |
| SA           |   1 |
| VNS          |   1 |

## 6. Reproducibility Artifacts

- Figures:
  - `paper/figures/exp1/exp1_metric_panels.png` (combined)
  - `paper/figures/exp1/exp1_metric_panels_4h.png`
  - `paper/figures/exp1/exp1_metric_panels_8h.png`
- Tables:
  - `paper/figures/exp1/summary_table.md` (combined)
  - `paper/figures/exp1/summary_table_4h.md`
  - `paper/figures/exp1/summary_table_8h.md`
  - `paper/figures/exp1/statistical_tests.md` (combined)
  - `paper/figures/exp1/statistical_tests_4h.md`
  - `paper/figures/exp1/statistical_tests_8h.md`
- Machine-readable stats:
  - `paper/results/exp1_algorithm_comparison/exp1_analysis_stats.json`

