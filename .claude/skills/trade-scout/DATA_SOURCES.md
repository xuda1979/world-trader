# Trade Scout -- Internet Data Sources

> **Primary tool:** run `python3 tools/scan.py` (from repo root) for an
> end-to-end scan. Full endpoint/key inventory is in `SOURCES_CATALOG.md`.
> This file keeps the WebSearch patterns for manual catalyst/news research.

Use these source categories during Phase 2. Always prefer multiple
independent, reputable sources and record the date of each data point.
Use `WebSearch`/`WebFetch` (or any configured market-data tools). If a
source needs a paid login or is unavailable, note it and lower confidence.

## Local scanner (preferred — does Phases 2-4 automatically)
`tools/scan.py` (stdlib only) pulls live quotes across crypto, US, China, and
Taiwan, scores reward:risk, enriches with technicals, and ranks by a composite
quality score. Prefer it over WebSearch for raw prices/screening:

```
python3 tools/scan.py --doctor     # verify keys + every source is alive
python3 tools/scan.py              # regime + 80+ live quotes + ranked opportunity table
python3 tools/scan.py --full       # + news + alt-data (FRED/COT/curve/funding)
```

## Local price fetcher (single-symbol cross-check fallback)
`tools/fetch.py` (stdlib only) pulls quotes from several free APIs at once and
cross-checks them, so prefer it over WebSearch for raw prices:

```
python3 tools/fetch.py crypto BTC ETH SOL    # Coinbase, Binance, CoinGecko, Kraken, CoinCap
python3 tools/fetch.py equity AAPL MSFT      # Stooq, Yahoo
python3 tools/fetch.py fx USD EUR GBP JPY    # Frankfurter (ECB)
python3 tools/fetch.py crypto BTC --json     # machine-readable
```

Each symbol reports a median, the number of agreeing sources, and the spread.
A quote is flagged `ok` only when >=2 sources agree within 1%; otherwise
`UNVERIFIED` -- treat unverified/`NO DATA` quotes as stale and lower
confidence (or fall back to WebSearch). Exit code is non-zero when no symbol
returned data. Network availability varies by environment; failed sources are
listed per symbol, not hidden.

## Price / volume / technicals
- Exchange and broker quote pages, charting sites (free tiers).
- Look for: trend, support/resistance, breakouts, gaps, ATR, volume surge,
  relative strength vs sector and index.
- Search patterns: "<ticker> stock chart", "<ticker> support resistance levels",
  "<ticker> ATR", "<ticker> relative strength sector".

## Catalysts / events
- Earnings calendars, company press releases / investor relations pages.
- Regulatory: FDA calendars, central-bank schedules.
- Macro: economic calendars (CPI, FOMC, NFP, PMI).
- Crypto: project blogs, token unlock schedules, upgrade roadmaps.
- Search patterns: "<ticker> earnings date", "<ticker> upcoming catalysts",
  "economic calendar this week", "<token> unlock schedule".

## Order flow / positioning
- Unusual options activity, short interest & days-to-cover.
- Futures: CFTC Commitments of Traders (COT).
- Crypto: funding rates, open interest, exchange flows.
- Search patterns: "<ticker> short interest", "<ticker> unusual options",
  "<token> funding rate open interest".

## Sentiment / narrative (secondary, contrarian-aware)
- Reputable financial news, analyst rating/target changes.
- Social momentum -- treat as a crowding warning, not a buy signal.
- Search patterns: "<ticker> analyst rating change", "<ticker> news today".

## Macro / regime context
- Index trend, VIX, rates/yields, sector rotation, risk-on/off tone.
- Search patterns: "market today summary", "VIX level", "sector performance today".

## Verification rules
- Cross-check every price/date across >= 2 sources before relying on it.
- Distinguish confirmed facts from rumor/speculation in the report.
- Flag stale data (more than ~1 trading day old for prices) explicitly.
