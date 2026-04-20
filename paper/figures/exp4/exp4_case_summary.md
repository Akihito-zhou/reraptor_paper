# Exp4 Case Summary

- Main cases panel: `paper/figures/exp4/exp4_main_cases.png`
- Appendix panel: `paper/figures/exp4/exp4_appendix_cases.png`

## Case A: Ours Clearly Leads in Score and Time

- Case id: `case_a_clear_score_lead`
- Role: `success_case` / `main`
- Query: `fukudaimae`, `07:00`, `8h`, `score_seed=20260325`, `seed=0`
- Focus: Inspect whether Ours reaches more high-value stops while still generating the route faster than the slower baseline.
- Selection: Selected from the main Exp1/Exp3 results as the strongest query where Ours is both higher-scoring and faster than NSGA-II. At query level, Ours averages 1390.0 vs 758.3 stop score while reducing generation time from 24831.7 ms to 16358.5 ms.
- Panel: `paper/figures/exp4/exp4_case_a_clear_score_lead_panel.png`

| Algorithm | Stop Score | Gen ms | Score/h | Effective Time | Scored Stops | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Ours | 1459.0 | 9091.1 | 185.5 | 472.0 | 22 | True |
| NSGA-II | 854.0 | 14129.0 | 108.1 | 474.0 | 13 | True |
| VNS | 508.0 | 37.0 | 68.5 | 445.0 | 10 | True |

## Case B: Ours Achieves the Best Quality-Speed Balance

- Case id: `case_b_quality_speed_balance`
- Role: `balance_case` / `main`
- Query: `tenjin`, `07:00`, `8h`, `score_seed=20260325`, `seed=0`
- Focus: Compare Ours against a slower high-quality baseline and a faster lower-quality heuristic to show why the ideal-point ranking favors Ours.
- Selection: Selected as the cleanest balance case where Ours is the closest-to-ideal algorithm without being the top-scoring one. Ours trails the best query-level score by only 0.53% and still ranks first by ideal-point distance on this query.
- Panel: `paper/figures/exp4/exp4_case_b_quality_speed_balance_panel.png`

| Algorithm | Stop Score | Gen ms | Score/h | Effective Time | Scored Stops | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Ours | 1276.0 | 4473.7 | 164.6 | 465.0 | 18 | True |
| NSGA-II | 1590.0 | 18956.2 | 200.8 | 475.0 | 22 | True |
| SA | 1506.0 | 156.4 | 192.7 | 469.0 | 20 | True |

## Case C: A Counterexample Where Ours Does Not Win on Score

- Case id: `case_c_contrastive_counterexample`
- Role: `contrast_case` / `appendix`
- Query: `yakuin`, `14:00`, `8h`, `score_seed=20260327`, `seed=0`
- Focus: Use this case to show the limitation clearly: Ours can be faster yet still miss the highest-scoring route.
- Selection: Selected as an honest counterexample where NSGA-II reaches a meaningfully higher stop score, so Ours should not be described as universally best. At query level, Ours is still faster (8211.3 ms vs 39120.9 ms), but the score gap remains 244.2.
- Panel: `paper/figures/exp4/exp4_case_c_contrastive_counterexample_panel.png`

| Algorithm | Stop Score | Gen ms | Score/h | Effective Time | Scored Stops | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Ours | 1358.0 | 2730.8 | 187.3 | 435.0 | 18 | True |
| NSGA-II | 1556.0 | 20367.1 | 207.9 | 449.0 | 19 | True |
| VNS | 1461.0 | 192.6 | 186.5 | 470.0 | 19 | True |

