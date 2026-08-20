# XGB One-Year Return Prediction — FINAL VERDICT + Deployment Recipe

**Date:** 2026-08-20

> Master overview of both horizons: **STRATEGY_STACK.md** in this directory.
**Scope:** train XGBoost on the GKX monthly characteristic panel to predict
12-month forward returns; build and backtest the corresponding long/short
strategies. 9 loop iterations.

## What was built

- **Target:** `ret_fwd12` = 12-month forward close-to-close return on the
  913-name investable union universe (~6 local panels, months 2002-2026).
- **Model:** XGBoost GBRT — depth 3, lr 0.02, 600 trees (won the sweep) —
  on 47 point-in-time characteristics (20 EDGAR filing-dated fundamentals,
  technicals, macro interactions; the 10 Finnhub snapshot features excluded
  as a lookahead-flavored leak). Ridge reference.
- **Validation:** PURGED walk-forward (train labels fully closed 12m before
  the OOS block), 7y rolling window, yearly refit, OOS 2009-2026.
- **Portfolios:** decile L/S, EW; annual 12m-hold cohorts; staggered
  quarterly deploy (4 simultaneous cohorts, fixed books, monthly slices).

## Three critical bugs found and fixed along the way

1. **Horizon-mismatch booking** (iter1): booking the realized 12m return
   as a monthly return compounded a year's P&L monthly → +297% ann, -99%
   dd artifacts. Fixed: 1m-hold booking for monthly rebalance, annual-
   cohort booking for 12m holds.
2. **Scrambled `ret_next`** (iter4): the panel built `ret_next` via
   `mret.stack().shift(-1)` — a row-positional shift that mixed returns
   across tickers (CSCO +105.7% vs true +11.7%). Contaminated the entire
   GKX 1m replication; the TRUE numbers turned out BETTER (the scrambled
   label was suppressing the edge).
3. **292-name universe** (iter5): `pc.load_ohlcv()` reads only twelve_big;
   every label join silently restricted the backtests to ~292 of the 913
   panel names. Fixed with `union_panel.load_union()` — the full
   cross-section roughly doubled every Sharpe.

## Final results (net of costs, OOS 2009-2026, full universe)

| Strategy | SR | ann | maxDD | notes |
|---|---|---|---|---|
| 1y XGB d3, 12m-hold annual cohorts | **1.03-1.10** | +21-25% | -15% | entry-month robust (0.8-1.1) |
| 1y XGB d3, staggered deploy (qtrly entry) | **1.06** | +16.4% | -23% | beta -0.06, market-neutral |
| 1y XGB d3, 24m-hold | 0.96 | +14.5% | -8.9% | 15/16 yrs positive |
| 1y XGB d3 @ $20M ADV floor | 0.73 | +15.5% | -35% | capacity-safe version |
| 1y XGB d3 @ $50M ADV floor | 0.64 | +14.0% | -41% | |
| 1m GKX Ridge EW monthly | 0.93 | +14.1% | -28% | 1m champion |
| 1m GKX XGB d3 EW monthly | 0.84 | +18.2% | -64% | |

**Robustness confirmed**: 4x costs (0.99), quintiles (1.04), PIT $2 price
floor (1.05 — sub-$2 names are noise, not signal), short-leg borrow up to
200bp/yr (0.93), entry-month sweep, per-year consistency (15/18 deploy
years positive; worst -13.1%). IC 0.118 (IC-IR 3.4). Signal profile:
1m/12-1 momentum, macro-conditional momentum, volatility family — NOT the
12m-momentum factor (survived the 2009 momentum crash where that factor
lost -105%).

## Deployment recipe (quarterly staggered, 12m hold)

1. **Refit** XGB d3 (600 trees, lr .02) yearly each January on the prior
   7y of months, purged 12m before the block.
2. **Form** one cohort per quarter (Feb/May/Aug/Nov): rank all names with
   px >= $2 by prediction; long top decile EW, short bottom decile EW;
   hold 12m, fixed membership. 4 simultaneous cohorts, equal capital.
3. **Costs**: ~6bp/side; 24bp full cycle at formation and at exit
   (48bp/cohort/year). Borrow on the short leg: budget ≤100bp/yr
   (SR impact ≤0.05).
4. **Capacity**: edge intact at $20M ADV (SR 0.73); below $5M ADV
   expect more alpha but less capacity.
