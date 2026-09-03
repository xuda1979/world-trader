# DATA_MORE_FRED — download MORE free FRED macro/rates/credit/commodity daily series (track C)

Working: FRED_KEY in .env.local (TESTED working). API:
  https://api.stlouisfed.org/fred/series/observations?series_id=ID&api_key=KEY&file_type=json
  (+&observation_start=YYYY-MM-DD). Free tier: many requests/day; add sleep(0.5-1s); handle 429.
Also the CSV endpoint fredgraph.csv (may be slow; prefer API).

DELIVER into a NEW dir: tools/quant/data/more_fred/<ID>.csv  (columns date,value). Save DAILY or
the native frequency (weekly/monthly OK — store, they may become helpers); flag frequency.

PRIORITY (decorrelated, extend existing FRED dir):
- Commodity/energy spot: WTI (DCOILWTICO — already on disk? check; add if missing), BRENT
  (DCOILBRENTEU), NATGAS (DHHNGSP), GASREGCO (reg gas), DPROPANE, DFOIL (fuel), DJFUEL,
  GASBREW, DHOILNYH, GASREGW.
- Rates/credit: MO (Moody's AAA), BAA (corporate BAA), FEDFUNDS, TB3MS, TB6MS, DGS1, DGS3MO
  (likely already), DGS2/5/7/10/20/30 (maybe already), DFII5/DFII10/DFII20/DFII30 (real yields),
  T10YIE, T5YIE, T5YIFP, AAA, BAA10Y, H15 on/off TB.
- Internals/money/liquidity: WALCL (add if missing), M2SL, MZM, REALLN, NFCI, STLFSI4, DTWEXBGS,
  TWEXAFEGSMTH, BOGMBASE.
- Macro: PAYEMS, UNRATE, CPIAUCSL, UMCSENT, ICSA, PERMIT, HOUST, INDPRO, RRSFS, DFF.
- Volatility: VIXCLS (on disk), add VXVCLS if exists, MOVE (bond vol — VERY useful, decorrelated),
  OVX (oil vol), GVZ (gold vol), JNK-style HY OAS via BAMLH0A0HYM2 (if not on disk).
For each: lint (span, n, gaps, frequency) + append to a manifest.csv. Only write inside
tools/quant/data/more_fred/. Report symbol/failure/span in FINDINGS.md. DATA-ONLY, no backtests.
Last line exactly: DATA_MORE_FRED DONE
