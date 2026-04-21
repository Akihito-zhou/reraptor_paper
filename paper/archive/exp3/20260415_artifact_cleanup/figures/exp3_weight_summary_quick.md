# Experiment 3b: Weight Profile Sensitivity Summary

- Aggregation unit: query-level means (averaged over seeds).

| variant_label       | score_profile   |   budget_hours |   composite_score |   elapsed_ms |   ride_minutes |   unique_stops |   hull_area |   feasible_rate |
|:--------------------|:----------------|---------------:|------------------:|-------------:|---------------:|---------------:|------------:|----------------:|
| Ours (W:Balanced)   | balanced        |         4.0000 |            0.4086 |    1673.4400 |       134.0000 |         5.0000 |     50.5371 |          1.0000 |
| Ours (W:Default)    | default         |         4.0000 |            0.3502 |    1803.3100 |       134.0000 |         5.0000 |     50.5371 |          1.0000 |
| Ours (W:Geometry)   | geometry_biased |         4.0000 |            0.4718 |    1816.7000 |       134.0000 |         5.0000 |     50.5371 |          1.0000 |
| Ours (W:Time+Stops) | time_stops      |         4.0000 |            0.3241 |    1972.8800 |       177.0000 |        11.0000 |     23.2989 |          1.0000 |
| Ours (W:TimeOnly)   | time_only       |         4.0000 |            0.3854 |    1948.6400 |       185.0000 |         6.0000 |     22.8845 |          1.0000 |