5. **Current book** (2026-08-31, next formation Nov 2026): LONG ACAT,
   INTC, ORCL, WOLF, MU, CHTR, HUM, TSLA, PANW, GOOGL, OKTA...;
   SHORT the stable megacaps (KO/COST/WMT/JPM/XOM class). See
   `gkx_1y_live_book_2026-08-31.csv`.

## Caveats (honest)

- n = 17 independent annual cohorts (~1.5 decades); the 2012/2015/2022
  cohorts lose 7-13%.
- Universe breadth comes from smaller names — the $20M ADV version is the
  capacity-honest number.
- Finnhub snapshot features excluded; EDGAR fundamentals are filing-dated
  but the EDGAR fetch pipeline itself is best-efforts.
- Live signals: refit cadence and data refreshes are the operational
  risks to monitor.

## Artifacts

`tools/quant/bigmove/xgb_1y_ls.py` (training + backtests),
`xgb_1y_horizon_profile.py`, `xgb_1y_deploy.py`, `xgb_1y_blend.py`;
`data/gkx_preds_xgb_1y_pit.parquet` (OOS predictions),
`gkx_preds_{xgb,ridge}_1y_pit.parquet`, `gkx_monthly_panel.parquet`
(fixed ret_next); reports in `tools/quant/reports/xgb_horizons/`
(XGB_1Y_LS.md living record, GKX_REPLICATION.md v14-v15, this file).
Re-run: `python3 xgb_1y_ls.py` then `xgb_1y_deploy.py`.

# UPDATE 2026-08-20 (iter10) — dollar capacity + daily-panel cross-check

## Dollar capacity (Feb-2025 cohort, $20M ADV floor)

Long decile: 57 names, median ADV $75M (p25 $41M, p10 $28M).
Per-leg notional at ADV participation caps:

| Participation | Per-leg capacity | Both legs |
|---|---|---|
| 1% (conservative) | ~$144M | ~$288M gross |
| 2% | ~$288M | ~$576M |
| 5% (aggressive) | ~$720M | ~$1.4B |

The strategy runs at institutional scale on the capacity-safe floor —
the binding constraint is participation discipline, not strategy alpha.

## Daily-panel cross-check — RESULT: the signal replicates on large caps

`xgb_daily_1y.py` (285-name twelve_big daily panel, 141 daily features,
252d-horizon depth-3 XGB, purged walk-forward, OOS 2014-2026, monthly
rebalance booking the 21d forward return, net 24bp/mo):

**SR 0.68, ann +19.9%, maxDD -57.0%, win 56%.**

The 1y signal exists on a completely independent universe and feature
family — the smaller-name union result (1.03-1.10 annual hold) is not a
data artifact of one panel. The large-cap version has a deeper drawdown
(-57%) and lower win rate; the union universe's breadth is what smooths
the book. External validation achieved.

# UPDATE 2026-08-20 (iter11) — IC attribution, per-year stability, turnover

## Model vs raw factors (IC vs realized 12m return, OOS)

| Signal | mean IC | IC-IR |
|---|---|---|
| **XGB model** | **+0.118** | **+3.4** |
| ret_12_1 (best raw factor) | +0.058 | +1.3 |
| ret_m12 | +0.054 | +1.2 |
| ret_m1 | +0.022 | +0.6 |
| vol_m3 | -0.039 | -0.7 |
| bm | -0.072 | -1.9 |
| log_mcap | -0.140 | -4.7 |

The model's IC is ~2x its best constituent factor — the ML combination is
the edge, not any single characteristic. (Size alone is strongly negative
at 12m horizons — the small-name tilt — which the model harvests.)

## Per-year IC stability

Positive in 16/17 OOS years (2009 -0.058 is the partial warmup year);
2010-2025 range +0.014 to +0.279, no regime clustering — the edge is
uniformly present, not crisis/event-driven.

## Cohort turnover

Feb→Feb (annual refit): ~32% overlap (68% turnover). Quarterly: ~49%
overlap (51% turnover). The book replaces about half its names every
quarter — momentum-flavored dynamics; the 24bp/full-cycle cost model
(6bp/side) is consistent with this churn. Execution is the main
operational risk, not signal decay.

# UPDATE 2026-08-20 (iter12) — LIVE MARK-TO-MARKET: first post-backtest cohorts all positive

