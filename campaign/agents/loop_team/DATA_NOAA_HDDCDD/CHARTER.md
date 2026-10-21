# DATA_NOAA_HDDCDD — acquire US population-weighted degree-days axis

## Mission
Acquire a NEW raw data axis for the beat-the-champion goal: monthly US population-weighted heating/cooling degree-days (HDD/CDD, base 65F) — national + 9 climate regions — from NOAA NCEI Climate at a Glance (1895-2026, 1580 months per series, 20 series). This is weather-demand fundamental data for the natgas/energy complex; it is NOT covered by any existing axis (noaa_climate = ONI/NAO/MEI climate indices; cpc_dd = CPC drought monitor stub, no data).

## Inputs / on-disk data (verify yourself)
- None at charter time. Sources verified live 2026-10-08:
  - https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/{national,regional}/time-series/{110,101..109}/{hdd,cdd}/1/0/1895-2026/data.json (20/20 endpoints live, 1580 months each)
  - Weekly CPC files (wsaohdd*.txt) exist but archive only ~4 weeks of history — excluded by design; noted for provenance.

## Deliverable
- tools/quant/data/noaa_hddcdd/: hdd_monthly.csv + cdd_monthly.csv (date,US,NE,UP,OH,SE,NO,SO,SW,NW,WE; 1895-01..2026-08; 1580 rows each), hddcdd_dl.py (stdlib-only downloader+parser, fail-closed lint), test_hddcdd_dl.py (TDD pins, RED first), manifest.csv, README.md.
- campaign/results/RAW_DATA_MANIFEST.csv re-emit (86->87 axes, tree sha16 3a94f43736fd9737 -> d02c0d3050e3ffbc) + re-pin campaign/bt/tests/test_raw_data_manifest.py.
- FINDINGS.md + STANDUP_LOG.md round record.
- Commits with EXPLICIT PATHSPECS only (staged champion trio staged-unchanged).

## Rules (team contract — read campaign/team/docs/ORG.md)
- No browser; direct HTTP only for data. TDD RED->GREEN. Short code. Evidence before claims.
- Fail-closed lint: order, dupes, zero-gap span, plausibility (0<=v<2000), n>=300, span anchors (Jan-1895 US HDD=1006 byte-match to live source).
- Honesty gates: this is data acquisition only — NO signal claims. Any uncomputable check = FAIL.

## Done marker
Last line of FINDINGS.md exactly: DATA_NOAA_HDDCDD DONE
