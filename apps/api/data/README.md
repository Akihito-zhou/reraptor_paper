# Local transit-data layout

This directory is intentionally empty in the public paper companion. The
experiments use Fukuoka transit data obtained through Ekispert, but the raw
provider-derived files and API credentials are not redistributed.

## Expected authorized layout

Researchers who independently hold the necessary provider authorization can
place equivalent local inputs at:

```text
apps/api/data/
|- base/
|  `- line_stop_edges.csv
|- raw/
|  `- stations.csv
`- timetables/
   `- segments_fukuoka_20251224.csv
```

- `line_stop_edges.csv` records the ordered stop codes for each line.
- `stations.csv` records station codes, names, latitude, and longitude.
- `segments_fukuoka_20251224.csv` is the scheduled-segment snapshot used by
  the reported experiments.

The exact service date, SHA-256 checksum, row count, stop count, and line count
for the timetable used in the paper are recorded in
[`paper/results/timetable_provenance.json`](../../../paper/results/timetable_provenance.json).
The released canonical JSON/CSV outputs remain inspectable without the raw
timetable, and the manuscript verifier checks all displayed numerical claims
against those artifacts.

Do not commit provider data, `.env` files, API keys, or other credentials.
Exact raw-input reproduction requires licensed Ekispert access and the authors'
input-edge inventory; obtain equivalent inputs only under the provider's terms.
