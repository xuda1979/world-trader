
## Update 2026-08-13 (loop fire) — DEPLOYMENT GAP FOUND & FIXED: data pipeline was stale

### The gap
- Panels (twelve_big/twelve_liq/twelvedata) stopped at 2026-08-10 while
  the TwelveData API has data through 2026-08-12 (verified by direct
  query).
- Root cause: the extend/fetch scripts SKIP symbols already at >=4900
  rows, so re-running them never refreshes full files. No launchd agent
  fetches price data (all 5 agents are scan/digest scripts, none
  loaded). Data refresh was manual AND effectively broken.
- Impact: the live signal depends on fresh data; staleness was silent.

### The fix
- tools/quant/refresh_panel.py: ALWAYS refetches every symbol
  (outputsize=5000, rolling 20y window — the API returns the most
  recent 5000 bars, so the window shifts forward). Covers twelve_big +
  twelve_liq + twelvedata (~330 unique symbols, 9s sleep, ~50 min,
  within free-tier 800/day quota).
- Launched 2026-08-13 in background. After completion: re-verify the
  champion smoke test (numbers should be unchanged — 2 days of new data
  in a 224-month backtest), then the next month-end will trigger the
  normal signal update path.

## Update 2026-08-13 (loop fire) — Data pipeline self-maintaining

refresh_panel.py idempotent fast-path verified: when current, a run
costs ~seconds (skip-fresh via mtime + last-row check); only lagging
files get refetched (this run: 6 files, 4 ok, 2 expected 404s for the
underscore FX pairs). Data current at 2026-08-12 across all panels.
The loop's monitoring can now include a refresh attempt each fire —
cheap when current, ~1.5 min when a few files lag, ~70 min only after
a multi-day gap.

## Update 2026-08-13 (loop fire) — Refresh cycle fully silent

refresh_panel.py: added SKIP_SYMS (EUR_JPY/USD_JPY/VIXCLS — provider
never resolves them) and simplified freshness to mtime-today alone (the
4 files whose API data legitimately ends earlier — SQ renamed to XYZ,
BK/MMC/FLT data gaps — no longer refetched every run). Verified:
routine run now 0 ok / 0 err in 0.04s. The monitoring cycle is free
when data is current; a run only does work after a data gap.
