# Wilcoxon Signed-Rank Test Results (Query-Level Means)

**Baseline:** `Ours (Full)`
Paired by `(origin, depart_time, budget_minutes)`, N=60.
Scope: all budgets combined (4h + 8h).

## Metric: `composite_score`
| Algorithm | Pairs (N) | Mean Diff (Ours-Other) | W-Statistic | p-value | Significant (p<0.05) |
|---|---:|---:|---:|---:|---|
| Greedy (L=3) | 60 | +0.121730 | 12.0 | 2.98057e-11 | Yes |
| ILS+2opt | 60 | +0.083642 | 50.0 | 1.91775e-10 | Yes |
| McRAPTOR | 60 | +0.206167 | 7.0 | 2.31975e-11 | Yes |
| NSGA-II | 60 | +0.034884 | 430.0 | 0.000356467 | Yes |
| Pure RAPTOR | 60 | +0.254434 | 21.0 | 4.66437e-11 | Yes |
| SA | 60 | +0.132998 | 10.0 | 2.69665e-11 | Yes |
| VNS | 60 | +0.100080 | 22.0 | 4.90104e-11 | Yes |

## Metric: `ride_minutes`
| Algorithm | Pairs (N) | Mean Diff (Ours-Other) | W-Statistic | p-value | Significant (p<0.05) |
|---|---:|---:|---:|---:|---|
| Greedy (L=3) | 60 | -65.916667 | 62.5 | 3.47441e-10 | Yes |
| ILS+2opt | 60 | -72.680000 | 13.0 | 3.1333e-11 | Yes |
| McRAPTOR | 60 | +87.540000 | 35.0 | 1.40083e-10 | Yes |
| NSGA-II | 60 | -79.300000 | 6.0 | 2.20495e-11 | Yes |
| Pure RAPTOR | 60 | +98.993333 | 58.0 | 2.80727e-10 | Yes |
| SA | 60 | -32.320000 | 319.5 | 1.166e-05 | Yes |
| VNS | 60 | -57.926667 | 64.0 | 3.73333e-10 | Yes |

## Metric: `hull_area`
| Algorithm | Pairs (N) | Mean Diff (Ours-Other) | W-Statistic | p-value | Significant (p<0.05) |
|---|---:|---:|---:|---:|---|
| Greedy (L=3) | 60 | +79.621988 | 0.0 | 1.62956e-11 | Yes |
| ILS+2opt | 60 | +73.196116 | 0.0 | 1.62956e-11 | Yes |
| McRAPTOR | 60 | +61.350079 | 14.0 | 3.29368e-11 | Yes |
| NSGA-II | 60 | +64.746013 | 3.0 | 1.89644e-11 | Yes |
| Pure RAPTOR | 60 | +67.861659 | 43.0 | 1.36867e-10 | Yes |
| SA | 60 | +77.294882 | 0.0 | 1.62956e-11 | Yes |
| VNS | 60 | +75.267950 | 0.0 | 1.62956e-11 | Yes |

## Metric: `elapsed_ms`
| Algorithm | Pairs (N) | Mean Diff (Ours-Other) | W-Statistic | p-value | Significant (p<0.05) |
|---|---:|---:|---:|---:|---|
| Greedy (L=3) | 60 | +3640.219600 | 0.0 | 1.62956e-11 | Yes |
| ILS+2opt | 60 | +3551.669500 | 0.0 | 1.62956e-11 | Yes |
| McRAPTOR | 60 | +1095.939000 | 565.0 | 0.00997886 | Yes |
| NSGA-II | 60 | -11635.205733 | 0.0 | 1.62956e-11 | Yes |
| Pure RAPTOR | 60 | -59795.036400 | 0.0 | 1.62956e-11 | Yes |
| SA | 60 | +3617.250067 | 0.0 | 1.62956e-11 | Yes |
| VNS | 60 | +3606.377600 | 0.0 | 1.62956e-11 | Yes |

