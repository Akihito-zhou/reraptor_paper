# Private planner inputs (not distributed)

No transit input files are distributed here. Obtain them independently under
appropriate provider authorization. API credentials are not needed for offline
experiments once all inputs are installed. This repository does not grant data
access, and current API responses cannot recreate a historical snapshot exactly.

## Exact directory layout

```text
apps/api/data/
  base/
    stations_fukuoka.csv
    freepass_lines.yml
    fukuoka_city.geojson
    line_stop_edges.csv
  generated/
    boundary_overrides.json
  timetables/
    segments_fukuoka_20251224.csv
```

All six files are required to reproduce the frozen experiment configuration.
The earlier `raw/stations.csv` instruction was incorrect for this planner.
Do not substitute that path for `base/stations_fukuoka.csv`.

## Input contract

Files are UTF-8. Keep station/line codes as strings, including leading zeroes.
The authoritative parsers are `apps/api/services/planner_loader.py` and
`apps/api/services/planner.py`.

| File | Contract and role |
| --- | --- |
| stations_fukuoka.csv | CSV: `ekispert_station_code` (or `station_code`), `name`, `lat`, `lon`; valid numeric coordinates; station lookup and origin resolution. |
| freepass_lines.yml | YAML mapping with a `freepass_lines` list; each entry has `line_id`, `name` (or `line_name`), and boolean `eligible`; only eligible lines enter the graph. |
| fukuoka_city.geojson | GeoJSON city boundary used for spatial filtering and boundary construction. Preserve the original geometry for exact reproduction. |
| line_stop_edges.csv | CSV with `line_id` and `station_code`; row order within each line defines ordered stops. |
| boundary_overrides.json | JSON mapping; `include`/`exclude` stop codes and optional `substitute` entries (`target`, `via`, `auto`, `radius_km`, `min_degree`); affects boundary exceptions. |
| segments_fukuoka_20251224.csv | CSV: `line_id`, `direction`, `service_date`, `from_stop`, `to_stop`, `depart`, `arrive`; preserve `trip_id`/`segment_id` when present. `depart`/`arrive` use HH:MM (hours may exceed 23); `service_date` is 20251224. Optional names are `from_name`, `to_name`. |

Stop references must resolve to the station inventory and line references to the
eligible line inventory. Do not regenerate trip identifiers or reorder line-stop
rows if exact reproduction is intended. The loader has fallbacks, but those do
not establish equivalence with the original experiment inputs.

## Validate before a solver run

From the repository root, in the Python environment from the tutorial:

```sh
python -m paper.experiments.check_reproduction --require-data
```

This checks all six byte sizes and SHA-256 hashes against the frozen identities
recorded in the checker. It exits nonzero for absent, partial, or mismatched
inputs. It also rejects multiple segment snapshots because the original loader
selects the most recently modified matching file, not necessarily the service
date in the filename. Keep only the intended snapshot in this directory.
The frozen timetable has 304,344 segments, 1,032 stops, and 302 lines.

Equivalent independently prepared inputs can support a new experiment, but will
fail this **exact** snapshot check and must not be described as reproducing the
reported numerical values. Document their own provenance, hashes, dates, and
origin mapping in `paper/experiments/common/planner_bridge.py`.

Do not commit any inputs, generated caches, `.env` files, or credentials.
The repository ignores the contents of this directory except this README and
`.gitkeep`. See [the full tutorial](../../../paper/REPRODUCTION_TUTORIAL.md).
