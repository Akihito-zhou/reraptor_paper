# Experiment 3b: Weight Profile Sensitivity Summary

- Aggregation unit: query-level means (averaged over seeds).

| variant_label       | score_profile   |   budget_hours |   composite_score |   elapsed_ms |   ride_minutes |   unique_stops |   hull_area |   feasible_rate |
|:--------------------|:----------------|---------------:|------------------:|-------------:|---------------:|---------------:|------------:|----------------:|
| Ours (W:Balanced)   | balanced        |         8.0000 |            0.7563 |    6365.9833 |       254.0667 |        10.4000 |    138.7745 |          1.0000 |
| Ours (W:Default)    | default         |         8.0000 |            0.6813 |    6289.5606 |       259.2000 |        10.4333 |    138.4359 |          1.0000 |
| Ours (W:Geometry)   | geometry_biased |         8.0000 |            0.9640 |    6214.6922 |       254.1333 |        10.4333 |    139.6168 |          1.0000 |
| Ours (W:Time+Stops) | time_stops      |         8.0000 |            0.5880 |    8099.0408 |       343.0000 |        14.6333 |     42.1941 |          1.0000 |
| Ours (W:TimeOnly)   | time_only       |         8.0000 |            0.7414 |    8076.8371 |       355.8667 |         9.3667 |     38.9615 |          1.0000 |
