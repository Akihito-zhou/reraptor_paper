# Exp2 Supporting Summary

## Key Findings

- Paired tasks: `384` route-theme cases.
- `Full` improves theme-hit ratio in `226/384` pairs, with `156` ties and only `2` regressions.
- Final routes change in `366/384` pairs, so `neg` is changing selected routes rather than only search traces.
- Mean delta: `ThemeHit +0.288`, `ThemeSat +0.312`, `RideMinutes +37.891`, `Runtime +12.17s`.
- Strongest theme-level gain appears on `century-ride` in this run.
- Tested pressure settings have very similar averages in this run, so the main effect here is route-theme preservation rather than pressure sensitivity.

## negative_project_theme_alignment

| Algorithm | RideMinutes | Rate | ThemeScore | ThemeHit | ThemeSat | Mean ms | Labels | Success | CapHit | Timeout |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 318.984 | 2.678 | 13.805 | 0.965 | 0.958 | 18473.950 | 264348.8 | 1.000 | 0.023 | 0.023 |
| Ours (NoNeg) | 281.094 | 1.453 | 5.583 | 0.677 | 0.646 | 6304.285 | 104760.0 | 1.000 | 0.000 | 0.000 |

## negative_project_theme_alignment: Full vs NoNeg

| Metric | Mean | FullBetter | Tie | NoNegBetter |
|---|---|---|---|---|
| ThemeHit delta | 0.2882 | 226 | 156 | 2 |
| ThemeSat delta | 0.3125 | 120 | 264 | 0 |
| RideMinutes delta | 37.891 | 210 | 28 | 146 |
| Runtime delta ms | 12169.664 | 8 | 0 | 376 |
| ThemeAdvantage rate | 0.5885 | 226 | 158 | 0 |

### Route Selection Difference

| Metric | Value |
|---|---|
| Paired cases | 384 |
| Same-route cases | 18 |
| Changed-route cases | 366 |
| Changed-route rate | 0.9531 |

### By Pressure

| Pressure | cases | d_theme_hit | d_theme_sat | d_stop_score | d_elapsed_ms | theme_advantage_rate | changed_route_rate |
|---|---|---|---|---|---|---|---|
| Default | 192 | 0.2882 | 0.3125 | 37.911 | 12435.767 | 0.5885 | 0.9531 |
| Tight | 192 | 0.2882 | 0.3125 | 37.870 | 11903.562 | 0.5885 | 0.9531 |

### By Theme

| Theme | cases | d_theme_hit | d_theme_sat | d_stop_score | d_elapsed_ms | theme_advantage_rate |
|---|---|---|---|---|---|---|
| century-ride | 96 | 0.3879 | 0.4583 | -23.188 | 15335.236 | 0.6250 |
| odd-bus-tour | 96 | 0.1107 | 0.0833 | 34.604 | 9412.692 | 0.7083 |
| random-subset | 96 | 0.3364 | 0.3750 | 78.375 | 12812.511 | 0.4375 |
| single-digit | 96 | 0.3180 | 0.3333 | 61.771 | 11118.218 | 0.5833 |

### By Start Mode

| StartMode | cases | d_theme_hit | d_theme_sat | d_stop_score | d_elapsed_ms | theme_advantage_rate |
|---|---|---|---|---|---|---|
| mixed_route_start | 384 | 0.2882 | 0.3125 | 37.891 | 12169.664 | 0.5885 |

