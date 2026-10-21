# FINDINGS — DATA_VALUABLE (2026-09-03)

Mission: acquire CBOE vol/sentiment indices + CFTC COT positioning + commodity futures.
Method: direct urllib HTTP ONLY (no browser, per permanent user boundary). TDD for the COT parser
and market matcher (RED observed before each implementation; Red-Green regression on the one real
parser bug). Fail-closed lint every series. All numbers below quoted from fresh verification runs.

## DELIVERED: 29 new free data series (11 CBOE/FRED vol + 18 COT weekly), all lint PASS

### A. CBOE vol/sentiment — tools/quant/data/more_vol/ (11 series, lint PASS)
Source: https://cdn.cboe.com/api/global/us_indices/daily_prices/<SYM>_History.csv (direct urllib).
Columns: date,open,high,low,close (close-only files have o=h=l=c). Weekly release cadence: none (daily).

| symbol | n | span | span_days | max_gap | min | max | last (2026-09-02) |
|--------|------|------|-----------|---------|-----|-----|------|
| SKEW  | 9219 | 1990-01-02..2026-09-02 | 13392 | 13d | 101.23 | 183.12 | 144.12 |
| VIX   | 9264 | 1990-01-02..2026-09-02 | 13392 | 7d | 9.14 | 82.69 | 15.20 |
| VIXMO | 9229 | 1990-01-02..2026-09-02 | 13392 | 7d | 8.68 | 82.53 | 15.44 |
| VIX9D | 3939 | 2011-01-04..2026-09-02 | 5720 | 5d | 7.10 | 106.66 | 12.57 |
| VIX3M | 4265 | 2009-09-18..2026-09-02 | 6193 | 5d | 11.85 | 72.98 | 17.73 |
| VIX6M | 4697 | 2008-01-02..2026-09-02 | 6818 | 5d | 13.75 | 61.47 | 20.36 |
| VVIX  | 4946 | 2007-01-03..2026-09-02 | 7182 | 5d | 59.74 | 207.59 | 86.25 |
| RVX   | 4262 | 2009-09-16..2026-09-02 | 6195 | 5d | 11.83 | 83.19 | 19.45 |
| OVX   | 4263 | 2009-09-18..2026-09-02 | 6193 | 5d | 14.50 | 325.15 | 47.77 |
| GVZ   | 4263 | 2009-09-18..2026-09-02 | 6193 | 5d | 8.88 | 48.98 | 26.14 |
| VXV   | 4715 | 2007-12-04..2026-09-01 | 6846 | — | 11.85 | 72.98 | 18.33 |

NOTE: VXV MUST come from FRED (more_fred/VXVCLS.csv, already on disk) — the CBOE CDN file
VXV_History.csv is a BOGUS 23-row stub (2017-09-19..2017-10-19 only, n=23, 492B). Charter fallback
used. Full term structure now on disk: 9d/30d(VIX)/3m/6m + VVIX + SKEW + RVX/OVX/GVZ sector vols.
NaNs=0, monotone dates=TRUE, out-of-range=0 for ALL 11.

### B. CFTC COT — tools/quant/data/more_cot/ (18 weekly series, lint PASS)
Sources (direct urllib, 34 zips, 2010..2026): fut_disagg_txt_YYYY.zip (commodities, 17 files)
+ fut_fin_txt_YYYY.zip (financial TFF, 17 files). Columns per file: date,net_noncomm,
net_noncomm_pct_oi,open_interest. WEEKLY (Tue report date); NOT daily.
"noncomm" = M_Money (disagg) / Lev_Money (TFF). Parser: cot_parser.py; matcher: cot_matcher.py;
builder: build_cot.py. REBUILD BYTE-REPRO: 18/18 CSVs sha256-identical, exit 0.

| family | weeks | span | OI range | net_pct_oi range |
|--------|-------|------|----------|------------------|
| crude_wti_nymex | 869 | 2010-01-05..2026-08-25 | 1,214,183..2,706,454 | -0.020..+0.205 |
| nat_gas_nymex | 869 | 2010-01-05..2026-08-25 | 320,266..1,668,101 | -0.231..+0.187 |
| gold | 869 | 2010-01-05..2026-08-25 | 326,052..796,883 | -0.235..+0.456 |
| silver | 869 | 2010-01-05..2026-08-25 | 95,684..244,196 | -0.230..+0.448 |
| copper | 869 | 2010-01-05..2026-08-25 | 112,374..333,951 | -0.273..+0.392 |
| sp500_emini | 841 | 2010-07-20..2026-08-25 | 1,879,423..4,554,164 | -0.255..+0.053 |
| nasdaq_emini | 841 | 2010-07-20..2026-08-25 | 177,937..597,830 | -0.315..+0.375 |
| dow_emini | 841 | 2010-07-20..2026-08-25 | 50,161..176,108 | -0.306..+0.518 |
| jpy | 841 | 2010-07-20..2026-08-25 | 90,072..520,825 | -0.452..+0.392 |
| eur | 841 | 2010-07-20..2026-08-25 | 146,781..986,986 | -0.399..+0.326 |
| gbp | 841 | 2010-07-20..2026-08-25 | 67,820..392,591 | -0.420..+0.545 |
| us_tbond | 841 | 2010-07-20..2026-08-25 | 403,170..2,245,352 | -0.374..+0.108 |
| us_10y_note | 841 | 2010-07-20..2026-08-25 | 1,318,394..6,254,472 | -0.485..+0.291 |
| us_5y_note | 841 | 2010-07-20..2026-08-25 | 881,044..7,476,821 | -0.528..+0.338 |
| us_2y_note | 841 | 2010-07-20..2026-08-25 | 645,108..4,960,871 | -0.598..+0.362 |
| eurodollar_3m | 674 | 2010-07-20..2023-06-13 | 511,711..17,721,954 | -0.283..+0.193 |
| sofr_3m | 422 | 2018-07-24..2026-08-25 | 8,817..14,100,241 | -0.227..+0.603 |
| vix | 841 | 2010-07-20..2026-08-25 | 84,826..704,831 | -0.426..+0.188 |

