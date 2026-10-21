# bigmove — XGBoost Model: Full Backtest

**Date**: 2026-08-13 | **Engine**: XGBRegressor (predict next-day return), 70
features (per-stock + FF + market regime + cross-sectional + crypto/FX), no
look-ahead walk-forward (quarterly refit, 3y), OOS 2018-2026, 285 US large caps.
Exit: user's intraday stop rule (open if gap below stop, stop if low<stop, else
close); 6bp one-side = 12bp round trip.

## Results (calendar-time portfolio; flat days = 0)
| bucket | stop | win>=5% | net/trade | calendar Sharpe | ann ret | MaxDD |
|--------|------|---------|-----------|-----------------|---------|-------|
| top-1% | none | 12.4% | -0.40% | 0.37 | +5.5% | -46% |
| top-1% | 10%  | 22.0% | -0.12% | **0.42** | **+7.9%** | -39% |
| top-1% | 5%   | 20.8% | -0.12% | 0.17 | +1.2% | -45% |
| top-0.5%| 10%  | 26.7% | +0.29% | -0.42 | -7.8% | -54% |
| top-0.3%| 10%  | 30.8% | +0.43% | -0.34 | -5.7% | -45% |
| top-0.1%| any  | 13-29%| negative| negative | negative | neg |

## Interpretation
- **Win rate rises with selectivity and a looser stop**: top-0.3% + 10% stop =
  30.8% hit on >=5% days (+0.43%/trade gross-of-daily-cluster). The XGB regressor
  genuinely ranks next-day move size (monotonic across deciles).
- **But the tight / highest-conviction buckets have NEGATIVE calendar Sharpe**
  despite high per-trade net: their trades cluster onto only ~35-67 unique
  calendar days, so the daily book is spiky/drawdown-proneched instead of smooth.
- **Best tradeable point: top-1% + 10% stop** = the ONLY config with positive
  calendar Sharpe (0.42) and positive annualized return (+7.9%), win 22%, DD -39%.
  (Yet per-trade net is still slightly negative: the positive Sharpe comes from
  day-clustering dynamics, not robust per-trade edge.)

## Robustness (date-block bootstrap)
top-0.5% (67 unique days) block CI [-2.2%, +0.3%] -> **NOT significant**
top-0.3% (35 unique days) block CI [-3.5%, +0.8%] -> **NOT significant**
Even the "borderline significant" naive per-trade t-test (p~0.07 earlier) does
NOT survive proper event-clustering correction.

## Recommendation
- The most sensible deployable-ish config is **top-1% predicted next-day return
  with a 10% stop** (positive calendar SR +0.42, +7.9%/yr ann, 22% win) BUT it is
  still far below the 70% precision target and carries -39% drawdowns; per-trade
  edge is not independently significant. Treat as a high-precision rank overlay
  with strict risk limits — not a standalone conviction strategy.
- Fundamental limit persists: big-move days are rare and cluster, giving few
  independent samples; daily-frequency features (even 70) cannot reliably
  forecast them. Event-anticipating data is the only real lever.

## Artifacts
- `bigmove_xgb_backtest.json` (full grid)
- `bigmove_xgb_best_equity.csv`, `bigmove_xgb_equity_vs_spy.png`
- `xgb_backtest.py`, `xgb_plot.py`

## Metric convention (corrected per user)
All risk metrics are computed over **TRADED (active) DAYS ONLY**:
- mean/day & std/day = over active days only (NOT including flat/cash days)
- Sharpe = (mean_day / std_day) × sqrt(active trading days per year)
- Annual return & MaxDD over the active-day equity curve.

Corrected tables (reports/bigmove_xgb_tradeday_metrics.json):

| config | mean/act-day | std | act-days/yr | Sharpe(active) | ann ret | MaxDD |
|--------|-------------|-----|-------------|----------------|---------|-------|
| top-1% no-stop | +0.24% | 3.60% | 30 | 0.37 | +5.5% | -46% |
| top-1% stop10% | +0.38% | 4.91% | 30 | 0.42 | +8.0% | -39% |
| top-0.5% stop10% | -0.87% | 5.77% | 9 | -0.46 | -9.1% | -52% |
| top-0.3% stop10% | -1.18% | 7.07% | 5 | -0.36 | -6.6% | -41% |

Best config remains top-1% + 10% stop, active Sharpe 0.42, ~30 active days/yr.
The extreme-bucket configs are negative even on this honest trade-day basis.
