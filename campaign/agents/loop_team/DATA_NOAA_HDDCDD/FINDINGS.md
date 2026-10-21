# DATA_NOAA_HDDCDD — FINDINGS

## Result
NEW data axis acquired and certified: `tools/quant/data/noaa_hddcdd/` — monthly
US population-weighted heating/cooling degree-days (base 65F), national + 9
climate regions, 1895-01..2026-08 (1580 months/series, 20 series, zero gaps).

## What was built
- `tools/quant/data/noaa_hddcdd/hdd_monthly.csv` (74921 B, sha256-16 0be7aa2620a76e52)
- `tools/quant/data/noaa_hddcdd/cdd_monthly.csv` (63859 B, sha256-16 f658bcdcdda3dcaa)
- columns: date,US,NE,UP,OH,SE,NO,SO,SW,NW,WE (US=CONUS national; NE=Northeast,
  UP=Upper Midwest, OH=Ohio Valley, SE=Southeast, NO=Northern Rockies-Plains,
  SO=South, SW=Southwest, NW=Northwest, WE=West)
- `hddcdd_dl.py` — stdlib-only downloader/parser, fail-closed lint (order, dupe,
  zero-gap span, plausibility 0<=v<2000, n>=300)
- `test_hddcdd_dl.py` — 9 TDD pins, observed RED first (ModuleNotFoundError, then
  lint-order assertion RED), fresh-run GREEN 9/9
- `manifest.csv`, `README.md` (canonical layout per DATA_ORGANIZE)

## Source provenance
- NCEI Climate at a Glance JSON endpoints (national code 110 + regional 101..109,
  hdd/cdd), verified live 2026-10-08, 20/20 endpoints OK, 1580 months each.
- Weekly CPC files (wsaohdd*.txt) inspected and EXCLUDED by design: archive
  retains only ~4 weeks of history; unusable for backtest spans.
- License: US public domain. Update cadence: monthly (~2wk lag).

## Verification evidence
- lint: 20/20 series zero-gap, ordered, plausible; span 1895-01..2026-08.
- Independent live cross-check post-build: re-fetched national HDD, compared all
  1580 months against stored CSV: **0 mismatches**.
- Anchor: Jan-1895 US HDD = 1006 (byte-match to live source sample).
- RAW_DATA_MANIFEST re-emit: 87 axes / 11756 files, tree sha16
  3a94f43736fd9737 -> **d02c0d3050e3ffbc**; --verify GREEN (byte-identical).
- Re-pinned campaign/bt/tests/test_raw_data_manifest.py (86->87 axes,
  11750->11756 files, new tree sha16); pytest 6/6 GREEN.

## Novelty check
- DEAD_IDEAS.csv: no HDD/CDD/degree-day rows. Existing axes: noaa_climate =
  ONI/NAO/MEI (climate indices, not demand); cpc_dd = CPC drought monitor stub
  (manifest has zero data rows). C5_newdata history has no weather-demand
  coverage. This axis is genuinely NEW on disk.

## Usage notes for coordinator
- MONTHLY data; joins as-of month-start with ~2wk publication lag — T+1 gate
  means a month M signal is tradeable only after NCEI posts (mid-M+1); as-of
  join must use posting convention, not month-start.
- Nat-gas complex relevance: HDD deviation-from-seasonal, cumulative
  surplus/deficit vs normal, CDD summer variant for power/gas cooling demand.
- Regions allow population-weighted demand composition (NE/UP/OH heavy heating).
- Suggested next step: pre-registered weather-demand hunt charter under honesty
  gates (natgas complex tilt; windows: HDD-dev z-score, cumulative surplus,
  CDD summer variant). NOT started here — acquisition charter scope only.

DATA_NOAA_HDDCDD DONE
