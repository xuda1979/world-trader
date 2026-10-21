# Hourly XGB Next-Close Prediction — US Equities (Intraday POC)

**Date:** 2026-08-15
**Objective:** Predict next-hour close from hourly bars for a basket of US
equities. If the predicted next-hour close is **≥ +2% above the current close**,
buy now (at current close) and liquidate at next-hour close. Trading cost 6 bps
per side (12 bps round-trip). Maximize feature usage. Backtest.

## Data & Setup
- Source: `tools/quant/data/polygon_intraday/` — 5-min polygon bars for **17
  liquid US names** (AAPL, META, ORCL, QCOM, TXN, NOW, CRM, MU, INTC, JMJ-like
  defensive names, etc.).
- Span: **2024-12-02 → 2025-06-16** (~6 months, ~134 sessions, 17 names).
- Resampled to **regular-session hourly bars** (10:00–16:00 ET, 7 full bars/day).
- Panel: 932 hourly stamps × 17 tickers → 10,734 complete (feature+target) rows.

## Features (very rich, all causal at bar-close T)
Per-ticker: return horizons (1/2/3/6/12/24h), realized vol (3/6/12/24h),
distance-from-MA (6/12/24/48), 12-bar position-in-range, RSI(14), hour-of-day,
day-of-week.
Cross-sectional / market (known at T): equal-weight hourly market return
(1/2/3/6h), cross-sectional dispersion (6/12h), rolling market vol (6/12h),
market breadth (share of universe up that hour).
Total: **41 feature families → 41×17 = 697 model columns.**

## Model
- XGBoost regressor (300 trees, depth 5, lr 0.05, subsample .8, colsample .8).
- Target: next-hour return `close(T+1)/close(T)-1` — i.e. exactly the "next hour
  close vs now" the user wants (entered at close T, exited at close T+1).

## Results
**Predictive power: essentially ZERO (out-of-sample).**
- Single 70/30 split: train RMSE 1.02% vs hourly std 0.86%; IC = +0.026 (weak,
  likely split-luck).
- **Proper expanding walk-forward (retrain every 20 days): OOS IC = −0.007
  ≈ 0.** The model cannot predict next-hour closes from past bars.

**Strategy backtest (net of 12 bps round-trip), walk-forward OOS (4,352 rows):**

| predicted≥ (thresh) | #trades | gross | net | winrate | bootstrap p-value |
|---|---|---|---|---|---|
| 2.0% | 8 | +2.7% | **+1.7%** | 62% | 0.51 (no edge) |
| 1.5% | 25 | +7.7% | **+4.5%** | 48% | 0.52 (no edge) |
| 1.0% | 59 | +22.5% | **+14.1%** | 54% | 0.50 (no edge) |
| 0.8% | 88 | +9.8% | −1.2% | 48% | — |
| 0.5% | 182 | +7.1% | −13.9% | 43% | — |
| 0.0% (all) | 1979 | −52% | −96% | 36% | — |

## Why the strategy does not work (honest root-cause)
1. **A +2% single-hour move is rare and news-driven.** Base rate of next-hour
   return > +2% is only ~2% across the universe. Such moves are driven by
   earnings/surprises, not predictable from past hourly bars.
2. **No forecastable signal**: walk-forward IC ≈ 0 ⇒ the model's high-prediction
   buckets are not meaningfully more likely to deliver +2%. Apparent profit at
   2%/1.5%/1% thresholds is from **8/25/59 trades clustered on 7/10/16 dates**
   and a few tickers (ABBV heavy) — block-bootstrap p ≈ 0.5 ⇒ indistinguishable
   from noise.
3. **12 bps round-trip is a huge hurdle at hourly frequency.** Below the ~0.8%
   threshold, costs overwhelm any signal and net return collapses to deeply
   negative as trade count rises.

## Recommendation
Do **NOT** trade this strategy. The available intraday sample (~6 months, 17
names) is far too short to establish hourly edge, and the target itself (next-
hour close) is fundamentally near-unpredictable from bar features (IC≈0). If an
hourly strategy is desired, the path forward is:
1. Acquire **multi-year** tick/1-min intraday history for a large universe
   (Polygon/TWELVE paid tiers) — 6 months is not enough.
2. Re-frame the trade to a **statistical intraday mean-reversion / momentum**
   signal with faster hold and realistic fills, benchmark against baseline
   costs, and require walk-forward IC and block-bootstrap p<0.05 before any go.

## Artifacts
- `hourly_main.py` — data prep (intraday→hourly), feature build, single-split
  model + 2% backtest.
- `hourly_backtest.py` — proper expanding walk-forward backtest + threshold sweep.
- `data/hourly_oos_frame.csv` — all walk-forward OOS predictions/targets.
- `data/hourly_xgb_model.json`, `data/hourly_trades.csv` — first-pass artifacts.

## Addendum (2026-08-15, continuation) — triple confirmation of NO edge
Additional tests to rule out every alternative explanation:

**1. Cross-sectional relative signal (long top-K / short bottom-K by predicted
next-hour return) — NEGATIVE even gross of costs:**
- Per-hour cross-sectional IC = **−0.031** (median −0.021), n=382 hours
  ⇒ model's relative rankings are anti-predictive out-of-sample.
- L/S top/bottom-K equal-weight: K=2 −0.04%/hr, K=4 −0.03%/hr, K=6 −0.06%/hr
  (all negative BEFORE any costs), hourly Sharpe **−3.0 to −7.2**.
  ⇒ No relative (not just absolute) edge exists.

**2. Permutation / random-label null on the exact 2% rule:**
- Observed net +1.73% (N=8 trades) sits at the **15.2nd percentile** of the
  pure-chance null — i.e. 85% of random trade-labels beat it; two-sided
  p = 0.52. Indistinguishable from chance. (Consistent with block-bootstrap
  p≈0.5 above.)
- Gross (0-cost) +2.71% also at the 15th percentile of the null — the profit
  is exactly what random picks would produce (model adds nothing).

**Bottom line:** the hourly next-close strategy fails on BOTH absolute and
relative formulations, in every significance test (walk-forward IC≈0,
cross-section IC<0, permutation p≥0.15, block-bootstrap p≈0.5), and standard
12 bps round-trip costs turn even thin apparent profits deeply negative.
**Verdict held: do not trade.**
