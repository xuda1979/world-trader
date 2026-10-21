# DATA_NOAA_HDDCDD — acquire US population-weighted degree-days axis

## Mission
Acquire a NEW raw data axis for the beat-the-champion goal: monthly US population-weighted heating/cooling degree-days (HDD/CDD, base 65F) — national + 9 climate regions — from NOAA NCEI Climate at a Glance (1895-2026, 1580 months per series, 20 series). This is weather-demand fundamental data for the natgas/energy complex; it is NOT covered by any existing axis (noaa_climate = ONI/NAO/MEI climate indices; cpc_dd = CPC drought monitor stub, no data).

## Inputs / on-disk data (verify yourself)
- None yet. Sources verified live 2026-10-08:
  - https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/{national,regional}/time-series/{110,101..109}/{hdd,cdd}/1/0/1895-2026/data.json
  - Weekly CPC files (wsaohdd*.txt etc.) exist but archive only ~4 weeks — NOT usable for history; excluded by design, noted here for provenance.

## Deliverable
- tools/quant/data/noaa_hddcdd/ containing:
  - hdd_monthly.csv — date,US,NE,UP,OH,SE,NO,SO,SW,NW,WE (10 cols; date YYYY-MM-01, 1895-01..2026-08)
  - cdd_monthly.csv — same layout
  - hddcdd_dl.py — downloader+parser (stdlib only, fail-closed)
  - test_hddcdd_dl.py — TDD pins (RED first)
  - manifest.csv, README.md (canonical layout per DATA_ORGANIZE)
- campaign/results/RAW_DATA_MANIFEST.csv re-emit (adds noaa_hddcdd axis, tree sha16 changes) + re-pin tests in campaign/bt/tests/test_raw_data_manifest.py
- FINDINGS.md entry + STANDUP_LOG.md round record
- Commits with EXPLICIT PATHSPECS only (staged champion trio must remain staged-unchanged)

## Rules (team contract — read campaign/team/docs/ORG.md)
- No browser; direct HTTP only for data. TDD RED->GREEN. Short code. Evidence before claims.
- Fail-closed lint: order, dupes, span completeness (1895-01..latest, zero missing months in span), plausibility (HDD/CDD >= 0, < 2000), value sanity vs known anchors (e.g. Jan national HDD ~ 1000, Jul national HDD ~ 15-20).
- Honesty gates: this is data acquisition only — NO signal claims. Any uncomputable check = FAIL.
- RAW_DATA_MANIFEST verify must pass before commit (fail-closed, exit 1 on drift).

## Done marker
Last line of FINDINGS.md exactly: DATA_NOAA_HDDCDD DONE
