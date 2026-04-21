# Exp2 Supporting Experiments Summary

## theme_negative::coastal_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.672820 | 0.718528 | 10955.044 | 12512.374 | 12604.828 | 0.000 | 0.000 | 0.433273 | 0.165812 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 333720.7 | 0.183 | 0.333 | 297975.0 | 794.64 |
| Ours (NoNeg) | 3 | 0.676379 | 0.716194 | 8226.475 | 8943.349 | 8973.079 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.159 | 0.333 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.003559, dThemeComp=+0.002334, dThemeHit=+0.023569, dThemeSat=+0.000000, dNegThemeHit=+297975.000, dMeanMs=+2728.569

## theme_negative::east_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.626847 | 0.689862 | 12210.935 | 14779.232 | 15021.755 | 0.000 | 0.000 | 0.492694 | 0.090803 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 356927.3 | 0.252 | 0.333 | 321000.0 | 789.45 |
| Ours (NoNeg) | 3 | 0.676379 | 0.693972 | 8140.042 | 8841.885 | 8864.359 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.070 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.049532, dThemeComp=-0.004110, dThemeHit=+0.181689, dThemeSat=+0.333333, dNegThemeHit=+321000.000, dMeanMs=+4070.893

## theme_negative::mountain_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.668040 | 0.683192 | 11711.268 | 12792.263 | 12918.644 | 0.000 | 0.000 | 0.408130 | 0.217094 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 361680.7 | 0.061 | 0.000 | 326093.0 | 836.28 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 8129.224 | 8807.978 | 8818.472 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.008339, dThemeComp=+0.006813, dThemeHit=+0.060606, dThemeSat=+0.000000, dNegThemeHit=+326093.000, dMeanMs=+3582.044

## theme_negative::north_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.666996 | 0.782969 | 11542.708 | 12762.690 | 12768.072 | 0.000 | 0.000 | 0.435546 | 0.113960 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 325350.3 | 0.464 | 1.000 | 286075.7 | 720.86 |
| Ours (NoNeg) | 3 | 0.676379 | 0.785176 | 7942.466 | 8676.417 | 8714.913 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.435 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.009383, dThemeComp=-0.002207, dThemeHit=+0.028704, dThemeSat=+0.333333, dNegThemeHit=+286075.667, dMeanMs=+3600.242

## theme_negative::north_coastal_like

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.673879 | 0.881876 | 8909.148 | 9795.206 | 9873.664 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 69346.3 | 0.832 | 1.000 | 35518.7 | 113.83 |
| Ours (NoNeg) | 3 | 0.676379 | 0.885638 | 7951.841 | 8684.315 | 8705.830 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.837 | 1.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.003762, dThemeHit=-0.005050, dThemeSat=+0.000000, dNegThemeHit=+35518.667, dMeanMs=+957.307

## theme_negative::outer_ring

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.667223 | 0.757501 | 9706.906 | 10818.703 | 10853.212 | 0.000 | 0.000 | 0.414939 | 0.147293 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 278429.0 | 0.361 | 1.000 | 244150.7 | 720.67 |
| Ours (NoNeg) | 3 | 0.676379 | 0.759713 | 7868.503 | 8526.544 | 8549.230 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.333 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.009156, dThemeComp=-0.002212, dThemeHit=+0.027778, dThemeSat=+0.333333, dNegThemeHit=+244150.667, dMeanMs=+1838.403

## theme_negative::park_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.650881 | 0.690945 | 11509.421 | 13297.461 | 13445.373 | 0.000 | 0.000 | 0.445083 | 0.071429 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 366008.0 | 0.160 | 0.333 | 330421.7 | 854.55 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 8164.483 | 8789.751 | 8798.847 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.025498, dThemeComp=+0.014566, dThemeHit=+0.160256, dThemeSat=+0.333333, dNegThemeHit=+330421.667, dMeanMs=+3344.938

## theme_negative::shrine_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.667189 | 0.683856 | 10379.736 | 11507.257 | 11604.648 | 0.000 | 0.000 | 0.402154 | 0.196115 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 339598.3 | 0.067 | 0.333 | 305355.0 | 849.88 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 8088.014 | 8771.629 | 8804.823 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.009190, dThemeComp=+0.007477, dThemeHit=+0.066667, dThemeSat=+0.333333, dNegThemeHit=+305355.000, dMeanMs=+2291.722

