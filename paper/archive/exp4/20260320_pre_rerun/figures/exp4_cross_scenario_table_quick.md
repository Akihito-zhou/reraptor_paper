# Experiment 4: Cross-Scenario Summary

- Aggregation unit: query-level means after averaging over seeds.
- `scenario_primary_value` uses the scenario-specific primary metric.

| scenario         | algorithm   | scenario_primary_label   |   scenario_primary_value |   scenario_score |   elapsed_ms |   feasible_rate |   scenario_satisfied_rate |
|:-----------------|:------------|:-------------------------|-------------------------:|-----------------:|-------------:|----------------:|--------------------------:|
| longest-duration | Ours        | Ride Minutes             |                 182      |      7.3137e+06  |     7222     |               1 |                         1 |
| longest-duration | NSGA-II     | Ride Minutes             |                 210      |      8.43204e+06 |    18003.9   |               1 |                         1 |
| longest-duration | ILS+2opt    | Ride Minutes             |                 210      |      8.43113e+06 |      353.395 |               1 |                         1 |
| longest-duration | VNS         | Ride Minutes             |                 203      |      8.15187e+06 |      127.031 |               1 |                         1 |
| most-stops       | Ours        | Unique Stops             |                  18      | 200093           |    20239.6   |               1 |                         1 |
| most-stops       | NSGA-II     | Unique Stops             |                  14      | 156099           |    21312.2   |               1 |                         1 |
| most-stops       | ILS+2opt    | Unique Stops             |                  10      | 113056           |      315.882 |               1 |                         1 |
| most-stops       | VNS         | Unique Stops             |                  12      | 129806           |      132.743 |               1 |                         1 |
| city-loop        | Ours        | Hull Area                |                  18.45   |   4477.11        |     8478.03  |               1 |                         0 |
| city-loop        | NSGA-II     | Hull Area                |                  57.8095 |  47408.2         |    16782.5   |               1 |                         0 |
| city-loop        | ILS+2opt    | Hull Area                |                  55.3841 |  42859.8         |      281.332 |               1 |                         0 |
| city-loop        | VNS         | Hull Area                |                  22.2653 |  28608.3         |      209.355 |               1 |                         0 |
| single-digit     | Ours        | Single-Digit Ratio       |                   1      | 484800           |     9343.47  |               1 |                         1 |
| single-digit     | NSGA-II     | Single-Digit Ratio       |                   1      | 447200           |    17514.7   |               1 |                         1 |
| single-digit     | ILS+2opt    | Single-Digit Ratio       |                   1      | 338700           |      433.201 |               1 |                         1 |
| single-digit     | VNS         | Single-Digit Ratio       |                   1      | 241450           |      149.422 |               1 |                         0 |
| odd-lines        | Ours        | Odd-Line Ratio           |                   1      | 642200           |    39423     |               1 |                         1 |
| odd-lines        | NSGA-II     | Odd-Line Ratio           |                   1      | 383750           |    20329.6   |               1 |                         1 |
| odd-lines        | ILS+2opt    | Odd-Line Ratio           |                   1      | 348500           |      676.976 |               1 |                         1 |
| odd-lines        | VNS         | Odd-Line Ratio           |                   1      | 383750           |      426.981 |               1 |                         1 |
| triple-digit     | Ours        | Triple-Digit Ratio       |                   1      | 528300           |     2138.89  |               1 |                         1 |
| triple-digit     | NSGA-II     | Triple-Digit Ratio       |                   1      | 475400           |    17116.5   |               1 |                         1 |
| triple-digit     | ILS+2opt    | Triple-Digit Ratio       |                   1      | 367700           |      185.001 |               1 |                         1 |
| triple-digit     | VNS         | Triple-Digit Ratio       |                   1      | 418450           |      262.143 |               1 |                         1 |
| balanced         | Ours        | Composite Score          |                   0.3495 |      0.3495      |     1970.23  |               1 |                         1 |
| balanced         | NSGA-II     | Composite Score          |                   0.4747 |      0.4747      |    16527.3   |               1 |                         1 |
| balanced         | ILS+2opt    | Composite Score          |                   0.4049 |      0.4049      |      258.077 |               1 |                         1 |
| balanced         | VNS         | Composite Score          |                   0.401  |      0.401       |      176.553 |               1 |                         1 |
