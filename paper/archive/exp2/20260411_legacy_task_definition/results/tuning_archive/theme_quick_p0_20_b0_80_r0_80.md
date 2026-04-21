# Exp2 Supporting Experiments Summary

## theme_negative::coastal_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.672820 | 0.718528 | 10576.601 | 12012.151 | 12104.445 | 0.000 | 0.000 | 0.433273 | 0.165812 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 328834.7 | 0.183 | 0.667 | 293476.7 | 793.14 |
| Ours (NoNeg) | 3 | 0.676379 | 0.716194 | 8039.852 | 8823.188 | 8862.420 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.159 | 0.333 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.003559, dThemeComp=+0.002334, dThemeHit=+0.023569, dThemeSat=+0.333334, dNegThemeHit=+293476.667, dMeanMs=+2536.749

## theme_negative::east_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.642958 | 0.722212 | 11379.896 | 12912.968 | 13008.724 | 0.000 | 0.000 | 0.472898 | 0.075397 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 333799.0 | 0.317 | 0.667 | 299194.3 | 769.52 |
| Ours (NoNeg) | 3 | 0.676379 | 0.693972 | 8067.733 | 8891.175 | 8944.534 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.070 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.033421, dThemeComp=+0.028240, dThemeHit=+0.246646, dThemeSat=+0.666667, dNegThemeHit=+299194.333, dMeanMs=+3312.163

## theme_negative::mountain_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.670191 | 0.683012 | 11331.957 | 12403.687 | 12529.291 | 0.000 | 0.000 | 0.411967 | 0.228312 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 353512.0 | 0.051 | 0.000 | 318113.3 | 833.70 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 8100.374 | 8831.286 | 8859.599 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.006188, dThemeComp=+0.006633, dThemeHit=+0.051282, dThemeSat=+0.000000, dNegThemeHit=+318113.333, dMeanMs=+3231.583

## theme_negative::north_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.668055 | 0.767824 | 11655.450 | 13144.396 | 13182.639 | 0.000 | 0.000 | 0.412687 | 0.147293 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 314498.7 | 0.399 | 0.667 | 275164.3 | 699.72 |
| Ours (NoNeg) | 3 | 0.676379 | 0.785176 | 8108.761 | 8872.544 | 8906.498 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.435 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.008324, dThemeComp=-0.017352, dThemeHit=-0.036111, dThemeSat=+0.000000, dNegThemeHit=+275164.333, dMeanMs=+3546.689

## theme_negative::north_coastal_like

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.673879 | 0.881876 | 8793.988 | 9569.911 | 9619.573 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 57869.7 | 0.832 | 1.000 | 24496.7 | 78.99 |
| Ours (NoNeg) | 3 | 0.676379 | 0.885638 | 8116.080 | 8856.830 | 8876.546 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.837 | 1.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.003762, dThemeHit=-0.005050, dThemeSat=+0.000000, dNegThemeHit=+24496.667, dMeanMs=+677.908

## theme_negative::outer_ring

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.673879 | 0.758475 | 9433.385 | 10315.583 | 10318.073 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 263038.3 | 0.338 | 0.667 | 227986.3 | 689.66 |
| Ours (NoNeg) | 3 | 0.676379 | 0.759713 | 8006.883 | 8628.608 | 8654.021 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.333 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.001238, dThemeHit=+0.005051, dThemeSat=+0.000000, dNegThemeHit=+227986.333, dMeanMs=+1426.502

## theme_negative::park_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.661144 | 0.689634 | 11150.338 | 12900.679 | 13033.110 | 0.000 | 0.000 | 0.437347 | 0.084416 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 362867.3 | 0.114 | 0.000 | 327093.0 | 859.07 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 8012.810 | 8676.212 | 8704.336 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.015235, dThemeComp=+0.013255, dThemeHit=+0.113960, dThemeSat=+0.000000, dNegThemeHit=+327093.000, dMeanMs=+3137.528

## theme_negative::shrine_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.676220 | 0.690109 | 10069.314 | 11151.239 | 11231.558 | 0.000 | 0.000 | 0.392148 | 0.191453 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 336067.0 | 0.056 | 0.000 | 302131.0 | 850.73 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 7952.019 | 8731.669 | 8770.507 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.000159, dThemeComp=+0.013730, dThemeHit=+0.055556, dThemeSat=+0.000000, dNegThemeHit=+302131.000, dMeanMs=+2117.295

