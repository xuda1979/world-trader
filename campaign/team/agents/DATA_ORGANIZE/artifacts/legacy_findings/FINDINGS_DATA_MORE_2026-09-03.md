
---

# SESSION 2 — 2026-09-03 (goal re-armed): sovereign curve expansion

## 5. Japan MoF JGB curve — NEW dir mof_jgb/ (1974→2026, 15 tenors)
- jgb_curve.csv: 13,290 daily rows, wide format date + 1Y..40Y (%), 1974-09-24..2026-08-31
- Source: mof.go.jp historical jgbcme_all.csv (1.2MB full history; the non-historical path 404s)
- TDD'd parser jgb_dl.py (10 tests GREEN): '-' = pre-issue tenor -> None; plausibility band [-1,11]%
- Era-gated lint (new semantics, test-locked): pre-steady suspensions documented not failed —
  1Y steady from 1980-08, 2Y from 1979-08, 3Y from 1978-08 (MoF debt-mgmt regime change);
  10Y starts 1986, 30Y 1999, 40Y 2007. All 15 tenors PASS (steady gaps <= 25d).

## 6. Bank of England curves — NEW dir boe_curve/ (3 families, 1979→2026)
Downloaded official archive zips (glcnominalddata/glcrealddata/oisddata ~110MB total):
- gilt_nominal_spot_daily.csv: 12,415 days (1979-01→2026-07), 79 tenors 1y-40y quarter-grid,
  ZERO missing bdays across 47 years. Spot curve nominal gilts.
- gilt_real_spot_daily.csv: 10,869 days (1985-01→2026-08), 73 tenors 4y-40y (month-grid).
- ois_sonia_spot_daily.csv: 4,605 days (2009-01→2026-08), 94 tenors (0.5y-25y) GBP OIS/Sonia
  swap curve. Long format: date,maturity_years,yield_pct,family.
- TDD'd parser boe_dl.py (11 tests GREEN). Engineering notes:
  * sheet name varies by family ("4. spot curve" / "4. nominal spot curve" / "2. spot curve") —
    auto-picker with deterministic preference, fail-closed if none
  * real/inflation xlsx carry Excel FORMULAS in maturity row — need data_only=True (cached vals)
  * month-grid maturities (2.0833y=2y1m) snap to 1/12-year grid (0.25-snap would COLLIDE columns)
  * EXCLUDED fail-closed: 0.5y nominal (chronic 55-182d seasonal gaps all 47y = publication
    cadence), OIS sub-0.5y stubs, real-family tenors<4y (chronic 400-600d holes: BoE fitting
    policy changes 1996/2005/2018 — not renames)

