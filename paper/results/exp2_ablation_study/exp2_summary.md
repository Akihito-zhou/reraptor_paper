# Experiment 2 Summary

- Primary metric: `Stop Score`
- Aggregation unit: `(origin, depart_time, budget, score_seed)`

## Key Findings

- `Ours (Full)` is the best overall configuration in this run: `StopScore 999.27`, `Runtime 4668.15 ms`, `Labels 115437`, and zero cap hits.
- `Ours (NoNeg)` is nearly tied on score (`996.10`, gap `+3.17`), but is slightly slower and larger, which matches the claim that negative pruning is not the main speedup layer.
- Removing dominance pruning is clearly expensive overall: `Ours (NoDom)` is `2.91x` slower, uses `3.03x` labels, and changes score by `-27.37`.
- Removing beam control materially increases search cost: `Ours (NoBeam)` is `9.53x` slower, uses `12.89x` labels, and changes score by `-87.23`.
- `Ours (NoBeam-NoDom)` isolates the joint removal of the two main search-space control layers: relative to `Full`, it is `13.22x` slower, uses `24.36x` labels, and changes score by `-685.48`. The further change from `NoBeam-NoDom` to `NoBeam-NoDom-NoNeg` is `-24.42` score and `-40764.59 ms`, which helps separate the role of `Negative` from the beam/dominance pair.
- In `4h`, `NoBeam` scores higher than `Full` (`803.80` vs `737.04`), but needs `35.10x` runtime and `18.89%` cap hits.
- In `8h`, `Full` dominates `NoBeam`: `1261.50` vs `1020.28` stop score, `8564.82` vs `61897.36` ms runtime, with `NoBeam` hitting the cap on `100.00%` of tasks.

## Overall Table

| Algorithm                 |   StopScore |   RuntimeMs |     Labels |   GapToBestPct |   SuccessPct |   CapHitPct |
|:--------------------------|------------:|------------:|-----------:|---------------:|-------------:|------------:|
| Ours (Full)               |      999.27 |     4668.15 |  115436.61 |           0.00 |        97.78 |        0.00 |
| Ours (NoNeg)              |      996.10 |     4865.37 |  119326.83 |           0.32 |        97.22 |        0.00 |
| Ours (NoDom)              |      971.91 |    13589.45 |  349945.64 |           2.74 |        97.78 |        0.00 |
| Ours (NoBeam)             |      912.04 |    44486.93 | 1487639.84 |           8.73 |        97.78 |       59.44 |
| Ours (NoBeam-NoDom)       |      313.79 |    61694.58 | 2811579.67 |          68.60 |       100.00 |      100.00 |
| Ours (NoDom-NoNeg)        |      973.06 |    12984.17 |  350980.81 |           2.62 |        97.78 |        0.00 |
| Ours (NoBeam-NoNeg)       |      911.56 |    44700.47 | 1509040.26 |           8.78 |        97.78 |       60.00 |
| Ours (NoBeam-NoDom-NoNeg) |      289.37 |    20929.99 | 1000000.00 |          71.04 |       100.00 |      100.00 |

## By Budget

| Budget   | Algorithm                 |   StopScore |   RuntimeMs | Labels   |   SuccessPct |   CapHitPct |
|:---------|:--------------------------|------------:|------------:|:---------|-------------:|------------:|
| 4h       | Ours (Full)               |      737.04 |      771.47 | 24.4K    |        97.78 |        0    |
| 4h       | Ours (NoNeg)              |      729.81 |      806.95 | 25.1K    |        96.67 |        0    |
| 4h       | Ours (NoDom)              |      737.92 |     5282.16 | 152.9K   |        97.78 |        0    |
| 4h       | Ours (NoBeam)             |      803.8  |    27076.5  | 847.1K   |        95.56 |       18.89 |
| 4h       | Ours (NoBeam-NoDom)       |      342.6  |    61584.7  | 2.74M    |       100    |      100    |
| 4h       | Ours (NoDom-NoNeg)        |      740.04 |     5037.39 | 154.0K   |        97.78 |        0    |
| 4h       | Ours (NoBeam-NoNeg)       |      802.4  |    27486.1  | 865.1K   |        95.56 |       20    |
| 4h       | Ours (NoBeam-NoDom-NoNeg) |      304.18 |    21576    | 1.00M    |       100    |      100    |
| 8h       | Ours (Full)               |     1261.5  |     8564.82 | 206.5K   |        97.78 |        0    |
| 8h       | Ours (NoNeg)              |     1262.39 |     8923.78 | 213.5K   |        97.78 |        0    |
| 8h       | Ours (NoDom)              |     1205.89 |    21896.7  | 546.9K   |        97.78 |        0    |
| 8h       | Ours (NoBeam)             |     1020.28 |    61897.4  | 2.13M    |       100    |      100    |
| 8h       | Ours (NoBeam-NoDom)       |      284.99 |    61804.5  | 2.88M    |       100    |      100    |
| 8h       | Ours (NoDom-NoNeg)        |     1206.07 |    20930.9  | 547.9K   |        97.78 |        0    |
| 8h       | Ours (NoBeam-NoNeg)       |     1020.72 |    61914.8  | 2.15M    |       100    |      100    |
| 8h       | Ours (NoBeam-NoDom-NoNeg) |      274.57 |    20284    | 1.00M    |       100    |      100    |

## Interpretation

- `Beam` and `dominance` should be presented as co-core efficiency layers that jointly control search-space growth.
- `Negative pruning` should be presented as a light constraint / stability layer, not as the main source of score gain.
- The fairest statement for Experiment 2 is therefore: `Ours (Full)` has the best combined profile across quality, runtime, and search size.
