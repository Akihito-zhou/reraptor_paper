# Exp4 Case Summary

- Main cases panel: `paper/figures/exp4/exp4_main_cases.png`
- Appendix panel: `paper/figures/exp4/exp4_appendix_cases.png`

## Case A: Ours Clearly Leads in Score and Time

- Case id: `case_a_clear_score_lead`
- Role: `success_case` / `main`
- Query: `fukudaimae`, `07:00`, `8h`, `score_seed=20260325`, `seed=0`
- Focus: Inspect whether Ours reaches more high-value stops while still generating the route faster than the slower baseline.
- Selection: Selected from the main Exp1/Exp3 results as the strongest query where Ours is both higher-scoring and faster than NSGA-II. At query level, Ours averages 1376.8 vs 893.5 stop score while reducing generation time from 37191.0 ms to 11570.7 ms.
- Panel: `paper/figures/exp4/exp4_case_a_clear_score_lead_panel.png`

| Algorithm | Stop Score | Gen ms | Score/h | Effective Time | Scored Stops | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Ours | 1455.0 | 13831.1 | 186.1 | 469.0 | 21 | True |
| NSGA-II | 684.0 | 31749.8 | 87.1 | 471.0 | 11 | True |
| VNS | 508.0 | 103.2 | 64.3 | 474.0 | 10 | True |

## Case B: Ours Achieves the Best Quality-Speed Balance

- Case id: `case_b_quality_speed_balance`
- Role: `balance_case` / `main`
- Query: `kashii`, `10:00`, `2h`, `score_seed=20260326`, `seed=0`
- Focus: Compare Ours against a slower high-quality baseline and a faster lower-quality heuristic to show why the ideal-point ranking favors Ours.
- Selection: Selected as the cleanest balance case where Ours is the closest-to-ideal algorithm without being the top-scoring one. Ours trails the best query-level score by only 0.05% and still ranks first by ideal-point distance on this query.
- Panel: `paper/figures/exp4/exp4_case_b_quality_speed_balance_panel.png`

| Algorithm | Stop Score | Gen ms | Score/h | Effective Time | Scored Stops | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Ours | 375.0 | 115.8 | 192.3 | 117.0 | 6 | True |
| Pure RAPTOR | 376.0 | 10918.7 | 201.4 | 112.0 | 6 | True |
| Greedy | 263.0 | 0.8 | 131.5 | 120.0 | 4 | True |

## Case C: A Counterexample Where Ours Does Not Win on Score

- Case id: `case_c_contrastive_counterexample`
- Role: `contrast_case` / `appendix`
- Query: `ohori-koen`, `14:00`, `8h`, `score_seed=20260323`, `seed=0`
- Focus: Use this case to show the limitation clearly: Ours can be faster yet still miss the highest-scoring route.
- Selection: Selected as an honest counterexample where NSGA-II reaches a meaningfully higher stop score, so Ours should not be described as universally best. At query level, Ours is still faster (12764.1 ms vs 47864.3 ms), but the score gap remains 276.4.
- Panel: `paper/figures/exp4/exp4_case_c_contrastive_counterexample_panel.png`

| Algorithm | Stop Score | Gen ms | Score/h | Effective Time | Scored Stops | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Ours | 1479.0 | 4113.0 | 185.3 | 479.0 | 21 | True |
| NSGA-II | 1680.0 | 50922.9 | 210.9 | 478.0 | 20 | True |
| VNS | 1482.0 | 829.1 | 185.2 | 480.0 | 19 | True |

