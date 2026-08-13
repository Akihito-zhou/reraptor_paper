# ReRAPTOR Paper Repository

This repository contains the supplementary materials, experiment scripts, generated figures, and released result files for the ReRAPTOR paper:

`ReRAPTOR: Reverse-Objective RAPTOR for Time-Budgeted Value-Maximizing Transit Itinerary Planning`

It is a paper-focused extraction from the original `reroute_fukuoka` project. The goal of this repository is to provide a clean supplementary-materials entry point for readers, researchers, and future reuse.

## Contents

- `paper/document/`
  - `supplementary_materials.tex` and `.pdf`: the typeset supplementary tables and figure
- `paper/experiments/`
  - experiment pipelines for Exp1 to Exp4
  - canonical result-merging and reliability/sensitivity analyses
  - R scripts used to produce the manuscript's vector PDF figures
  - common utilities and algorithm implementations used in the paper
- `paper/figures/`
  - generated figures used in the manuscript and supplementary materials
- `paper/results/`
  - frozen canonical outputs and the derived tables used by the manuscript
- `paper/SUPPLEMENTARY_MATERIALS.md`
  - direct index to the additional tables, source data, and supplementary images promised in the manuscript
- `paper/REPRODUCIBILITY.md`
  - claim-to-artifact map, environment record, verification commands, and the raw-data availability boundary
- `apps/api/services/` and `apps/api/clients/`
  - the planner and service-layer code reused by the paper experiments

## Data Availability

The experiments depend on Fukuoka transit schedule data provided through Ekispert services. Those raw timetable files are not redistributed in this repository.

The expected data location is:

- `apps/api/data/`

See [apps/api/data/README.md](apps/api/data/README.md) for the expected directory layout and release policy. Exact service-date metadata, SHA-256, and inventory counts are recorded in [`paper/results/timetable_provenance.json`](paper/results/timetable_provenance.json).

What is included here:

- supplementary-material source
- generated figures
- released experiment outputs
- experiment and planner code

What is not included here:

- the article manuscript itself (submitted separately to the journal)
- proprietary raw timetable files from Ekispert
- private credentials or API keys
- unrelated web frontend and infrastructure files from the original project

## Reproducing the Paper Assets

### 1. Compile the supplementary materials

The supplementary-material source is under `paper/document/`:

- `paper/document/supplementary_materials.tex`

Run `latexmk -pdf supplementary_materials.tex` from that directory to rebuild
the six-page A4 supplement. The repository PDF is a checked preview; the
manuscript itself is not distributed in this repository (see the journal
submission for the article text).

### 2. Reuse the released outputs directly

The simplest way to inspect the released results is to use the generated files under:

- `paper/results/`
- `paper/figures/`

These are the frozen canonical outputs used for the manuscript.
See `paper/SUPPLEMENTARY_MATERIALS.md` for the public supplementary-material
index and `paper/results/README.md` for the released file set's relationship to
the four experiments.

### 3. Re-run experiments

The experiment scripts expect the original directory layout to remain intact. This repository preserves that layout deliberately.

The canonical analyses were recorded with Python 3.12.7. Install their pinned
packages with `python -m pip install -r paper/requirements.txt`. The API
application has a separate Poetry environment declared in
`apps/api/pyproject.toml` and `apps/api/poetry.lock`.

Full solver reruns also require:

- timetable and station data placed under `apps/api/data/`

Typical entry points:

- `paper/experiments/exp1_algorithm_comparison/run_exp1.py`
- `paper/experiments/exp2_ablation_study/run_exp2.py`
- `paper/experiments/exp3_parameter_sensitivity/run_exp3.py`
- `paper/experiments/exp3_parameter_sensitivity/run_sensitivity.py`
- `paper/experiments/exp4_route_visualization/run_exp4.py`

The repository test suite can be checked with:

```text
python -m paper.experiments.verify_manuscript_claims
python -m pytest paper/experiments/tests -q
git lfs fsck
```

The first command verifies the manuscript's displayed numerical claims against
the released canonical artifacts. When the proprietary timetable is absent,
it validates the released provenance metadata instead of treating the withheld
file as publicly downloadable. See
[`paper/REPRODUCIBILITY.md`](paper/REPRODUCIBILITY.md) for the complete mapping.

## Repository Layout

```text
reraptor_paper/
|- apps/
|  |- api/
|  |  |- clients/
|  |  |- data/
|  |  |- services/
|  |  |- poetry.lock
|  |  `- pyproject.toml
`- paper/
   |- document/
   |- experiments/
   |- figures/
   `- results/
```

## Notes

- The repository is intended as a paper companion, not as a production application.
- Editorial correspondence, response letters, internal revision notes, pilot
  runs, smoke tests, and superseded intermediate outputs are intentionally
  excluded.
- Some experiment scripts assume access to the original planner data and therefore will not run end-to-end without the withheld timetable files.
- Generated result JSON and figure files are included so the paper remains inspectable even without redistributing the raw data.
