# CHARTER: ITER60_DATA_AXES — acquire NEW data axes (positioning / flow / depth)

## Why
Frontier closure (ITER56/#147, ledger #146) states the per-axis measurement
program is EXHAUSTED at 33 measured axes and the remaining operator levers are
NEW DATA / rule change ONLY. This round executes the NEW DATA lever.

## Scope (from operator request 2026-09-24)
Acquire new data axes, explicitly considering: licensed COT/positioning feeds,
options-flow, order-book depth. Constraints: free-tier only (no licensed feeds
purchasable here), no-key or already-owned keys, canonical layout
(campaign/team/charters/DATA_ORGANIZE.md), TDD parsers, fail-closed lint,
honest negatives for blocked sources.

## Pre-probe inventory (done first, this round)
- COT positioning: ALREADY COVERED (more_cot/ 106 manifest rows: legacy + TFF
  + trader-count panel; DATA_COTMORE rounds 1-7 complete). Licensed feeds add
  nothing obtainable free -> NOT acquired (not a new axis).
- Options flow: cboe_flow/cboe_pcr exist; PCR archive FROZEN upstream at
  2019-10-04 (re-verified R5). CBOE delayed_quotes historical endpoint still
  200s for index levels but that is already-captured index data, not flow.
  -> no NEW free options-flow axis identified this round.
- Equity short interest (FINRA): BLOCKED at WAF (see FINRA_BLOCKED.md) -> honest
  negative on ACCESS, logged, axis stays open for future network/probe.
- Crypto futures positioning + taker flow (Binance Vision metrics): FREE,
  NO KEY, 5-min granularity, BTCUSDT from 2020-09-01, ETHUSDT from 2021-12-01
  -> ACQUIRED (new axis 34-input: derivatives positioning).
- Order-book depth (Binance Vision bookDepth): FREE, NO KEY, ~60s snapshots,
  both symbols from 2023-01-01 -> ACQUIRED (new axis 35-input: book depth).

## Deliverables
1. tools/quant/data/binance_metrics/ — parser + TDD tests + downloader + README
   + manifest + BTCUSDT/ETHUSDT daily CSVs (lint PASS required).
2. tools/quant/data/binance_bookdepth/ — same structure (FINRA_BLOCKED.md
   documents the blocked short-interest probe).
3. Campaign/bt-suite lint test pinning the acquired facts (rows, spans, holes)
   so no later session can silently corrupt the new axes.
4. FINDINGS.md (this dir) + campaign memo GOAL100_ITER60_DATA_AXES.md +
   STANDUP entry.

## Non-goals (hard charter caps)
- NO signal/backtest on the new data (hunting is HUNT_* territory; data is an
  INPUT, not a verified gain — standup 2026-09-20 line ~11953).
- NO change to champion, weights, manifests of record, LEDGER/LEDGER_AXES
  (data acquisition does not measure an axis; the 33-axis count is untouched
  until a HUNT round measures these inputs).
- NO deletion of any existing CSV.
