# Released Results

This directory contains only the frozen outputs needed to inspect and reproduce
the analyses reported in the manuscript. Pilot runs, smoke tests, partial
merges, superseded outputs, and private timetable inputs are excluded.

## Experiment 1

`exp1_algorithm_comparison/exp1_results_canonical_final_10alg_manuscript_20260723.json`
is the frozen ten-algorithm result set. The canonical summary, score
interpretability files, and underperformance files in the same directory are
derived from it and feed the manuscript tables and figures.

## Experiment 2

`exp2_ablation_study/exp2_results_canonical_final_8config_20260725.json`
contains the complete eight-configuration ablation. The canonical JSON/CSV
analysis files are derived from it. Supporting route cases are retained for
the supplementary mechanism checks.

## Experiment 3

The two `sensitivity_results_canonical_*_20260727.json` files contain the
18 one-at-a-time and four interaction configurations. The
`sensitivity_canonical_*_20260727` files contain their derived comparisons.

## Experiment 4

`exp4_route_visualization/exp4_cases.json` and the `routes/` directory contain
the frozen route cases used to generate the supplementary maps.

The filenames are date-stamped to identify the frozen release used by the
manuscript. All raw transit schedules remain excluded because they are supplied
under the Ekispert data agreement.
