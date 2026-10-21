# DATA_FXHIST FINDINGS (2026-09-08)

## Deliverable
tools/quant/data/fx_hist/ — 552-pair FX cross-rate matrix (date,close), 1999-01-04..2026-09-07,
from ECB reference rates (direct HTTP, no key, no browser) + same-publisher SDW splice.
Charter universe: 21/22 charter currencies delivered (TWD not published by ECB — documented);
CNY included (charter "etc."). charter target list AUD,NZD,JPY,GBP,CHF,CAD,ZAR,INR,BRL,TRY,SEK,
NOK,DKK,PLN,HUF,CZK,SGD,HKD,KRW,TWD,THB,MXN -> all present except TWD (source omission).

## TDD evidence (RED -> GREEN)
- RED: campaign/team/tests/test_data_fxhist.py 5/5 FAILED (builder absent, FileNotFoundError).
- GREEN final: 6/6 PASSED in 9.75s (pytest campaign/team/tests/test_data_fxhist.py), pins:
  end-to-end build (EUR_USD start 1999-01-04, 7087 rows, all positive/NaN-free);
  cross-identity EUR_GBP*GBP_USD==EUR_USD (max abs diff < 1e-9, 7087 inner-joined rows);
  coverage+span (9 majors start <= 1999-01-31); manifest rows==recomputed CSV stats for
  EUR_USD/TRY_USD/SGD_JPY; lint fail-closed (negative rate -> exit 1);
  SDW splice extends USD_BRL/USD_INR to 2000-01-13 with exact-overlap seam.

## Checks with exact numbers
1. Source reachability: GET eurofxref-hist.zip -> HTTP 200 application/zip, 638,684 bytes;
   inner CSV 1,919,595 bytes, 7087 rows x 42 currencies, 1999-01-04..2026-09-07.
2. Volume: 552 pairs = 24x23 ordered matrix (TWD absent). Rows: min 6820 / median 7087 / max 7087.
   max_gap = 5 calendar days for ALL 552 pairs (weekends + Good Friday only; no data holes).
   420/552 pairs start exactly 1999-01-04 (21 full-history currencies x 20 partners).
3. Gaps/lint (fail-closed, exit 1 on any): nonpositive/NaN rates; gap > 10 days; cross-identity
   vs ECB (recomputed q_quote/q_base from the same zip) tolerance 5e-5. Negative probe: planted
   close=0.0 in EUR_USD -> "LINT FAIL (2 problems)" exit 1 (independent of pytest).
4. Cross-identity: EUR_GBP x GBP_USD vs EUR_USD max |diff| = 4.7e-7 BEFORE precision fix
   (storage round(6)); 0.0 < 1e-9 after storing full float precision -> fix kept.
5. Historical spot checks (all match public record): EUR_USD 2000-10-26 0.8252 (record low
   ~0.83); EUR_USD 2008-07-15 1.5990 (pre-GFC ATH ~1.60); USD_JPY 2011-10-31 78.009
   (intervention zone 75-79); GBP_USD 2016-06-24 1.37040 (Brexit day close ~1.3679-1.3741);
   USD_CHF 2011-08-11 0.74235 (SNB-panic low ~0.71-0.79); USD_TRY 2018-08-10 6.0500 (crisis,
   ~6.0+); USD_ZAR 2001-12-21 12.4500 (crisis 12-13).
6. Independent-source comparison vs existing market data tools/quant/data/fx/ (2019+ overlap):
   median ratio ECB/market = 0.99976 (USD_JPY), 1.00023 (EUR_GBP), 0.99992 (AUD_USD);
   same-day daily-log-return corr 0.589/0.606/0.535. Diagnosed, not a data bug: ECB is the
   14:15 CET single fix; market file is a late intraday close. corr with market lagged +1 day
   is 0.403-0.435, +/-2 days ~0 -> dates are correctly aligned T-day, residual dispersion is
   fix-vs-close noise (ratio std 24.6-38.1 bps), consistent with daily FX vol ~50-70bps and
   published ECB-fix studies. Honest caveat recorded in README.
7. EM history extension (same-publisher splice): discovered zip carries BRL/INR/MXN only from
   2008-01-02/2009-01-02 while existing ecb_fx/ (ECB SDW EXR, same official series) has BRL/INR
   from 2000-01-13. Overlap identity EXACT: BRL 4781 overlap pts max|diff|=0.0; INR 4525 -> 0.0;
   MXN 4781 -> 0.0. Splice prepends pre-zip rows (BRL 2037, INR 2293, MXN 2304, CNY 1332,
   ILS 2806, TRY 1537, THB/PHP/IDR/MYR 1599 each, RON 1664). Result: USD_CNY/USD_INR/USD_BRL
   start 2000-01-13 (8.2770/43.5228/1.8215 on day one, consistent with the CNY peg and 2000
   levels). Single publisher throughout; BGN splice auto-skipped (2e-4 rounding diff) — no
   foreign-source blending.
8. Code discipline: build_fx_hist.py 194 lines (<200), functions < 40 lines, deterministic,
   --download/--lint-only/--sdw flags, writes ONLY inside tools/quant/data/fx_hist/
   (existing fx/ and ecb_fx/ untouched).

## Known limitations (honest)
- TWD unavailable from ECB reference rates (not published) — would need a second source.
- ECB daily fix, not tradable close: 20-30bps RMS vs market close; ~1.3-1.6 corr attenuation
  same-day. For RES_CARRY daily research this is fine; document for execution-level use.
- ISK excluded (2008 crisis quote break); RUB suspended by ECB since 2022-03 (excluded).
- fx_hist/ is git-ignored (100MB on disk; 554 files). Rebuild is one command.

DATA_FXHIST DONE
