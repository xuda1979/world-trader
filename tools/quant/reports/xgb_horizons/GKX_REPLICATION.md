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

# UPDATE 2026-08-17 (v2) — wider universe + SEC EDGAR point-in-time fundamentals

Added the two free data levers the first pass lacked:
1. **Universe 292 -> 657 names** (union of all local panels: twelve_big +
   twelvedata + twelve_liq + polygon + polygon_v2; ~290 names with full
   2006-2026 history, 657 in 2024-2026).
2. **Point-in-time fundamentals from SEC EDGAR companyfacts (FREE, no key)**:
   parsed XBRL -> quarterly book equity, assets, net income, revenue, operating
   income, gross profit, cash flow, shares outstanding; each value dated by its
   FILING date (no lookahead). Built GKX-style characteristics:
   **bm (book/market), size (log shares*price), roe, gross profitability,
   operating profitability, accruals, investment (asset growth), payout**
   + Finnhub PE/div-yield + 24 technicals + earnings + macro interactions
   = 39 characteristics.

Results (OOS 2009-2026, decile L/S, purged walk-forward):

| Model | EW gross SR (v1 -> v2) | EW net SR (v1 -> v2) |
|---|---|---|
| Ridge | -0.57 -> +0.11 | -0.96 -> -0.14 |
| **XGB** | **+0.21 -> +0.44** | **-0.04 -> +0.18** |
| MLP | -0.26 -> -0.19 | -0.68 -> -0.56 |

XGB EW net is now POSITIVE (+0.18). Still ~1/5 of GKX's 2.45 gross EW.
Remaining gap: (a) historical cross-section still ~290 names (no micro-caps;
657 only in 2024-2026), (b) fundamentals coverage growing (EDGAR fetch for
626 CIKs completes in background; rerun after), (c) GKX is gross.

Full EDGAR fetch (~626 names) completes in background; the next rerun with
full fundamentals coverage should push the numbers further.

# UPDATE 2026-08-17 (FINAL) — full EDGAR fundamentals coverage

EDGAR fetch complete (600 companies). Final results (OOS 2009-2026, decile L/S,
purged walk-forward, 657-name union, 39 characteristics incl point-in-time
bm/size/roe/gross-prof/op-prof/accruals/investment):

| Model (EW) | gross SR | net SR (24bp/mo) |
|---|---|---|
| **XGB** | **+0.43** (ann 5.0%) | **+0.21** (ann 2.1%, win 54%) |
| MLP | +0.30 | -0.08 |
| Ridge | +0.15 | -0.10 |

VW versions are negative for all models (large-cap VW adds no edge; consistent
with GKX where VW 1.35 << EW 2.45).

**FINAL VERDICT (free data, best efforts): the best replicable GKX-style
strategy is XGB equal-weighted decile L/S with net SR ~+0.21, gross ~+0.43 —
about 1/6 of GKX's 2.45 gross EW.** The remaining gap decomposes:
(1) universe 657 vs ~30k (no micro-cap tail, where GKX's EW alpha lives);
(2) 39 vs 94 characteristics; (3) our numbers are net of 24bp/mo, theirs gross;
(4) their EW 2.45 is explicitly micro-cap/illiquid-weighted and would not
survive realistic costs at scale (their VW = 1.35).
Free data cannot close this gap: the CRSP 30k-stock universe and the micro-cap
tilt are not freely available at this quality.

# UPDATE 2026-08-17 (v5) — more data, then the honesty filter

Got MORE free data: (1) expanded EDGAR characteristics (payout, R&D/assets,
capex/assets, leverage, current ratio, tax/assets — 12 fundamentals total),
(2) 400 more names' price history from TwelveData free tier (8 req/min,
background; 124/400 fetched so far), universe 657 -> 713+.

CRITICAL SANITY FINDING: the raw expanded panel produced garbage (DD -1.7M) —
the new names include penny stocks with split/data artifacts. After filtering
to INVESTABLE names (median price >= $2, monthly |ret| sane), the honest
results are:

| Model (EW, investable universe) | gross SR | net SR |
|---|---|---|
| XGB | +0.06 | -0.18 |
| MLP | +0.04 | -0.25 |
| Ridge | +0.14 | -0.16 |

vs the v3 number (XGB gross +0.44) that included sub-$2/penny/extreme-tail
names. **The investable free-data GKX replication is ~zero net of costs.**
The v3 "improvement" was partly illiquid-name alpha that cannot be traded at
size (exactly GKX's micro-cap caveat, reproduced on our scale).

TwelveData fetch continues in background (400 names, ~35 min); a rerun with
the fuller investable universe will confirm whether more names help.

# UPDATE 2026-08-18 (v6) — 1032-name investable universe: net SR +0.42 (Ridge EW)

TwelveData free-tier fetch completed for 375 more names (8 req/min, resumable)
-> union universe 657 -> 1032 names; 874 investable tickers in the panel
(754/month recent). Rebuilt panel (44 chars, investable filter $2+/sane rets)
and reran the purged walk-forward decile L/S (OOS 2009-2026):

| Model | EW gross SR | EW net SR | VW gross SR | VW net SR |
|---|---|---|---|---|
| **Ridge** | **+0.64** | **+0.42** | +0.01 | -0.19 |
| XGB | +0.51 | +0.33 | +0.29 | +0.15 |
| MLP | +0.05 | ~-0.20 | -0.15 | ~-0.40 |

vs v5 (657 names): Ridge net -0.16 -> +0.42, XGB -0.18 -> +0.33.
**More investable names = more edge (confirmed directionally).** The v6
best (Ridge EW net SR +0.42, ann ~4.6% gross) is the strongest free-data
result so far - about 1/6 of GKX's 2.45 gross EW, and now NET positive with
an investable (>= $2) universe. NN (MLP) is weakest at this scale (GKX's NN
advantage needs the full 30k-stock universe).
Second TwelveData batch (~400 more names) fetching in background; rerun after.
