# Exp2 Supporting Experiments Summary

## theme_negative::coastal_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 6 | 0.672939 | 0.716315 | 10954.593 | 12334.394 | 12388.111 | 0.000 | 0.000 | 0.440089 | 0.139423 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 323508.3 | 0.174 | 0.667 | 287089.3 | 754.11 |
| Ours (NoNeg) | 6 | 0.676379 | 0.716194 | 8002.893 | 8599.104 | 8603.321 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.159 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.003440, dThemeComp=+0.000121, dThemeHit=+0.014245, dThemeSat=+0.000000, dNegThemeHit=+287089.333, dMeanMs=+2951.700

## theme_negative::east_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 6 | 0.642958 | 0.722212 | 11750.279 | 13696.569 | 13754.368 | 0.000 | 0.000 | 0.472898 | 0.075397 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 337843.0 | 0.317 | 0.667 | 302875.0 | 755.95 |
| Ours (NoNeg) | 6 | 0.676379 | 0.693972 | 8009.186 | 8697.112 | 8697.836 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.070 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.033421, dThemeComp=+0.028240, dThemeHit=+0.246646, dThemeSat=+0.666667, dNegThemeHit=+302875.000, dMeanMs=+3741.093

## theme_negative::mountain_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 6 | 0.670191 | 0.683012 | 11648.768 | 12853.935 | 12885.985 | 0.000 | 0.000 | 0.411967 | 0.228312 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 358383.0 | 0.051 | 0.000 | 323375.3 | 823.01 |
| Ours (NoNeg) | 6 | 0.676379 | 0.676379 | 8105.590 | 8984.800 | 9000.394 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.006188, dThemeComp=+0.006633, dThemeHit=+0.051282, dThemeSat=+0.000000, dNegThemeHit=+323375.333, dMeanMs=+3543.178

## theme_negative::north_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 6 | 0.668055 | 0.767824 | 11915.948 | 13477.013 | 13514.227 | 0.000 | 0.000 | 0.412687 | 0.147293 | 1.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 311349.7 | 0.399 | 1.000 | 270790.7 | 670.07 |
| Ours (NoNeg) | 6 | 0.676379 | 0.785176 | 7988.350 | 8796.748 | 8863.388 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.435 | 1.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.008324, dThemeComp=-0.017352, dThemeHit=-0.036111, dThemeSat=+0.000000, dNegThemeHit=+270790.667, dMeanMs=+3927.598

## theme_negative::north_coastal_like

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 6 | 0.673879 | 0.881876 | 8605.228 | 9489.671 | 9527.696 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 50644.3 | 0.832 | 1.000 | 17440.7 | 56.52 |
| Ours (NoNeg) | 6 | 0.676379 | 0.885638 | 8016.666 | 8795.962 | 8796.476 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.837 | 1.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.003762, dThemeHit=-0.005050, dThemeSat=+0.000000, dNegThemeHit=+17440.667, dMeanMs=+588.562

## theme_negative::outer_ring

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 6 | 0.673879 | 0.758475 | 9693.665 | 10911.180 | 10957.774 | 0.000 | 0.000 | 0.410414 | 0.199145 | 1.667 | 0.000000 | 0.000 | 0.0 | 1.000 | 265346.3 | 0.338 | 1.000 | 229230.0 | 685.40 |
| Ours (NoNeg) | 6 | 0.676379 | 0.759713 | 8123.178 | 8813.677 | 8821.822 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.333 | 0.667 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.002500, dThemeComp=-0.001238, dThemeHit=+0.005051, dThemeSat=+0.333333, dNegThemeHit=+229230.000, dMeanMs=+1570.487

## theme_negative::park_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 6 | 0.661144 | 0.689634 | 11682.419 | 13715.749 | 13737.555 | 0.000 | 0.000 | 0.437347 | 0.084416 | 1.000 | 0.000000 | 0.000 | 0.0 | 1.000 | 369980.3 | 0.114 | 0.000 | 334208.3 | 837.34 |
| Ours (NoNeg) | 6 | 0.676379 | 0.676379 | 8020.264 | 8800.174 | 8857.753 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.015235, dThemeComp=+0.013255, dThemeHit=+0.113960, dThemeSat=+0.000000, dNegThemeHit=+334208.333, dMeanMs=+3662.155

## theme_negative::shrine_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 6 | 0.689349 | 0.696925 | 10601.371 | 11702.558 | 11737.140 | 0.000 | 0.000 | 0.399754 | 0.254701 | 2.333 | 0.000000 | 0.000 | 0.0 | 1.000 | 346167.0 | 0.030 | 0.000 | 312075.7 | 845.79 |
| Ours (NoNeg) | 6 | 0.676379 | 0.676379 | 7900.590 | 8700.857 | 8745.646 | 0.000 | 0.000 | 0.408152 | 0.193590 | 1.667 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=+0.012970, dThemeComp=+0.020546, dThemeHit=+0.030303, dThemeSat=+0.000000, dNegThemeHit=+312075.667, dMeanMs=+2700.781

