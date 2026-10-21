# RV Mean-Reversion Backtest at Scale (Real Data)

Generated: 2026-07-27 19:22:29  |  Elapsed: 2.9s

## Methodology

- **Universe**: 10 RV pairs (4 yield-curve spreads + 6 FX crosses, all via FRED)
- **Data**: real daily history, ~1500 bars (~6 years)
- **Walk-forward**: 60% IS / 40% OOS chronological split
- **Signal**: rolling z-score over prior 60 bars, enter at |z|>2.0, exit at z crosses 0, max hold 10 bars
- **Sizing**: 1% equity at 1-sigma spread move
- **Commission**: IBKR Fixed (FX 0.2bp/side, YIELD 0.05bp/side)
- **Slippage**: 0.3 bp/side (user-specified)
- **Round-trip cost**: FX=4.40bp, YIELD=3.20bp (2 legs x 2 sides x (comm+slip))

## Per-Pair Results (sorted by OOS Sharpe)

| Pair | Mkt | RT cost | IS n | IS Sharpe | OOS n | OOS Sharpe | OOS Win% | OOS PnL $ | Final Eq $ | Total Ret |
|------|-----|---------|------|-----------|-------|------------|----------|-----------|------------|-----------|

## Portfolio Tear-Sheet (compounded across all 10 pairs)

| Metric | Value |
|--------|-------|
| Trades | 0 |
| Win rate | 0.0% |
| Avg win | +0.000 stdev |
| Avg loss | +0.000 stdev |
| Exp/trade | +0.000 stdev |
| SD/trade | 0.000 stdev |
| Per-trade Sharpe | +0.00 |
| t-stat | +0.00 |
| Total return | +0.0% |
| Final equity | $100,000 |
| Max drawdown | 0.0% |
| Years (est) | 0.0 |
| Trades/year | 0.0 |
| CAGR | +0.0% |
| Ann. Sharpe | +0.00 |
| Calmar | +0.00 |
| Total PnL | $0 |
| Worst trade | +0.000 stdev |
| Best trade | +0.000 stdev |

**IS/OOS split**: 0 IS trades (exp/trade +0.000 stdev), 0 OOS trades (exp/trade +0.000 stdev)

## Key Findings

- **0/0 pairs have positive OOS Sharpe**; 0 have non-positive.
- **Portfolio max DD = 0.0%** — **UNTRADEABLE as-is**.  Despite a 2-stdev stop-loss (added 2026-07-26), yield-curve trades can still move 4+ stdev against before the stop triggers.
- **CAGR +0.0% / Ann Sharpe +0.00** is DOMINATED by the 0% DD — Calmar +0.00 confirms risk-adjusted return is poor.
- **Cost impact**: at ~3.8bp RT per trade and ~0 trades/year, cost drag ~0.0%/year — small relative to signal variance but meaningful for low-edge pairs.
