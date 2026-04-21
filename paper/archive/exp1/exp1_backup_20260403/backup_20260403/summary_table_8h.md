# Experiment 1: Algorithm Comparison Summary (Query-Level Means)

- Aggregation unit: `(origin, depart_time, budget_minutes)` after averaging over 5 seeds.
- Number of independent queries: 30.
- Scope: 8h budget only.

| algorithm    |   rank_composite |   composite_score |   elapsed_ms |   ride_minutes |   unique_stops |   hull_area |   feasible_rate |
|:-------------|-----------------:|------------------:|-------------:|---------------:|---------------:|------------:|----------------:|
| Ours (Full)  |                1 |            0.6816 |    5989.39   |       260.267  |        10.3333 |    138.386  |               1 |
| NSGA-II      |                2 |            0.6244 |   17094      |       374.44   |        16.4    |     45.2906 |               1 |
| ILS+2opt     |                3 |            0.5695 |     136.031  |       364.367  |        12.2267 |     34.9838 |               1 |
| VNS          |                4 |            0.542  |      44.3329 |       341.007  |        12.5933 |     31.1674 |               1 |
| Greedy (L=3) |                5 |            0.51   |       0.7917 |       355.933  |         8.8667 |     22.6566 |               1 |
| SA           |                6 |            0.5011 |      29.8349 |       308.9    |        11.7867 |     28.8588 |               1 |
| McRAPTOR     |                7 |            0.3427 |    2552.8    |       111.18   |        10.6533 |     39.1204 |               1 |
| Pure RAPTOR  |                8 |            0.2693 |   63538.4    |        93.5667 |         4.3333 |     26.08   |               1 |
