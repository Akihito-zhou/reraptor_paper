# Exp2 Supporting Experiments Summary

## theme_negative::coastal_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.673879 | 0.714957 | 10394.525 | 12048.643 | 12190.215 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 295530.0 | 0.164 | 0.667 | 260750.7 | 754.48 |
| Ours (NoNeg) | 3 | 0.676379 | 0.716194 | 8435.682 | 9241.017 | 9275.676 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.159 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.001237, dThemeHit=+0.005051, dThemeSat=+0.000000, dNegThemeHit=+260750.667, dMeanMs=+1958.843

## theme_negative::east_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.669828 | 0.702572 | 10630.089 | 12069.583 | 12154.739 | 0.000 | 0.000 | 0.419408 | 0.138034 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 303883.7 | 0.131 | 0.000 | 270595.0 | 758.50 |
| Ours (NoNeg) | 3 | 0.676379 | 0.693972 | 8201.394 | 8771.884 | 8779.466 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.070 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.006551, dThemeComp=+0.008600, dThemeHit=+0.060606, dThemeSat=+0.000000, dNegThemeHit=+270595.000, dMeanMs=+2428.695

## theme_negative::mountain_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.673879 | 0.673879 | 10610.611 | 11688.227 | 11813.724 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 325869.3 | 0.000 | 0.000 | 291400.3 | 817.23 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 8055.373 | 8753.996 | 8769.407 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.002500, dThemeHit=+0.000000, dThemeSat=+0.000000, dNegThemeHit=+291400.333, dMeanMs=+2555.238

## theme_negative::north_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.667223 | 0.758658 | 10168.570 | 11605.867 | 11688.508 | 0.000 | 0.000 | 0.414939 | 0.147293 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 275400.3 | 0.366 | 1.000 | 238725.7 | 671.92 |
| Ours (NoNeg) | 3 | 0.676379 | 0.785176 | 8023.802 | 8801.155 | 8835.051 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.435 | 1.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.009156, dThemeComp=-0.026518, dThemeHit=-0.069444, dThemeSat=+0.000000, dNegThemeHit=+238725.667, dMeanMs=+2144.768

## theme_negative::north_coastal_like

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.673879 | 0.881876 | 8621.425 | 9409.771 | 9449.667 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 50586.3 | 0.832 | 1.000 | 17162.7 | 55.88 |
| Ours (NoNeg) | 3 | 0.676379 | 0.885638 | 7965.218 | 8806.951 | 8856.642 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.837 | 1.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.003762, dThemeHit=-0.005050, dThemeSat=+0.000000, dNegThemeHit=+17162.667, dMeanMs=+656.207

## theme_negative::outer_ring

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.673879 | 0.758475 | 9116.331 | 9849.645 | 9858.049 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 255997.3 | 0.338 | 1.000 | 222034.7 | 686.14 |
| Ours (NoNeg) | 3 | 0.676379 | 0.759713 | 7976.871 | 8629.084 | 8654.306 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.333 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.001238, dThemeHit=+0.005051, dThemeSat=+0.333333, dNegThemeHit=+222034.667, dMeanMs=+1139.460

## theme_negative::park_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.657812 | 0.679892 | 10322.417 | 11707.296 | 11820.660 | 0.000 | 0.000 | 0.447909 | 0.149495 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 330736.0 | 0.088 | 0.000 | 296973.3 | 834.62 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 7944.368 | 8488.972 | 8512.869 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.018567, dThemeComp=+0.003513, dThemeHit=+0.088319, dThemeSat=+0.000000, dNegThemeHit=+296973.333, dMeanMs=+2378.049

## theme_negative::shrine_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.673879 | 0.673879 | 9815.301 | 10875.297 | 10951.150 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 318542.3 | 0.000 | 0.000 | 285185.3 | 839.35 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 8180.024 | 8929.561 | 8956.947 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.002500, dThemeHit=+0.000000, dThemeSat=+0.000000, dNegThemeHit=+285185.333, dMeanMs=+1635.277

