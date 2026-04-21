# 8h Trade-off Pilot Analysis (2026-03-25)

Source:
- `paper/results/exp1_algorithm_comparison/exp1_tradeoff_tradeoff_8h_pilot.json`

Configuration:
- travel budget: `480` minutes
- origins: `hakata`, `meinohama`
- depart times: `07:00`
- compute budgets: `30s`, `120s`, `600s`
- algorithms: `Ours`, `NSGA-II`
- seeds: `0`, `1`

## Average score by compute budget

| algorithm | 30s | 120s | 600s |
| --- | ---: | ---: | ---: |
| Ours (Full) | 770.0 | 1050.5 | 1554.25 |
| NSGA-II | 1497.0 | 1497.0 | 1497.0 |

Observed average elapsed time:

| algorithm | 30s | 120s | 600s |
| --- | ---: | ---: | ---: |
| Ours (Full) | 30.704s | 123.734s | 651.787s |
| NSGA-II | 30.074s | 48.413s | 44.800s |

## Query-level average over seeds

### hakata / 07:00 / 8h

| compute budget | Ours avg | NSGA-II avg | diff |
| --- | ---: | ---: | ---: |
| 30s | 674.0 | 1609.0 | -935.0 |
| 120s | 939.0 | 1609.0 | -670.0 |
| 600s | 1430.0 | 1609.0 | -179.0 |

### meinohama / 07:00 / 8h

| compute budget | Ours avg | NSGA-II avg | diff |
| --- | ---: | ---: | ---: |
| 30s | 866.0 | 1385.0 | -519.0 |
| 120s | 1162.0 | 1385.0 | -223.0 |
| 600s | 1678.5 | 1385.0 | +293.5 |

## Interpretation

- `Ours` shows a strong monotonic improvement as more wall-clock time is allowed.
- `NSGA-II` is effectively saturated by `30s` on this pilot set.
- `Ours` does not dominate `NSGA-II` universally under long budgets.
- However, `Ours` clearly behaves as a constructive method that can keep trading more compute for better score.
- This trade-off is scenario-dependent:
  - `hakata`: `Ours` improves substantially but still does not catch `NSGA-II` by `600s`
  - `meinohama`: `Ours` overtakes `NSGA-II` by `600s`

## Practical narrative

This pilot supports a paper narrative closer to:

`Ours is a competitive constructive alternative whose solution quality improves steadily with additional computation, while NSGA-II reaches a high-quality plateau much earlier.`

It does **not** yet support:

`Ours consistently outperforms NSGA-II under 8h queries.`
