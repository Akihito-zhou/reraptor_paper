# ReRAPTOR: step-by-step reproduction

All commands below run from the repository root unless stated otherwise.
The Python command lines are deliberately on one line and work in PowerShell
and POSIX shells. The canonical environment was Python **3.12.7 on Windows 11**.
Use Python 3.12 for this release; other Python versions are not validated.

## 1. Choose what you want to reproduce

| Path | Private inputs needed? | What it establishes |
| --- | --- | --- |
| Installation check and unit tests | No | Planner imports, ten manuscript methods, scoring and protocol checks |
| Audit released results and recompute statistics | No | Consistency with already released canonical result rows |
| Rebuild statistical figures | No | Figure rendering from released outputs |
| Rerun the transit solvers | Yes, all six files | A new execution of the algorithms on the frozen inputs |

Private inputs are not downloadable from this repository. A successful public
result audit is not an end-to-end solver reproduction. No command below fetches
provider data or requires uploading local inputs. Existing public results remain
available, but this code/tutorial update does not add datasets or result files.

## 2. Clone and create an isolated Python environment

```sh
git clone https://github.com/Akihito-zhou/reraptor_paper.git
cd reraptor_paper
python --version
python -m venv .venv-paper
```

Activate on Windows PowerShell:

```powershell
.\.venv-paper\Scripts\Activate.ps1
```

Activate on Linux/macOS:

```sh
source .venv-paper/bin/activate
```

If PowerShell blocks activation, invoke `.venv-paper/Scripts/python.exe` in
place of `python` in subsequent commands. Activation is only a convenience.

```sh
python -m pip install -r paper/requirements.txt
python -m pip check
python -m paper.experiments.check_reproduction
python -m pytest -q paper/experiments/tests
python -m paper.experiments.verify_manuscript_claims
```

Expected: preflight reports ten manuscript algorithms, notes that private inputs
are absent, then prints PASS. Pytest must pass; the claim verifier prints five
check PASS lines followed by `PASS all manuscript claim checks`. The verifier
covers its encoded numerical claims, not every sentence of the paper.
No web server, frontend, Docker, Poetry installation, or API key is required.
`paper/requirements.txt` pins the direct Python dependencies; transitive packages
are resolved by pip, so this is not a full historical environment lock.

The algorithm registry intentionally has **ten** methods including the two recent
adapted baselines. Exploratory methods from the private development project are
not part of the manuscript protocol and must not be added to this registry.

## 3. Recompute analyses from the public results

```sh
python -m paper.experiments.exp1_algorithm_comparison.analyze_score_interpretability --results-dir tmp/reproduction/exp1 --suffix check
python -m paper.experiments.exp1_algorithm_comparison.analyze_underperformance --results-dir tmp/reproduction/exp1 --figures-dir tmp/reproduction/figures --suffix check
```

These use the frozen 22,800-row Exp1 JSON and the default 20,000 bootstrap
replications/recorded bootstrap seed. Inspect generated CSV, Markdown and JSON
under `tmp/reproduction/exp1`. Runtime and output timestamps can differ.
The original source manifest is not included in the public clone. The scripts
therefore report unavailable manifest hashes and source gates as `null`; they
still hash the actual result file. They do not invent a canonical PASS status.
If you have the original manifest, pass `--source-manifest PATH`. An explicitly
specified missing file is an error. These analyses do not verify raw-input
provenance; use the authorized-input check in section 5 for that.

Sensitivity analysis reads the two released canonical sensitivity panels:

```sh
python -m paper.experiments.exp3_parameter_sensitivity.analyze_sensitivity
```

This command overwrites stable `sensitivity_canonical_*` derived files in
`paper/results/exp3_parameter_sensitivity/`. Run in a separate clone if you want
to retain byte-for-byte original artifacts. It uses 20,000 bootstrap repetitions
by default. Exp3's older `run_exp3.py` is the quality/speed balance analysis;
`run_sensitivity.py` is the solver-based sensitivity experiment.

## 4. Rebuild figures (optional R environment)

Install Conda separately, then:

