# Canonical Ours vs NSGA-II underperformance analysis

- Source: `paper/results/exp1_algorithm_comparison/exp1_results_canonical_final_10alg_manuscript_20260723.json`
- Paired unit: `(origin, departure, budget, reward seed)`.
- NSGA-II aggregation: arithmetic mean over five algorithm seeds; algorithm failures retain score 0.
- Uncertainty: 20,000-rep crossed block bootstrap over reward seeds and origin-departure scenarios (seed 20260723).
- Tie rule: exact equality within the configured numerical epsilon.

## Overall result

Ours leads by **69.899 Stop Score** on average (blocked-bootstrap 95% CI **[8.054, 130.917]**), with **380 wins / 49 ties / 171 losses** across 600 paired tasks.
When Ours loses, the conditional mean loss magnitude is **236.423**. The mean gap in the worst 10% of tasks is **-556.350**.

NSGA-II has **288/3000** algorithm-seed failures across **148/600** paired tasks; these failures are recorded as `effective_budget_exceeded` and scored as zero under the pre-registered all-task policy.

The auxiliary paired Wilcoxon test gives `p=3.23148e-18` and paired rank-biserial `r=0.428`. This test is secondary to the effect size and blocked-bootstrap interval.

## Reliability sensitivity

The primary all-task estimand keeps algorithm failures at score 0 because returning a budget-feasible route is part of algorithm performance. Two secondary estimands show how much the quality conclusion depends on this failure policy:

| estimand                          |   task_count |   mean_gap |   bootstrap_ci95_low |   bootstrap_ci95_high |   ours_wins |   ties |   ours_losses |
|:----------------------------------|-------------:|-----------:|---------------------:|----------------------:|------------:|-------:|--------------:|
| all_five_nsga_runs_feasible       |          452 |      4.708 |              -63.024 |                67.875 |         243 |     49 |           160 |
| mean_over_feasible_nsga_runs_only |          581 |     -3.059 |              -71.301 |                62.44  |         313 |     55 |           213 |

## By budget

|   budget_minutes |   task_count |   mean_gap |   bootstrap_ci95_low |   bootstrap_ci95_high |   ours_wins |   ties |   ours_losses |   conditional_loss_magnitude_mean |
|-----------------:|-------------:|-----------:|---------------------:|----------------------:|------------:|-------:|--------------:|----------------------------------:|
|              120 |          150 |     70.633 |               34.86  |               118.036 |          79 |     46 |            25 |                            40.448 |
|              240 |          150 |    147.243 |               93.412 |               204.994 |         116 |      1 |            33 |                            83.885 |
|              360 |          150 |     22.967 |              -75.432 |               117.743 |          87 |      0 |            63 |                           263.867 |
|              480 |          150 |     38.753 |             -105.307 |               167.186 |          98 |      2 |            50 |                           400.508 |

## By origin

| origin_name   |   task_count |   mean_gap |   bootstrap_ci95_low |   bootstrap_ci95_high |   ours_wins |   ties |   ours_losses |
|:--------------|-------------:|-----------:|---------------------:|----------------------:|------------:|-------:|--------------:|
| fukudaimae    |           60 |    252.967 |              117.36  |               431.813 |          46 |     10 |             4 |
| hakata        |           60 |     29.223 |              -79.917 |               137.613 |          30 |      3 |            27 |
| kaizuka       |           60 |    147.13  |               57.72  |               267.167 |          42 |      6 |            12 |
| kashii        |           60 |    153.56  |               15.45  |               317.707 |          47 |      4 |             9 |
| meinohama     |           60 |    192.007 |              127.91  |               255.74  |          49 |      7 |             4 |
| nishijin      |           60 |    112.477 |               -7.59  |               255.83  |          43 |      3 |            14 |
| noke          |           60 |   -225.693 |             -361.123 |               -88.403 |          25 |      2 |            33 |
| ohori-koen    |           60 |    -17.383 |             -161.437 |               116.793 |          29 |      5 |            26 |
| tenjin        |           60 |     72.363 |              -17.33  |               153.91  |          38 |      4 |            18 |
| yakuin        |           60 |    -17.66  |             -227.19  |               131.063 |          31 |      5 |            24 |

## By departure

|   depart_time |   task_count |   mean_gap |   bootstrap_ci95_low |   bootstrap_ci95_high |   ours_wins |   ties |   ours_losses |
|--------------:|-------------:|-----------:|---------------------:|----------------------:|------------:|-------:|--------------:|
|           420 |          200 |     32.125 |              -83.329 |               149.383 |         114 |     13 |            73 |
|           600 |          200 |    120.373 |               14.141 |               207.916 |         144 |     15 |            41 |
|           840 |          200 |     57.199 |              -30.363 |               130.67  |         122 |     21 |            57 |

## Origin × budget

