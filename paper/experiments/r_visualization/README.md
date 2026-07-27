# Unified R figure pipeline

This directory contains the manuscript-wide visual language and the R scripts
that render publication figures as vector PDF and high-resolution PNG files.

## Environment

Create the isolated environment once:

```powershell
conda env create -f paper/experiments/r_visualization/environment.yml
```

## Render

From the repository root:

```powershell
conda run -n reroute-paper-r Rscript paper/experiments/r_visualization/render_all.R
```

Individual scripts can also be run separately:

```powershell
conda run -n reroute-paper-r Rscript paper/experiments/r_visualization/render_method_framework.R
conda run -n reroute-paper-r Rscript paper/experiments/r_visualization/plot_exp1.R
conda run -n reroute-paper-r Rscript paper/experiments/r_visualization/plot_exp2.R
conda run -n reroute-paper-r Rscript paper/experiments/r_visualization/plot_exp3_sensitivity.R
conda run -n reroute-paper-r Rscript paper/experiments/r_visualization/plot_exp4.R
```

Experiment 2 is rendered after the eight canonical shards have been merged:

```powershell
conda run -n reroute-paper-r Rscript paper/experiments/r_visualization/plot_exp2.R --input=paper/results/exp2_ablation_study/<merged-canonical-result>.json
```

Experiment 3 sensitivity statistics are generated before plotting:

```powershell
python -m paper.experiments.exp3_parameter_sensitivity.analyze_sensitivity
conda run -n reroute-paper-r Rscript paper/experiments/r_visualization/plot_exp3_sensitivity.R
```

The scripts overwrite the stable figure paths already referenced by the
manuscript. Statistical plots read the frozen canonical result files directly.
All plots share `paper_theme.R`, which fixes typography, spacing, palette, and
export settings across experiments.
