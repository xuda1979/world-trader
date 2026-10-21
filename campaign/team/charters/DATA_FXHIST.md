# DATA_FXHIST — 160-currency long-history foreign exchange (1999+)
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Pull BROAD multi-currency FX history (160+ currencies back to 1999) from free REST APIs the campaign
lacks — the existing fx/ has only 8 pairs. Enables the FX carry / cross-currency engine (RES_CARRY).

## Source (DIRECT HTTP, no browser)
- AllRatesToday (160+ currencies, 1999+), currencyarchiveapi (25+ years, offline), ExchangeRate-API
  (100/mo), ECB reference rates (daily, long span, free): https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip
  - ECB is the strongest: free, long, official. Build all-pairs from EUR cross-rates.

## Deliverable
- tools/quant/data/fx_hist/<CURRENCYPAIR>.csv (date,close/rate) for a broad cross matrix (AUD, NZD, JPY,
  GBP, CHF, CAD, ZAR, INR, BRL, TRY, SEK, NOK, DKK, PLN, HUF, CZK, SGD, HKD, KRW, TWD, THB, MXN, etc.)
  + manifest.csv (pair,start,end,rows,max_gap). Lint daily gaps and plausibility.

## Rules
- DIRECT HTTP; respect each API's rate limits (sleep + retry on 429). Prefer ECB (no key, long span).
- DATA-ONLY; only write inside tools/quant/data/fx_hist/. Do not overwrite existing fx/.

## Done marker
Last line of FINDINGS.md exactly: DATA_FXHIST DONE
