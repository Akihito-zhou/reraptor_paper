# Experiment 3 (Balance and Hyperparameter Sensitivity)

This folder contains two linked analyses:

1. the post-Exp1 quality-speed balance analysis; and
2. the canonical Stop Score hyperparameter sensitivity analysis.

The sensitivity runner changes the actual Stop Score search coefficients,
candidate cap, and bucket beam width. It does not reuse the older
geometry-objective weight experiment.

## Scripts

- `run_exp3.py`
  - Loads Exp1 score-guided results
  - Aggregates them into task-level rows over `(algorithm, origin, depart_time, budget, score_seed)`
- `plot_exp3.py`
  - Generates quality-speed scatter plots, Pareto-front rate plots, and markdown summaries
- `generate_exp3_full_analysis.py`
  - Generates detailed JSON stats plus long-form markdown interpretation
- `sensitivity_protocol.py`
  - Freezes the one-at-a-time (OAT) grid and the four new corner cells needed
    to complete the 3-by-3 beam-width/candidate-cap interaction panel
- `run_sensitivity.py`
  - Runs deterministic Stop Score sensitivity configurations with
    checkpoint/resume and complete parameter metadata
- `run_sensitivity_queue.ps1`
  - Runs all 18 OAT configurations and four new interaction corner cells
    serially in the Python 3.10 `research` environment
- `../common/merge_sensitivity_shards.py`
  - Strictly validates the frozen configuration snapshots, shared metadata,
    exact panel task grids, source hashes, and global task-key uniqueness
    before producing separate canonical OAT and interaction payloads
- `analyze_sensitivity.py`
  - Produces paired OAT effects, 20,000-rep crossed block-bootstrap intervals,
    budget slices, and the confirmatory 3-by-3 interaction summary
- `../r_visualization/plot_exp3_sensitivity.R`
  - Renders the manuscript sensitivity figure as embedded-font vector PDF 1.5
    and 360-dpi PNG

## Main Metrics

- `stop_score_total` as route quality
- `elapsed_ms` as generation speed
- `Pareto front rate`
- `ideal-point distance`
- `Ours vs NSGA-II` tradeoff categories
- paired Stop Score change versus the dedicated sensitivity default
- runtime and explored-label multipliers
- candidate-trim and bucket-beam activation
- timeout/label-cap incidence

## Frozen sensitivity grid

- Beam width: 10, 25, **50**, 100, 200
- Candidate-cap pair: (15,10), **(30,20)**, (60,40), uncapped
- Reward coefficient: 5,000, **10,000**, 20,000
- Score-per-hour coefficient: 0, 2.5, **5**, 10
- Effective-time coefficient: 0, 0.05, **0.1**, 0.2
- Negative-penalty scale: 0.5, **1**, 2

The default is run once as a dedicated 600-task sensitivity shard. The four
new interaction corner cells use Hakata, Fukudaimae, and Noke; all three
departure times; all four budgets; and reward seeds 20260323 and 20260325.
The five remaining cells of the 3-by-3 interaction panel are reused from the
OAT/default results after filtering to the same task subset.

## Output Paths

- Results:
  - `paper/results/exp3_parameter_sensitivity/exp3_results_canonical_exp1_final_10alg_20260727.json`
  - `paper/results/exp3_parameter_sensitivity/sensitivity_results_canonical_oat_18config_20260727.json`
  - `paper/results/exp3_parameter_sensitivity/sensitivity_results_canonical_interaction_4corner_20260727.json`
  - `paper/results/exp3_parameter_sensitivity/sensitivity_canonical_analysis_20260727.json`
  - `paper/results/exp3_parameter_sensitivity/sensitivity_canonical_*.csv`
- Figures / tables:
  - `paper/figures/exp3/exp3_quality_speed_scatter.png`
  - `paper/figures/exp3/exp3_ideal_distance.png`
  - `paper/figures/exp3/exp3_tradeoff_summary.md`
  - `paper/figures/exp3/exp3_ours_vs_nsga_tradeoff.md`
  - `paper/figures/exp3/exp3_overview.md`
  - `paper/figures/exp3/exp3_hyperparameter_sensitivity.pdf`
  - `paper/figures/exp3/exp3_hyperparameter_sensitivity.png`

## Typical Usage

```bash
# 1) rebuild the full balance analysis
python paper/experiments/exp3_parameter_sensitivity/run_exp3.py
python paper/experiments/exp3_parameter_sensitivity/plot_exp3.py
python paper/experiments/exp3_parameter_sensitivity/generate_exp3_full_analysis.py

# 2) validate one sensitivity configuration before a full run
python -m paper.experiments.exp3_parameter_sensitivity.run_sensitivity \
  --panel oat --include-default --configs default \
  --origins hakata --depart-times 420 --budgets 120 \
  --score-seeds 20260323 --output tmp/sensitivity_default_check.json

# 3) canonical serial queue (PowerShell)
powershell -ExecutionPolicy Bypass -File \
  paper/experiments/exp3_parameter_sensitivity/run_sensitivity_queue.ps1

# 4) after all 22 shards finish, merge each panel with the strict merger,
# then analyze and render (the exact --input list is recorded in the merged
# payload's source_shards metadata)
python -m paper.experiments.exp3_parameter_sensitivity.analyze_sensitivity
conda run -n reroute-paper-r Rscript \
  paper/experiments/r_visualization/plot_exp3_sensitivity.R
```

## Canonical findings (2026-07-27)

- All 11,088 scheduled runs completed; both merged panels pass the generic
  integrity gate with zero missing, duplicate, unexpected, schema, or semantic
  errors.
- Scores are identical to the default on all 600 tasks for
  `W=25/100/200`, every tested score-per-hour coefficient, and every tested
  effective-time coefficient. `W=10` changes the mean by only -0.313.
- Candidate cap is the material sensitivity dimension. Caps `15/10` are too
  restrictive; caps `60/40` improve score but hit a resource limit on 48.5%
  of tasks; uncapped expansion hits a limit on 67.7% and lowers mean score.