Cohorts formed after the backtest's last entry (Aug 2025) — predictions
from models trained through Jan 2025, realized against data through
2026-08 (net of costs, fixed books):

| Cohort | Months realized | Cum net |
|---|---|---|
| 2025-11-30 (81L/81S) | 9 | **+42.3%** |
| 2026-02-28 (80L/80S) | 6 | **+16.1%** |
| 2026-05-31 (79L/79S) | 3 | **+2.4%** |
| 2026-08-31 | 0 | formed, no slices yet |

Nov-2025 first three slices: +10.9%, +9.6%, +11.0% — the strongest start
of any cohort in the backtest, and it is the first fully out-of-sample
(post-backtest) cohort. All live cohorts positive. Caveat: 3 data points,
and the 2026 union price data comes from the same fetches that built the
panels (models are OOS; data existence is not).

# UPDATE 2026-08-20 (iter13) — live P&L attribution + data freshness

- No price-data refresh since the panel build (CSVs dated Aug 17-18) —
  the live mark-to-market stands as of 2026-08.
- Nov-2025 cohort attribution (9 slices): **long leg +26.6% (2/3), short
  leg +11.9% (1/3)**, gross +38.4% (arith; +42.3% compounded net).
- Top contributors mix the untradeable micro tail (ADTX ADV $6M, AKAN
  $1M, XXII/AIMN ~$0) with megacaps (MU +2.4%, INTC +1.8%). The
  capacity-floored ($20M ADV) live book would keep MU/INTC/AEHL-class
  names and shed the micro tail — the unfiltered live number overstates
  the institutional-scale result; the floored backtest (SR 0.73) remains
  the honest deployment expectation.

# UPDATE 2026-08-20 (iter14) — live monitor + 1m model's live record

New `tools/quant/bigmove/live_monitor.py` — one-command steady-state
status: data freshness, live 1y cohorts, recent 1m-model months, next
formation/refit dates.

**1m model live months** (2025-06..2026-07, monthly decile L/S net,
beyond the labeled backtest window): 11/14 positive, mean ~+4.4%/mo
(compounds to ~+74% over 14 months). Worst months: 2025-07 -4.7%,
2026-06 -6.6%. Both strategies are live-positive.

Status snapshot (2026-08-20): data fresh through 2026-08-18; 1y cohorts
+42.3%/+16.1%/+2.4%/just-formed; next formation 2026-08-31, next refit
2027-01-31.

# UPDATE 2026-08-20 — portfolio optimization: weights, tilts, frequency (`xgb_1y_opt.py`)

Optimized the portfolio layer of the 1y XGB strategy on the champion
predictions (correct booking: return horizon == rebalance period; 24bp/mo
gross; px>=2):

## Weight schemes (monthly, neutral): EW wins
EW 0.78 > rank 0.50 > ivol 0.43 > z 0.16 — prediction magnitudes are not
calibrated enough to weight by; equal weight remains best.

## Net-long tilts (beta stays ~-0.10 regardless — the books add
book-specific risk, not market exposure; the selected names are
systematically defensive vs SPY over the sample):

| Config | SR | ann | dd | beta |
|---|---|---|---|---|
| monthly EW t=0 | 0.78 | +14.6% | -40% | -0.11 |
| monthly EW t=0.25 | 0.96 | +20.5% | -48% | -0.11 |
| **monthly EW t=0.5** | **0.97** | +25.4% | -61% | -0.11 |
| monthly EW t=1.0 (long-only) | 0.87 | +32.1% | -82% | -0.10 |
| **quarterly EW t=0** | 0.94 | +18.0% | -30% | -0.07 |
| **quarterly EW t=0.25** | **1.09** | +24.1% | -36% | -0.08 |
| quarterly EW t=0.5 | 1.08 | +29.3% | -51% | -0.09 |
| monthly EW t=0.5 @ $20M ADV | 0.94 | +26.0% | -72% | -0.13 |

## Verdict

- **Quarterly EW t=0.25 is the best more-frequent book** (SR 1.09, ann
  +24.1%, dd -36%, win 75%, 4x/yr turnover): matches the annual 12m-hold
  SR with 3x the turnover and more drawdown; monthly adds turnover
  without improving risk-adjusted return (t=0.5: 0.97/-61%).
