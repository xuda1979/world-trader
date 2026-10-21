# DATA_VALUABLE — acquire HIGH-VALUE free, decorrelated data (track C+, user goal: "get more valuable free data")

The campaign already has equities (twelve_big/liq), FRED macro/rates/credit, crypto, and ETF sectors.
The MOST VALUABLE NEW free families (decorrelated, long-span, untested for standalone engines) are
(a) CBOE volatility/sentiment indices (VIX family + SKEW term structure), (b) CFTC Commitments of
Traders (COT) positioning (commodities + financial futures), (c) additional commodity futures
continuous series. These are all DIRECT HTTP (NO browser — permanent user boundary; use urllib/requests).

## A. CBOE index daily CSVs (works, TESTED by coordinator 2026-09-03)
Base: https://cdn.cboe.com/api/global/us_indices/daily_prices/<SYM>_History.csv ; format DATE,OPEN,HIGH,LOW,CLOSE
Fetch at minimum these (all TESTED reachable, 1990-2010+ span):
  SKEW, VIX, VIX9D, VXV (if exists at that URL, else use existing more_fred/VXVCLS), VVIX, RVX,
  OVX, GVZ, VXFLS?, FTP? (skip if 404). Also try VIX3M/VIX6M via the SAME base URL (e.g. VIX3M_History).
  Provide a full term-structure (9d/30d/3m/6m) => enables the term-slope engine (HUNT_VXV_TERM only had
  VIX+VXV; 9d/6m adds the curve).
  LINT each: span, n rows, NaNs, monotonic date, value plausibility (SKEW 90-180; VIX 0-100+).
  Save to tools/quant/data/more_vol/<SYM>.csv (date,open,high,low,close) + manifest.

## B. CFTC COT positioning (works, TESTED)
 URLs: https://www.cftc.gov/files/dea/history/fut_disagg_txt_YYYY.zip (disaggregated commodities, per year
 YYYY=2010..2026) and https://www.cftc.gov/files/dea/history/fut_fin_txt_YYYY.zip (financial futures).
 Each zip = a TXT with per-market weekly records: columns include Market_and_Exchange_Names,
 Report_Date_as_MM_DD_YYYY, Open_Interest_All, Noncomm_Positions_Long/Short/Spread, Comm_Positions_..., etc.
 Build per-market daily/weekly positioning series: "net noncommercial" = Noncomm_Long - Noncomm_Short
 (and % of OI), weekly (Report_Date). Markets to keep (match name): CRUDE OIL (WTI/BRENT), NATURAL GAS,
 GOLD, SILVER, COPPER, S&P500 (E-mini S&P 500 STOCK PRICE INDEX), NASDAQ, DOW, YEN, EURO, GBP, TBOND,
 10Y NOTE, 5Y NOTE, 2Y NOTE, SOFR?, VIX. For each market produce: date, net_noncomm, net_noncomm_pct_oi,
 open_interest. LINT (span, weekly gaps, OI>0). Save tools/quant/data/more_cot/<market_slug>_cot.csv + manifest.
 NOTE: COT is WEEKLY (Tue release, usually Friday-report date); state it's weekly (not daily) in manifest.

## C. Additional commodity futures continuous (optional, if cheap network allows)
 Try Stooq continuous (may be JS-blocked — if so log and SKIP). Otherwise rely on FRED spot (already have
 DCOIL/DHHNGSP) — do NOT burn time if blocked. Softs via FRED if series exist (DPROPANE done; others: none).

## RULES
- DIRECT HTTP only (urllib/requests). NEVER browser. Respect rate limits (sleep  fallout .5-1s; CBOE fine).
- Fail-closed lint EVERY series (span/nan/gaps/plausibility); write manifest.csv with exact spans.
- Write ONLY inside tools/quant/data/more_vol/ and more_cot/ (and any new more_fut/ you create).
- DATA-ONLY: NO strategy backtests. Record symbol/failure/span in FINDINGS.md.
- TDD where you build a parser (write a small test that the COT row parser returns expected fields for a
  known line; CBOE CSV parser trivial — still add a 3-line sanity assert).
- Last line exactly: DATA_VALUABLE DONE
