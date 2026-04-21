# Exp2 Supporting Experiments Summary

## theme_negative::coastal_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.672939 | 0.716315 | 10952.902 | 12072.043 | 12097.613 | 0.000 | 0.000 | 0.440089 | 0.139423 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 323508.3 | 0.174 | 0.667 | 287089.3 | 754.11 |
| Ours (NoNeg) | 3 | 0.676379 | 0.716194 | 7938.862 | 8558.845 | 8578.927 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.159 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.003440, dThemeComp=+0.000121, dThemeHit=+0.014245, dThemeSat=+0.000000, dNegThemeHit=+287089.333, dMeanMs=+3014.040

## theme_negative::east_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.642958 | 0.722212 | 11632.153 | 13245.983 | 13324.845 | 0.000 | 0.000 | 0.472898 | 0.075397 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 337843.0 | 0.317 | 0.667 | 302875.0 | 755.95 |
| Ours (NoNeg) | 3 | 0.676379 | 0.693972 | 7987.921 | 8592.227 | 8612.453 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.070 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.033421, dThemeComp=+0.028240, dThemeHit=+0.246646, dThemeSat=+0.666667, dNegThemeHit=+302875.000, dMeanMs=+3644.232

## theme_negative::mountain_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.670191 | 0.683012 | 11450.779 | 12402.469 | 12518.072 | 0.000 | 0.000 | 0.411967 | 0.228312 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 358383.0 | 0.051 | 0.000 | 323375.3 | 823.01 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 7904.014 | 8675.487 | 8705.521 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.006188, dThemeComp=+0.006633, dThemeHit=+0.051282, dThemeSat=+0.000000, dNegThemeHit=+323375.333, dMeanMs=+3546.765

## theme_negative::north_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.668055 | 0.767824 | 11942.497 | 13591.049 | 13650.553 | 0.000 | 0.000 | 0.412687 | 0.147293 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 311349.7 | 0.399 | 1.000 | 270790.7 | 670.07 |
| Ours (NoNeg) | 3 | 0.676379 | 0.785176 | 8188.400 | 9023.394 | 9068.249 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.435 | 1.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.008324, dThemeComp=-0.017352, dThemeHit=-0.036111, dThemeSat=+0.000000, dNegThemeHit=+270790.667, dMeanMs=+3754.097

## theme_negative::north_coastal_like

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.673879 | 0.881876 | 8733.827 | 9484.320 | 9522.008 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 50644.3 | 0.832 | 1.000 | 17440.7 | 56.52 |
| Ours (NoNeg) | 3 | 0.676379 | 0.885638 | 8209.800 | 8942.807 | 8963.422 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.837 | 1.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.003762, dThemeHit=-0.005050, dThemeSat=+0.000000, dNegThemeHit=+17440.667, dMeanMs=+524.027

## theme_negative::outer_ring

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.673879 | 0.758475 | 9659.441 | 10711.401 | 10737.968 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 265346.3 | 0.338 | 1.000 | 229230.0 | 685.40 |
| Ours (NoNeg) | 3 | 0.676379 | 0.759713 | 8099.204 | 8730.443 | 8752.217 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.333 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.001238, dThemeHit=+0.005051, dThemeSat=+0.333333, dNegThemeHit=+229230.000, dMeanMs=+1560.237

## theme_negative::park_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.661144 | 0.689634 | 11797.365 | 13707.033 | 13841.569 | 0.000 | 0.000 | 0.437347 | 0.084416 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 369980.3 | 0.114 | 0.000 | 334208.3 | 837.34 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 7993.525 | 8746.094 | 8778.229 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.015235, dThemeComp=+0.013255, dThemeHit=+0.113960, dThemeSat=+0.000000, dNegThemeHit=+334208.333, dMeanMs=+3803.840

## theme_negative::shrine_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.689349 | 0.696925 | 10663.513 | 11655.816 | 11748.546 | 0.000 | 0.000 | 0.399754 | 0.254701 | 2.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 346167.0 | 0.030 | 0.000 | 312075.7 | 845.79 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 8010.339 | 8719.710 | 8744.968 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=+0.012970, dThemeComp=+0.020546, dThemeHit=+0.030303, dThemeSat=+0.000000, dNegThemeHit=+312075.667, dMeanMs=+2653.174