| origin_name   |   budget_minutes |   mean_gap |   ours_wins |   ties |   ours_losses |
|:--------------|-----------------:|-----------:|------------:|-------:|--------------:|
| fukudaimae    |              120 |     14.267 |           5 |     10 |             0 |
| fukudaimae    |              240 |    250.92  |          15 |      0 |             0 |
| fukudaimae    |              360 |    351.213 |          13 |      0 |             2 |
| fukudaimae    |              480 |    395.467 |          13 |      0 |             2 |
| hakata        |              120 |     63.653 |           5 |      3 |             7 |
| hakata        |              240 |     -1.547 |           7 |      0 |             8 |
| hakata        |              360 |    -27.627 |           8 |      0 |             7 |
| hakata        |              480 |     82.413 |          10 |      0 |             5 |
| kaizuka       |              120 |     49.733 |           9 |      4 |             2 |
| kaizuka       |              240 |    252.587 |          11 |      0 |             4 |
| kaizuka       |              360 |     77.933 |          10 |      0 |             5 |
| kaizuka       |              480 |    208.267 |          12 |      2 |             1 |
| kashii        |              120 |     74.733 |          11 |      4 |             0 |
| kashii        |              240 |    134.947 |          12 |      0 |             3 |
| kashii        |              360 |    139.093 |          11 |      0 |             4 |
| kashii        |              480 |    265.467 |          13 |      0 |             2 |
| meinohama     |              120 |     34.84  |           6 |      7 |             2 |
| meinohama     |              240 |    172.973 |          14 |      0 |             1 |
| meinohama     |              360 |    276.573 |          14 |      0 |             1 |
| meinohama     |              480 |    283.64  |          15 |      0 |             0 |
| nishijin      |              120 |    109.773 |          10 |      3 |             2 |
| nishijin      |              240 |    105.787 |          12 |      0 |             3 |
| nishijin      |              360 |    127.84  |          11 |      0 |             4 |
| nishijin      |              480 |    106.507 |          10 |      0 |             5 |
| noke          |              120 |     84.72  |          10 |      2 |             3 |
| noke          |              240 |    168.627 |          11 |      0 |             4 |
| noke          |              360 |   -468.92  |           2 |      0 |            13 |
| noke          |              480 |   -687.2   |           2 |      0 |            13 |
| ohori-koen    |              120 |    123.213 |           9 |      4 |             2 |
| ohori-koen    |              240 |    153.947 |          11 |      1 |             3 |
| ohori-koen    |              360 |   -160.4   |           3 |      0 |            12 |
| ohori-koen    |              480 |   -186.293 |           6 |      0 |             9 |
| tenjin        |              120 |     41.587 |           7 |      4 |             4 |
| tenjin        |              240 |    137.053 |          12 |      0 |             3 |
| tenjin        |              360 |     63.827 |          11 |      0 |             4 |
| tenjin        |              480 |     46.987 |           8 |      0 |             7 |
| yakuin        |              120 |    109.813 |           7 |      5 |             3 |
| yakuin        |              240 |     97.133 |          11 |      0 |             4 |
| yakuin        |              360 |   -149.867 |           4 |      0 |            11 |
| yakuin        |              480 |   -127.72  |           9 |      0 |             6 |

## Reliability by NSGA-II failure count

|   nsga_failure_count |   task_count |   task_share |   mean_gap |   ours_wins |   ties |   ours_losses |
|---------------------:|-------------:|-------------:|-----------:|------------:|-------:|--------------:|
|                    0 |          452 |        0.753 |      4.708 |         243 |     49 |           160 |
|                    1 |           89 |        0.148 |    163.575 |          79 |      0 |            10 |
|                    2 |           22 |        0.037 |    358.409 |          21 |      0 |             1 |
|                    3 |           12 |        0.02  |    441.867 |          12 |      0 |             0 |
|                    4 |            6 |        0.01  |    351.267 |           6 |      0 |             0 |
|                    5 |           19 |        0.032 |    524.105 |          19 |      0 |             0 |

## Largest Ours losses

| origin_name   | departure_label   |   budget_minutes |   score_seed |   ours_score |   nsga_score |   score_gap |   nsga_failure_count |
|:--------------|:------------------|-----------------:|-------------:|-------------:|-------------:|------------:|---------------------:|
| yakuin        | 07:00             |              480 |     20260323 |          325 |       1531.4 |     -1206.4 |                    0 |
| noke          | 10:00             |              480 |     20260327 |          275 |       1471.8 |     -1196.8 |                    0 |
| noke          | 07:00             |              480 |     20260325 |          366 |       1559.2 |     -1193.2 |                    0 |
| noke          | 10:00             |              480 |     20260326 |          307 |       1498   |     -1191   |                    0 |
| noke          | 07:00             |              480 |     20260326 |          450 |       1492.4 |     -1042.4 |                    0 |
| yakuin        | 14:00             |              480 |     20260323 |          470 |       1506.6 |     -1036.6 |                    0 |
| noke          | 07:00             |              480 |     20260323 |          616 |       1531.2 |      -915.2 |                    0 |
| noke          | 07:00             |              480 |     20260327 |          339 |       1245.2 |      -906.2 |                    1 |
| yakuin        | 07:00             |              360 |     20260323 |          405 |       1286.4 |      -881.4 |                    0 |
| noke          | 10:00             |              360 |     20260326 |          335 |       1182.4 |      -847.4 |                    0 |
| noke          | 14:00             |              480 |     20260327 |          665 |       1507.8 |      -842.8 |                    0 |
| noke          | 07:00             |              360 |     20260325 |          460 |       1268.8 |      -808.8 |                    0 |
| noke          | 14:00             |              360 |     20260327 |          369 |       1172.8 |      -803.8 |                    0 |
| yakuin        | 10:00             |              360 |     20260323 |          413 |       1215   |      -802   |                    0 |
| noke          | 14:00             |              480 |     20260326 |          727 |       1528   |      -801   |                    0 |
| noke          | 07:00             |              360 |     20260327 |          416 |       1203.2 |      -787.2 |                    0 |
| ohori-koen    | 10:00             |              480 |     20260326 |          787 |       1542.2 |      -755.2 |                    0 |
| ohori-koen    | 14:00             |              480 |     20260326 |          787 |       1495.2 |      -708.2 |                    0 |
| noke          | 14:00             |              480 |     20260325 |          636 |       1336   |      -700   |                    0 |
| ohori-koen    | 07:00             |              480 |     20260326 |          825 |       1517.8 |      -692.8 |                    0 |

Interpretation must remain conditional: the data identify where losses occur, but do not by themselves prove a causal search-mechanism explanation.