```sh
conda env create -f paper/experiments/r_visualization/environment.yml
conda run -n reroute-paper-r Rscript paper/experiments/r_visualization/render_all.R
```

The R scripts overwrite stable figure paths under `paper/figures/` and use
`paper_theme.R` for formatting. See [R pipeline details](experiments/r_visualization/README.md).
Without the private city boundary, the public R Exp4 renderer emits a warning
and renders route-only panels from already released route traces. Full map
background reproduction needs the authorized boundary file. Fonts/platforms
can affect layout; binary-identical PDFs are not promised.

To compile the supplementary document, install a TeX distribution with latexmk:

```sh
cd paper/document
latexmk -pdf supplementary_materials.tex
cd ../..
```

## 5. Install authorized private inputs locally

Follow [the six-file layout and schema](../apps/api/data/README.md). Do not
rename a current API download to the historical date and assume equivalence.
The study snapshot is **24 December 2025**. All six original identities are
checked by:

```sh
python -m paper.experiments.check_reproduction --require-data
```

Proceed only after PASS for an exact-input rerun. Keep only one
`segments_fukuoka_*.csv` in `apps/api/data/timetables/`: the existing planner
chooses by file modification time. Offline loading is set by
`common/planner_bridge.py` (`enable_realtime=False`). Credentials are unnecessary.

## 6. Run small solver checks before the full grids

These commands require private inputs and write new local outputs:

```sh
python -m paper.experiments.exp1_algorithm_comparison.run_exp1 --quick --include-recent-adapted-baselines --output-tag smoke_test
python -m paper.experiments.exp2_ablation_study.run_exp2 --quick --configs full,noneg --output tmp/reproduction/exp2/smoke_test.json
python -m paper.experiments.exp3_parameter_sensitivity.run_sensitivity --panel oat --include-default --configs default --origins hakata --depart-times 420 --budgets 120 --score-seeds 20260323 --output tmp/reproduction/exp3/smoke_test.json
```

These are installation/data-loading checks, not the manuscript benchmark.
Check output metadata, record counts, feasibility flags, objective validity,
and termination reasons before starting larger runs. Exp1 writes tagged files
under `paper/results/exp1_algorithm_comparison/`; do not stage those outputs.

## 7. Full manuscript grids

The shared grid is ten origins, three departures (420/600/840 minutes), four
budgets (120/240/360/480 minutes), five score seeds (20260323?20260327), score
range 1?100, a 10-minute effective charge per unique scored non-origin stop,
and a 3-minute transfer buffer. The effective charge is resource accounting;
it does not shift scheduled vehicle departure times.

### Experiment 1: ten algorithms, 22,800 records

```sh
python -m paper.experiments.exp1_algorithm_comparison.run_exp1 --checkpoint-every 20 --score-seeds 20260323,20260324,20260325,20260326,20260327 --score-min 1 --score-max 100 --dwell-minutes 10 --objective-mode score_guided --origins hakata,tenjin,nishijin,ohori-koen,yakuin,kashii,noke,meinohama,kaizuka,fukudaimae --depart-times 420,600,840 --budgets 120,240,360,480 --seeds 0,1,2,3,4 --include-recent-adapted-baselines --output-tag independent_reproduction
```

Each deterministic method runs once on 600 tasks; each stochastic method runs
five algorithm seeds (3,000 records). Do not add `--repeat-deterministic-seeds`.
See [Exp1 details](experiments/exp1_algorithm_comparison/README.md).

### Experiment 2: eight configurations, 4,800 records

```sh
python -m paper.experiments.exp2_ablation_study.run_exp2 --checkpoint-every 10 --timeout-seconds 60 --no-pruning-max-labels 1000000 --score-seeds 20260323,20260324,20260325,20260326,20260327 --score-min 1 --score-max 100 --dwell-minutes 10 --objective-mode score_guided --origins hakata,tenjin,nishijin,ohori-koen,yakuin,kashii,noke,meinohama,kaizuka,fukudaimae --depart-times 420,600,840 --budgets 120,240,360,480 --seeds 0 --configs full,noneg,nodom,nobeam,nobeamnodom,nodomnoneg,nobeamnoneg,nobeamnodomnoneg --output tmp/reproduction/exp2/results.json
```

