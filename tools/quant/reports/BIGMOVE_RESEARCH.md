# BIGMOVE — Next-Day Huge-Return (>=5%) Prediction: Can We Hit 70% Precision?

**Date**: 2026-08-13  
**Ask**: "Develop strategies to predict next-day huge return (>=5%). Trade
when the probabilities are large (maybe >70%). Backtest."
**Return definition**: `next_day_close / today_close - 1` (user-specified).
Signal built from info available at today's close only.

---

## TL;DR — Honest verdict

**A >=5% next-day hit rate of ~70% is NOT achievable from daily OHLCV
technical data.** We developed a rigorous, no-look-ahead ML pipeline and ran an
8.5-year out-of-sample walk-forward (2018-2026). The model has a genuine,
statistically significant edge (out-of-sample ROC-AUC ~0.82, ~10-18x precision
lift over the ~1.6% base rate), but the *maximum* precision it reaches at the
top-confidence bucket is only:

| target | precision @ pred≥0.7 | precision @ pred≥0.9 |
|--------|---------------------|---------------------|
| next-day ≥ +5% (long) | ~10% | ~16% |
| next-day ≥ +3% (long) | ~19% | ~28% |
| \|next-day\| ≥ 5% | ~19% | ~30% |
| next-day ≤ -5% (short) | ~8% | ~9% |

Nobody reaches 70%. **This is not a tuning failure — it is a data ceiling.**

---

## Data
- **Universe**: 285 US large-cap common stocks, `twelve_big` daily panel
  (2006-09 .. 2026-08), excluding ETFs/ADRs (QQQ, SPY, XLF, ASML, HMC, TM).
- OHLCV daily bars.
- ~1.31M stock-day observations. Base rate of next-day ≥ +5% = **~1.6%**.

## Methodology (no look-ahead)
1. **Target**: `y[T] = 1[ close[T+1]/close[T]-1 >= +5% ]`.
2. **Features (49)**: multi-horizon momentum (1/2/3/5/10/20/60/120/250d),
   realized vol (5/10/20/60d), scaled momentum, RSI-14, distance-to-MA
   (5/20/60/200), intraday range & close position, overnight gap, log-volume &
   volume ratios, per-stock vol-normalized moves, market-relative moves,
   historical per-stock big-move frequency, 5d high/low distance, breakout
   proximity, volume-return confirmation.
3. **Model**: `HistGradientBoostingClassifier`, class-balanced for the rare
   positive class.
4. **Walk-forward**: retrained quarterly on a rolling 3-year window strictly
   before each prediction window. Data leakage is impossible by construction.

## Results (out-of-sample, 2018-2026)
- ROC-AUC ~0.82 on test — real predictive signal for *relative* risk.
- Precision caps shown in the table above — the model correctly ranks stocks
  that are *relatively more likely* to jump, but never concentrates certainty
  to 70%.
- Estimated profitability of the long-only rule (even below 70%):
  - threshold ≥ 0.9, target ≥5%: avg **+0.18% net/trade**, daily-EW Sharpe
    ~0.63, ann ~+22%, but MaxDD ~-48%, ~3.4 signals/day (concentrated).
  - threshold ≥ 0.7: Sharpe ~0.27, ann ~+2.9%, MaxDD ~-67%.

## Why 70% is unreachable with this data
A single-day >=5% move in a large-cap is dominated by **unanticipated
idiosyncratic news**: earnings surprises, guidance changes, FDA/legal rulings,
macro shocks, sector-specific events. Daily OHLCV bars simply do not contain
the information that would be required to know *when* such news lands and
*what* it will say. The ~10-30% precision cap corresponds exactly to the
"volatility-regime/momentum" component that IS forecastable; the rest is noise.

## What would be required to move toward 70% (not present in this dataset)
- **Earnings calendar + consensus estimates** (big-move days cluster heavily
  at earnings; this is the single most powerful missing feature).
- **Analyst revisions / ratings changes** (much of the information that moves
  a single-day return).
- **News/NLP event data** (headlines, FDA, guidance).
- **Options flow / unusual activity** (reveals informed positioning).
- **Level-2 / order-flow microstructure**.

## Recommendation
- **Do not deploy the OHLCV-only version** as a standalone "70% big-move"
  strategy — the precision is far below the target and concentration/drawdowns
  are severe.
- If the objective is *weakly* to harvest the asymmetric payoff of rare big
  moves, the model can serve as a **small-risk overlay / enhancement** on an
  existing book (the >=0.9 bucket has positive expected value net of costs),
  but with strict sizing given ~16% precision on a fat-tailed payoff.
- To genuinely reach ~70%, the next investment is **earnings-calendar and
  news features**, not more technical features.

## Artifacts
- Code: `tools/quant/bigmove/` (see `README.md`).
- Results:
  - `tools/quant/reports/bigmove_walkforward_results.json`
  - `tools/quant/reports/bigmove_multi_target_diag.json`
  - `tools/quant/reports/bigmove_equity_by_threshold.csv`
  - `tools/quant/reports/bigmove_equity_vs_spy.png`
