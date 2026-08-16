# Monthly Top-100 High-Sharpe US Momentum — Backtest

**Run:** 2026-08-12 · Script: `tools/quant/monthly_top100_momentum.py` · Data: real daily OHLCV

## Strategy (as directed)

On the **1st trading day of every month**:
1. Compute **past-year daily returns** (252 trading days) for every universe name.
2. Compute **past-year Sharpe** = `mean(daily ret)/std(daily ret) × √252`.
3. **Keep only positive-Sharpe** stocks.
4. Select the **top 100** by past-year Sharpe.
5. **Equal-weight** them; hold one month; rebalance (full churn each month).

**Universe:** 285 US-listed common stocks (broad liquid panel, history since 2006).
ETFs (SPY/QQQ/XLF) and foreign ADRs (ASML/HMC/TM) excluded so rankings are of real US equities.

**Costs:** Net of 3.8 bp one-side commission, charged on rebalance-day turnover
(~ round-trip on the ~99% of the book that changes each month). No look-ahead:
signal at date *t* uses data strictly before *t*.

## Results (net of cost) — 2007-10 → 2026-08

| Metric | Top-100 strategy | SPY | EW whole pool (285) |
|---|---|---|---|
| Annualized return | **11.29%** | 8.92% | 12.96% |
| Annualized vol | 20.6% | ~15-17% | ~18% |
| **Sharpe** | **0.62** | 0.53 | **0.76** |
| Max drawdown | -50.6% | -56.5% | -42.0% |
| Split-half Sharpe | 0.34 / 0.98 | — | — |
| Avg monthly turnover | 99.4% (≈99 of 100 names) | — | — |

## Interpretation

- **Beats SPY** on Sharpe (0.62 vs 0.53), return, and drawdown. High past-year
  Sharpe is a real, tradable screen versus the broad index over this 19-year window.
- **But lags the equal-weight whole pool** (Sharpe 0.76, return 12.96%, DD -42%).
  Concentrating into the top-100-by-Sharpe adds only marginal return over just
  holding the full liquid universe, and costs via concentration (higher DD).
- **Turnover is ~100%/month** — the book is entirely replaced at every rebalance.
  Even at just 3.8 bp one-side that is ~0.8%/month of round-trip cost drag
  (≈9.6%/yr), which shaves the gross ~12.3% to ~11.3% and materially lowers net Sharpe.
- **Split-half instability** (0.34 early vs 0.98 late) means the edge is
  regime-dependent, not a stable premium across the whole sample.

## Honest caveats / friction points

- Single long-Side screen; no position sizing, vol-targeting, or stop-loss discipline
  built in — raw long-only momentum with deep late-2008/2020 drawdowns.
- The +0.62 net Sharpe is **long-only equity beta dressed as alpha**; it is not a
  market-neutral book and would still ride market downturns.
- With ~99% monthly turnover it is a **high-friction** strategy; real net Sharpe is
  sensitive to the true cost assumption. Only robust at institutional-grade execution.

## Files

- `top100_momentum_eq.csv` — daily strategy return + equity curve
- `top100_momentum.json` — machine-readable stats

*For a market-neutral, cost-aware, backtested book see the `tools/quant/ls` framework
and `build_high_sharpe_portfolio.py` (scramble-validated legs only).*
