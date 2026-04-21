# Exp2 Supporting Experiments Summary

## theme_negative::coastal_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.675320 | 0.719765 | 12546.058 | 14344.583 | 14450.504 | 0.000 | 0.000 | 0.431011 | 0.160256 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 365195.7 | 0.178 | 0.333 | 327226.7 | 794.86 |
| Ours (NoNeg) | 3 | 0.676379 | 0.716194 | 8079.327 | 8783.320 | 8798.816 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.159 | 0.333 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.001059, dThemeComp=+0.003571, dThemeHit=+0.018519, dThemeSat=+0.000000, dNegThemeHit=+327226.667, dMeanMs=+4466.731

## theme_negative::east_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.629421 | 0.692436 | 13545.407 | 15743.218 | 15898.208 | 0.000 | 0.000 | 0.491084 | 0.072421 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 389523.3 | 0.252 | 0.667 | 350801.3 | 779.96 |
| Ours (NoNeg) | 3 | 0.676379 | 0.693972 | 7884.340 | 8429.205 | 8431.978 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.070 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.046958, dThemeComp=-0.001536, dThemeHit=+0.181689, dThemeSat=+0.666667, dNegThemeHit=+350801.333, dMeanMs=+5661.067

## theme_negative::mountain_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.668040 | 0.683192 | 12636.053 | 13788.189 | 13878.124 | 0.000 | 0.000 | 0.408130 | 0.217094 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 389504.7 | 0.061 | 0.333 | 353231.7 | 827.22 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 7964.390 | 8595.911 | 8606.489 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.008339, dThemeComp=+0.006813, dThemeHit=+0.060606, dThemeSat=+0.333333, dNegThemeHit=+353231.667, dMeanMs=+4671.663

## theme_negative::north_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.666996 | 0.782969 | 12538.259 | 13968.388 | 13989.726 | 0.000 | 0.000 | 0.435546 | 0.113960 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 336349.3 | 0.464 | 1.000 | 297170.3 | 701.89 |
| Ours (NoNeg) | 3 | 0.676379 | 0.785176 | 7998.400 | 8693.409 | 8725.973 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.435 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.009383, dThemeComp=-0.002207, dThemeHit=+0.028704, dThemeSat=+0.333333, dNegThemeHit=+297170.333, dMeanMs=+4539.859

## theme_negative::north_coastal_like

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.673879 | 0.881876 | 8926.785 | 9677.709 | 9730.552 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 58760.3 | 0.832 | 1.000 | 25307.3 | 81.24 |
| Ours (NoNeg) | 3 | 0.676379 | 0.885638 | 8289.731 | 9130.638 | 9175.170 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.837 | 1.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.003762, dThemeHit=-0.005050, dThemeSat=+0.000000, dNegThemeHit=+25307.333, dMeanMs=+637.054

## theme_negative::outer_ring

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.673879 | 0.758475 | 10077.137 | 11291.293 | 11346.917 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 270583.0 | 0.338 | 0.667 | 235762.7 | 682.47 |
| Ours (NoNeg) | 3 | 0.676379 | 0.759713 | 8090.184 | 8840.557 | 8876.023 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.333 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.001238, dThemeHit=+0.005051, dThemeSat=+0.000000, dNegThemeHit=+235762.667, dMeanMs=+1986.953

## theme_negative::park_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.650881 | 0.690945 | 12978.398 | 15396.322 | 15602.827 | 0.000 | 0.000 | 0.445083 | 0.071429 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 406101.7 | 0.160 | 0.333 | 367885.0 | 861.09 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 8068.072 | 8791.812 | 8821.695 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.025498, dThemeComp=+0.014566, dThemeHit=+0.160256, dThemeSat=+0.333333, dNegThemeHit=+367885.000, dMeanMs=+4910.326

## theme_negative::shrine_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.664780 | 0.686245 | 11316.432 | 12531.136 | 12671.748 | 0.000 | 0.000 | 0.382051 | 0.142308 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 365235.0 | 0.086 | 0.000 | 330018.0 | 852.89 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 8025.927 | 8613.043 | 8626.631 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.011599, dThemeComp=+0.009866, dThemeHit=+0.085859, dThemeSat=+0.000000, dNegThemeHit=+330018.000, dMeanMs=+3290.505

