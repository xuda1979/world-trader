# FINDINGS: wiki_attention + sec_ftd resume + probe round 2 — 2026-09-07 (PM)

## Adopted

### 1. wiki_attention/ — Wikipedia per-article pageviews (NEW domain: retail attention)
- Source: Wikimedia REST pageviews, keyless, CC0, daily per-article 2015-07 -> now
- 10 series certified 0-gap inside steady_from windows: aapl nvda tsla gme btc spx vix
  recession fomc cpi (see manifest.csv; tsla cert 2017-02+, recession cert 2024-07+)
- 12 offline tests GREEN; fail-closed lint (zero-view day inside window => reject)
- Sanity vs known events: GME 2021-01-26 attention z=+6.1 (31172 views vs 1215 baseline);
  VIX article 10x jump 2024-08-05; BTC article 124k views 2017-12-17 top
- Gotchas: article titles 404 WHOLE WINDOWS before the title existed (Tesla,_Inc.
  pre-2017 rename) -> fetch_article(tolerate_404_before=steady_from); persistent
  zero-view API holes exist (Economic_recession 2024-07-10, verified 2x)
- PIT: day-D views complete ~D+1 00:00 UTC -> use T+1 alignment (README documents)

### 2. sec_ftd/ — resumed + completed the interrupted 01:43 build
- Root cause of abort: cnsfails201910a.zip does not exist (SEC archive hole)
- HEAD-scanned entire 2017-08..2026-09 range: 12 verified-missing files
  (201910a; 202002a..202004b COVID publication halt; 202605a/b, 202608b, 202609a/b post late)
- build_ftd.py patched with VERIFIED_MISSING skip set (anything else still fails closed)

## Probe round 2 verdicts (this environment, 2026-09-07 PM)
- Kalshi: OPEN keyless read API, 793 Economics series, but keyless history is
  SHALLOW (CPI series reach mid-2026; volume=None keyless; candles need
  in-lifetime ts windows). -> live event-prob feed only, not a backtest panel. Deferred.
- mempool.space: OPEN (fees/hashrate/difficulty) but REDUNDANT — CoinMetrics
  HashRate/FeeTotNtv already in more_onchain/. Rejected.
- Daily EPU: EPU_Daily_Update.xlsx 404; only monthly xlsx exists (and it is the
  same monthly series PETSTK already flagged). Rejected.
- EIA-930 hourly grid: v2 API needs a key we do not have; dashboard paths HTML-only. Rejected (no key).
- TSA throughput: yearly xls paths 404. Stocktwits public API: 404. Rejected.
- Wikimedia single-window cap: 366 days per request (year_chunks handles it).

## Environment notes
- SSL handshake on sec.gov is flaky (201806a dropped once, retried fine)
- options_rviv.py was refactored at 08:00 today by a parallel session and
  test_options_cboe.py HISTORY_PROVIDERS tests now fail — NOT from this session
