# CHARTER: HUNT_BINANCE_AXES — first measurement of ITER60's two new data axes

## Why
ITER60_DATA_AXES (2026-09-24) acquired two new data axes under a hard
non-goal of NO signal/backtest work ("measuring these inputs is HUNT
territory"). That hunt has not happened. This round executes it.

## Inputs (acquired, lint PASS, TDD-pinned)
- `tools/quant/data/binance_metrics/{BTCUSDT,ETHUSDT}-metrics.csv`
  (positioning: oi, oi_value, toptrader L/S account+position ratios,
   global L/S account ratio, taker buy/sell ratio; 2020-09-01+)
- `tools/quant/data/binance_bookdepth/{BTCUSDT,ETHUSDT}-bookdepth.csv`
  (order-book depth: bid/ask/total notional at 1% and 5%, imbalance,
   n_snapshots; 2023-01-01+)
- Price history: `tools/quant/data/more_crypto/{BTC,ETH}.csv` (2017/2018+)

## Scope (pre-registered, before looking at any result)
Signal families to measure, on each asset, T+1, costs per TRADE_RECORD_STANDARD:
1. **metrics / positioning**: contrarian-fade and momentum of
   toptrader_ls_position_ratio, global_ls_account_ratio, taker_buy_sell_ratio
   (z-scores over trailing windows 21/63d, sign both ways), oi / oi_value
   change momentum and its contrarian.
2. **bookdepth / microstructure**: imbalance_1pct and imbalance_5pct
   (levels, 21d z, 5d mean), depth-change momentum (total_notional_1pct),
   imbalance x return interaction.
3. **cross-sectional BTC-vs-ETH**: relative-value on each metric.

## Gates — the SHARED HONESTY + GATES CONTRACT (coord/GATES_CONTRACT.md)
ALL of: net SR >= 1.0 after costs; halves >= 0.5/0.5; param-plateau;
signal-scramble 200x p < 0.05; |corr| < 0.15 vs champion daily
(corr_ok_secondary 0.15-0.35); vol-target 10% trailing, clip <= 3.0;
T+1; 6.4bps one-side |dW| + 0.5%/yr borrow.

## Short-span honesty (pre-registered)
- bookdepth axis spans 2023-01+ (~2.7y): gates 3c/3d (halves, neg-years)
  are LOW-POWER on this span. Any bookdepth "pass" is provisionally
  reported as SHORT-SPAN, never champion-eligible without a governed
  re-verify at >= 4y span (same rule as HUNT_CN futures spans).
- metrics axis spans 2020-09+ (~5.0y): halves/neg-year gates at full power.
- NO IS/OOS cherry-pick inside the span: all params pre-registered above;
  the scramble + plateau gates are the selection discipline.

## Deliverables
- FINDINGS.md with exact numbers for every family (pass or honest negative)
- DEAD_IDEAS.csv rows for dead families
- Sleeve CSV + .meta only for gate-passing families (expected: few or none)
- No change to champion, weights, LEDGER, manifests (report-only round)
