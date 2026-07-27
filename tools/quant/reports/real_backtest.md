# Real-Data Backtest Suite

Generated: 2026-07-27 11:45:05  |  Elapsed: 4.9s

## Methodology

- **Data**: real daily OHLC via `data_history.py` (Polygon / Binance / Twelve Data, CSV-cached)
- **Walk-forward**: 60% in-sample / 40% out-of-sample for both RV pairs and setup replays
- **Sizing**: 1-sigma risk = 1% of equity per trade
- **Universe**: 8 ETF/crypto pairs + 10 liquid US large-caps
- ⚠️ Pairs/setups with `n_trades < 20` are flagged 🚩 — Sharpe is dominated by noise

## 1. RV Mean-Reversion on Real ETF Pairs

| Pair | Provider | Bars (IS/OO) | HL (bars) | Lookback | Trades | Win% | Expectancy | Per-trade Sharpe | t-stat | Ann Sharpe | Max DD | Total PnL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SPY/QQQ 🚩 | polygon/polygon | 501 (300/201) | 45.2 | 45 | 6 | 0.0% | -10.75% | -5.68 | -13.92 | -20.88 | 0.6% | $-643 |
| SPY/IWM 🚩 | polygon/polygon | 501 (300/201) | 38.6 | 38 | 8 | 0.0% | -9.49% | -25.45 | -71.97 | -121.11 | 0.8% | $-756 |
| QQQ/IWM 🚩 | polygon/polygon | 501 (300/201) | 53.7 | 53 | 6 | 0.0% | -9.74% | -8.14 | -19.93 | -31.32 | 0.6% | $-583 |
| SPY/DIA 🚩 | polygon/polygon | 499 (299/200) | 46.7 | 46 | 8 | 0.0% | -9.82% | -14.88 | -42.09 | -59.76 | 0.8% | $-783 |
| XLF/XLE 🚩 | polygon/twelvedata | 501 (300/201) | 36.9 | 36 | 8 | 0.0% | -10.71% | -2.53 | -7.15 | -10.36 | 0.9% | $-854 |
| XLI/XLB 🚩 | twelvedata/twelvedata | 1000 (600/400) | 405.0 | 60 | 13 | 0.0% | -9.69% | -8.99 | -32.41 | -32.54 | 1.2% | $-1,252 |
| EWA/EWC 🚩 | twelvedata/twelvedata | 999 (599/400) | 37.4 | 37 | 17 | 0.0% | -10.12% | -7.20 | -29.69 | -29.28 | 1.7% | $-1,706 |
| BTC/ETH 🚩 | binance/binance | 1000 (600/400) | 815.0 | 60 | 8 | 0.0% | -13.64% | -1.92 | -5.44 | -5.26 | 1.1% | $-1,086 |

## 2. Renaissance Setups on Real US Equities

Universe: AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, SPY, QQQ, IWM

| Setup | Trades | Win% | Expectancy | Per-trade Sharpe | t-stat | Ann Sharpe | Total PnL |
|---|---|---|---|---|---|---|---|
| OSbounce | 62 | 56.5% | +1.55% | +0.34 | +2.68 | +2.42 | $+28,695 |
| High52w | 65 | 41.5% | +0.36% | +0.12 | +0.97 | +0.85 | $+8,647 |
| OutsideRevLong 🚩 | 15 | 53.3% | +0.33% | +0.10 | +0.39 | +0.72 | $+1,846 |
| Breakout | 178 | 50.6% | +0.26% | +0.08 | +1.10 | +0.58 | $+17,408 |
| TurnOfMonth | 47 | 44.7% | +0.06% | +0.02 | +0.12 | +0.12 | $-679 |
| ConnorsLong | 323 | 41.8% | -0.02% | -0.01 | -0.08 | -0.03 | $+1,256 |
| KeyRevLong | 38 | 42.1% | -0.02% | -0.01 | -0.03 | -0.04 | $-1,000 |
| PinBarLong | 110 | 42.7% | -0.04% | -0.01 | -0.12 | -0.08 | $+305 |
| Pullback | 138 | 42.8% | -0.36% | -0.10 | -1.22 | -0.74 | $-2,130 |
| RangeBreak | 29 | 41.4% | -0.34% | -0.11 | -0.59 | -0.78 | $-3,498 |
| TrendRide50 | 448 | 40.8% | -0.33% | -0.11 | -2.36 | -0.79 | $-52,906 |
| **BLENDED** | **1453** | **43.6%** | **-0.03%** | **-0.01** | **-0.34** | **-0.06** | **$-2,056** |

### Per-symbol breakdown

| Symbol | Trades | Win% | Expectancy | Total PnL |
|---|---|---|---|---|
| IWM | 139 | 56.1% | +0.50% | $+40,073 |
| MSFT | 138 | 45.6% | -0.04% | $+5,363 |
| AAPL | 154 | 43.5% | +0.17% | $+1,866 |
| GOOGL | 143 | 39.9% | -0.02% | $+406 |
| META | 102 | 39.2% | +0.01% | $-1,389 |
| QQQ | 164 | 43.9% | +0.04% | $-4,204 |
| SPY | 210 | 47.1% | -0.02% | $-6,550 |
| NVDA | 152 | 37.5% | -0.33% | $-7,532 |
| AMZN | 144 | 41.0% | -0.20% | $-11,314 |
| TSLA | 107 | 38.3% | -0.52% | $-18,775 |

## Key takeaways

> **These are real-data numbers, not synthetic.**
>
> The synthetic OU Sharpe +6/+24/+34 from `backtest_report.md` described the
> *model*, not the *market*.  The numbers in this file are what the market
> actually gave us over the last ~2-4 years of daily bars.

- **RV pairs**: 0/8 pairs had positive OOS Sharpe. 0/8 had ≥20 trades (credible sample).
- **Renaissance setups blended**: OOS ann Sharpe -0.06 over 1453 trades, t-stat -0.34.
  - ⚠️ Blended edge is **NOT** statistically significant (|t| < 2).

> **Next steps**: (1) extend history to 5-10 years via a paid Polygon tier
> or yfinance; (2) walk-forward re-fit the OU half-life periodically, not
> just once at the IS/OO split; (3) add a stop-loss to RV trades to cap max DD.
> (Transaction costs ARE now applied: IBKR retail ~10bp RT on 2-leg spreads,
> converted to stdev units via the 1-sigma-risk sizing convention.)
