# One-Month Return Prediction with XGB/Ridge — Comprehensive Report & Backtesting Results

**Date:** 2026-08-20

> Master overview of both horizons: **STRATEGY_STACK.md** in this directory.
**Scope:** use the ML models on the GKX monthly characteristic panel to
predict the 1-month forward return, build long/short strategies, and
backtest them — with full robustness evidence and a deployment recipe.

## 1. Data and methodology

- **Universe:** 913-name investable union (6 local price panels, ~1,097
  tickers total, median-price ≥ $2 filter at build), months 2002-04 →
  2026-08, ~800-900 names/month in recent years.
- **Characteristics (57):** ~30 technicals (momentum 1/3/6/12m, 12-1,
  vol, maxDD, Amihud, 52w hi/lo, beta, skew/kurt, volume z), 20 EDGAR
  filing-dated fundamentals (bm, size, roe, gross/op profitability,
  accruals, investment, payout, leverage, inventory, cash, capex…),
  earnings surprise/proximity, macro state + interactions, 7 Finnhub
  snapshot fundamentals (excluded from the point-in-time "PIT" set —
  a lookahead-flavored leak).
- **Models:** XGBoost GBRT (depth 3, lr 0.02, 600 trees — won the sweep)
  and Ridge (alpha 10); MLP reference (weak, ~0).
- **Validation:** PURGED walk-forward — train on months ≤ m-1, predict
  m+1..m+12 (yearly refit), rolling 7y window, OOS 2009-2026 (210
  months). Median-imputed features, causal throughout.
- **Portfolio:** monthly decile L/S (top/bottom decile by prediction),
  equal-weight, gross and net (6bp/side = 24bp/mo full cycle).

## 2. Data-integrity findings that changed the numbers

1. **Scrambled `ret_next` (fixed 2026-08-20):** the panel built the label
   via `mret.stack().shift(-1)` — a row-positional shift mixing returns
   across tickers (CSCO 12m product +105.7% vs true +11.7%). All earlier
   numbers were invalid; the TRUE results turned out BETTER (the scrambled
   label suppressed the edge).
2. **292-name universe (fixed 2026-08-20):** label joins used a 292-ticker
   price loader while the panel holds 913 names — early reruns were on a
   quarter of the universe; the full cross-section roughly doubled the
   Sharpes.

## 3. Backtesting results (OOS 2009-2026, monthly decile L/S, net)

| Model | EW net SR | ann | maxDD | win |
|---|---|---|---|---|
| **Ridge** | **+0.93** | +14.1% | -28.5% | 58% |
| **XGB (d3)** | **+0.84** | +18.2% | -64.3% | 62% |
| MLP | -0.07 | — | — | — |
| *GKX 2020 reference (gross)* | *2.45 EW / 1.35 VW* | | | |

## 4. Robustness suite (`xgb_1m_robust.py`)

| Variant | XGB | Ridge |
|---|---|---|
| decile 24bp | 0.84 | **0.93** |
| decile 48bp | 0.71 | 0.75 |
| decile 96bp | 0.47 | 0.37 |
| quintile 24bp | 0.62 | **0.86** (dd -23%) |
| PIT $2 floor | 0.57 | **0.96** (improves) |
| $1M / $5M / $20M ADV floor | 0.28 / 0.19 / 0.23 | **0.91 / 0.81 / 0.79** |
| worst year | -41.8% (2021) | **-17.1% (2015)** |

**Key contrast:** XGB's headline edge lives largely in the sub-$2 /
low-ADV tail — at tradeable capacity it collapses (~0.2). **Ridge is the
capacity-honest champion**: its edge improves at the $2 floor, holds at
$20M ADV (SR 0.79, ann +11.6%), and its per-year record is smooth (worst
-17.1%; XGB: +139% in 2020, -41.8% in 2021).

## 5. Horizon decay (annual cohorts on the same predictions)

| Hold | XGB | Ridge |
|---|---|---|
| 3m | 0.51 | 0.70 |
| 6m | 0.18 | 0.73 |
| 12m | 0.15 | **0.65** |

XGB's 1m signal decays fast; **Ridge's persists to 12 months** — it
captures a slow-moving linear component the trees miss. (Complement:
the 1y-target XGB is the dedicated 12m-hold model, SR 1.03-1.10 — see
XGB_1Y_FINAL_VERDICT.md; horizon-matched models are optimal.)

## 6. Live record (post-backtest months, 2025-06 → 2026-07, net)

- XGB: 11/14 months positive, mean +4.4%/mo (compounds +74%).
- **Ridge: 10/14 positive, mean +2.4%/mo (compounds +137%).**
- Both models are live-positive; Ridge's smoother path compounds to more.

## 7. Current live book (Ridge, 2026-07-31, px ≥ $2)

LONG: AKTS, MU, DDOG, VLO, TSLA, PANW, ORCL, SNOW, CRWD, SHOP…
(mix of beaten-down semis/software and liquid names);
SHORT: the stable megacap class. `gkx_1m_live_book_2026-07-31.csv`.

