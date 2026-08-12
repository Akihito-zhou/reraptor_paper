# Experiment 2: pruning ablation

Run commands from the repository root after installing
`paper/requirements.txt`. The canonical manuscript artifact is:

`paper/results/exp2_ablation_study/exp2_results_canonical_final_8config_20260725.json`

It contains 4,800 records: 600 query/score-map tasks for each of eight
deterministic configurations.

## Frozen full grid

- stop-score seeds: `20260323,20260324,20260325,20260326,20260327`
- stop-score range: 1--100; effective-time charge: 10 min
- origins: `hakata,tenjin,nishijin,ohori-koen,yakuin,kashii,noke,meinohama,kaizuka,fukudaimae`
- departure times: `420,600,840` min after midnight
- time budgets: `120,240,360,480` min
- algorithm seed: `0` (all ablations are deterministic)
- per-run timeout: 60 s
- no-pruning label cap: 1,000,000 labels
- objective mode: `score_guided`
- configurations: `full,noneg,nodom,nobeam,nobeamnodom,nodomnoneg,nobeamnoneg,nobeamnodomnoneg`

## Full solver rerun

Write the reproduction to a new path so the frozen result cannot be
overwritten. The command is computationally expensive.

```powershell
python -m paper.experiments.exp2_ablation_study.run_exp2 `
  --checkpoint-every 10 --timeout-seconds 60 `
  --no-pruning-max-labels 1000000 `
  --score-seeds 20260323,20260324,20260325,20260326,20260327 `
  --score-min 1 --score-max 100 --dwell-minutes 10 `
  --objective-mode score_guided `
  --origins hakata,tenjin,nishijin,ohori-koen,yakuin,kashii,noke,meinohama,kaizuka,fukudaimae `
  --depart-times 420,600,840 --budgets 120,240,360,480 `
  --seeds 0 `
  --configs full,noneg,nodom,nobeam,nobeamnodom,nodomnoneg,nobeamnoneg,nobeamnodomnoneg `
  --output tmp/reproduction/exp2/exp2_results.json
```

For a short installation and data-loading check, run:

```powershell
python -m paper.experiments.exp2_ablation_study.run_exp2 `
  --quick --configs full,noneg --output tmp/reproduction/exp2/smoke_test.json
```

The historical shard queue in `run_remaining_canonical_queue.ps1` documents how
the released configurations were generated and audited individually. It writes
into the canonical result tree and is retained for provenance; use the explicit
temporary output command above for an independent rerun.

Finally, run `python -m paper.experiments.verify_manuscript_claims` to compare
the frozen artifacts with every numerical value displayed in the manuscript.
