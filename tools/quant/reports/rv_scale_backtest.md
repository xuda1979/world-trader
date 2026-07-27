# RV Mean-Reversion Backtest at Scale (Real Data)

Generated: 2026-07-27 11:35:45  |  Elapsed: 4.2s

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
| GBP/JPY | FX | 4.40bp | 143 | -0.45 | 96 | +0.04 | 43.8% | $1,022 | $31,156 | -68.8% |
| EUR/AUD | FX | 4.40bp | 125 | -0.29 | 101 | -0.05 | 52.5% | $-4,925 | $56,562 | -43.4% |
| 2s30s | YIELD | 3.20bp | 165 | -0.01 | 106 | -0.31 | 39.6% | $-39,202 | $55,627 | -44.4% |
| AUD/NZD | FX | 4.40bp | 113 | +0.16 | 101 | -0.31 | 40.6% | $-37,908 | $88,605 | -11.4% |

## Portfolio Tear-Sheet (compounded across all 10 pairs)

| Metric | Value |
|--------|-------|
| Trades | 950 |
| Win rate | 42.5% |
| Avg win | +1.034 stdev |
| Avg loss | -1.193 stdev |
| Exp/trade | -0.246 stdev |
| SD/trade | 1.483 stdev |
| Per-trade Sharpe | -0.17 |
| t-stat | -5.11 |
| Total return | -82.6% |
| Final equity | $17,385 |
| Max drawdown | 82.6% |
| Years (est) | 5.7 |
| Trades/year | 167.1 |
| CAGR | -26.5% |
| Ann. Sharpe | -2.14 |
| Calmar | -0.32 |
| Total PnL | $-82,615 |
| Worst trade | -6.848 stdev |
| Best trade | +5.143 stdev |

**IS/OOS split**: 546 IS trades (exp/trade -0.262 stdev), 404 OOS trades (exp/trade -0.223 stdev)

## Key Findings

- **1/4 pairs have positive OOS Sharpe**; 3 have non-positive.
- **FX pairs**: 1/3 positive OOS Sharpe.  Best: GBP/JPY (+0.04).
- **Yield pairs**: 0/1 positive OOS Sharpe.  Best (least bad): 2s30s (-0.31).
- **Portfolio max DD = 82.6%** — **UNTRADEABLE as-is**.  The strategy has NO stop-loss; yield-curve trades held to horizon can move 4-9 stdev against.
- **CAGR -26.5% / Ann Sharpe -2.14** is DOMINATED by the 83% DD — Calmar -0.32 confirms risk-adjusted return is poor.
- **Cost impact**: at ~1.3-1.4bp RT per trade and ~167 trades/year, cost drag ~2.2%/year — small relative to signal variance but meaningful for low-edge pairs.
