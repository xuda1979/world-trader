# FINDINGS — ITER60_DATA_AXES (2026-09-24)

## Status: COMPLETE — both new axes acquired, lint PASS, tests GREEN

Charter (../CHARTER.md): execute the NEW-DATA lever (the only open operator lever
after frontier closure at 33 axes). Two axes acquired this round; one honest
negative on access (FINRA, already logged); zero licensed feeds (free-tier cap).

## Axis 34-input: binance_metrics (positioning + taker flow, crypto futures)

- Source: Binance Vision USD-M futures daily `metrics` archive (free, no key).
- Files: `tools/quant/data/binance_metrics/{BTCUSDT,ETHUSDT}-metrics.csv`
  + `manifest.csv` + parser/builder/TDD tests + README.
- Coverage: BTC 2020-09-01..2026-09-23 n=2214; ETH 2021-12-01..2026-09-23 n=1758.
  Lint PASS both (fail-closed: sorted, unique, floor-anchored, no hole > 9d).
- Columns: oi, oi_value, toptrader_ls_{account,position}_ratio,
  global_ls_account_ratio, taker_buy_sell_ratio (LAST-of-day convention).
- Structural seams MEASURED against raw archives (probe transcripts in session log):
  * BTC OI-only window 2021-12-31..2022-01-18: ALL ratio cells EMPTY (verified
    last-row "" on 5 sampled dates); oi/oi_value populated throughout.
  * toptrader columns activate INTRADAY 2022-12-14 15:35 UTC (101/288 rows that
    day; 2022-12-13 has 0). Last-of-day aggregation therefore carries 12-14
    values — the TDD-red pin "starts 2022-12-15" in test_iter60_data_axes.py
    was corrected to the measured onset (12-14 non-empty, 12-13 empty).
  * taker/global columns first non-empty last-row 2022-01-30 (BTC).
- The pre-acquisition pin `bmap["2022-01-11"][2] == ""` was an off-by-one
  (index 2 = oi_value, which is POPULATED on OI-only days); corrected to assert
  ratio cells [3..6] empty AND oi_value populated.

## Axis 35-input: binance_bookdepth (order-book resting depth, crypto futures)

- Source: Binance Vision USD-M futures daily `bookDepth` archive (free, no key).
- Files: `tools/quant/data/binance_bookdepth/{BTCUSDT,ETHUSDT}-bookdepth.csv`
  + `manifest.csv` + parser/builder/TDD tests + README.
- Coverage: BTC 2023-01-01..2026-09-23 n=1354; ETH 2023-01-01..2026-09-23 n=1355.
  Lint PASS both. ~2856 60s-snapshots/day aggregated to mean bid/ask notional
  at 1%/5% bands + imbalance + n_snapshots.
- Documented absences (both in test + here, verified live post-build):
  * Gate-rejected sparse days (<100 snapshots): 2023-01-09, 2023-01-15,
    2023-01-16, 2023-01-21 (Jan-2023 cluster, both symbols), 2024-06-12
    (~20 rows / ~2 snaps, both symbols).
  * Upstream 404 (never published, re-verified 2026-09-24): 2023-02-08,
    2023-02-09 (both symbols), 2024-04-18 (BTCUSDT only).
  * KNOWN_DEPTH_ABSENT in the test was extended with the three 404 days
    (pre-acquisition set listed only the sparse cluster + 06-12).

## COT positioning axis: REFRESHED (existing axis, not new)

- `data_cot/cot_tidy.csv`: 2026-08-11 -> 2026-09-15 (+4 weekly reports; n
  189,735->191,161; 685 contracts). `tff_tidy.csv`: -> 2026-09-15 (n 39,912).
- Stale local 2026 zips (com_disagg 8,877 rows / com_fin 2,773 rows, both cut
  2026-08-11) deleted and re-downloaded (10,303 / 3,342 rows, cut 2026-09-15);
  deacom.txt current-week file verified live at 2026-09-15.
- No test pins the COT max-date; no suite impact (verified A/B).

## Honest negatives / blocked (no new axis obtained)

- FINRA consolidated short interest: BLOCKED at WAF (FINRA_BLOCKED.md, probed
  2026-09-24). Logged, not retried.
- Licensed COT/positioning feeds (e.g. paid vendor panels): free-tier cap in
  charter; NOT acquired (more_cot/ already covers free CFTC positioning at
  106 manifest rows).
- CBOE options-flow historical: upstream archive frozen 2019-10-04 (re-verified
  this round); no NEW free options-flow axis obtainable.

## Pre-existing breakage flagged (NOT touched, outside charter non-goals)

- `test_frontier_closure_manifest.py` PIN-1/PIN-2 champion hashes RED:
  worktree files match git HEAD (verified blob-exact), but the pinned ITER49
  champion (cfa9ec4d38158691 / a384d6b92e258fd5) is the Sep-19/20 UNCOMMITTED
  vintage that was overwritten on Sep-22 back to the committed ITER16 vintage
  (ee03f5c096aabb6d / 745bc5f1d2037dc8), and the pinned diescrack input file
  (diescrack_L40Z20_net.csv) no longer exists on disk or in HEAD. The current
  system of record is the V7 lineage (test_v7_decay_freshness +
  test_v7_oos_decay_monitor 9/9 PASS). Champion re-emit / re-pin is a
  coordinator decision, explicitly excluded from this data round.
- Same class: 5 failures in test_camp_short_r4_lsfix / test_camp_cost_r3_brwt
  (verified pre-existing via stash A/B; they pin the same overwritten vintages).

## Charter caps held

- LEDGER_AXES still 33; no binance family added to LEDGER (acquisition only;
  measuring these inputs is HUNT territory).
- No champion/weights/manifest-of-record touched. No CSV deleted (only stale
  zip caches replaced by re-download, same source, same schema).
- Suite state: ITER60 pins 3/3 GREEN (run with sibling frontier module present);
  parser+downloader TDD 32/32 GREEN; V7 decay monitors 9/9 GREEN.

ITER60_DATA_AXES DONE
