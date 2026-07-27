# Experiment 4: Main-Task Case Visualization

Experiment 4 is a qualitative case study, not a new benchmark.

It now serves the same main task as Experiments 1 and 3:
- route quality: `stop_score_total`
- generation speed: `elapsed_ms`

The goal is to visualize three representative situations:
- a clear success case for `Ours`
- a quality-speed balance case where `Ours` is closest to the ideal tradeoff
- an honest counterexample where `Ours` does not obtain the highest stop score

## Scripts

- `run_exp4.py`
  - selects representative cases from the frozen canonical `Exp1` and balance data
  - rebuilds the selected routes under the corresponding `score_seed`
  - verifies replayed route scores against the exact canonical rows
  - reports the frozen canonical generation time, while retaining replay time as provenance
  - exports route JSON files in the project route format
- `plot_exp4.py`
  - renders per-algorithm route maps from the exported JSON files
  - stitches them into case panels and main/appendix overview panels
- `generate_exp4_full_analysis.py`
  - writes a markdown casebook for paper drafting

## Default Cases

By default the pipeline selects:

- `Case A`: Ours clearly leads on both stop score and generation time
- `Case B`: Ours is the best quality-speed balance case
- `Case C`: a counterexample where Ours is faster but not the top-scoring route

## Run

```powershell
python paper\experiments\exp4_route_visualization\run_exp4.py
python paper\experiments\exp4_route_visualization\plot_exp4.py
python paper\experiments\exp4_route_visualization\generate_exp4_full_analysis.py
```

Only inspect which cases would be selected:

```powershell
python paper\experiments\exp4_route_visualization\run_exp4.py --select-only
```

Run only one case:

```powershell
python paper\experiments\exp4_route_visualization\run_exp4.py --case-ids case_b_quality_speed_balance
python paper\experiments\exp4_route_visualization\plot_exp4.py --case-ids case_b_quality_speed_balance
```

Optionally restrict the algorithms rerun for the selected cases:

```powershell
python paper\experiments\exp4_route_visualization\run_exp4.py --algorithms ours,nsga2
```

## Outputs

- `paper/results/exp4_route_visualization/exp4_cases.json`
- `paper/results/exp4_route_visualization/routes/*.json`
- `paper/figures/exp4/exp4_*_panel.png`
- `paper/figures/exp4/exp4_*_panel.pdf`
- `paper/figures/exp4/exp4_main_cases.png`
- `paper/figures/exp4/exp4_main_cases.pdf`
- `paper/figures/exp4/exp4_appendix_cases.png`
- `paper/figures/exp4/exp4_appendix_cases.pdf`
- `paper/figures/exp4/exp4_case_summary.md`
- `paper/results/exp4_route_visualization/exp4_full_text_analysis.md`
