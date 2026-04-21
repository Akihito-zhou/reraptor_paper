# Ours Stop-Aware Upper Bound Probe (2026-03-24)

This probe keeps the original three-layer pruning structure and only replaces
the third-layer upper bound with a stop-aware reachable-score bound.

Implementation notes:
- Bound remains optional through `use_upper_bound_pruning=True`.
- Default `Ours` behavior is unchanged because the switch remains off.
- The new bound uses the current stop's optimistic minimum-ride reachability
  instead of only global top scores.

Cases and results:

## meinohama / 07:00 / 4h

| variant | stop_score_total | elapsed_s | labels | upper_bound_pruned | termination |
| --- | ---: | ---: | ---: | ---: | --- |
| base | 742.0 | 6.818 | 52283 | 0 | completed |
| stop-aware UB | 742.0 | 11.922 | 52271 | 2836 | completed |

## hakata / 07:00 / 4h

| variant | stop_score_total | elapsed_s | labels | upper_bound_pruned | termination |
| --- | ---: | ---: | ---: | ---: | --- |
| base | 981.0 | 330.532 | 2184153 | 0 | completed |
| stop-aware UB | 981.0 | 277.450 | 1807913 | 938069 | completed |

## hakata / 07:00 / 8h (same 600s compute budget)

| variant | stop_score_total | elapsed_s | labels | upper_bound_pruned | termination |
| --- | ---: | ---: | ---: | ---: | --- |
| base (`timeout_seconds=600`) | 1112.0 | 602.351 | 4468255 | 0 | timeout |
| stop-aware UB (`timeout_seconds=600`) | 981.0 | 601.577 | 3501618 | 8432 | timeout |

Takeaways:
- The stop-aware upper bound helps on the difficult 4h case.
- It is not robust enough for the hardest 8h case under a fixed compute budget.
- Therefore it should remain experimental and should not replace the default method.
