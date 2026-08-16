# bigmove — Sharpe Optimization: Honest Result

**Date**: 2026-08-13
**Objective**: maximize Sharpe of the next-day-≥5% prediction strategy.

## Method
- Reused the cached, no-look-ahead walk-forward predictions (606,383 OOS
  stock-days, 2018-2026, 285 US large caps).
- New: proper **calendar-time portfolio** backtest (flat days = 0% return) so the
  Sharpe is not inflated by annualizing over only active days.
- Swept the full trading-rule space: prob threshold (0.6-0.95) x cross-sectional
  top-K (1/5/10/20/None) x intraday weighting (equal/prob/sqrt/rank) x
  per-name position caps.

## Result
**Best calendar-time Sharpe = 0.22 (zero annual-return-positive configs).**
- Across the ENTIRE grid, **0 configurations had a positive annual return.**
- Best config: thr≥0.8, top-5, prob-weighted → SR 0.22, **ann −3.3%, maxDD −87.5%**.
- Higher-prob configs (thr≥0.9) → SR ~0.18, ann −1%, DD −55%.

## The definitive statistical finding
The per-trade edge is **statistically indistinguishable from zero after 12bp cost**:
- thr≥0.9: mean net +0.065%/trade, **t-stat 0.61, p = 0.54 (not significant)**
- Bootstrap 95% CI on the mean: **[−0.14%, +0.28%]** (includes 0)
- **P(losing year, ~340 iid trades) ≈ 42%**

Earlier attractive figures ("per-trade SR 0.64", "active-day Sharpe 0.63", "+22%
annualized") were **artifacts** of (a) annualizing over only the ~40% of active
days, and (b) averaging highly-correlated same-day names, which overstates the
standalone per-name edge Mendieta.

## Conclusion
**Trading-rule optimization cannot create Sharpe where there is no per-trade
edge.** The underlying signal (predicting next-day ≥5% from daily OHLCV) has an
out-of-sample per-trade Sharpe of ~0.01-0.03 even gross of costs. This is the
data ceiling — a single-day ≥5% large-cap move is dominantly idiosyncratic news,
not predictable from price history.

**Recommendation**: Do NOT deploy. The edge is not statistically robust, all
optimized variants are annual-return-negative in calendar time, and drawdowns are
severe. The only genuine route to a profitable big-move strategy is a materially
richer signal set (earnings calendar, news/NLP, options flow) — not more trading-rule
tuning on the current prediction.

## Artifacts
- `bigmove_sharpe_opt.json` (full grid results)
- `optimize_sharpe.py` (harness)
- `data/pred_frame.parquet` (cached OOS predictions)
