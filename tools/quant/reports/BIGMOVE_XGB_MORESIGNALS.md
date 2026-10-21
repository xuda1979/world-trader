# bigmove — XGBoost + Exogenous Signals: Genuine Precision Gain, Still No Significant Edge

**Date**: 2026-08-13
**Ask**: "include more signals" + "build xgb models to predict next day return."

## What was added
1. **XGBoost** (libomp fixed; `XGBClassifier` for P(>=5%) + `XGBRegressor` for
   next-day return magnitude) — no-look-ahead walk-forward (quarterly refit, 3y).
2. **More signals** (49 -> **70 feature families**):
   - Fama-French factors (MktRF, SMB, HML, MOM)
   - Market regime (SPY momentum 1/5/21/63d, vol 10/21/63d, vol-ratio, dist-to-200ma)
   - Cross-sectional breadth (share of universe in high chop, avg vol, vol-ratio)
   - Crypto (BTC) + FX (EURUSD) risk-on proxies

## Results (OOS 2018-2026)

### A. Classifier (P(next-day>=5%)) — no better than before, marginal/negative
| thr | win>=5% | avg net/trade | t | p |
|-----|--------|---------------|-----|-----|
| 0.9 | 12.1% | -1.02% | -4.4 | <0.001 |
All thresholds negative net; classifier is not the right engine.

### B. Regression (predict next-day return) — the right engine, right tail
| bucket | n | win>=5% | avg net/trade | SR | t | p |
|--------|-----|--------|---------------|-----|-----|-----|
| top 0.3% | 1,820 | **31.3%** | +0.42% | 0.044 | 1.89 | 0.059 |
| top 0.5% | 3,032 | 26.9% | +0.28% | 0.033 | 1.83 | 0.067 |
| top 1.0% | 6,064 | 22.2% | -0.12% | -0.016 | -1.27 | 0.206 |

Decile check (regression ranking is monotonic): top decile win5 6.28% vs ~1%
for middle deciles -> the model genuinely ranks next-day return magnitude.

## The decisive robustness test (date-block bootstrap)
Naive per-trade t-test (p~0.06) OVERSTATES significance because the extreme-top
trades CLUSTER on a handful of high-volatility days (few independent events).
Date-block bootstrap (10-day blocks) on the top-0.5% mean:
  observed daily-mean -0.008%, 95% CI [-1.9%, +0.3%] -> **includes <=0**.
=> The positive per-trade point estimate is NOT statistically robust once
autocorrelation / event-clustering is accounted for.

## Honest verdict
Adding exogenous signals + XGBoost + regression was genuinely productive:
- Precision (win>=5% in top bucket) more than doubled: ~16% -> ~31%.
- The regression model is a real RANKER of next-day return magnitude.
But the tradable per-trade edge remains **statistically fragile** (block CI
spans zero). Root cause is fundamental: a >=5% single-day move is a rare,
news-driven event; firing only on extreme predictions concentrates trades onto
a few regime days -> very few independent observations -> cannot establish a
robust positive edge from this data.

**Recommendation**: The regression signal is a useful high-precision *rank*
(~31% win in the top 0.3%) and could anchor a disciplined overlay, but it should
NOT be deployed as a standalone expected-positive strategy — the edge is not
statistically reliable and extreme buckets cluster risk. To make it robust you'd
need many independent event-days (longer/spliced history) or genuinely
event-anticipating data (earnings/news), which is what determines these moves.

## Artifacts
- `bigmove_xgb_results.json`, `bigmove_xgb_equity.csv`
- `data/xgb_pred_frame.parquet` (cached OOS regression+classifier predictions)
- `xgb_walkforward.py`, `features3.py` (70-feature exogenous pipeline)

### Final robustness check (top-0.3% best bucket)
- 1,820 trades cluster on ONLY **35 unique calendar days** (~52 trades/day).
- So ~1,820 trades = effectively ~**35 independent events**.
- Date-block bootstrap mean -0.013%, 95% CI [-3.8%, +1.2%] -> **NOT significant**.

**Why win5=31% is misleading**: the strategy fires its top signals all on the
same handful of high-volatility regime days, so the impressive precision is
driven by a few days, not 1,820 independent chances. When correctly treated as
~35 independent events, the edge is not statistically distinguishable from zero.

**Conclusion**: even with 70 features + XGBoost regression, the tradable edge
cannot be established as robustly positive. This is the data ceiling for
daily-frequency big-move prediction.
