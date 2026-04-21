# Experiment 1: Algorithm Comparison Summary (Query-Level Means)

- Aggregation unit: `(origin, depart_time, budget_minutes)` after averaging over 5 seeds.
- Number of independent queries: 60.
- Scope: all budgets combined (4h + 8h).

| algorithm    |   rank_composite |   composite_score |   elapsed_ms |   ride_minutes |   unique_stops |   hull_area |   feasible_rate |
|:-------------|-----------------:|------------------:|-------------:|---------------:|---------------:|------------:|----------------:|
| Ours (Full)  |                1 |            0.5359 |    3640.88   |       195.75   |         9.3667 |     97.6417 |               1 |
| NSGA-II      |                2 |            0.501  |   15276.1    |       275.05   |        14.2467 |     32.8957 |               1 |
| ILS+2opt     |                3 |            0.4522 |      89.2112 |       268.43   |        10.1533 |     24.4456 |               1 |
| VNS          |                4 |            0.4358 |      34.5031 |       253.677  |        10.5533 |     22.3738 |               1 |
| Greedy (L=3) |                5 |            0.4141 |       0.6611 |       261.667  |         7.8833 |     18.0197 |               1 |
| SA           |                6 |            0.4029 |      23.6307 |       228.07   |         9.8233 |     20.3468 |               1 |
| McRAPTOR     |                7 |            0.3297 |    2544.94   |       108.21   |         9.9133 |     36.2916 |               1 |
| Pure RAPTOR  |                8 |            0.2814 |   63435.9    |        96.7567 |         4.5233 |     29.7801 |               1 |
