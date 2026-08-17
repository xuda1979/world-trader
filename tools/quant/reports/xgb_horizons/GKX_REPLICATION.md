# GKX (Gu-Kelly-Xiu 2020) Replication — Best Efforts with FREE Data

**Date:** 2026-08-17
**Goal:** replicate Gu, Kelly & Xiu (2020) "Empirical Asset Pricing via Machine
Learning" (RFS) monthly long/short Sharpe using only free data.

## Setup (best efforts)
- **Universe:** 292 US large caps (local twelve_big panel, 20y daily OHLCV).
- **Characteristics (33):** ~24 technicals from local daily prices (momentum
  1/3/6/12m + 12-1, vol 3/12m, maxDD, Amihud, 52w hi/lo distance, beta,
  cross-sectional dispersion, skew/kurt, volume z) + **7 free fundamentals**
  (Finnhub stock/metric, free tier: market cap, ROE, revenue growth, asset
  turnover, PE, EPS growth, div yield) + earnings surprise/proximity (local
  earnings panel) + macro state & interactions (VIX z, mkt 3m).
- **Models:** Ridge (linear baseline), XGBoost GBRT, MLP 3-layer NN (32-16-8,
  GKX-style architecture).
- **Validation:** monthly, PURGED walk-forward (train on months <= m-1 to
  predict month m+1 return; NO label overlap), 7y rolling window, yearly
  refit. OOS 2009-2026 (211 months).
- **Portfolio:** monthly decile L/S, equal-weight AND market-cap-weight,
  gross AND net (6bp/side full cycle = 24bp/mo).

## Results (OOS 2009-2026, decile L/S)

| Model | EW gross SR | EW net SR | VW gross SR | VW net SR |
|---|---|---|---|---|
| Ridge | -0.57 | -0.96 | -0.58 | -0.97 |
| **XGB (GBRT)** | **+0.21** | **-0.04** | **+0.23** | **-0.02** |
| MLP (NN) | -0.26 | -0.68 | -0.23 | -0.68 |
| *GKX 2020 (ref)* | *2.45* | *gross* | *1.35* | *gross* |

## Honest conclusion: Gu's result does NOT replicate with free data
The best model (XGB) achieves **SR +0.21 gross, ~0 net** — about **1/10 of
GKX's equal-weighted 2.45**. The gap is structural, not methodological:

1. **Universe (292 vs ~30,000 stocks).** GKX's equal-weighted 2.45 Sharpe
   lives in the small/micro-cap tail — they explicitly note the EW strategy
   tilts to micro-caps and is hard to implement at scale. Their implementable
   value-weighted Sharpe is 1.35; on large caps alone it would be materially
   lower. We trade 292 liquid large caps — the least alpha-dense part of the
   cross-section.
2. **Characteristics (33 vs 94+).** GKX uses point-in-time CRSP/Compustat
   fundamentals (value, profitability, investment, accruals, payout, etc.) —
   the proven drivers. Free data gives us technicals + 7 current-snapshot
   fundamentals (no history: the model cannot learn time-varying fundamental
   signals; PB and leverage are premium metrics, all-null on the free tier).
3. **Costs.** GKX reports gross; with honest 24bp/month full-cycle costs our
   best model's edge (~0.2%/mo gross) is fully consumed.

## What would be needed to approach GKX (none free)
- CRSP universe (all US stocks incl. micro-caps) + Compustat point-in-time
  fundamentals -> the two data sources ARE the edge.
- Realistic borrow/cost modeling would still cut their headline numbers
  (their own paper notes the EW 2.45 is largely micro-cap/illiquid).

## Honest bottom line
With free data on a large-cap universe, the GKX-style ML monthly L/S is
**not profitable net of costs (best: XGB, SR ~0)**. The 2.45 Sharpe is a
data-advantage + micro-cap-tilt result, not a free-data-large-cap result.
This is consistent with the desk's own leak-free measurement (IC ~0.02 on
large caps) and with the published literature's practical conclusion that
net-of-cost large-cap monthly ML Sharpe sits around 0.5-1.0 at best.

## Artifacts
- `gkx_monthly.py` — monthly characteristic panel builder (free data).
- `gkx_backtest.py` — purged walk-forward ML + decile L/S (ridge/xgb/mlp,
  EW/VW, gross/net).
- `data/gkx_monthly_panel.parquet`, `data/gkx_names.json`,
  `data/finnhub_metrics.json` (fetched fundamentals), `gkx_results.json`.
- Re-run: `python3 gkx_monthly.py` (needs finnhub_metrics.json) then
  `python3 gkx_backtest.py`.
