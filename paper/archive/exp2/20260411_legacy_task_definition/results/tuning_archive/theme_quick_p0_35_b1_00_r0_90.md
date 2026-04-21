# Exp2 Supporting Experiments Summary

## theme_negative::coastal_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.675320 | 0.719765 | 13090.961 | 15180.113 | 15293.429 | 0.000 | 0.000 | 0.431011 | 0.160256 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 389841.0 | 0.178 | 0.333 | 349604.0 | 798.95 |
| Ours (NoNeg) | 3 | 0.676379 | 0.716194 | 7894.903 | 8543.229 | 8570.311 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.159 | 0.333 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.001059, dThemeComp=+0.003571, dThemeHit=+0.018519, dThemeSat=+0.000000, dNegThemeHit=+349604.000, dMeanMs=+5196.058

## theme_negative::east_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.644705 | 0.707720 | 14988.831 | 17171.894 | 17270.724 | 0.000 | 0.000 | 0.491733 | 0.051587 | 0.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 430028.3 | 0.252 | 0.333 | 389966.7 | 801.58 |
| Ours (NoNeg) | 3 | 0.676379 | 0.693972 | 8152.786 | 8788.029 | 8806.991 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.070 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.031674, dThemeComp=+0.013748, dThemeHit=+0.181689, dThemeSat=+0.333333, dNegThemeHit=+389966.667, dMeanMs=+6836.045

## theme_negative::mountain_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.583028 | 0.613584 | 14427.881 | 15574.332 | 15601.360 | 0.000 | 0.000 | 0.515156 | 0.192064 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 425877.3 | 0.122 | 0.333 | 386671.0 | 829.93 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 8071.111 | 8817.183 | 8847.782 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.093351, dThemeComp=-0.062795, dThemeHit=+0.122222, dThemeSat=+0.333333, dNegThemeHit=+386671.000, dMeanMs=+6356.770

## theme_negative::north_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.666996 | 0.782969 | 13571.707 | 15292.070 | 15331.916 | 0.000 | 0.000 | 0.435546 | 0.113960 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 370577.3 | 0.464 | 1.000 | 328870.3 | 729.74 |
| Ours (NoNeg) | 3 | 0.676379 | 0.785176 | 8149.844 | 8875.660 | 8896.659 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.435 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.009383, dThemeComp=-0.002207, dThemeHit=+0.028704, dThemeSat=+0.333333, dNegThemeHit=+328870.333, dMeanMs=+5421.863

## theme_negative::north_coastal_like

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.673879 | 0.881876 | 9118.014 | 9690.624 | 9744.798 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 76468.7 | 0.832 | 1.000 | 41438.0 | 129.82 |
| Ours (NoNeg) | 3 | 0.676379 | 0.885638 | 8110.794 | 8850.945 | 8886.813 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.837 | 1.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.003762, dThemeHit=-0.005050, dThemeSat=+0.000000, dNegThemeHit=+41438.000, dMeanMs=+1007.220

## theme_negative::outer_ring

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.657218 | 0.759400 | 10369.542 | 11466.423 | 11468.937 | 0.000 | 0.000 | 0.439069 | 0.092593 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 290942.7 | 0.409 | 1.000 | 253632.0 | 708.23 |
| Ours (NoNeg) | 3 | 0.676379 | 0.759713 | 7940.299 | 8550.811 | 8560.897 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.333 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.019161, dThemeComp=-0.000313, dThemeHit=+0.075397, dThemeSat=+0.333333, dNegThemeHit=+253632.000, dMeanMs=+2429.243

## theme_negative::park_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.659217 | 0.700349 | 14339.841 | 16574.717 | 16789.356 | 0.000 | 0.000 | 0.418767 | 0.097070 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 438846.3 | 0.165 | 0.333 | 397080.3 | 839.86 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 8015.791 | 8692.758 | 8707.080 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.017162, dThemeComp=+0.023970, dThemeHit=+0.164530, dThemeSat=+0.333333, dNegThemeHit=+397080.333, dMeanMs=+6324.050

## theme_negative::shrine_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 3 | 0.668412 | 0.695218 | 12316.101 | 13501.579 | 13667.430 | 0.000 | 0.000 | 0.377124 | 0.140476 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 388536.0 | 0.107 | 0.333 | 353169.3 | 849.06 |
| Ours (NoNeg) | 3 | 0.676379 | 0.676379 | 8017.054 | 8580.956 | 8586.549 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.007967, dThemeComp=+0.018839, dThemeHit=+0.107226, dThemeSat=+0.333333, dNegThemeHit=+353169.333, dMeanMs=+4299.047

