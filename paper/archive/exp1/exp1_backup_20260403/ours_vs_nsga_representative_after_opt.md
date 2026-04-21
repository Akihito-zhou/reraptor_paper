# Ours vs NSGA-II Representative Benchmark After Optimization

- Ours candidate cap short: 30
- Ours candidate cap long: 20
- Dwell minutes: 10

## Overall averages
- Ours (Full): avg_score=1195.000, avg_elapsed_ms=3530.105
- NSGA-II: avg_score=1159.875, avg_elapsed_ms=24365.814

## By budget
- budget=240
  - Ours (Full): avg_score=788.750, avg_elapsed_ms=536.625
  - NSGA-II: avg_score=763.250, avg_elapsed_ms=20098.638
- budget=480
  - Ours (Full): avg_score=1601.250, avg_elapsed_ms=6523.585
  - NSGA-II: avg_score=1556.500, avg_elapsed_ms=28632.990

## Query winners
- ('hakata', 420, 240): NSGA-II score=925.0
- ('hakata', 420, 480): NSGA-II score=1690.0
- ('hakata', 840, 240): Ours (Full) score=959.0
- ('hakata', 840, 480): Ours (Full) score=1704.0
- ('meinohama', 420, 240): Ours (Full) score=742.0
- ('meinohama', 420, 480): Ours (Full) score=1554.0
- ('meinohama', 840, 240): NSGA-II score=683.0
- ('meinohama', 840, 480): Ours (Full) score=1580.0
