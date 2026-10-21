# DATA_PULL FINDINGS — session 2026-09-08 (charter execution)

## Mission routing (evidence-based, no re-fetch)
Verified on disk BEFORE pulling (charter rule: check first). MAESTRO gap list
(campaign/team/docs/DATA_COVERAGE.md) is partially stale:
- Gap 1 CBOE VIX term structure: ALREADY ON DISK — more_vol/manifest.csv has VIX9D
  (3,939 rows 2011-01-04..2026-09-02), VIX3M (4,265), VIX6M (4,697), all lint PASS. Skip.
- Gap 2 CFTC COT financials: ALREADY ON DISK — more_cot/ has 106 csv incl. 52 TFF series
  (13 families x 4 categories, 2010-07..2026-08, session-3 pull). Skip.
- Gap 3 commodity futures: stooq_c5 + more_fut/STOOQ_BLOCKED.md record stooq.com blocked
  (JS gate, 3/3 probes 2026-09-03); FRED/EIA spot fallback already delivered
  (eia_weekly: brent RBRTEd 9,298 rows 1990..2026-09-01; natgas HH RNGWHHDd 5,265;
  wti RWTCd 10,236; plus 8 more daily spots, all lint ok). Skip.
- Gap 4 international curves: PARTIALLY OPEN — ECB AAA euro curve done (ecb_yc, 17
  tenors PASS), BoE done (3 curves, 47y), BUT cb_rates/ EMPTY and rba_bond/ had an
  abandoned RED test with no module, no data. THIS was the highest-value open lane. Pulled it.

## DELIVERED 1 — cb_rates/ (NEW family, Bank of Canada Valet, keyless direct HTTP)
TDD: RED (collection ImportError, cb_rates_dl absent) -> GREEN 7/7 (test_cb_rates_dl.py).
Parser bug caught by the run itself: urlopen(req, timeout) positional -> int landed in
data=; fixed to timeout=timeout, re-proved GREEN before fetching.
Endpoint probing (all keyless, direct urllib, UA 'Mozilla/5.0 (research; world-trader)'):
- valet/lists/groups + lists/series JSON: OK 200 (1,275,531 B series list)
- classic V39xxx benchmark codes: 404 except policy-rate family (V39076..79 = operating
  band low 2.20 / high 2.50 / bank rate 2.50 / target 2.25 on 2026-09-04 — coherent with
  published BoC policy corridor)
- marketable-bond avg yields found as CDN.AVG.1YTO3Y / 3YTO5Y / 5YTO10Y / OVER.10
- span test: start_date=1934 returns 6,420 obs but only from 2001-01-02; year windows
  1975/1991/1997/1998/1999/2000 all EMPTY -> honest available span starts 2001-01-02
- FXUSDCAD reachable but REDUNDANT (fx/USD_CAD.csv already on disk) -> skipped
- one full call returns all 6,420 obs (no pagination needed); start+end+recent=0 => 400
DELIVERED SERIES (CSV close-only, wide 2 cols; politeness sleep 1.0s between calls):
| symbol | code | span | n | max_gap | min..max | last |
|---|---|---|---|---|---|---|
| GOC_1_3Y | CDN.AVG.1YTO3Y.AVG | 2001-01-02..2026-09-03 | 6,420 | 5d | 0.14..5.14 | 3.09 |
| GOC_3_5Y | CDN.AVG.3YTO5Y.AVG | 2001-01-02..2026-09-03 | 6,420 | 5d | 0.25..5.55 | 3.39 |
| GOC_5_10Y | CDN.AVG.5YTO10Y.AVG | 2001-01-02..2026-09-03 | 6,420 | 5d | 0.35..5.87 | 3.64 |
| GOC_OVER10 | CDN.AVG.OVER.10.AVG | 2001-01-02..2026-09-03 | 6,420 | 5d | 0.52..6.12 | 4.10 |
| GOC_POLICY | V39079 | 2009-04-21..2026-09-04 | 4,520 | 5d | 0.25..5.00 | 2.25 |
ALL 5 lint PASS: 0 nans, 0 out-of-band, monotone, span_days 9,375 (yields) / 6,345 (policy).
Plausibility corroborated: 2020 COVID lows 0.14-0.52% and 2026 corridor 2.20-2.50 match
independent live probes. Independent re-verify from written files (not memory):
re-lint 5/5 PASS, cross-checked row counts vs canonical manifest 5/5 exact-match
=> REVERIFY: ALL_PASS. 25-year daily GoC yield buckets + policy rate = decade+ span,
decorrelated to existing US/FX/eq families (MAESTRO criterion).

