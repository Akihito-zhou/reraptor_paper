# Experiment 4 Full Text Analysis

Generated at: 2026-04-14 14:56:25

## 1. Positioning

Experiment 4 is a qualitative case study for the same main task used in Experiments 1 and 3: maximize stop score under a fixed time budget, while also discussing generation time.

The purpose is not to add another benchmark, but to visually explain three concrete situations: a clear Ours win, a quality-speed balance case, and an honest counterexample.

## 2. Selected Cases

### Case A: Ours Clearly Leads in Score and Time

- Role: `success_case` / `main`
- Source: `exp1_exp3_main_task` / `score-superiority`
- Query: `fukudaimae`, `07:00`, `8h`, `score_seed=20260325`, `seed=0`
- Selection rule: Selected from the main Exp1/Exp3 results as the strongest query where Ours is both higher-scoring and faster than NSGA-II. At query level, Ours averages 1390.0 vs 758.3 stop score while reducing generation time from 24831.7 ms to 16358.5 ms.
- Intended focus: Inspect whether Ours reaches more high-value stops while still generating the route faster than the slower baseline.
- Figure panel: `/Users/aki/Desktop/reroute_fukuoka/paper/figures/exp4/exp4_case_a_clear_score_lead_panel.png`
- Selection evidence: `{'query_tradeoff_category': 'higher score + faster', 'query_score_gap': 631.72, 'query_speedup_ratio': 1.5179637246222677, 'query_ours_stop_score': 1390.0, 'query_nsga2_stop_score': 758.28, 'query_ours_elapsed_ms': 16358.534, 'query_nsga2_elapsed_ms': 24831.661200000002, 'task_score_seed': 20260325, 'task_score_gap': 645.0, 'task_ours_stop_score': 1459.0, 'task_nsga2_stop_score': 814.0, 'representative_seed': 0}`

| Algorithm | Stop Score | Gen Time (ms) | Score/h | Effective Time (min) | Scored Stops | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Ours | 1459.0 | 9091.1 | 185.5 | 472.0 | 22 | True |
| NSGA-II | 854.0 | 14129.0 | 108.1 | 474.0 | 13 | True |
| VNS | 508.0 | 37.0 | 68.5 | 445.0 | 10 | True |

Ours wins this case on both axes in the regenerated example: stop score 1459.0 vs 854.0, generation time 9091.1 ms vs 14129.0 ms. Inspect whether Ours reaches more high-value stops while still generating the route faster than the slower baseline.

### Case B: Ours Achieves the Best Quality-Speed Balance

- Role: `balance_case` / `main`
- Source: `exp1_exp3_main_task` / `quality-speed-balance`
- Query: `tenjin`, `07:00`, `8h`, `score_seed=20260325`, `seed=0`
- Selection rule: Selected as the cleanest balance case where Ours is the closest-to-ideal algorithm without being the top-scoring one. Ours trails the best query-level score by only 0.53% and still ranks first by ideal-point distance on this query.
- Intended focus: Compare Ours against a slower high-quality baseline and a faster lower-quality heuristic to show why the ideal-point ranking favors Ours.
- Figure panel: `/Users/aki/Desktop/reroute_fukuoka/paper/figures/exp4/exp4_case_b_quality_speed_balance_panel.png`
- Selection evidence: `{'query_best_score_gap_ratio': 0.005305757830053273, 'query_balance_margin': 0.06265273325247298, 'query_ours_stop_score': 1469.8, 'query_ours_ideal_distance': 0.20232695697258282, 'query_best_score': 1477.6399999999999, 'task_score_seed': 20260325, 'task_ours_stop_score': 1276.0, 'task_best_score': 1507.2, 'task_nsga2_stop_score': 1507.2, 'task_nsga2_elapsed_ms': 51562.022, 'representative_seed': 0}`

| Algorithm | Stop Score | Gen Time (ms) | Score/h | Effective Time (min) | Scored Stops | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Ours | 1276.0 | 4473.7 | 164.6 | 465.0 | 18 | True |
| NSGA-II | 1590.0 | 18956.2 | 200.8 | 475.0 | 22 | True |
| SA | 1506.0 | 156.4 | 192.7 | 469.0 | 20 | True |

This is the intended balance example: Ours is not required to be the absolute fastest or the absolute highest-scoring route in every comparison, but it stays close to the top score while avoiding the much larger runtime of NSGA-II (4473.7 ms vs 18956.2 ms). Compare Ours against a slower high-quality baseline and a faster lower-quality heuristic to show why the ideal-point ranking favors Ours.

### Case C: A Counterexample Where Ours Does Not Win on Score

- Role: `contrast_case` / `appendix`
- Source: `exp1_exp3_main_task` / `contrastive-counterexample`
- Query: `yakuin`, `14:00`, `8h`, `score_seed=20260327`, `seed=0`
- Selection rule: Selected as an honest counterexample where NSGA-II reaches a meaningfully higher stop score, so Ours should not be described as universally best. At query level, Ours is still faster (8211.3 ms vs 39120.9 ms), but the score gap remains 244.2.
- Intended focus: Use this case to show the limitation clearly: Ours can be faster yet still miss the highest-scoring route.
- Figure panel: `/Users/aki/Desktop/reroute_fukuoka/paper/figures/exp4/exp4_case_c_contrastive_counterexample_panel.png`
- Selection evidence: `{'query_tradeoff_category': 'lower score + faster', 'query_score_gap': -244.16000000000008, 'query_score_ratio': 0.8370049934577691, 'query_ours_stop_score': 1253.8, 'query_nsga2_stop_score': 1497.96, 'query_ours_elapsed_ms': 8211.26, 'query_nsga2_elapsed_ms': 39120.93519999999, 'task_score_seed': 20260327, 'task_score_gap': -182.20000000000005, 'representative_seed': 0}`

| Algorithm | Stop Score | Gen Time (ms) | Score/h | Effective Time (min) | Scored Stops | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Ours | 1358.0 | 2730.8 | 187.3 | 435.0 | 18 | True |
| NSGA-II | 1556.0 | 20367.1 | 207.9 | 449.0 | 19 | True |
| VNS | 1461.0 | 192.6 | 186.5 | 470.0 | 19 | True |

This case should be presented as a counterexample. NSGA-II achieves the higher stop score (1556.0 vs 1358.0), so the paper should not claim universal superiority for Ours even though Ours is faster (2730.8 ms vs 20367.1 ms). Use this case to show the limitation clearly: Ours can be faster yet still miss the highest-scoring route.

## 3. Usage in the Paper

The main text can use the success case and the balance case together. The counterexample should be kept as an appendix or limitation figure so the paper explicitly avoids claiming that Ours wins every query.

The recommended narrative is: Ours provides the best overall balance between route quality and generation time, not universal dominance on every instance.