See [Exp2 details](experiments/exp2_ablation_study/README.md). Preserve timeout
and label-cap outcomes; excluding unsuccessful runs changes the estimand.

### Experiment 3: 18 OAT configurations and four interaction corners

```sh
python -m paper.experiments.exp3_parameter_sensitivity.run_sensitivity --panel oat --include-default --checkpoint-every 10 --output tmp/reproduction/exp3/oat.json
python -m paper.experiments.exp3_parameter_sensitivity.run_sensitivity --panel interaction --checkpoint-every 10 --output tmp/reproduction/exp3/interaction.json
```

The defaults freeze the full protocol: 10,800 OAT records and 288 interaction
records (11,088 total). Interaction uses three origins and two score seeds;
the other five cells of the 3-by-3 panel reuse OAT records on the same subset.
Do not use `--panel all` to combine these two differently sized task grids.
To analyze the new runs (overwrites stable derived outputs):

```sh
python -m paper.experiments.exp3_parameter_sensitivity.analyze_sensitivity --oat tmp/reproduction/exp3/oat.json --interaction tmp/reproduction/exp3/interaction.json
```

See [Exp3 protocol](experiments/exp3_parameter_sensitivity/README.md).
The older PowerShell queue writes into canonical result directories; prefer
these new output paths for an independent reproduction.

### Experiment 4: selected route cases

```sh
python -m paper.experiments.exp4_route_visualization.run_exp4 --select-only
python -m paper.experiments.exp4_route_visualization.run_exp4
python -m paper.experiments.exp4_route_visualization.plot_exp4
python -m paper.experiments.exp4_route_visualization.generate_exp4_full_analysis
```

All four commands write stable case paths (`--select-only` also replaces the
case manifest); use a separate clone. The full replay and plotting commands
also overwrite route and figure paths. Case selection is based on the released canonical comparison. Replays
check route scores; canonical elapsed time and replay time have distinct roles.
See [Exp4 details](experiments/exp4_route_visualization/README.md).

## 8. Interpret and validate the rerun

Full grids are expensive. At 60 seconds per call, tens of thousands of calls
can take days; no fixed completion time is promised. Use checkpoints and
`--resume` with the same arguments/output paths (where supported by `--help`).
Never merge unrelated grids or different snapshots just to reach a row count.
The `common/merge_*_shards.py` utilities enforce task-key and metadata checks.

Compare scores, feasibility, cap/timeout status and task-level aggregates.
Wall-clock runtime varies by machine and load. Time-limited stochastic searches
may also return different routes/scores on another machine even with fixed
seeds. Record hardware, Python/package versions, commit, input hashes and limits.
The claim verifier audits the **released** canonical filenames; passing it after
a new tagged run does not validate that new run automatically.

## Troubleshooting

- `numpy.core.multiarray failed to import`: create the isolated environment and
  install the pinned requirements; do not use an unrelated global Conda stack.
- `No module named paper` / `services`: run from the repository root with
  `python -m ...` and install the requirements in that same interpreter.
- Missing stations, no edges, or wrong network: check all six filenames, hashes,
  eligible lines, station references, boundary geometry, and snapshot selection.
- Missing manifest: default public analyses support its absence with null
  provenance fields. Supply `--source-manifest` only for an existing record.
- Missing R or LaTeX executable: those are optional separate installations and
  are not installed by pip.
- Rerun differs: check exact inputs, grid, seeds, caps and resource limits first;
  retain failed runs and inspect metadata before interpreting a score difference.

## Keeping local data private

`apps/api/data/`, `.venv*`, `tmp/`, `.env*`, and common key files are ignored.
Git ignore rules do not protect forced additions or previously tracked files.
Use `git status --short` and `git diff --cached --name-only` before any commit.
Never force-add private inputs or newly generated result/route dumps. This
release only updates source code, dependency declarations and documentation.