eurodollar_3m ENDING 2023-06-13 IS REAL (contract reporting wound down with SOFR transition),
not a gap. All series: max weekly gap 8d (sofr_3m 14d at launch), OI>0, |net|<=OI, pct in [-1,1].

### C. Commodity futures continuous — BLOCKED, logged, skipped
Stooq cl.f/ng.f/gc.f: 3/3 returned 796B HTML JS-gate (no CSV). See more_fut/STOOQ_BLOCKED.md.

## FAILURES / HTTP codes (exact)
- CBOE 403 (4): VXFLS, FTP, SKET, HESKW (do not exist at CDN).
- CBOE CDN VXV: 200 but bogus stub (23 rows) -> replaced by FRED VXVCLS.
- One transient DNS gaierror on cftc.gov (resolved on retry; all 34 zips fetched, 0 final failures).

## BUGS FOUND BY TDD + LINT (root-cause documented)
1. cot_parser parse_row returned None on real WTI fixture. ROOT CAUSE: `replace("", "0")` on the
   short field inserts '0' between every char -> int() raises -> fail-closed None. RED observed,
   fixed to `replace(",", "")`, RED->GREEN->revert-RED regression run (revert fails at
   test_disagg_row, restore passes).
2. v1 COT series POLLUTED by substring matching (caught by lint/jump audit, systematic-debugging):
   - crude 2022+ rows were ICE-EU WTI (NYMEX renamed to WTI-PHYSICAL 2022-02); 869 rows mixed exchanges.
   - nat_gas OI range 13450..6.8M: ICE basis pipelines mixed in.
   - indexes mixed full-size/micro/Consolidated contracts; jpy/eur mixed cross-rates; sofr mixed ERIS swaps.
   FIX: exact full-name matcher (cot_matcher.py) encoding CFTC rename history; 12 negative tests pin
   the pollution cases to None. All rename boundaries verified year-by-year from the zips themselves.
3. Feb-2022 batch rename recovered: CRUDE OIL LIGHT SWEET->WTI-PHYSICAL, NATURAL GAS->HENRY HUB,
   10-YEAR U.S. TREASURY NOTES->UST 10Y NOTE (etc.), NASDAQ-100 (MINI)->NASDAQ MINI, E-MINI S&P 500
   STOCK INDEX->E-MINI S&P 500. Copper grade variant (COPPER-GRADE #1) + GBP (BRITISH POUND STERLING)
   + EURODOLLARS-3M post-2022 variants added after audit (TDD RED first).
4. 2018-2021 natgas DUAL LISTING (same zip, same dates): NATURAL GAS (physical) and HENRY HUB
   (financial) coexist -> 186 collisions; resolved by explicit priority (physical kept, rank test);
   rebuild byte-repro confirms determinism. natgas continuity: max week-over-week pct jump 0.087.
5. CBOE plausibility gates initially failed 3 series; root-cause per series: OVX 325.15 @2020-04-21
   REAL (WTI May-2020 settled -$37.63 on 04-20; spike 95.91->226.13->325.15->236.80 coherent);
   VIX9D 7.10 REAL (2017 calm); VVIX 2006 PILOT DATA (n=150, 21d gaps, min 15.71 never seen again)
   -> trimmed VVIX at 2007-01-01 (documented in cboe_lint.py), OVX cap 350, VIX9D floor 7.

## TESTS (TDD, all fresh-run GREEN)
- test_cot_parser.py: 5 tests (real 2024 WTI fixture, legacy MM/DD/YYYY dates, TFF Lev_Money,
  malformed->None). RED observed first (ModuleNotFoundError, then 2 assertion REDs).
- test_cot_matcher.py: 12 tests incl. 25 negative pollution cases + priority ranking. RED first.
- test_cboe_sanity.py: 3 tests (OHLC format, close-only format, malformed drop). RED first.
- Total 20 tests, all PASS in final fresh run. COT rebuild: 18/18 sha256 byte-identical.

## USAGE NOTES FOR COORDINATOR
- Term-slope engines: VIX9D/VIX/VIX3M/VIX6M (+VXV) all daily 2007+ (9d from 2011). HUNT_VXV_TERM
  family can now use the full curve (prior hunt had only VIX+VXV).
- COT is WEEKLY: join as-of Friday report date, no lookahead before Tue release.
- VVIX starts 2007 (2006 pilot trimmed), VIX9D starts 2011, sofr_3m 2018; everything else 2010+.
- more_vol CSVs: date,open,high,low,close; more_cot CSVs: date,net_noncomm,net_noncomm_pct_oi,open_interest.
- Raw zips kept in more_cot/_raw (34 files) and more_vol/_raw (10 files) for re-parse.
