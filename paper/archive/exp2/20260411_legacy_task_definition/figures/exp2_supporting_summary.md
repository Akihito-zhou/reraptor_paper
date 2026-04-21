# Exp2 Supporting Experiments Summary

## beam_width_sweep_stress

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Beam10) | 36 | 0.955046 | 0.955046 | 11935.153 | 20293.157 | 20300.432 | 0.083 | 0.083 | 0.378043 | 0.157879 | 1.750 | 0.000000 | 0.417 | 5.2 | 1.000 | 72020.7 | 0.000 | 0.000 | 0.0 | 0.00 |
| Ours (Beam20) | 36 | 0.955046 | 0.955046 | 11924.163 | 20307.506 | 20341.165 | 0.083 | 0.083 | 0.378043 | 0.157879 | 1.750 | 0.000000 | 0.000 | 0.0 | 1.000 | 72219.4 | 0.000 | 0.000 | 0.0 | 0.00 |
| Ours (Beam5) | 36 | 0.956411 | 0.956411 | 11595.780 | 20332.360 | 20337.109 | 0.083 | 0.083 | 0.381919 | 0.152918 | 1.833 | 0.000000 | 1.000 | 1840.8 | 1.000 | 61954.1 | 0.000 | 0.000 | 0.0 | 0.00 |
| Ours (Beam50) | 36 | 0.955046 | 0.955046 | 11951.011 | 20310.039 | 20319.478 | 0.083 | 0.083 | 0.378043 | 0.157879 | 1.750 | 0.000000 | 0.000 | 0.0 | 1.000 | 72560.9 | 0.000 | 0.000 | 0.0 | 0.00 |
| Ours (NoBeam) | 36 | 0.955046 | 0.955046 | 12006.848 | 20284.972 | 20295.854 | 0.083 | 0.083 | 0.378043 | 0.157879 | 1.750 | 0.000000 | 0.000 | 0.0 | 1.000 | 71548.6 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- (no predefined pairwise delta rule)

## theme_negative::coastal_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 48 | 0.796500 | 0.839561 | 10564.116 | 20277.331 | 20285.682 | 0.125 | 0.125 | 0.405893 | 0.116057 | 1.354 | 0.022222 | 0.000 | 0.0 | 1.000 | 312385.9 | 0.172 | 0.688 | 269968.0 | 728.44 |
| Ours (NoNeg) | 48 | 0.799655 | 0.833167 | 8098.728 | 15626.934 | 15913.946 | 0.000 | 0.000 | 0.393856 | 0.119841 | 1.250 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.134 | 0.375 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.003155, dThemeComp=+0.006394, dThemeHit=+0.038196, dThemeSat=+0.312500, dNegThemeHit=+269968.042, dMeanMs=+2465.388

## theme_negative::east_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 48 | 0.756786 | 0.815932 | 11310.398 | 20272.767 | 20279.685 | 0.125 | 0.125 | 0.417878 | 0.109949 | 1.333 | 0.036111 | 0.000 | 0.0 | 1.000 | 353800.2 | 0.237 | 0.562 | 309239.9 | 790.64 |
| Ours (NoNeg) | 48 | 0.799655 | 0.811556 | 8071.513 | 15724.903 | 15773.682 | 0.000 | 0.000 | 0.393856 | 0.119841 | 1.250 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.048 | 0.062 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.042869, dThemeComp=+0.004376, dThemeHit=+0.188979, dThemeSat=+0.500000, dNegThemeHit=+309239.896, dMeanMs=+3238.885

## theme_negative::mountain_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 48 | 0.784219 | 0.793133 | 11292.630 | 20285.301 | 20428.979 | 0.125 | 0.125 | 0.389579 | 0.113606 | 1.250 | 0.000000 | 0.000 | 0.0 | 1.000 | 376164.5 | 0.036 | 0.125 | 331432.9 | 844.55 |
| Ours (NoNeg) | 48 | 0.799655 | 0.799655 | 8049.927 | 15613.553 | 15752.823 | 0.000 | 0.000 | 0.393856 | 0.119841 | 1.250 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.000 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.015436, dThemeComp=-0.006522, dThemeHit=+0.035657, dThemeSat=+0.125000, dNegThemeHit=+331432.854, dMeanMs=+3242.703

