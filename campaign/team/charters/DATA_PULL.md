# DATA_PULL — fetch NEW free data (direct HTTP, no browser)
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Acquire the HIGHEST-VALUE missing free data the roadmap (DATA_MAESTRO) needs. Tested keys in
.env.local (TWELVEDATA_KEY, FINNHUB_KEY, FRED_KEY, POLYGON_KEY, ALPHAVANTAGE_KEY).

## Priority sources (all DIRECT HTTP — never touch the user's browser)
- CBOE index daily CSVs: https://cdn.cboe.com/api/global/us_indices/daily_prices/<SYM>_History.csv
- CFTC COT: https://www.cftc.gov/files/dea/history/fut_disagg_txt_YYYY.zip | fut_fin_txt_YYYY.zip
- Twelvedata (/time_series?symbol=..&interval=1day&outputsize=5000), Finnhub, FRED, Stooq, ECB, BOE, BIS.
- Avoid re-fetching what's already on disk in tools/quant/data/ (check before you pull).

## Deliverable
New CSVs in tools/quant/data/<new_family>/ plus a manifest.csv (symbol,start,end,rows,max_gap).
DO NOT overwrite existing data dirs. Write ONLY in your new output dir.

## Rules
- Sleep between calls (free Twelvedata ~8 req/min); on 429 wait 20-30s, retry once. Lint every series.
- Fail-closed: any series that doesn't lint (span/na/gaps/plausible range) is NOT delivered.
- This is DATA-ONLY — no strategy backtests.

## Done marker
Last line of FINDINGS.md exactly: DATA_PULL DONE
