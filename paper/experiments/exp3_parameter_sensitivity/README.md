# Experiment 3 (Quality-Speed Balance)

This folder now implements the post-Exp1 tradeoff analysis requested by the
teacher. It reuses the full score-guided Exp1 benchmark and evaluates whether
an algorithm achieves the best balance between route quality and generation
speed.

## Scripts

- `run_exp3.py`
  - Loads Exp1 score-guided results
  - Aggregates them into task-level rows over `(algorithm, origin, depart_time, budget, score_seed)`
- `plot_exp3.py`
  - Generates quality-speed scatter plots, Pareto-front rate plots, and markdown summaries
- `generate_exp3_full_analysis.py`
  - Generates detailed JSON stats plus long-form markdown interpretation

## Main Metrics

- `stop_score_total` as route quality
- `elapsed_ms` as generation speed
- `Pareto front rate`
- `ideal-point distance`
- `Ours vs NSGA-II` tradeoff categories

## Output Paths

- Results:
  - `paper/results/exp3_parameter_sensitivity/exp3_results.json`
  - `paper/results/exp3_parameter_sensitivity/exp3_results_quick.json`
  - `paper/results/exp3_parameter_sensitivity/exp3_analysis_stats.json`
  - `paper/results/exp3_parameter_sensitivity/exp3_full_text_analysis.md`
- Figures / tables:
  - `paper/figures/exp3/exp3_quality_speed_scatter.png`
  - `paper/figures/exp3/exp3_pareto_front_rate.png`
  - `paper/figures/exp3/exp3_ideal_distance.png`
  - `paper/figures/exp3/exp3_tradeoff_summary.md`
  - `paper/figures/exp3/exp3_ours_vs_nsga_tradeoff.md`
  - `paper/figures/exp3/exp3_overview.md`

## Typical Usage

```bash
# 1) quick smoke subset
python paper/experiments/exp3_parameter_sensitivity/run_exp3.py --quick
python paper/experiments/exp3_parameter_sensitivity/plot_exp3.py --quick
python paper/experiments/exp3_parameter_sensitivity/generate_exp3_full_analysis.py \
  --results paper/results/exp3_parameter_sensitivity/exp3_results_quick.json \
  --stats-out paper/results/exp3_parameter_sensitivity/exp3_analysis_stats_quick.json \
  --md-out paper/results/exp3_parameter_sensitivity/exp3_full_text_analysis_quick.md

# 2) full analysis
python paper/experiments/exp3_parameter_sensitivity/run_exp3.py
python paper/experiments/exp3_parameter_sensitivity/plot_exp3.py
python paper/experiments/exp3_parameter_sensitivity/generate_exp3_full_analysis.py
```
