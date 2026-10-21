# GOAL100 ITER60 - NEW DATA AXES: binance_metrics + binance_bookdepth (2026-09-24)

Objective verbatim: acquire new data axises!!! (e.g. licensed COT/positioning feeds,
options-flow, or order-book depth).

## Acquired (both lint PASS, TDD-pinned, canonical layout)

1. **binance_metrics** (34-input; crypto-futures positioning + taker flow):
   BTC 2020-09-01..2026-09-23 n=2214, ETH 2021-12-01..2026-09-23 n=1758.
   Columns: oi, oi_value, toptrader L/S account+position ratios, global L/S
   account ratio, taker buy/sell ratio. Source: Binance Vision daily metrics
   archive (free, no key). Last-of-day convention; OI-only seam
   2021-12-31..2022-01-18 and intraday toptrader onset 2022-12-14 15:35 UTC
   measured and pinned (the pre-acquisition "12-15 onset" and ratio-index pins
   in the TDD-red test were corrected to measured archive reality).
2. **binance_bookdepth** (35-input; order-book resting depth): BTC
   2023-01-01..2026-09-23 n=1354, ETH n=1355. Mean bid/ask notional at 1%/5%
   bands, imbalance, n_snapshots (~2856/day). Documented absences: 5
   gate-rejected sparse days + 3 upstream-404 days (all re-verified live;
   KNOWN_DEPTH_ABSENT extended accordingly).

## Refreshed (existing axis)

3. **CFTC COT positioning** (data_cot): stale 2026 zips (cut 2026-08-11)
   re-downloaded; cot_tidy 2026-08-11 -> 2026-09-15 (+4 weeks, n 191,161),
   tff_tidy -> 2026-09-15 (n 39,912). No suite pins affected (A/B verified).

## Honest negatives (charter free-tier cap)

- FINRA short interest: BLOCKED at WAF (FINRA_BLOCKED.md).
- Licensed COT/positioning feeds: not purchasable under free-tier cap; free
  CFTC panel already on disk (more_cot/, 106 manifest rows).
- CBOE options-flow: upstream archive frozen 2019-10-04 (re-verified);
  no new free flow axis exists.

## Caps held / flags raised

- LEDGER_AXES still 33 (acquisition only; measurement is HUNT territory).
- Champion of record untouched (V7 lineage 9/9 GREEN; ITER60 pins 3/3 GREEN;
  parser/downloader TDD 32/32 GREEN).
- PRE-EXISTING RED flagged for coordinator (NOT this round's doing, verified
  via stash A/B and git blob comparison): test_frontier_closure_manifest PIN-1/2
  pin the Sep-19/20 UNCOMMITTED ITER49 champion vintage (cfa9ec4d…/a384d6b9…)
  which was overwritten Sep-22 back to the committed ITER16 vintage
  (ee03f5c0…/745bc5f1…); pinned diescrack_L40Z20_net.csv no longer exists on
  disk or in HEAD; 5 related reds in test_camp_short_r4_lsfix /
  test_camp_cost_r3_brwt pin the same overwritten vintages. Re-pin or
  re-emit is a coordinator decision.

Full detail: campaign/agents/chief/coord/ITER60_DATA_AXES/FINDINGS.md
