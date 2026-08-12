# Experiment 1: algorithm comparison

Run commands from the repository root after installing
`paper/requirements.txt`. The canonical manuscript artifact is:

`paper/results/exp1_algorithm_comparison/exp1_results_canonical_final_10alg_manuscript_20260723.json`

It contains 22,800 records: 600 query/score-map tasks for each deterministic
method and 3,000 records (600 tasks times five algorithm seeds) for each
stochastic method. The ten compared methods are recorded in the JSON metadata.

## Frozen full grid

- stop-score seeds: `20260323,20260324,20260325,20260326,20260327`
- stop-score range: 1--100; effective-time charge: 10 min
- origins: `hakata,tenjin,nishijin,ohori-koen,yakuin,kashii,noke,meinohama,kaizuka,fukudaimae`
- departure times: `420,600,840` min after midnight
- time budgets: `120,240,360,480` min
- stochastic algorithm seeds: `0,1,2,3,4`
- objective mode: `score_guided`

## Full solver rerun

Use a new output tag. Do not reuse the canonical tag or edit the frozen result.
The command is computationally expensive.

```powershell
python -m paper.experiments.exp1_algorithm_comparison.run_exp1 `
  --checkpoint-every 20 `
  --score-seeds 20260323,20260324,20260325,20260326,20260327 `
  --score-min 1 --score-max 100 --dwell-minutes 10 `
  --objective-mode score_guided `
  --origins hakata,tenjin,nishijin,ohori-koen,yakuin,kashii,noke,meinohama,kaizuka,fukudaimae `
  --depart-times 420,600,840 --budgets 120,240,360,480 `
  --seeds 0,1,2,3,4 `
  --include-recent-adapted-baselines `
  --output-tag independent_reproduction
```

The result is written below `paper/results/exp1_algorithm_comparison/` with the
new tag. Deterministic methods run once per query/score-map task; do not add
`--repeat-deterministic-seeds` when reproducing the canonical protocol.

For a short installation and data-loading check, run:

```powershell
python -m paper.experiments.exp1_algorithm_comparison.run_exp1 `
  --quick --include-recent-adapted-baselines --output-tag smoke_test
```

## Recompute the manuscript analyses

These commands read the frozen canonical JSON by default and place derived
outputs in temporary directories:

```powershell
python -m paper.experiments.exp1_algorithm_comparison.analyze_score_interpretability `
  --results-dir tmp/reproduction/exp1 --suffix check
python -m paper.experiments.exp1_algorithm_comparison.analyze_underperformance `
  --results-dir tmp/reproduction/exp1 `
  --figures-dir tmp/reproduction/figures --suffix check
```

Finally, run `python -m paper.experiments.verify_manuscript_claims` to compare
the frozen artifacts with every numerical value displayed in the manuscript.
