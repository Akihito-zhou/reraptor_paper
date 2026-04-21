# Ours Pruning Enhancement Probe (2026-03-24)

Backup:
- `paper/archive/ours_pruning_enhancement_backup_20260324_125123`

Enhancement switches tested inside the original three-layer framework:
- `use_bound_dominance`
- `use_upper_bound_pruning`

Cases and results:

## meinohama / 07:00 / 4h

| variant | stop_score_total | elapsed_s | labels | upper_bound_pruned | termination |
| --- | ---: | ---: | ---: | ---: | --- |
| base | 742.0 | 2.692 | 52301 | 0 | completed |
| dominance only | 742.0 | 3.573 | 52301 | 0 | completed |
| upper bound only | 742.0 | 3.394 | 52289 | 2808 | completed |
| dominance + upper bound | 742.0 | 3.483 | 52289 | 2808 | completed |

## hakata / 07:00 / 4h

| variant | stop_score_total | elapsed_s | labels | upper_bound_pruned | termination |
| --- | ---: | ---: | ---: | ---: | --- |
| base | 981.0 | 189.495 | 2184278 | 0 | completed |
| dominance only | 981.0 | 221.681 | 2184278 | 0 | completed |
| upper bound only | 981.0 | 111.285 | 1807314 | 935258 | completed |
| dominance + upper bound | 981.0 | 106.827 | 1807314 | 935258 | completed |

## hakata / 07:00 / 8h (same 600s compute budget)

| variant | stop_score_total | elapsed_s | labels | upper_bound_pruned | termination |
| --- | ---: | ---: | ---: | ---: | --- |
| base (`timeout_seconds=600`) | 1367.0 | 601.769 | 7687984 | 0 | timeout |
| upper bound (`timeout_seconds=600`) | 1273.0 | 601.708 | 6733704 | 3796 | timeout |

Takeaways:
- Bound-enhanced dominance alone did not help on the tested cases.
- Upper-bound pruning materially improved the difficult 4h case without changing solution quality.
- On the hard 8h case under a fixed 600s compute budget, the current upper-bound pruning reduced state growth slightly but did not improve quality.
- The current upper bound is useful for medium budgets but is still too loose to control the longest-budget cases.
