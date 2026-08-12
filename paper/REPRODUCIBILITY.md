# ReRAPTOR manuscript reproducibility record

This record maps the manuscript claims to the exact input, code, canonical
results, and figure sources in this repository. Commands are run from the
repository root.

## Frozen input

- Service date: Wednesday, 24 December 2025
- Authorized local file: `apps/api/data/timetables/segments_fukuoka_20251224.csv`
- Public provenance record: `paper/results/timetable_provenance.json`
- SHA-256: `319d443ac097f8964f8774d38fc63c6c8f7ef90e505eb167ffd38bc317727c82`
- Inventory: 304,344 scheduled segments, 1,032 stops, and 302 lines
- Transfer buffer: 3 min
- Per-stop effective-time charge: 10 min per unique scored non-origin stop

The effective-time charge is a resource-accounting term. It does not alter
scheduled departure or connection times. The timetable was obtained through
the Ekispert API. The public paper companion does not redistribute this
provider-derived raw snapshot. It retains the checksum and inventory metadata.
Exact raw-input reproduction requires licensed Ekispert access and the
authors' input-edge inventory; those prerequisites cannot be redistributed.
Researchers with equivalent authorization can obtain the same service date
under the provider's terms and place the snapshot at the authorized local path
above. The released canonical outputs allow every displayed numerical claim to
be checked without that proprietary file.

## Environment

The canonical runs used Windows 11 build 26200 and Python 3.12.7. The recorded
analysis package versions are pinned in `paper/requirements.txt`. The API
application has a separate Poetry lock file.

```powershell
python -m venv .venv-paper
.\.venv-paper\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r paper/requirements.txt
```

The R figure environment is defined in
`paper/experiments/r_visualization/environment.yml`.

## Claim-to-artifact map

| Manuscript evidence | Canonical source | Analysis or rendering code |
| --- | --- | --- |
| Table 2, Fig. 2, Supplement S1--S3 | `paper/results/exp1_algorithm_comparison/exp1_results_canonical_final_10alg_manuscript_20260723.json` and the derived `score_interpretability_*` / `underperformance_*` CSV files | `paper/experiments/exp1_algorithm_comparison/` |
| Table 3, Supplement S4 | `paper/results/exp2_ablation_study/exp2_results_canonical_final_8config_20260725.json` and `exp2_canonical_*.csv` | `paper/experiments/exp2_ablation_study/` |
| Fig. 4, Supplement S5 | `paper/results/exp3_parameter_sensitivity/sensitivity_results_canonical_oat_18config_20260727.json`, `sensitivity_results_canonical_interaction_4corner_20260727.json`, and `sensitivity_canonical_*.csv` | `paper/experiments/exp3_parameter_sensitivity/` and `paper/experiments/r_visualization/plot_exp3_sensitivity.R` |
| Table 4, Supplement S6 and Fig. S1 | `paper/results/exp4_route_visualization/exp4_cases.json` and `routes/*.json` | `paper/experiments/exp4_route_visualization/` |
| Timetable provenance | `paper/results/timetable_provenance.json`; the raw snapshot is not redistributed | `paper/experiments/verify_manuscript_claims.py` |
| Experiment environment provenance | metadata embedded in the frozen canonical JSON files | `paper/experiments/common/build_canonical_manifest.py` |

Exact full-grid rerun commands and expected record counts are documented in
`paper/experiments/exp1_algorithm_comparison/README.md` and
`paper/experiments/exp2_ablation_study/README.md`. Experiment 3 and 4 have their
own READMEs in the corresponding experiment directories.

Canonical JSON metadata contains machine-local absolute paths captured at run
time. These fields are provenance records, not runtime inputs; all executable
code resolves paths relative to the repository.

## Fast verification without rerunning 41,000+ solver calls

```powershell
python -m paper.experiments.verify_manuscript_claims
python -m pytest -q paper/experiments/tests
git lfs fsck
```

The first command fails if the displayed headline values, taskwise counts,
case selections, or released timetable provenance disagree with the canonical
artifacts. If an authorized timetable snapshot is present locally, it also
checks the raw file's checksum and inventory. The test suite checks scoring
semantics, deterministic timetable loading, canonical merge gates, and analysis
protocols.

## Recompute derived analyses

Use temporary output directories to avoid overwriting the frozen artifacts:

```powershell
python -m paper.experiments.exp1_algorithm_comparison.analyze_score_interpretability `
  --results-dir tmp/reproduction/exp1 --suffix check
python -m paper.experiments.exp1_algorithm_comparison.analyze_underperformance `
  --results-dir tmp/reproduction/exp1 --figures-dir tmp/reproduction/figures --suffix check
python -m paper.experiments.exp3_parameter_sensitivity.analyze_sensitivity
conda env create -f paper/experiments/r_visualization/environment.yml
conda run -n reroute-paper-r Rscript paper/experiments/r_visualization/render_all.R
```

The Experiment 3 analysis command writes the stable canonical CSV paths. Run it
only on a clean copy or after preserving the released files. Full solver reruns
are expensive; the experiment-specific READMEs document the queue commands and
frozen configuration grids.

## Public-release gate

The package is not ready to be described as publicly available until all of the
following are true:

1. Anonymous access to the repository URL succeeds.
2. Git LFS objects download successfully in a fresh clone.
3. `paper/document/supplementary_materials.tex`, its PDF, and this
   reproducibility record are committed. Editorial response and marked-review
   files remain outside the public paper companion.
4. Timetable redistribution permission is documented, or provider-derived raw
   data are excluded and their provenance, checksum, inventory, and access
   boundary are documented without claiming an unavailable public command.
5. The three verification commands above pass in a fresh environment.
6. The authors confirm and add any declarations required by the target venue,
   including funding, conflicts of interest, author contributions, and use of
   generative AI. These statements require author knowledge and must not be
   inferred from the code or manuscript.
