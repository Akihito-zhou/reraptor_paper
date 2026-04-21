# Experiment 1: Algorithm Comparison Summary (Query-Level Means)

- Aggregation unit: `(origin, depart_time, budget_minutes)` after averaging over 5 seeds.
- Number of independent queries: 30.
- Scope: 4h budget only.

| algorithm    |   rank_composite |   composite_score |   elapsed_ms |   ride_minutes |   unique_stops |   hull_area |   feasible_rate |
|:-------------|-----------------:|------------------:|-------------:|---------------:|---------------:|------------:|----------------:|
| Ours (Full)  |                1 |            0.3902 |    1292.37   |       131.233  |         8.4    |     56.8974 |               1 |
| NSGA-II      |                2 |            0.3776 |   13458.2    |       175.66   |        12.0933 |     20.5008 |               1 |
| ILS+2opt     |                3 |            0.335  |      42.3915 |       172.493  |         8.08   |     13.9074 |               1 |
| VNS          |                4 |            0.3296 |      24.6734 |       166.347  |         8.5133 |     13.5801 |               1 |
| Greedy (L=3) |                5 |            0.3183 |       0.5305 |       167.4    |         6.9    |     13.3828 |               1 |
| McRAPTOR     |                6 |            0.3167 |    2537.08   |       105.24   |         9.1733 |     33.4629 |               1 |
| SA           |                7 |            0.3047 |      17.4264 |       147.24   |         7.86   |     11.8348 |               1 |
| Pure RAPTOR  |                8 |            0.2936 |   63333.4    |        99.9467 |         4.7133 |     33.4801 |               1 |