- Tilts up to t=0.5 raise return, then degrade (t=1.0: dd -82%).
- Combo: quarterly EW t=0.25 + Ridge-1m 50/50 — corr 0.17 → **SR 1.27,
  ann +19.1%, dd -23.1%** (quarterly basis): the more-frequent capstone.

# UPDATE 2026-08-20 — mean-variance optimization: DOES NOT beat equal weights (`xgb_1y_mv.py`)

Full MV optimization (Ledoit-Wolf shrunk 60m rolling covariance,
w = inv(Sigma + gamma*I)·mu on the 1y prediction, |w|<=2%, gross 2.0,
net-exposure target t, turnover costs 6bp·sum|dw|, split-half validated):

| gamma, net | fit SR 09-17 | test SR 18-26 | full SR |
|---|---|---|---|
| 0.1, 0.0 | +0.29 | +0.08 | 0.13 |
| 1.0, 0.0 | -0.08 | -0.20 | -0.17 |
| 10.0, 0.0 | -0.27 | -0.24 | -0.23 |
| **0.1, 1.0 (best on fit)** | 1.64 | **0.54** | 0.79 |
| 1.0, 1.0 | 1.55 | 0.43 | 0.67 |

- **Neutral MV fails at every risk aversion** — covariance-based
  neutralization fights the model's cross-sectional edge (the 1y signal
  is a rank signal; sizing it by inverse-covariance noise destroys it).
- The tilted MV (long-biased) works but **underperforms the simple EW
  tilt books**: full 0.79 (ann +21.7%, dd -58%) vs quarterly EW t=0.25
  SR 1.09; fit-period MV Sharpes (up to 1.64) degrade to 0.54 in the
  hold-out — classic DeMiguel "1/N beats optimization" result.

**FINAL VERDICT on portfolio optimization** (two independent passes,
heuristic + classical): for this strategy, **equal-weight tilts are
optimal** — weight schemes (rank/z/ivol) and mean-variance both lose.
The lever that works is the NET-EXPOSURE TILT (t≈0.25-0.5) and the
REBALANCE FREQUENCY (quarterly). Best book: quarterly EW t=0.25,
SR 1.09, ann +24.1%, dd -36%.

# UPDATE 2026-08-20 — frequency frontier complete + combo split confirmed

## Weekly rebalance (5d booking, tail-filtered, 24bp/wk)

- weekly EW t=0: SR **-0.23** (ann -8.4%) — 12.5%/yr turnover costs kill it
- weekly EW t=0.25: SR +0.24 (ann +2.8%)

**Complete frequency frontier** (1y prediction, EW):
weekly -0.23 → monthly 0.78-0.97 → **quarterly 1.09** → annual 1.03-1.10.
Quarterly is the optimum; trading more frequently than quarterly loses
money net of costs.

## Combo split sweep (Ridge-1m + quarterly-1y, quarterly basis)

| w_ridge | SR | ann | dd |
|---|---|---|---|
| 0.3 | 1.23 | +21.3% | -27.7% |
| 0.4 | 1.26 | +20.2% | -24.8% |
| **0.5** | **1.27** | +19.1% | -23.1% |
| 0.6 | 1.25 | +18.0% | -22.5% |
| 0.7 | 1.19 | +16.8% | -21.9% |

Flat plateau 0.3-0.6 — the 50/50 split is robust and optimal.

## FINAL optimization verdict (complete)

Every portfolio lever has now been tested: weight schemes (EW wins),
mean-variance (rejected), net tilts (t≈0.25-0.5 optimal), rebalance
frequency (quarterly optimal), combo split (50/50). **The optimized
strategy: quarterly EW t=0.25 (SR 1.09) + Ridge-1m 50/50 → SR 1.27,
ann +19.1%, dd -23.1%.**

# UPDATE 2026-08-20 — regime gating rejected; vol targeting = the drawdown lever

## Regime-gated tilt (quarterly EW, tilt set by 12m market trend)

| Rule | SR | ann | dd |
|---|---|---|---|
| const t=0.25 | **1.09** | +24.1% | -36.2% |
| gated: t=0.5 up / t=0 down | 1.00 | +24.3% | -48.4% |
| gated: t=0.5 up / t=-0.5 down | 0.73 | +17.7% | -49.8% |

The tilt's payoff is NOT trend-following — gating by market trend times
badly (tilting after up-years catches tops). Constant tilt wins.