## DELIVERED 2 — rba_bond/ (fail-closed: tests GREEN, zero data delivered)
Inherited an abandoned RED test (test_rba_dl.py, ImportError since 2026-09-07 session).
TDD: implemented rba_dl.py parser -> GREEN 6/6 (13/13 across both suites in one run:
'13 passed in 0.03s'). Root-caused 3 iterations, all visible in test output:
1. Title-row scan: rows are lists of whole CSV lines (flatten first), col names derive
   from 'Title,A$1=USD,...' tokens via '=([A-Z]{3})$' regex -> ['USD','CNY','JPY','TWI']
2. RBA intraday revision contract: 2 same-date prints legitimate, >2 = duplication;
   monotone rule must allow equal consecutive dates (b<a not b<=a)
3. Check order: plausibility BEFORE duplicate rule (6.55 print must report
   'plausibility', not 'duplicate')
Host probe (fail-closed): www.rba.gov.au HTTP 403 Forbidden on ALL 3 official paths
(f11.1-data.csv, f11-data.csv, xls-hist/2010-2026.xls), research UA AND full Chrome UA.
=> NO DATA DELIVERED (charter: fail-closed). rba_dl.py ready if block lifts.
Documented in rba_bond/RBA_BLOCKED.md; manifest carries explicit BLOCKED exception row
(rows=0). Prior-session F2.1 note (monthly-only) preserved in the test docstring.

## Probed and rejected this session (this environment, 2026-09-08)
- RBA (above): 403 host-level. BoC V39055..V39080 legacy benchmark codes: 404 (retired;
  CDN.AVG.* are the live equivalents). BoC V121761/V121762: 404. BoC start+end+recent=0
  combined: HTTP 400. rba.gov.au with Chrome UA: 403 (not a UA issue).

## Interlock notes (for MAESTRO / ORGANIZE / CLEAN)
- A parallel DATA_ORGANIZE session passed through mid-run (14:10): replaced my lint
  manifest with canonical format + scaffolded rba_bond/README. Reconciled: kept their
  canonical manifest.csv (5 series rows + manifest self-row, exact row-count match
  verified), lint detail preserved in cb_rates/manifest_lint.csv (my charter format),
  rba_bond/manifest.csv restored with explicit BLOCKED row. No data dirs overwritten.
- MAESTRO DATA_COVERAGE.md gap list should be updated: gaps 1-3 already satisfied;
  gap 4 now has ECB+BoE+BoC delivered, RBA blocked. 25y span on BoC (not 70y):
  Valet truncates CDN.AVG.* at 2001 — the 1934+ depth needs BoC offline archive
  (not reachable direct-HTTP), recorded here as the honest ceiling.

## Coverage of the charter's deliverable
tools/quant/data/cb_rates/: 5 lint-PASS daily series + manifest.csv + manifest_lint.csv
+ cb_rates_dl.py + test_cb_rates_dl.py (7 tests) + README.md (canonical, ORGANIZE).
tools/quant/data/rba_bond/: parser + 6 tests GREEN + RBA_BLOCKED.md + explicit-empty
canonical manifest. Zero existing dirs touched. No browser used anywhere.

DATA_PULL DONE
