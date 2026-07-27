# ReRAPTOR Supplementary Materials

This page is the index for the additional tables, source data files, and
supplementary images announced in the manuscript.

## Additional Tables

- Experiment 1 overall summary:
  [`results/exp1_algorithm_comparison/exp1_score_guided_multiseed_summary_canonical_20260727.md`](results/exp1_algorithm_comparison/exp1_score_guided_multiseed_summary_canonical_20260727.md)
- Stop Score interpretation tables:
  [`score_interpretability_summary_20260723.csv`](results/exp1_algorithm_comparison/score_interpretability_summary_20260723.csv) and
  [`score_interpretability_task_level_20260723.csv`](results/exp1_algorithm_comparison/score_interpretability_task_level_20260723.csv)
- Underperformance tables by origin, budget, and failure mode:
  [`results/exp1_algorithm_comparison/`](results/exp1_algorithm_comparison/)
- Experiment 2 ablation tables:
  [`results/exp2_ablation_study/`](results/exp2_ablation_study/)
- Experiment 3 sensitivity tables:
  [`results/exp3_parameter_sensitivity/`](results/exp3_parameter_sensitivity/)
- Experiment 4 route-case comparison:
  [`results/exp4_route_visualization/exp4_full_text_analysis.md`](results/exp4_route_visualization/exp4_full_text_analysis.md)

## Source Data Files

The source data supporting the reported tables and figures are the frozen,
query-level or configuration-level JSON/CSV outputs:

- Experiment 1, ten-algorithm comparison:
  [`exp1_results_canonical_final_10alg_manuscript_20260723.json`](results/exp1_algorithm_comparison/exp1_results_canonical_final_10alg_manuscript_20260723.json)
- Experiment 2, eight-configuration ablation:
  [`exp2_results_canonical_final_8config_20260725.json`](results/exp2_ablation_study/exp2_results_canonical_final_8config_20260725.json)
- Experiment 3, 18 one-at-a-time and four interaction configurations:
  [`results/exp3_parameter_sensitivity/`](results/exp3_parameter_sensitivity/)
- Experiment 4, selected cases and route traces:
  [`results/exp4_route_visualization/`](results/exp4_route_visualization/)

The Python pipelines that generated and analyzed these files are under
[`experiments/`](experiments/). The R scripts used to regenerate the manuscript
figures are under
[`experiments/r_visualization/`](experiments/r_visualization/).

## Supplementary Images

- Experiment 1 budget slices and reliability heatmap:
  [`figures/exp1/`](figures/exp1/)
- Experiment 2 ablation and mechanism plots:
  [`figures/exp2/`](figures/exp2/)
- Experiment 3 quality--speed and sensitivity plots:
  [`figures/exp3/`](figures/exp3/)
- Experiment 4 route maps and case panels:
  [`figures/exp4/`](figures/exp4/)

Scientific plots are released as vector PDF files, with PNG counterparts for
browser preview where appropriate.

## Data-Availability Boundary

The released JSON and CSV files are the source data behind the paper's reported
results. Raw Fukuoka timetable files obtained through Ekispert are not
redistributed because they are proprietary. Their expected local layout is
documented in [`../apps/api/data/README.md`](../apps/api/data/README.md).
