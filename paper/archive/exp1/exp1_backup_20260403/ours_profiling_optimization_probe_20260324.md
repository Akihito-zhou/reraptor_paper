# Ours Profiling + Implementation Optimization Probe (2026-03-24)

Goal:
- Preserve the original method definition.
- Use profiling to find real hotspots.
- Apply only low-risk implementation optimizations.

## Profiling target

Case:
- `hakata / 07:00 / 4h`
- `timeout_seconds=120`

### Before optimization

Result:
- `stop_score_total = 680.0`
- `elapsed_ms = 120203.210`
- `labels = 369758`
- `termination_reason = timeout`

Top hotspots by cumulative time:
- `compute_or_get_metrics`: `50.028s`
- `_insert_label`: `35.330s`
- tuple/hash overhead: `22.339s`
- `_extend_edge`: `21.585s`
- `dominance_fn`: `14.667s`
- `dataclasses.replace`: `11.639s`
- `metrics_from_label`: `9.360s`
- `_next_edges`: `0.898s`

Interpretation:
- The bottleneck was not timetable expansion itself.
- The main cost came from metrics caching / hashing / dominance / label object churn.

### After optimization

Optimization applied:
- Replace tuple-based metrics cache keys with per-label instance caching.
- Reuse computed metrics for scored labels instead of forcing the cache to rebuild through expensive tuple hashing.

Result:
- `stop_score_total = 784.0`
- `elapsed_ms = 120882.250`
- `labels = 598646`
- `termination_reason = timeout`

Top hotspots by cumulative time:
- `_extend_edge`: `31.903s`
- `compute_or_get_metrics`: `27.393s`
- `_insert_label`: `26.281s`
- `dominance_fn`: `19.364s`
- `dataclasses.replace`: `13.945s`
- `metrics_from_label`: `10.746s`
- `_next_edges`: `1.151s`

Interpretation:
- Hash-heavy cache overhead was removed from the hotspot list.
- Under the same 120s compute budget, the search explored many more labels and found a higher-score solution.

## Non-profile runtime validation

### hakata / 07:00 / 4h

Before:
- `stop_score_total = 981.0`
- `elapsed_s = 391.696`
- `labels = 2183909`

After:
- `stop_score_total = 981.0`
- `elapsed_s = 150.815`
- `labels = 2183757`

### hakata / 07:00 / 8h with same 300s compute budget

Before:
- `stop_score_total = 918.0`
- `elapsed_s = 301.150`
- `labels = 2935031`
- `termination_reason = timeout`

After:
- `stop_score_total = 1112.0`
- `elapsed_s = 307.250`
- `labels = 4754354`
- `termination_reason = timeout`

## Takeaways

- The most important immediate gain came from implementation optimization, not from adding new pruning rules.
- `_next_edges` was not the bottleneck.
- The current strongest next target is reducing dominance / label-copy overhead while preserving the original method.
