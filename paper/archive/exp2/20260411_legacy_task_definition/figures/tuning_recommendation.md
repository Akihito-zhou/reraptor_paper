# Exp2 Supporting Tuning Recommendation

Date: 2026-03-12

## 1) Theme-negative tuning

Search space (quick mode, `theme_negative_multi`, 8 themes):
- `theme_penalty_scale` in {0.15, 0.20, 0.25, 0.30, 0.35}
- `theme_bonus_scale` in {0.60, 0.80, 1.00}
- `theme_min_ratio_scale` in {0.70, 0.80, 0.90}

Best trade-off:
- `theme_penalty_scale=0.25`
- `theme_bonus_scale=0.60`
- `theme_min_ratio_scale=0.70`

Validation (`quick-seed-count=2`, 8 themes):
- mean `dThemeComp` (Full - NoNeg): `+0.005805`
- positive-theme ratio: `0.625` (5/8 themes)
- mean `dThemeHit`: `+0.053`
- mean `dThemeSat`: `+0.125`
- mean runtime ratio (Full / NoNeg): `1.354`

Interpretation:
- Theme-aware objective improves (positive `dThemeComp`) in majority themes.
- Raw composite alone can slightly decrease; this is expected when enforcing theme alignment.

## 2) Beam stress tuning

Search space (quick mode, `beam_width_sweep_stress`):
- timeout in {30s, 20s, 15s}
- beam widths {5, 10, 20, 50} against NoBeam
- stress set: 3 origins x 2 departure times x 2 budgets (12h, 16h)

Best stress setting for showing beam effect:
- `timeout_seconds=20`
- beam variant with clearest gain: `Beam5`

Validation (`quick-seed-count=2`, timeout=20):
- NoBeam: `comp=0.955046`, `mean_ms=12373.9`, `p95=20313.6`, `cap_hit=0.125`
- Beam5: `comp=0.955114`, `mean_ms=12028.9`, `p95=20203.6`, `cap_hit=0.083`
- Delta (Beam5 - NoBeam):
  - `dComp=+0.000069`
  - `dMeanMs=-345.0`
  - `dP95=-110.0`
  - `dCapHit=-0.042`

Interpretation:
- Beam (especially narrow Beam5) reduces tail latency and cap-hit risk without quality loss.

## 3) Recommended commands

Theme-negative verification:
```bash
python paper/experiments/exp2_ablation_study/run_exp2_supporting.py \
  --quick \
  --experiments theme_negative_multi \
  --quick-seed-count 2 \
  --max-themes 8 \
  --theme-penalty-scale 0.25 \
  --theme-bonus-scale 0.60 \
  --theme-min-ratio-scale 0.70
```

Beam stress verification:
```bash
python paper/experiments/exp2_ablation_study/run_exp2_supporting.py \
  --quick \
  --experiments beam_width_sweep_stress \
  --quick-seed-count 2 \
  --timeout-seconds 20
```

