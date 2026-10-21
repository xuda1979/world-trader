# DATA_AKSHARE — AKShare broad-market coverage (A-share/HK/global/commodities/rates)
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Use the AKShare open-source Python library (aggregates EastMoney/Sina/etc., no key) to pull data the
campaign LACKS: China A-share/HK, India, global commodity/rates/currency breadth, index constituents.
Long history matters for engine validation.

## Source
- pip: akshare (if not installed, `pip install akshare --quiet`). Direct HTTP under the hood.
- Prioritise long-span, decorrelation-useful series: commodity forward/spot continuous, cross-rate
  (JPY/INR curry), global index breadth, HK/A-share equity for breadth factors.

## Deliverable
- tools/quant/data/akshare/<family>/<SYM>.csv (date,<fields>) + manifest.csv (symbol,start,end,rows,gap).
- Choose series with decade+ spans (prefer daily OHLC/close). Lint every series fail-closed.

## Rules
- DIRECT HTTP (akshare uses requests; no browser). Respect source rate limits (sleep between calls).
- Only write inside tools/quant/data/akshare/. DATA-ONLY, no backtests. Do not overwrite existing dirs.

## Done marker
Last line of FINDINGS.md exactly: DATA_AKSHARE DONE
