# Experiment 2: Stop-Score Ablation Study

- Primary metric: `Stop Score`
- Aggregation unit: `(origin, depart_time, budget, score_seed)`

| algorithm                 |   stop_score |   score_per_hour |   time_ms |   speedup_vs_no_pruning |     labels |   gap_to_best_score_pct |   success_rate_pct |   cap_hit_rate_pct |
|:--------------------------|-------------:|-----------------:|----------:|------------------------:|-----------:|------------------------:|-------------------:|-------------------:|
| Ours (Full)               |       999.27 |           190.08 |   4668.15 |                    4.48 |  115436.61 |                    0.00 |              97.78 |               0.00 |
| Ours (NoNeg)              |       996.10 |           188.71 |   4865.37 |                    4.30 |  119326.83 |                    0.32 |              97.22 |               0.00 |
| Ours (NoDom)              |       971.91 |           186.37 |  13589.45 |                    1.54 |  349945.64 |                    2.74 |              97.78 |               0.00 |
| Ours (NoBeam)             |       912.04 |           193.32 |  44486.93 |                    0.47 | 1487639.84 |                    8.73 |              97.78 |              59.44 |
| Ours (NoBeam-NoDom)       |       313.79 |           194.45 |  61694.58 |                    0.34 | 2811579.67 |                   68.60 |             100.00 |             100.00 |
| Ours (NoDom-NoNeg)        |       973.06 |           186.06 |  12984.17 |                    1.61 |  350980.81 |                    2.62 |              97.78 |               0.00 |
| Ours (NoBeam-NoNeg)       |       911.56 |           192.87 |  44700.47 |                    0.47 | 1509040.26 |                    8.78 |              97.78 |              60.00 |
| Ours (NoBeam-NoDom-NoNeg) |       289.37 |           200.61 |  20929.99 |                    1.00 | 1000000.00 |                   71.04 |             100.00 |             100.00 |
