# Wilcoxon Signed-Rank Test Results (Query-Level Means)

**Baseline:** `Ours (Full)`
Paired by `(origin, depart_time, budget_minutes)`, N=30.
Scope: 8h budget only.

## Metric: `composite_score`
| Algorithm | Pairs (N) | Mean Diff (Ours-Other) | W-Statistic | p-value | Significant (p<0.05) |
|---|---:|---:|---:|---:|---|
| Greedy (L=3) | 30 | +0.171570 | 1.0 | 3.72529e-09 | Yes |
| ILS+2opt | 30 | +0.112088 | 8.0 | 4.65661e-08 | Yes |
| McRAPTOR | 30 | +0.338920 | 0.0 | 1.86265e-09 | Yes |
| NSGA-II | 30 | +0.057213 | 79.0 | 0.00103817 | Yes |
| Pure RAPTOR | 30 | +0.412279 | 0.0 | 1.86265e-09 | Yes |
| SA | 30 | +0.180510 | 1.0 | 3.72529e-09 | Yes |
| VNS | 30 | +0.139604 | 2.0 | 5.58794e-09 | Yes |

## Metric: `ride_minutes`
| Algorithm | Pairs (N) | Mean Diff (Ours-Other) | W-Statistic | p-value | Significant (p<0.05) |
|---|---:|---:|---:|---:|---|
| Greedy (L=3) | 30 | -95.666667 | 4.0 | 1.30385e-08 | Yes |
| ILS+2opt | 30 | -104.100000 | 0.0 | 1.86265e-09 | Yes |
| McRAPTOR | 30 | +149.086667 | 0.0 | 1.86265e-09 | Yes |
| NSGA-II | 30 | -114.173333 | 0.0 | 1.86265e-09 | Yes |
| Pure RAPTOR | 30 | +166.700000 | 1.0 | 3.72529e-09 | Yes |
| SA | 30 | -48.633333 | 43.0 | 2.36668e-05 | Yes |
| VNS | 30 | -80.740000 | 5.0 | 1.86265e-08 | Yes |

## Metric: `hull_area`
| Algorithm | Pairs (N) | Mean Diff (Ours-Other) | W-Statistic | p-value | Significant (p<0.05) |
|---|---:|---:|---:|---:|---|
| Greedy (L=3) | 30 | +115.729410 | 0.0 | 1.86265e-09 | Yes |
| ILS+2opt | 30 | +103.402261 | 0.0 | 1.86265e-09 | Yes |
| McRAPTOR | 30 | +99.265647 | 0.0 | 1.86265e-09 | Yes |
| NSGA-II | 30 | +93.095460 | 0.0 | 1.86265e-09 | Yes |
| Pure RAPTOR | 30 | +112.306073 | 0.0 | 1.86265e-09 | Yes |
| SA | 30 | +109.527184 | 0.0 | 1.86265e-09 | Yes |
| VNS | 30 | +107.218605 | 0.0 | 1.86265e-09 | Yes |

## Metric: `elapsed_ms`
| Algorithm | Pairs (N) | Mean Diff (Ours-Other) | W-Statistic | p-value | Significant (p<0.05) |
|---|---:|---:|---:|---:|---|
| Greedy (L=3) | 30 | +5988.596133 | 0.0 | 1.86265e-09 | Yes |
| ILS+2opt | 30 | +5853.356867 | 0.0 | 1.86265e-09 | Yes |
| McRAPTOR | 30 | +3436.589200 | 0.0 | 1.86265e-09 | Yes |
| NSGA-II | 30 | -11104.591867 | 0.0 | 1.86265e-09 | Yes |
| Pure RAPTOR | 30 | -57549.053333 | 0.0 | 1.86265e-09 | Yes |
| SA | 30 | +5959.552933 | 0.0 | 1.86265e-09 | Yes |
| VNS | 30 | +5945.055000 | 0.0 | 1.86265e-09 | Yes |

