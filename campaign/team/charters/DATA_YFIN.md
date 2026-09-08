# DATA_YFIN — yfinance global equity/ETF/FX extension
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Use yfinance (no API key, direct HTTP) to EXTEND the equity/ETF/fx universe beyond twelve_big/12_extend
with names needed for decorrelated engines: international single names, sector/thematic ETFs, more FX.
Long, clean daily OHLCV.

## Source
- pip: yfinance (else `pip install yfinance --quiet`). `yf.download("SYM", start=..., auto_adjust=True)`.
- Prefer symbols NOT already in tools/quant/data/ (check first). Target: multi-decade liquid names.

## Deliverable
- tools/quant/data/yfin/<SYM>.csv (date,open,high,low,close,volume) + manifest.csv (symbol,start,end,rows,
  max_gap). Lint every series (span,NaNs,gaps,plausibility). Only write inside tools/quant/data/yfin/.

## Rules
- DIRECT HTTP (yfinance uses requests); rate-limit-sleep between tickers (avoid Yahoo throttling).
- DATA-ONLY, no backtests. Do not overwrite existing data dirs (twelve_big/12_extend already rich).

## Done marker
Last line of FINDINGS.md exactly: DATA_YFIN DONE
