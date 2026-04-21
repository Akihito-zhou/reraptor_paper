# Exp2 Supporting Summary

## negative_theme_alignment

| Algorithm | StopScore | Score/hr | ThemeScore | ThemeHit | ThemeSat | Mean ms | Labels | Success | CapHit | Timeout |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 928.390 | 183.972 | 26.902 | 0.027 | 0.004 | 4502.119 | 70144.1 | 1.000 | 0.000 | 0.000 |
| Ours (NoNeg) | 928.656 | 184.059 | 26.185 | 0.026 | 0.004 | 4519.232 | 71889.9 | 1.000 | 0.000 | 0.000 |

## negative_theme_alignment: Full vs NoNeg

| Metric | Mean | FullBetter | Tie | NoNegBetter |
|---|---|---|---|---|
| ThemeHit delta | 0.0005 | 3 | 476 | 1 |
| ThemeSat delta | 0.0000 | 0 | 480 | 0 |
| StopScore delta | -0.267 | 0 | 473 | 7 |
| Runtime delta ms | -17.113 | 201 | 0 | 279 |

### By Pressure

| Pressure | cases | d_theme_hit | d_theme_sat | d_stop_score | d_elapsed_ms | theme_advantage_rate | same_route_rate |
|---|---|---|---|---|---|---|---|
| Default | 240 | 0.0009 | 0.0000 | -0.450 | -28.738 | 0.0083 | 0.9917 |
| Tight | 240 | 0.0002 | 0.0000 | -0.083 | -5.487 | 0.0042 | 0.9792 |

### By Conflict

| Conflict | cases | d_theme_hit | d_theme_sat | d_stop_score | d_elapsed_ms | theme_advantage_rate |
|---|---|---|---|---|---|---|
| Low conflict | 160 | 0.0006 | 0.0000 | -0.388 | 3.219 | 0.0063 |
| Medium conflict | 160 | 0.0010 | 0.0000 | -0.362 | -66.807 | 0.0125 |
| High conflict | 160 | 0.0000 | 0.0000 | -0.050 | 12.250 | 0.0000 |

