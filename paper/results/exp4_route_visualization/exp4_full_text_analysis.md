# Experiment 4 Full Text Analysis

Generated at: 2026-07-27 18:30:15

## 1. Positioning

Experiment 4 is a qualitative case study for the same main task used in Experiments 1 and 3: maximize stop score under a fixed time budget, while also discussing generation time.

The purpose is not to add another benchmark, but to visually explain three concrete situations: a clear Ours win, a quality-speed balance case, and an honest counterexample.

## 2. Selected Cases

### Case A: Ours Clearly Leads in Score and Time

- Role: `success_case` / `main`
- Source: `exp1_exp3_main_task` / `score-superiority`
- Query: `fukudaimae`, `07:00`, `8h`, `score_seed=20260325`, `seed=0`
- Selection rule: Selected from the main Exp1/Exp3 results as the strongest query where Ours is both higher-scoring and faster than NSGA-II. At query level, Ours averages 1376.8 vs 893.5 stop score while reducing generation time from 37191.0 ms to 11570.7 ms.
- Intended focus: Inspect whether Ours reaches more high-value stops while still generating the route faster than the slower baseline.
- Figure panel: `C:\Users\12730\Desktop\reroute_fukuoka\paper\figures\exp4\exp4_case_a_clear_score_lead_panel.png`
- Selection evidence: `{'query_tradeoff_category': 'higher score + faster', 'query_score_gap': 483.32000000000005, 'query_speedup_ratio': 3.214230957836843, 'query_ours_stop_score': 1376.8, 'query_nsga2_stop_score': 893.4799999999999, 'query_ours_elapsed_ms': 11570.718, 'query_nsga2_elapsed_ms': 37190.96, 'task_score_seed': 20260325, 'task_score_gap': 661.6, 'task_ours_stop_score': 1455.0, 'task_nsga2_stop_score': 793.4, 'representative_seed': 0}`

| Algorithm | Stop Score | Gen Time (ms) | Score/h | Effective Time (min) | Scored Stops | Reward/Stop | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Ours | 1455.0 | 13831.1 | 186.1 | 469.0 | 21 | 69.3 | True |
| NSGA-II | 684.0 | 31749.8 | 87.1 | 471.0 | 11 | 62.2 | True |
| VNS | 508.0 | 103.2 | 64.3 | 474.0 | 10 | 50.8 | True |

Ours wins this regenerated example on both axes: stop score 1455.0 vs 684.0 for NSGA-II, and generation time 13831.1 ms vs 31749.8 ms. The route-level reason is mainly coverage: Ours collects 21 scored stops vs 11 (difference +10), while reward per scored stop differs by only +7.1. This is consistent with the aggregate coverage association, although one case is illustrative rather than causal.

### Case B: Ours Achieves the Best Quality-Speed Balance

- Role: `balance_case` / `main`
- Source: `exp1_exp3_main_task` / `quality-speed-balance`
- Query: `kashii`, `10:00`, `2h`, `score_seed=20260326`, `seed=0`
- Selection rule: Selected as the cleanest balance case where Ours is the closest-to-ideal algorithm without being the top-scoring one. Ours trails the best query-level score by only 0.05% and still ranks first by ideal-point distance on this query.
- Intended focus: Compare Ours against a slower high-quality baseline and a faster lower-quality heuristic to show why the ideal-point ranking favors Ours.
- Figure panel: `C:\Users\12730\Desktop\reroute_fukuoka\paper\figures\exp4\exp4_case_b_quality_speed_balance_panel.png`
- Selection evidence: `{'query_best_score_gap_ratio': 0.0004972650422675004, 'query_balance_margin': 0.2567284697470743, 'query_ours_stop_score': 402.0, 'query_ours_ideal_distance': 0.004414715698733823, 'query_best_score': 402.2, 'query_best_score_algorithm': 'Pure RAPTOR', 'query_best_score_elapsed_ms': 13956.670000000002, 'query_fast_lower_quality_algorithm': 'Greedy (L=3)', 'query_fast_lower_quality_score': 249.8, 'query_fast_lower_quality_elapsed_ms': 0.682, 'task_score_seed': 20260326, 'task_ours_stop_score': 375.0, 'task_best_score': 376.0, 'task_nsga2_stop_score': 356.0, 'task_nsga2_elapsed_ms': 24221.841999999997, 'representative_seed': 0}`

| Algorithm | Stop Score | Gen Time (ms) | Score/h | Effective Time (min) | Scored Stops | Reward/Stop | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Ours | 375.0 | 115.8 | 192.3 | 117.0 | 6 | 62.5 | True |
| Pure RAPTOR | 376.0 | 10918.7 | 201.4 | 112.0 | 6 | 62.7 | True |
| Greedy | 263.0 | 0.8 | 131.5 | 120.0 | 4 | 65.8 | True |

This is the intended balance example. Ours retains 99.73% of the score achieved by Pure RAPTOR (375.0 vs 376.0) while running 94.3 times faster (115.8 vs 10918.7 ms). Relative to the fastest lower-quality comparator, Greedy, Ours gains 112.0 points at a higher runtime. Its ideal-point rank follows from occupying the middle of these two extremes, not from being best on either raw axis.

### Case C: A Counterexample Where Ours Does Not Win on Score

- Role: `contrast_case` / `appendix`
- Source: `exp1_exp3_main_task` / `contrastive-counterexample`
- Query: `ohori-koen`, `14:00`, `8h`, `score_seed=20260323`, `seed=0`
- Selection rule: Selected as an honest counterexample where NSGA-II reaches a meaningfully higher stop score, so Ours should not be described as universally best. At query level, Ours is still faster (12764.1 ms vs 47864.3 ms), but the score gap remains 276.4.
- Intended focus: Use this case to show the limitation clearly: Ours can be faster yet still miss the highest-scoring route.
- Figure panel: `C:\Users\12730\Desktop\reroute_fukuoka\paper\figures\exp4\exp4_case_c_contrastive_counterexample_panel.png`
- Selection evidence: `{'query_tradeoff_category': 'lower score + faster', 'query_score_gap': -276.44000000000005, 'query_score_ratio': 0.8159569651940027, 'query_ours_stop_score': 1225.6, 'query_nsga2_stop_score': 1502.04, 'query_ours_elapsed_ms': 12764.086000000001, 'query_nsga2_elapsed_ms': 47864.3436, 'task_score_seed': 20260323, 'task_score_gap': -210.4000000000001, 'representative_seed': 0}`

| Algorithm | Stop Score | Gen Time (ms) | Score/h | Effective Time (min) | Scored Stops | Reward/Stop | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Ours | 1479.0 | 4113.0 | 185.3 | 479.0 | 21 | 70.4 | True |
| NSGA-II | 1680.0 | 50922.9 | 210.9 | 478.0 | 20 | 84.0 | True |
| VNS | 1482.0 | 829.1 | 185.2 | 480.0 | 19 | 78.0 | True |

This case is an explicit counterexample. NSGA-II achieves the higher stop score (1680.0 vs 1479.0) but takes 50922.9 ms vs 4113.0 ms. It collects 1 fewer scored stops than Ours and has a reward-per-stop difference of +13.6; here the higher reward density outweighs the stop-count difference and explains the observed score reversal. The result shows that width-controlled search can miss a better long-budget itinerary and rules out a universal-win claim.

## 3. Usage in the Paper

The main text can use the success case and the balance case together. The counterexample should be kept as an appendix or limitation figure so the paper explicitly avoids claiming that Ours wins every query.

The recommended narrative is: Ours provides the best overall balance between route quality and generation time, not universal dominance on every instance.