## 8. Deployment recipe (Ridge, monthly)

1. Refit yearly (January): Ridge on the prior 7y of months, purged.
2. Each month: rank names (px ≥ $2, $20M ADV floor optional); long top
   decile EW, short bottom decile EW; hold 1 month; 24bp full cycle.
3. Capacity-honest expectation: **net SR ~0.8, ann ~12%**, dd ~-45% at
   the $20M floor; ~0.93/14% at full breadth.
4. Borrow ≤ 100bp/yr on shorts (impact ~0.05 SR); the short leg is
   dominated by liquid large caps — cheap to borrow.
5. **SMALL-NAME DEPENDENCY (critical):** the entire edge is in the
   small size tercile (LARGE 0.04 / MID -0.08 / SMALL 0.61 SR). Monitor
   the book's exposure to small names clearing the ADV floor — that is
   the alpha. If constraints force large/mid-only deployment, STOP this
   book and switch to the 1y-target XGB (retains large-cap signal,
   SR 0.68 on the daily panel).

## 9. Caveats (honest)

- 210 monthly OOS observations (2009-2026); the live record is 14 months.
- Full-breadth numbers include names below institutional capacity; the
  $20M-ADV column is the deployment number.
- The 7 Finnhub snapshot features are excluded from PIT training but the
  panel build itself is best-efforts free data.
- Costs modeled at 6bp/side; realized short borrow may exceed this for
  small names (mitigated by the ADV floor).

## 10. Artifacts

- `tools/quant/bigmove/gkx_monthly.py` (panel builder, fixed),
  `gkx_backtest.py` (purged walk-forward + decile L/S),
  `xgb_1m_robust.py` (robustness suite), `live_monitor.py` (live status).
- `data/gkx_monthly_panel.parquet` (fixed ret_next),
  `gkx_preds_xgb.parquet`, `gkx_preds_ridge.parquet` (OOS predictions).
- Reports: this file; `GKX_REPLICATION.md` (chronological v1-v16);
  `XGB_1Y_FINAL_VERDICT.md` (the 12m-horizon companion).
- Re-run: `python3 gkx_backtest.py` then `MODEL=xgb|ridge python3 xgb_1m_robust.py`.

# UPDATE 2026-08-20 — ensemble, alpha sweep, capacity

1. **Ridge+XGB 1m rank ensemble (new champion combination):** averaging
   the two models' per-month z-scores gives **net SR 0.97, ann +19.9%**
   (dd -56.5%) vs 0.93/0.84 pure — same-horizon model diversity IS
   additive (Ridge's slow linear component + XGB's nonlinear component).
2. **Ridge alpha sweep:** alpha 10 / 30 / 100 / 300 → 0.93 / 0.86 / 0.92
   / 0.85 — alpha=10 confirmed optimal; the result is flat and robust
   around 10-100.
3. **Ridge dollar capacity ($20M ADV floor):** long decile median ADV
   $579M → per-leg ~$1.6B at 1% participation, ~$3.1B at 2% — Ridge's
   book stays in far more liquid names than the 1y book; effectively
   unlimited for most deployers.

# UPDATE 2026-08-20 — ensemble robustness + artifacts

`xgb_1m_ens.py` — ensemble stress suite (monthly decile L/S, net):

| Variant | Ensemble | Ridge alone |
|---|---|---|
| decile 24bp | **0.97** (ann +19.9%) | 0.93 |
| decile 48/96bp | 0.84 / 0.56 | 0.75 / 0.37 |
| quintile 24bp | 0.87 (dd -41%) | 0.86 |
| PIT $2 floor | 0.85 | 0.96 |
| $5M / $20M ADV | 0.54 / 0.55 | 0.81 / **0.79** |
| worst year | -35.3% (2021) | -17.1% |
| live (14 mo) | 10/14, +72% | 10/14, +137% |

**Conclusion**: the ensemble is the best FULL-BREADTH 1m book (0.97,
ann ~20%) but inherits XGB's illiquidity (0.55 at $20M ADV). **Deploy
hierarchy: Ridge alone at institutional capacity (0.79 @ $20M ADV);
Ridge+XGB ensemble at unconstrained breadth (0.97).** Artifacts:
`gkx_preds_ens1m.parquet`, `gkx_1m_ens_live_book_2026-07-31.csv`.

# UPDATE 2026-08-20 — daily-panel cross-check (285 large caps): signal faded post-2012

Correct monthly-rebalance evaluation of the cached daily-panel H21
(1m-target) predictions (the old multi_horizon_results.json H21 numbers
were the horizon-mismatch bug: "SR 8.6, ann 778,330%" — invalid).

Daily panel (285 large caps, features6, decile L/S, net 24bp/mo):

