# Experiment 2: Stop-Score Ablation Study

Mode: 4h budget only

- Primary metric: `Stop Score`
- Aggregation unit: `(origin, depart_time, budget, score_seed)`

| algorithm                 |   stop_score |   score_per_hour |   time_ms |   speedup_vs_no_pruning |     labels |   gap_to_best_score_pct |   success_rate_pct |   cap_hit_rate_pct |
|:--------------------------|-------------:|-----------------:|----------:|------------------------:|-----------:|------------------------:|-------------------:|-------------------:|
| Ours (Full)               |       737.04 |           208.78 |    771.47 |                   27.97 |   24416.67 |                    8.30 |              97.78 |               0.00 |
| Ours (NoNeg)              |       729.81 |           206.13 |    806.95 |                   26.74 |   25116.49 |                    9.20 |              96.67 |               0.00 |
| Ours (NoDom)              |       737.92 |           207.77 |   5282.16 |                    4.08 |  152941.81 |                    8.20 |              97.78 |               0.00 |
| Ours (NoBeam)             |       803.80 |           221.16 |  27076.49 |                    0.80 |  847140.44 |                    0.00 |              95.56 |              18.89 |
| Ours (NoBeam-NoDom)       |       342.60 |           195.14 |  61584.65 |                    0.35 | 2739584.91 |                   57.38 |             100.00 |             100.00 |
| Ours (NoDom-NoNeg)        |       740.04 |           207.31 |   5037.39 |                    4.28 |  154025.81 |                    7.93 |              97.78 |               0.00 |
| Ours (NoBeam-NoNeg)       |       802.40 |           221.02 |  27486.13 |                    0.78 |  865141.14 |                    0.17 |              95.56 |              20.00 |
| Ours (NoBeam-NoDom-NoNeg) |       304.18 |           205.23 |  21576.02 |                    1.00 | 1000000.00 |                   62.16 |             100.00 |             100.00 |
