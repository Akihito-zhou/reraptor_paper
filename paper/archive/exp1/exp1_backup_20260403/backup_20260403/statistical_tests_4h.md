# Wilcoxon Signed-Rank Test Results (Query-Level Means)

**Baseline:** `Ours (Full)`
Paired by `(origin, depart_time, budget_minutes)`, N=30.
Scope: 4h budget only.

## Metric: `composite_score`
| Algorithm | Pairs (N) | Mean Diff (Ours-Other) | W-Statistic | p-value | Significant (p<0.05) |
|---|---:|---:|---:|---:|---|
| Greedy (L=3) | 30 | +0.071890 | 5.0 | 1.86265e-08 | Yes |
| ILS+2opt | 30 | +0.055197 | 20.0 | 6.91041e-07 | Yes |
| McRAPTOR | 30 | +0.073413 | 7.0 | 3.53903e-08 | Yes |
| NSGA-II | 30 | +0.012554 | 147.0 | 0.0803274 | No |
| Pure RAPTOR | 30 | +0.096590 | 21.0 | 8.32602e-07 | Yes |
| SA | 30 | +0.085486 | 6.0 | 2.6077e-08 | Yes |
| VNS | 30 | +0.060557 | 9.0 | 6.14673e-08 | Yes |

## Metric: `ride_minutes`
| Algorithm | Pairs (N) | Mean Diff (Ours-Other) | W-Statistic | p-value | Significant (p<0.05) |
|---|---:|---:|---:|---:|---|
| Greedy (L=3) | 30 | -36.166667 | 35.5 | 7.99447e-06 | Yes |
| ILS+2opt | 30 | -41.260000 | 12.0 | 1.30385e-07 | Yes |
| McRAPTOR | 30 | +25.993333 | 35.0 | 7.93517e-05 | Yes |
| NSGA-II | 30 | -44.426667 | 5.0 | 1.86265e-08 | Yes |
| Pure RAPTOR | 30 | +31.286667 | 48.0 | 4.40758e-05 | Yes |
| SA | 30 | -16.006667 | 136.0 | 0.047259 | Yes |
| VNS | 30 | -35.113333 | 35.0 | 7.99447e-06 | Yes |

## Metric: `hull_area`
| Algorithm | Pairs (N) | Mean Diff (Ours-Other) | W-Statistic | p-value | Significant (p<0.05) |
|---|---:|---:|---:|---:|---|
| Greedy (L=3) | 30 | +43.514567 | 0.0 | 1.86265e-09 | Yes |
| ILS+2opt | 30 | +42.989971 | 0.0 | 1.86265e-09 | Yes |
| McRAPTOR | 30 | +23.434511 | 14.0 | 2.04891e-07 | Yes |
| NSGA-II | 30 | +36.396566 | 3.0 | 9.31323e-09 | Yes |
| Pure RAPTOR | 30 | +23.417245 | 43.0 | 2.36668e-05 | Yes |
| SA | 30 | +45.062579 | 0.0 | 1.86265e-09 | Yes |
| VNS | 30 | +43.317294 | 0.0 | 1.86265e-09 | Yes |

## Metric: `elapsed_ms`
| Algorithm | Pairs (N) | Mean Diff (Ours-Other) | W-Statistic | p-value | Significant (p<0.05) |
|---|---:|---:|---:|---:|---|
| Greedy (L=3) | 30 | +1291.843067 | 0.0 | 1.86265e-09 | Yes |
| ILS+2opt | 30 | +1249.982133 | 0.0 | 1.86265e-09 | Yes |
| McRAPTOR | 30 | -1244.711200 | 0.0 | 1.86265e-09 | Yes |
| NSGA-II | 30 | -12165.819600 | 0.0 | 1.86265e-09 | Yes |
| Pure RAPTOR | 30 | -62041.019467 | 0.0 | 1.86265e-09 | Yes |
| SA | 30 | +1274.947200 | 0.0 | 1.86265e-09 | Yes |
| VNS | 30 | +1267.700200 | 0.0 | 1.86265e-09 | Yes |