## theme_negative::north_axis

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 48 | 0.799579 | 0.899347 | 11695.611 | 20271.347 | 20547.677 | 0.125 | 0.125 | 0.400750 | 0.113444 | 1.250 | 0.000000 | 0.000 | 0.0 | 1.000 | 335990.2 | 0.399 | 1.000 | 291728.0 | 728.23 |
| Ours (NoNeg) | 48 | 0.799655 | 0.888238 | 8100.992 | 15684.450 | 15831.319 | 0.000 | 0.000 | 0.393856 | 0.119841 | 1.250 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.354 | 0.938 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.000076, dThemeComp=+0.011109, dThemeHit=+0.044743, dThemeSat=+0.062500, dNegThemeHit=+291728.021, dMeanMs=+3594.619

## theme_negative::north_coastal_like

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 48 | 0.804319 | 0.991561 | 8892.988 | 18310.686 | 19000.951 | 0.000 | 0.000 | 0.401355 | 0.116998 | 1.250 | 0.000000 | 0.000 | 0.0 | 1.000 | 58994.6 | 0.749 | 1.000 | 18196.6 | 57.27 |
| Ours (NoNeg) | 48 | 0.799655 | 0.981028 | 8162.363 | 15848.339 | 16034.873 | 0.000 | 0.000 | 0.393856 | 0.119841 | 1.250 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.725 | 1.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=+0.004664, dThemeComp=+0.010533, dThemeHit=+0.023478, dThemeSat=+0.000000, dNegThemeHit=+18196.625, dMeanMs=+730.625

## theme_negative::outer_ring

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 48 | 0.808123 | 0.899783 | 9559.140 | 19298.701 | 19913.305 | 0.000 | 0.000 | 0.393612 | 0.107383 | 1.188 | 0.000000 | 0.000 | 0.0 | 1.000 | 265864.2 | 0.367 | 1.000 | 223941.8 | 654.24 |
| Ours (NoNeg) | 48 | 0.799655 | 0.889372 | 7945.830 | 15357.300 | 15459.688 | 0.000 | 0.000 | 0.393856 | 0.119841 | 1.250 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.359 | 1.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=+0.008468, dThemeComp=+0.010411, dThemeHit=+0.007773, dThemeSat=+0.000000, dNegThemeHit=+223941.750, dMeanMs=+1613.310

## theme_negative::park_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 48 | 0.781036 | 0.801036 | 11403.374 | 20283.686 | 20487.978 | 0.125 | 0.125 | 0.404351 | 0.096598 | 1.104 | 0.022222 | 0.000 | 0.0 | 1.000 | 387282.7 | 0.080 | 0.125 | 342338.8 | 858.72 |
| Ours (NoNeg) | 48 | 0.799655 | 0.801218 | 7941.803 | 15269.951 | 15417.881 | 0.000 | 0.000 | 0.393856 | 0.119841 | 1.250 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.006 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.018619, dThemeComp=-0.000182, dThemeHit=+0.073748, dThemeSat=+0.125000, dNegThemeHit=+342338.792, dMeanMs=+3461.571

## theme_negative::shrine_keyword

| Algorithm | Runs | Composite | ThemeComp | Mean ms | P95 ms | P99 ms | CapHit | Timeout | WaitRatio | RevisitRatio | Backtrack | Diversity | BeamTrimRun | BeamTrimLbl | NegHitRun | NegHitMean | ThemeHit | ThemeSat | NegThemeHit | NegThemePerK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ours (Full) | 48 | 0.794043 | 0.808161 | 11172.468 | 20284.363 | 20298.391 | 0.125 | 0.125 | 0.387000 | 0.114739 | 1.312 | 0.000000 | 0.000 | 0.0 | 1.000 | 381051.6 | 0.056 | 0.000 | 335804.1 | 864.70 |
| Ours (NoNeg) | 48 | 0.799655 | 0.801218 | 8009.826 | 15597.143 | 16312.296 | 0.000 | 0.000 | 0.393856 | 0.119841 | 1.250 | 0.000000 | 0.000 | 0.0 | 0.000 | 0.0 | 0.006 | 0.000 | 0.0 | 0.00 |

Key deltas:
- Full - NoNeg: dComposite=-0.005612, dThemeComp=+0.006943, dThemeHit=+0.050222, dThemeSat=+0.000000, dNegThemeHit=+335804.062, dMeanMs=+3162.642