## Honest negatives (session 2)
- Bank of England IADB REST API (iadb.prod...): timeout/000 from this host
- policyuncertainty.com data files: /data/*.xlsx and World_Policy_Uncertainty_Data.csv -> 404
- CBOE put/call (from session 1): still 403, not retried

## Cumulative totals (both sessions today)
- JGB curve: +1 dataset (13,290 x 15 tenors, 52 years)
- BoE curves: +3 datasets (47y nominal, 41y real, 17y OIS-Sonia; ~246 tenor-series combined)
- Plus session 1: 17 COT markets, 7 FRED series, 30 ECB FX crosses = 54 series

---

# SESSION 3 — 2026-09-03 (goal re-armed again)

## 7. CFTC TFF trader categories — 52 NEW series (OFFLINE)
more_cot/: new TFF parser cot_parser_tff.py (5 tests) + build_cot_tff.py -> tff_<fam>_<cat>.csv
- 13 financial families x 4 categories (Dealer / Asset_Mgr / Lev_Money / Other_Rept):
  sp500_emini, nasdaq_emini, dow_emini, us_2y/5y/10y notes, us_tbond, eur, jpy, gbp,
  eurodollar_3m (to 2023-06), sofr_3m (2018+), vix. 2010-07..2026-08 weekly, ALL PASS.
- Structure confirmed: disagg zips = 22 commodity families (M_Money), fin zips = TFF financial
  categories. The split is CFTC-program-level, not a fetch gap. Net-of-cat signal families
  (dealer vs asset-mgr flows) now available for the whole rates/index/FX complex.
- 5 tests incl. fail-closed header/row semantics + priority collisions (0 in TFF block).

## 8. ECB euro-area AAA par-yield curve — NEW dir ecb_yc/
- ecb_eur_yc_aaa.csv: 17 tenors (3M..30Y), 2004-09-06..2026-09-02, 5,622 days each, ZERO
  steady-era gaps, ALL PASS. Keyless data-api (YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_*).
- Completes the euro fixed-income block alongside the 30 ECB FX crosses.

## 9. NOAA climate indices — NEW dir noaa_climate/ (3 series, 1950+/1979+)
- oni.csv (ENSO 3.4 SST anomaly, 3M seasons, 1950+), nao.csv (1950+), meiv2.csv (1979+).
- Monthly zero-gap lint PASS all. Regime covariates for the new ags/softs COT families.

## 10. US Treasury auction demand — NEW dir treasury_auctions/
- tauctions.csv: 7,852 auctions 2000-01..2026-09 (Bill 5,808 / Note 1,687 / Bond 357),
  bid_to_cover 7,845; direct/indirect bidder accepted 2010+.
- Era facts: btc empty pre-2000 upstream; TIPS/FRN rows carry no btc (excluded by lint
  implicitly via None); 5 known TA-WS keying defects (4W bills 2011-12/2015, btc 9-10.7,
  total_accepted=None) DROPPED; COVID real demand spikes 4.1-6.5 RETAINED (band [0.8,8]).

## Session 3 totals: 52 TFF + 17 ECB YC + 3 climate + 1 auction panel = 73 new series/files
## Cumulative (3 sessions): 54 + 4 curve datasets + 73 = 130+ new series/files, all lint PASS

---

# SESSION 4 — 2026-09-03 (loop iteration, /loop every 10m active)

## 11. FRED macro-core batch 2 — 10 NEW series (more_fred/ 25->47 on-disk series)
- JTSJOL (job openings, 2000+), JTSQUR (quits rate, 2000+) — JOLTS labor-flow family
- GFDEGDQ188S (federal debt/GDP, quarterly verified zero-gap, 1966+)
- MORTGAGE30US (30y mortgage, 1971+, Fri-cadence verified: no gap >10d)
- RIFSPPFAAD01NB (1m term repo SOFR-adjacent, era-gated 2013-03+; 1998 pre-era 6d hole)
- T10Y3M (10y-3m term spread, 1982+, the classic recession covariate)
- NFCICREDIT + NFCIRISK (NFCI credit/risk subindices, 1971+, zero gaps)
- STLFSI4 (St.Louis financial stress, 1993+, zero gaps; deduped against newdata copy)
- TEDRATE (FULL 1986-01..2022-01: all 66 short runs VERIFIED as interbank fixing-calendar
  holidays — JP fiscal YE/Easter/UK May bank hol+2012 Jubilee/GW/Xmas — via window test
  `outside=[]`; discontinued upstream 2022-01 documented)
- Honest negatives: LNS12300000 + BAVALLMAT + HQM + SOFR30DAYVOL HTTP400; U6RATE +
  A191RL1A225NBEA rejected by zero-gap monthly lint (real upstream holes) — not force-written.
- STOOQ still JS-challenge blocked (proof-of-work); documented again, not retried further.

## Session 4 totals: +10 series (FRED macro-core batch 2)
## Cumulative (4 sessions): ~140 new series/files, all lint PASS, 71 tests green across 9 suites

---

# SESSION 5 — 2026-09-03 (loop iteration 2)

## 12. CFTC CIT (Commodity Index Traders) supplemental — 13 NEW series
more_cot/_raw_cit/ (17 annual zips 2010-2026, correct path /files/dea/history/dea_cit_txt_YYYY.zip —
fut_cit_txt naming was wrong) + cit_parser.py (5 tests) + build_cit.py:
- 13 ags/livestock families with CIT net + pct-of-OI: cocoa, coffee_c, corn, cotton_no2,
  feeder_cattle, lean_hogs, live_cattle, soybean_meal (2013+), soybean_oil, soybeans,
  sugar_no11, wheat_hrw (2013+), wheat_srw. ALL PASS (0 collisions).
- CIT = the classic long-only index-flow family ( Roll-style); now separable from
  noncommercial nets for the ags complex. Financials don't have CIT (CFTC program scope).
- 30 COT-suite tests green after changes.

## Session 5 totals: +13 CIT series (+17 raw zips archived)
## Cumulative (5 sessions): ~153 new series/files, all lint PASS, ~101 tests across 10 suites

---

# SESSION 6 — 2026-09-03 (loop iteration 3)

## 13. BIS broad effective exchange rates — NEW dir bis_eer/ — 55 series
- Bulk route found (data.bis.org /static/bulk/WS_EER_csv_flat.zip 6.6MB; SDMX api v1/v2 404;
  bis.org direct files 404). Extracted for 20 ccys (US EA JP GB CA AU CH SE NO CN IN BR RU ZA MX KR SG HK TR PL):
  * NEERD: 19 daily series 1996-04-11..2026-09-01 (~7,929 obs each, zero gaps; RU 1998+)
  * NEERM: 20 monthly backfill 1994-01+ (n=391 each)
  * REERM: 20 monthly REER 1994-01+ (real effective = inflation-adjusted competitiveness)
- TR excluded fail-closed (NEERD 22 gaps + stops 2025-03 upstream; NEERM 25 gaps).
- Bug found+fixed en route: first pass collapsed BIS daily NEER onto month-starts (mixed
  frequencies); caught via n=8062 sanity check (monthly would be ~391). Stale 37 CSVs removed.
- BIS broad basket = 64 economies, time-varying trade weights, 2020=100. This is the
  currency-competitiveness family the 30 bilateral ECB crosses don't cover.

## 14. FRED global rates + commodity monthly — 11 NEW series (more_fred 47->58)
- MCOILWTICO + MHHNGSP (monthly WTI/Henry Hub, zero gaps), GASPRICE (1993-2014 discontinued)
- OECD LT bond yields monthly: US (1953+), DE (1956+), JP (1989+), GB (1960+), CA (1955+),
  AU (1969+), CH (1955+), KR (2000+) — 8 series, all zero-gap. Cross-country rate-cycle panel.
- Honest negatives: CN LT yield not on FRED; DSGWPI/WGRPLC/IR3TIBMDM01XX HTTP400.

## Session 6 totals: +55 BIS EER + 11 FRED = 66 series
## Cumulative (6 sessions): ~219 new series/files, all lint PASS

---

# SESSION 7 — 2026-09-03 (loop iteration 4)

## 15. OECD MEI cross-country CPI panel — 13 NEW series (more_fred 58->71+4)
- CPALTT01xxM657N x9 (US JP DE GB FR IT CA KR CN monthly CPI index, 1955->vintage-end ~2024):
  OECD MEI vintage LAGS ~2y by design — documented in manifest, long-window-regime use only.
- Current-vintage: CP0000EZ19M086NEST (EA HICP 1996->2026-07, current), JPNCPIALLMINMEI
  (1955+, discontinued 2021 vintage), GBRCPIALLMINMEI (1955->2025-03), UNRATENSA (1948->current;
  the SAME documented 2025-10 upstream hole as UNRATE — accepted with evidence note, not
  force-filled). CPIAUCSL/INDPRO deduped against existing block.
- Honest negatives: AU OECD CPI not on FRED; IMF-style IDs exist but same vintage lag; PROINDMISEA 400.

## Session 7 totals: +13 series
## Cumulative (7 sessions): ~232 new series/files; more_fred manifest now 75 series

---

# SESSION 8 — 2026-09-03 (loop iteration 5)

## 16. IMF PCPS primary commodity prices — 23 NEW series (more_fred -> ~98 manifest rows)
- Metals x7 (copper/aluminum/nickel/zinc/tin/lead/iron ore), ags/softs x10 (wheat-HRW/maize/
  soybeans/sunflower-oil/palm-oil/sugar-U-SA/coffee/cocoa/cotton/tea), livestock x2 (beef 2010+,
  pork), rice x1 (2010+), energy x3 (EU-TTF gas, JP-LNG, iron-ore-adjacent) — all monthly
  1992->2026-07, ZERO gaps, $-denominated global benchmark prices.
- ID archaeology: 10 HTTP400 probes corrected via PCPS naming (PWHEAMTUSDM not WHEAT_US_HRW,
  PMAIZMTUSDM not MAIZE, PSUGAUSAUSDM not PSUGAUSDM, PNGASJPUSDM...). Soybean meal/oil +
  coal + DAP/potash/urea + LNG-US + chicken not on FRED PCPS (documented negatives; the
  missing ones exist on IMF dataportal but behind their API, not free-FRED).
- This completes the fundamental-leg for the ags COT + NOAA climate families: positioning x
  weather-regime x global spot price, all monthly-lint PASS.

## Session 8 totals: +23 series
## Cumulative (8 sessions): ~255 new series/files

---

# SESSION 9 — 2026-09-07 (claude session, free-data expansion)

## 17. FRED batch-3 — 16 NEW series (more_fred/ manifest 98->114 lines)
- DPROPANEMBTX propane Mont Belvieu DAILY 1992-07..2026-09 n=8559 — UNBLOCKS the
  DEAD_IDEAS row 'propane, blocked, data missing' (that row referenced the old
  DPROPANEMTXCF id which HTTP400s; correct id is DPROPANEMBTX).
- CMT curve completion: DGS1 DGS3 DGS5 DGS7 (1962/1969+), DGS20 (era-gated 1993+ —
  7y pub hole 1987-1993), DGS1MO (2001+), DGS3MO DGS6MO (1981+). Daily curve panel
  now 1MO..30Y continuous.
- Labor: CCNSA continued claims weekly 1967+ (ICSA was already in newdata/, now in
  more_fred too for the linted manifest).
- Macro: PCEPI + PCEPILFE monthly 1959+ (the Fed's target inflation gauge — was missing).
- Policy: DFEDTARU 2008+ + IORB 2021+ (upper target / IORB corridor).
- PPI: WPU0911 nat-gas wellhead 1926+ + WPU0561 gold ores 1947+ (legacy long-window).
- All lint PASS, appended to manifest.csv with roles.

## 18. newdata/ repair — 4 HTML-corrupt files replaced, 1 id fix
- BAMLC0A1CAA / BAMLC1A01308B / DPROPANEMTXCF / DPUFUEUS2M contained 546 lines of
  HTML (failed fetch saved as .csv). REMOVED.
- Replaced with real ids: BAMLC0A1CAAA (AAA OAS, daily 2023-09+ FRED-span cap),
  GASDESW (diesel weekly 1994+), DDFUELUSGULF (ULSD Gulf daily 2006+).
- Refreshed BAMLC0A0CM + BAMLH0A0HYM2 (IG/HY OAS) to 2026-09-03.
- NOTE: BAML* OAS family on FRED starts 2023-09 only — confirms DEAD_IDEAS row 41
  ('BAML OAS daily as 2008+ signal, blocked: data starts 2023-09'). NOT unblockable
  via FRED; ICE 2008+ history is license-only.

## 19. SEC Fails-to-Deliver — NEW dir sec_ftd/ (in progress)
- TDD'd parser ftd_parser.py (12 tests GREEN under pytest + stdlib runner).
- Archive: https://www.sec.gov/files/data/fails-deliver-data/cnsfails<YYYYMM>{a,b}.zip
  starts 2017-08 (bisected: 201706 404, 201708 OK). ~9y x 2 files.
- Fetcher build_ftd.py: serial throttled 7s/file + 20/40/60/80s backoff on 429,
  fail-closed (no output on any hole), aggregates to ftd_daily.csv
  (date, n_issues, total_fails, total_notional_usd). Running in background.

## Honest negatives (session 9)
- Yahoo Finance v8 chart API: 403 for ALL symbols incl with repo's curl UA —
  wt/options_rviv.py yahoo_history() is silently broken (returns []).
- TwelveData: all index symbols (^N225 N225 SHCOMP 600519.SSE GSPC) 404/400.
- Finnhub stock/candle: 403 premium-only now.
- AlphaVantage TIME_SERIES_DAILY outputsize=full: premium-gated.
- quotes.money.163.com (CN A-share): 502 from this host.
- BoC valet API: 400/404 all syntaxes. Bundesbank: connection reset. RBA: 403.
  FINRA API: 307 -> error.waf.finra.org (WAF). USDA quickstats: 401 needs key.
  OFR FSI csv: 404. MoF Japan weekly flows: 404 (page restructured).
- SNB devkum cube: live but is FX NEER indices -> dedupe vs BIS EER, skipped.
- FRED rejected (real upstream holes, not force-filled): DGS20 pre-1993,
  DHHNGSP pre-2006 (10d hole @2005-09), WALCL (4d hole 2002), DCOILBRENTEU
  (two 3bd Christmas holes 1999+2018 — unfixable by era-gate), DEXBZUS pre-1996.
