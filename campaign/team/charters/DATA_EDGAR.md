# DATA_EDGAR — SEC EDGAR financial statements (fundamentals, no key)
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Pull US public-company financial statements from SEC EDGAR full-text search + XBRL (no API key,
direct HTTP). This is NEW fundamentals data the campaign lacks (it has price panels + FRED macro,
but no clean per-company fundamentals for fundamental/quality engines).

## Source (DIRECT HTTP only, never browser)
- EDGAR full-text: https://efts.sec.gov/LATEST/search-index?q=<ticker>&dateRange=custom
- XBRL company facts: https://data.sec.gov/api/xbrl/companyconcept/CIK##########/us-gaap/KEY.json
  (needs User-Agent header per SEC policy: "world-trader daxu contact@example.com")
- Ticker->CIK map: https://www.sec.gov/files/company_tickers.json

## Deliverable
- tools/quant/data/sec_edgar/<CIK>/... (revenue, net income, assets, equity, shares, margins,
  leverage) for a curated large-cap/sector universe. Manifest.csv (CIK, ticker, fields, years, rows).
- Focus on series a FUNDAMENTAL/QUALITY engine needs (i.e. quality & value factors), long-span.

## Rules
- DIRECT HTTP + UA header; respect SEC rate limits (~10 req/s, sleep between calls).
- Fail-closed lint: NaN/gaps/plausibility; no fabricated figures. DATA-ONLY (no backtests).
- Output dir shared with existing sec_ftd — create new sec_edgar/ to avoid colliding.

## Done marker
Last line of FINDINGS.md exactly: DATA_EDGAR DONE