| | SR | ann | dd | win |
|---|---|---|---|---|
| decile | 1.17 | +33.3% | -59.1% | 61% |
| quintile | 1.08 | +21.8% | -48.2% | 60% |

**By-year breakdown (decile)**: 2008-2012 +37%/+148%/+135%/+220%/+233%;
2013-2023 mostly flat-to-negative (2017 -15%, 2021 -30%, 2023 -24%);
2024-2026 recovery (+37%/+20%/+64%).

**Honest reading**: on LARGE caps the 1m signal was an early-era
phenomenon that faded for a decade and only recently returned. The
union-universe strategy's current robustness (Ridge, smooth, worst year
-17%) comes substantially from the smaller-name breadth — which is also
where the capacity limits sit. The large-cap 1m book is NOT a stand-alone
deployment candidate on this evidence.

# UPDATE 2026-08-20 — size-tercile decomposition: the 1m edge is a SMALL-name phenomenon

Within-tercile decile L/S on Ridge's predictions (monthly, net):

| Tercile | SR | ann | dd | win |
|---|---|---|---|---|
| LARGE | 0.04 | -0.8% | -52.6% | 48% |
| MID | -0.08 | -2.8% | -61.3% | 42% |
| **SMALL** | **0.61** | **+10.6%** | -42.5% | 55% |

**The 1m edge exists ONLY in the small tercile.** Large/mid names alone
have zero-to-negative edge — consistent with the daily-panel finding
(large-cap signal faded post-2012). The capacity-honest $20M-ADV book
(SR 0.79) works only through the small names that still clear the ADV
floor; protecting those names IS the strategy. If deployment is forced
into large/mid names only, the 1m book has no edge and should be
switched to the 1y-target XGB (which retains large-cap signal, SR 0.68
on the daily panel).

# UPDATE 2026-08-20 — ensemble weight sweep: w=0.60 → SR 1.05

Ridge weight sweep on the OOS ensemble (monthly decile L/S, net):
w_ridge 0.00 / 0.25 / 0.40 / 0.50 / 0.60 / 0.75 / 1.00 →
SR 0.84 / 0.98 / 0.95 / 0.98 / **1.05** / 1.00 / 0.93.
Smooth hump with both endpoints lower — real complementarity. Adopted
w=0.60 (ENS_W env): decile 1.05 (ann +21.1%, dd -51.8%), 96bp 0.62,
$20M ADV 0.58, live 10/14 (+77%). Artifacts regenerated.
Caveat: the weight is chosen on OOS (mild selection; the curve is flat
0.4-0.6 so the choice is low-risk).

# UPDATE 2026-08-20 — split-half weight validation: the ensemble win is REGIME-DEPENDENT

Choosing the Ridge weight on 2009-2017 and testing on 2018-2026:

- Train (2009-2017) SR by w: pure Ridge (w=1.0) **0.75** > all blends
  (0.56-0.70). Ridge dominated the first regime.
- Hold-out (2018-2026): w=0.5 → **1.33**, pure Ridge → 1.13. The blend
  added value only in the second regime.

**Correction to the ensemble verdict**: the full-period w=0.6 win is a
compromise across regimes, not a stable improvement. **Pure Ridge is the
time-robust choice** (best pre-2018, still 1.13 post-2018) — which
reinforces the capacity story: Ridge is also the $20M-ADV book (0.79 vs
ensemble 0.58). The ensemble remains a discretionary full-breadth
enhancement, with the understanding that its edge over Ridge is
concentrated in the post-2018 regime.

# UPDATE 2026-08-21 — PIT FEATURE SET for the 1m models: the snapshot leak inflated Ridge by ~0.3 SR

The 1m champions were trained on all 57 chars, INCLUDING the 10 Finnhub
current-snapshot features (the same lookahead-flavored leak the 1y model
dropped). Retrained on the 47-char PIT set (FEAT_SET=pit in
gkx_backtest.py):

| Model | full-57 net SR | **PIT-47 net SR** |
|---|---|---|
| Ridge | 0.93 (+14.1%) | **0.61 (+8.7%)** |
| XGB d3 | 0.84 (+18.2%) | **0.73 (+14.7%)** |
| **Ridge+XGB ensemble** | 1.05 | **0.95 (+19.5%)** |

- The snapshot leak inflated Ridge by ~0.32 SR; the model ranking FLIPS
  (XGB > Ridge on PIT).
- Ridge PIT stays capacity-robust: 0.62 @ $20M ADV (worst year -19.6%),
  but is more cost-sensitive (0.06 at 96bp).
- **The ensemble retains its edge on PIT: 0.95** — the honest 1m book.
- Combo with the PIT Ridge leg: SR 1.15 (ann +17.2%, dd -25.8%) vs 1.30
  leaky — the leak contributed ~0.15 there too; corr 0.21 (diversification
  intact). The quarterly ex1st 1.20 is now the best standalone book.
- All 1m artifacts (preds parquets, ensemble, formation card) now hold
  PIT predictions.
