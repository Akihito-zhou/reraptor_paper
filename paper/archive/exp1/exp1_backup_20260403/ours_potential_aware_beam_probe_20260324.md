# Ours Potential-Aware Beam Probe (2026-03-24)

This probe keeps the original three-layer structure and only changes the
first-layer beam ordering rule:

- base beam: sort by current label score
- potential-aware beam: sort by `current stop score + 0.5 * optimistic future score gap`

The implementation remains optional through `use_potential_aware_beam=True`.
Default `Ours` behavior is unchanged because the switch remains off.

Cases and results:

## meinohama / 07:00 / 4h

| variant | stop_score_total | elapsed_s | labels | termination |
| --- | ---: | ---: | ---: | --- |
| base | 742.0 | 5.695 | 52291 | completed |
| potential-aware beam | 742.0 | 10.101 | 52291 | completed |

## hakata / 07:00 / 4h

| variant | stop_score_total | elapsed_s | labels | termination |
| --- | ---: | ---: | ---: | --- |
| base | 981.0 | 391.696 | 2183909 | completed |
| potential-aware beam | 981.0 | 530.027 | 2242728 | completed |

## hakata / 07:00 / 8h (same 300s compute budget)

| variant | stop_score_total | elapsed_s | labels | termination |
| --- | ---: | ---: | ---: | --- |
| base (`timeout_seconds=300`) | 918.0 | 301.150 | 2935031 | timeout |
| potential-aware beam (`timeout_seconds=300`) | 824.0 | 301.214 | 2073821 | timeout |

Takeaways:
- The potential-aware beam reduced explored labels on the 8h timeout case.
- However, under the same compute budget it also reduced the achieved score.
- On 4h cases it either had no quality gain or became slower.
- Therefore this beam ordering should remain experimental and should not replace the default method.