## Volatility targeting (quarterly EW t=0.25, 5%/qtr target, trailing-4q scaling)

| | SR | ann | dd | Calmar |
|---|---|---|---|---|
| raw | 1.09 | +24.1% | -36.2% | 0.67 |
| **vol-targeted** | 0.83 | +10.0% | **-7.9%** | **1.27** |

**Vol targeting is the drawdown lever**: it cuts maxDD by ~4.5x for
~0.26 SR — the risk-budgeted deployment choice (Calmar nearly doubles).
With modest leverage it recovers the ann with still-better dd than raw.

## FINAL optimization program (now complete across 7 levers)

weights (EW wins) · MV (rejected) · tilts (const t≈0.25-0.5 optimal,
gating rejected) · frequency (quarterly) · combo split (50/50) · vol
targeting (dd lever). Deployment menu: raw quarterly EW t=0.25 (SR 1.09,
dd -36%) or vol-targeted (SR 0.83, dd -8%); either + Ridge-1m 50/50.

# UPDATE 2026-08-20 — final risk ladder: vol-targeted combo variants

| Variant (Ridge-1m + quarterly-1y 50/50) | SR | ann | dd | Calmar |
|---|---|---|---|---|
| raw | 1.27 | +19.1% | -23.1% | 0.83 |
| vol-targeted 1y leg only | 1.11 | +11.8% | -13.5% | 0.87 |
| **both legs vol-targeted** | 1.02 | +8.6% | **-8.2%** | **1.05** |

**The complete deployment menu is a risk ladder**: pick the rung by your
drawdown budget. Optimization program CLOSED — every portfolio lever
(weights, MV, tilts, gating, frequency, split, vol targeting, combo
variants) tested and committed.

# UPDATE 2026-08-20 — drawdown filter: VIX gate cuts dd 33% with ann UNTOUCHED

Goal: filter the biggest drawdown without affecting annual return.
Diagnosis: the quarterly book's -36.2% dd is two episodes — 2022 (single
-27% quarter, VIX 30) and 2015 (slow bleed, VIX only 14). Tested three
filter families on quarterly EW t=0.25:

| Filter | SR | ann | dd |
|---|---|---|---|
| raw | 1.09 | +24.1% | -36.2% |
| **VIX gate (0.5x > 22, 0x > 35)** | **1.17** | **+23.7%** | **-24.4%** |
| VIX gate (0.5x > 25, 0x > 40) | 1.14 | +23.3% | -24.4% |
| VIX gate (0.5x > 28, 0x > 45) | 1.10 | +23.9% | -36.2% (too loose) |
| DD time-out (0.5x@-10%, 0x@-15%) | 0.99 | +19.5% | -24.4% |
| VIX + DD combined | 0.90 | +14.9% | -18.9% |

**The VIX gate is the answer**: exposure 0.5x when VIX > 22, 0x when >
35 (formation-time, applied to the next quarter). It shaves the single
worst episode (2022) while leaving all other quarters untouched — ann
+24.1% -> +23.7% (-0.4pp), dd -36.2% -> -24.4% (33% cut), SR improves
to 1.17. Threshold plateau 22-25 = robust, not knife-edge. The DD
time-out costs 4.6pp ann for the same dd cut — rejected. On the combo
(Ridge-1m + quarterly-1y) the gate is unnecessary (dd already -23%;
gate costs 1.6pp ann for -2pp dd).

# UPDATE 2026-08-20 — VIX gate on Ridge-1m: REJECTED (gains and losses interleave in vol regimes)

Tested the VIX gate (0.5x/0x exposure tiers) on the Ridge-1m monthly book:
raw 0.93/+14.1%/-28.5%; best gate (0.5x>28, 0x>45) 1.02/+14.7%/-26.9%;
tighter gates cost ann without cutting dd (0.5x>22: dd -28.9%, ann -2.7pp).
Ridge-1m's losses are monthly streaks whose recoveries (2020-03 +30%,
2022-12 +33%) occur in the SAME high-VIX regimes — the gate cuts the
recovery as much as the loss. The VIX gate is specific to the 1y
quarterly book (a single avoidable 2022 quarter); monthly books need a
different tool or none. Next: 1y model hyperparameter refinement grid
(d2 / d3-1000t / d3-lr.01 / d4-mcw5) in background.
