# ReRAPTOR Paper Repository

This repository contains the manuscript, experiment scripts, generated figures, and released result files for the ReRAPTOR paper:

`ReRAPTOR: Reverse-Objective RAPTOR for Time-Budgeted Value-Maximizing Transit Itinerary Planning`

It is a paper-focused extraction from the original `reroute_fukuoka` project. The goal of this repository is to provide a clean supplementary-materials entry point for readers, reviewers, and future reuse.

## Contents

- `paper/document/`
  - `its_symposium_ijit_draft.tex`: the compressed 10-page ITS Symposium submission version
  - `its_symposium_ijit_draft_full_backup.tex`: the fuller pre-compression manuscript version
  - matching compiled PDFs, bibliography, and Springer class files
- `paper/experiments/`
  - experiment pipelines for Exp1 to Exp4
  - common utilities and algorithm implementations used in the paper
- `paper/figures/`
  - generated figures used in the manuscript and supplementary materials
- `paper/results/`
  - released result summaries and exported route/result JSON files
- `apps/api/services/` and `apps/api/clients/`
  - the planner and service-layer code reused by the paper experiments

## Data Availability

The experiments depend on Fukuoka transit schedule data provided through Ekispert services. Those raw timetable files are not redistributed in this repository.

The expected data location is:

- `apps/api/data/`

See [apps/api/data/README.md](apps/api/data/README.md) for the expected directory layout and the current release policy.

What is included here:

- manuscript source
- generated figures
- released experiment outputs
- experiment and planner code

What is not included here:

- proprietary raw timetable files from Ekispert
- private credentials or API keys
- unrelated web frontend and infrastructure files from the original project

## Reproducing the Paper Assets

### 1. Compile the manuscript

The manuscript files are under `paper/document/`.

Main submission version:

- `paper/document/its_symposium_ijit_draft.tex`

Fuller backup version:

- `paper/document/its_symposium_ijit_draft_full_backup.tex`

Both files rely on the bundled Springer class and bibliography files already included in the same directory.

### 2. Reuse the released outputs directly

The simplest way to inspect the released results is to use the generated files under:

- `paper/results/`
- `paper/figures/`

These are the exact outputs used to prepare the current paper draft.

### 3. Re-run experiments

The experiment scripts expect the original directory layout to remain intact. This repository preserves that layout deliberately.

The scripts depend on:

- Python 3.11
- the dependencies declared in `apps/api/pyproject.toml`
- timetable and station data placed under `apps/api/data/`

Typical entry points:

- `paper/experiments/exp1_algorithm_comparison/run_exp1.py`
- `paper/experiments/exp2_ablation_study/run_exp2.py`
- `paper/experiments/exp3_parameter_sensitivity/run_exp3.py`
- `paper/experiments/exp4_route_visualization/run_exp4.py`

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
- Some experiment scripts assume access to the original planner data and therefore will not run end-to-end without the withheld timetable files.
- Generated result JSON and figure files are included so the paper remains inspectable even without redistributing the raw data.
