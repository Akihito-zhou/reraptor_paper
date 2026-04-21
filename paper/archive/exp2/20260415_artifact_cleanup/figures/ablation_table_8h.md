# Experiment 2: Stop-Score Ablation Study

Mode: 8h budget only

- Primary metric: `Stop Score`
- Aggregation unit: `(origin, depart_time, budget, score_seed)`

| algorithm                 |   stop_score |   score_per_hour |   time_ms |   speedup_vs_no_pruning |     labels |   gap_to_best_score_pct |   success_rate_pct |   cap_hit_rate_pct |
|:--------------------------|-------------:|-----------------:|----------:|------------------------:|-----------:|------------------------:|-------------------:|-------------------:|
| Ours (Full)               |      1261.50 |           171.38 |   8564.82 |                    2.37 |  206456.56 |                    0.07 |              97.78 |               0.00 |
| Ours (NoNeg)              |      1262.39 |           171.29 |   8923.78 |                    2.27 |  213537.18 |                    0.00 |              97.78 |               0.00 |
| Ours (NoDom)              |      1205.89 |           164.97 |  21896.73 |                    0.93 |  546949.47 |                    4.48 |              97.78 |               0.00 |
| Ours (NoBeam)             |      1020.28 |           165.48 |  61897.36 |                    0.33 | 2128139.23 |                   19.18 |             100.00 |             100.00 |
| Ours (NoBeam-NoDom)       |       284.99 |           193.77 |  61804.51 |                    0.33 | 2883574.42 |                   77.42 |             100.00 |             100.00 |
| Ours (NoDom-NoNeg)        |      1206.07 |           164.82 |  20930.94 |                    0.97 |  547935.81 |                    4.46 |              97.78 |               0.00 |
| Ours (NoBeam-NoNeg)       |      1020.72 |           164.72 |  61914.81 |                    0.33 | 2152939.37 |                   19.14 |             100.00 |             100.00 |
| Ours (NoBeam-NoDom-NoNeg) |       274.57 |           195.98 |  20283.96 |                    1.00 | 1000000.00 |                   78.25 |             100.00 |             100.00 |
