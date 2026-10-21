# GOAL100 iter13: NEWDATA -- CBOE keyless options chains (2026-09-07)

## What landed

- `tools/wt/options_cboe.py` -- keyless CBOE delayed-quote chain analytics.
  parse_contract (OCC), chain_url (index -> _SYM.json), fetch_chain,
  chain_analytics (pc_vol, pc_oi, atm_iv call/put/mean, iv_atm_spread,
  iv_25d_call/put, skew_25d, totals), fetch_analytics, aggregate (multi-name
  sweep, per-name error isolation, breadth_pc_vol_gt1, median stats).
- `tools/wt/options_rviv.py` REPAIRED (was silently dead 2 ways):
  1. yahoo_history 403s from this host -> removed;
     HISTORY_PROVIDERS = ("nasdaq", "stooq", "cboe"); nasdaq_history +
     _nasdaq_rows (newest-first -> ascending reverse, $/comma strip, null
     close dropped); stooq PoW helpers (_parse_challenge/solve_pow/
     _stooq_opener) kept for the record.
  2. cboe_atm_iv filtered on o["option_type"] which the payload does not
     carry -> all-empty -> scan() returned 0 rows forever. Now classifies
     via OCC symbol (parse_contract); ATM + 7..45d expiry selection over
     iv>0 contracts.
- `tools/test_options_cboe.py` -- 47 offline checks, ALL GREEN. Covers
  parse vectors, analytics invariants, index URL form, aggregate isolation,
  fail-closed ValueError, rviv provider order, PoW helpers, nasdaq rows.

## Live verification (2026-09-07)

- aggregate([SPX,VIX,AAPL,TSLA,NVDA,GME]): 6/6 ok. SPX pc_vol 1.576,
  pc_oi 1.407, atm_iv 10.58%, skew25d +0.098; VIX atm_iv 47.7%; GME iv 64%.
- rviv.scan(default 21 names): 3 rows (NVDA +16.1, TSLA +12.3, NFLX +8.4
  long-gamma; GME/MSTR short-vol on the 6-name list).
- test_smoke.py: ALL PASS (no regressions).

## Campaign-relevant notes

- New signal surface for GOAL100 hunts: daily cross-sectional pc_vol /
  skew / atm_iv panel from keyless CDN (no rate limit observed; full SPX
  chain 28k contracts, ~12MB, fetches in seconds).
- chain data is point-in-time (delayed ~15min intraday; settled EOD after
  close) -- harvest after 16:15 ET for daily-bar semantics.
- Old `option_type`/`expiration_date`/`strike` flat keys do NOT exist;
  anything reading them silently sees nothing. cboe_options_dl.py (bulk
  pipeline) already knew this; wt/ scanner layer now matches.
- NOT yet wired into report.py / loop_scan / agent tools_registry; the
  rviv.scan() fix alone already restores the loop_scan ov_rows feed.
