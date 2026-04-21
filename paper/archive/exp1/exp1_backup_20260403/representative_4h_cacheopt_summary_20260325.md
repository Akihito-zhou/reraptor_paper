# Representative 4h Cache-Optimized Summary (2026-03-25)

Source:
- `paper/results/exp1_algorithm_comparison/exp1_results_representative_4h_cacheopt_20260325.json`

Query set:
- origins: `hakata`, `meinohama`
- depart times: `07:00`, `10:00`
- budget: `4h`
- seeds: `0`

Average stop score / runtime:

| algorithm | avg_stop_score | avg_elapsed_s |
| --- | ---: | ---: |
| Ours (Full) | 810.75 | 28.826 |
| NSGA-II | 812.50 | 19.887 |
| ILS+2opt | 671.00 | 0.124 |
| VNS | 694.25 | 0.063 |
| SA | 593.50 | 0.067 |
| McRAPTOR | 570.50 | 3.237 |
| Pure RAPTOR | 362.25 | 61.440 |
| Greedy (L=3) | 518.00 | 0.001 |

Per-query winners:

| query | winner | stop_score_total |
| --- | --- | ---: |
| `hakata / 07:00 / 4h` | Ours (Full) | 981.0 |
| `hakata / 10:00 / 4h` | NSGA-II | 941.0 |
| `meinohama / 07:00 / 4h` | McRAPTOR | 766.0 |
| `meinohama / 10:00 / 4h` | NSGA-II | 715.0 |

Win counts:

| algorithm | wins |
| --- | ---: |
| Ours (Full) | 1 |
| NSGA-II | 2 |
| McRAPTOR | 1 |

Takeaway:
- The cache-preserving implementation optimization materially improved the efficiency of `Ours`.
- However, on this 4h representative slice, `Ours` is not yet the overall best method on stop score.
