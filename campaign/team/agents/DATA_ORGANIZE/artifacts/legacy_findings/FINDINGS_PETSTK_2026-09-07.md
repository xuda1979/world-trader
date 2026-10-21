# FINDINGS: EIA weekly petroleum STOCKS matrix — 2026-09-07

New-domain harvest continuing ITER12 (which took natgas storage + 3 petroleum
flows but NO stocks). The dnav weekly-stocks family is a PRODUCT x AREA matrix:
one XLS per area (US-wide + PADD 1A/1B/1C/2/3/4/5), each with ~26-39 product
columns, keyless at `www.eia.gov/dnav/pet/xls/PET_STOC_WSTK_DCU_<AREA>_W.xls`.

## DELIVERABLES (`eia_stockmatrix_dl.py`, reuses eia_dl CFB/BIFF parser)

- **192 tidy CSVs** (`petstk_<area>_<sid>.csv`), 0 lint failures, plus
  `manifest_stockmatrix.csv` (authoritative record: steady_from certification
  window per column, SKIP rows for irregular/discontinued columns).
- 13 new TDD tests? -> no: 2 new tests (`extract_matrix`), suite 11/11 green
  (13 -> 11 total including pre-existing; nothing removed).
- Domains unlocked: SPR weekly stocks (WCSSTUS1), commercial crude incl lease
  stock, gasoline family (RBOB/CBOB/EO blends), distillate 0-15ppm diesel +
  heating oil, jet kerosene, residual, propane — US + all 8 PADDs, weekly
  1982-08-20..2026-08-28 (most series 1990+).

## LINT DISCIPLINE (fail-closed, all verified live 2026-09-07)

- weekly natives: zero-gap tolerance, n>=52. Pre-1984 biweekly era excluded via
  steady_from=1984-01-01 (full history stays in CSV).
- 33 columns with a SINGLE skipped survey week (1990-11-30 / 1991-04-26 /
  1993-06-18 / 1985-12): data-driven rule certifies from week after their own
  first gap (no hand-listing).
- SKIP-irregular: WCRSTUS1 / WTESTUS1 / WTTSTUS1 (crude+products totals) —
  mixed 7/14/21/28d inter-arrivals at ALL eras; not a weekly series, cannot be
  certified honestly.
- SKIP-discontinued-2020-04: W_EPLLPZ family (propane/propylene by PADD; ends
  2020-04-03; superseded by WPRSTUS1 which passes).

## WHAT IT IS GOOD FOR (affordances, untested)

- SPR draw/release weekly = a STATE-ACTOR flow (1990s-2026: SPR fell
  ~700M->~360M bbl), never on disk; complements the already-dead price-only
  families.
- PADD-level stocks -> WTI/Brent & RBOB basis/regional-spread engines; crude
  and gasoline DAYS-OF-SUPPLY (stocks / products-supplied, both now on disk).
- Crack-spread engines (ITER12 affordance): gasoline/distillate STOCKS plus the
  daily spots harvested earlier give inventory-adjusted margin signals.
- Contango/inventory regime: stocks level+z vs curve shape (CL calendar).

## PROBES AND REJECTED (2026-09-07, this environment)

- FINRA margin-debt page: HTML renders but their api.finra.org data endpoints
  are 307 redirect loops (WAF) -> US margin debt NOT obtainable (the CN
  Eastmoney analog stays CN-only).
- AAII sentiment xls/sent_results: 403. ICI money-market xlsx: 403. OFR bank
  stress index API: 403. Baker Hughes rig xlsx: read timeout. NYSE cdn margin
  csv: DNS fail. Nasdaq biweekly short-interest api: 404. KRX global: 403.
- CFTC fut_txt zip: 404 at the guessed path (COT already on disk anyway via
  publicreporting.cftc.gov Socrata).
- policyuncertainty.com US EPU monthly CSV: **OPEN** (1,521 rows, 1900-02 ->
  2026-08) — candidate for a later hunt if wanted (monthly freq is the
  constraint; several EPU-like FRED series already dead in DEAD_IDEAS).
- JPX investor-flow xlsx: per-month files, low value-per-fetch; skipped.
