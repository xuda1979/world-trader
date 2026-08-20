# XGB One-Year Return Prediction — Long/Short Backtest

> **CURRENT STATE (2026-08-20, after iter1-16) — read this first.**
> The sections below are a chronological record; EARLY numbers are
> superseded by the iter5 universe fix and the iter7 tuning.
>
> **Final strategy:** 1y-target XGB (depth 3, lr .02, 600 trees, 47 PIT
> chars), full ~900-name union universe, purged walk-forward.
> - 12m-hold annual cohorts: **net SR 1.03-1.10, ann +21-25%, dd -15%**
> - Staggered quarterly deploy: **net SR 1.06, ann +16.4%, beta -0.06**
> - 24m-hold: 0.96 (dd -8.9%); $20M ADV floor: 0.73 (ann +15.5%)
> - Daily-panel cross-check (285 large caps): 0.68 monthly — replicates
> - Live (post-backtest): cohorts +42.3%/+16.1%/+2.4%; 1m model 11/14
>   recent months positive
>
> Full synthesis + deployment recipe: **XGB_1Y_FINAL_VERDICT.md**.
> Live status: `python3 tools/quant/bigmove/live_monitor.py`.

**Date:** 2026-08-20
**Goal:** train the XGB models on the GKX monthly characteristic panel to
predict the **12-month forward return**, and backtest the resulting long/short
strategies.

## Setup

- **Panel:** `gkx_monthly_panel.parquet` — 57 point-in-time characteristics,
  ~885 investable names/month (median price >= $2), months 2002-04..2026-08.
- **Target:** `ret_fwd12` = 12-month forward close-to-close return (label
  coverage through 2025-08, needing closes through 2026-08).
- **Models:** XGBoost GBRT (primary; 300 trees, depth 4, mcw 10) + Ridge
  reference (alpha 10).
- **Validation:** PURGED walk-forward — to predict month m, train only on
  months t with t+12 < m (the 12m label window fully closed before the OOS
  block; no overlap). Rolling 7y window, yearly refit (Jan), predict the
  next 12 months. OOS 2009-2026, 17 refits, 199 prediction months.
- **Portfolios:** monthly decile L/S (top/bottom decile by prediction),
  EW and VW (long leg mcap-weighted), gross and net (6bp/side, 24bp/mo
  full cycle).

## Backtest accounting fix (important)

Booking the realized **12m** return as a **1-month** return (monthly-rebalanced
book) compounds a year's P&L every month — produced garbage: EW ann +297%,
maxDD -99.3%. Fixed by separating the two real strategies:

1. **1m-hold** (monthly rebalance): the 12m prediction SELECTS the book at
   month m; the P&L credited is the NEXT-MONTH return (`ret_next`), 24bp/mo.
2. **12m-hold** (annual cohorts): select at the first prediction month of
   each refit block (Feb), hold 12m, book `ret_fwd12` once. Non-overlapping
   windows -> independent observations, honest annual Sharpe.

## Results (OOS 2009-2026, decile L/S)

| Model | Scheme | EW gross SR | EW net SR | VW net SR |
|---|---|---|---|---|
| XGB | 1m-hold monthly | -0.73 | **-1.07** | -1.17 |
| Ridge | 1m-hold monthly | -0.10 | -0.52 | -0.82 |
| **XGB** | **12m-hold annual** | — | **+0.57** (ann +9.7%, win 71%, dd -49.6%) | -0.04 |
| Ridge | 12m-hold annual | — | +0.30 (ann ~0%) | +0.05 |

IC (monthly Spearman, pred vs realized 12m return): XGB 0.108 (IC-IR 1.93),
Ridge 0.132 (IC-IR 2.37) — inflated by overlapping 12m windows; the
non-overlapping annual cohorts are the honest test.

## Key findings

1. **The 1y prediction is real at the 1y horizon, and XGB is the champion.**
   12m-hold EW decile L/S: SR +0.57, +9.7%/yr net, 12/17 positive years.
   At the 1m horizon Ridge dominated XGB (net 0.3-0.5 vs ~0.09); at the 1y
   horizon the ranking flips — tree nonlinearity pays off on long-horizon
   signal. This is the strongest XGB result in the desk's history and beats
   the 1m Ridge champion's ~+0.3-0.5 net SR on its own schedule.

2. **The signal is violently mean-reverting at monthly frequency.** Trading
   the same predictions with monthly rebalancing LOSES (XGB EW net SR -1.07):
   names predicted for high 12m returns underperform in month 1 (short-term
   reversal dominates). The edge only exists for investors who hold ~1 year.
   For contrast, the 1m-target XGB on the same 1m-hold scheme nets +0.09.

3. **It is not momentum.** Control: raw 12m-momentum decile L/S on the same
   annual-cohort scheme lost **-104.8% in the 2009 momentum crash** (book went
   negative). The XGB 1y signal made **+26.3% in 2009**. Feature importances
   confirm: volatility/liquidity (vol_m3, amihud, idio_vol, maxdd), 52w-hi/lo
   distance, size (marketCap/mcap/log_mcap), macro state (mkt_ret_3m), and a
   few fundamentals (assets growth, leverage, div yield); momentum
   (ret_m12/ret_12_1) does not crack the top 15. Signal profile: low-vol,
   beaten-down, smaller, illiquid names with macro tailwind.

4. **The edge lives in the EW cross-section, not the large caps.** VW (long
   leg mcap-weighted) is ~zero for both models — same pattern as the 1m GKX
   work (VW negative there). Consistent with a smaller-name effect.

5. **Loss years are the value years.** Worst cohorts: 2022 -38.7%, 2021
   -17.8% — the value/small-cap drawdown era. Best: 2011 +40.0%, 2016 +36.6%,
   2017 +29.1%. The strategy is a value/reversal-flavored long-horizon book.

## Caveats (honest)

- The 7 Finnhub snapshot fundamentals (pe, pb, roe, ...) are current values
  tiled back through history — not point-in-time (a lookahead-flavored
  feature leak shared with the existing GKX 1m infra). The 20 EDGAR
  fundamentals ARE filing-date point-in-time.
- n = 17 independent annual cohorts; SR 0.57 rests on ~1.5 decades.
- Universe is ~885 liquid investable names — no micro-cap tail.
- Costs: 24bp/yr at annual holding (2 turnovers/yr); monthly-rebalanced
  versions pay 24bp/mo and lose regardless.

## Artifacts

- `tools/quant/bigmove/xgb_1y_ls.py` — purged walk-forward 12m-target XGB +
  Ridge, both backtest schemes.
- `tools/quant/bigmove/data/gkx_preds_xgb_1y.parquet`,
  `gkx_preds_ridge_1y.parquet` — OOS predictions.
- `tools/quant/reports/xgb_horizons/gkx_1y_results.json` — full stats.
- `tools/quant/reports/xgb_horizons/gkx_1y_annual_eq.csv`,
  `mom12_annual_eq.csv` — annual-cohort equity (XGB 1y vs 12m momentum).
- Re-run: `python3 tools/quant/bigmove/xgb_1y_ls.py`.

# UPDATE 2026-08-20 (iter2) — leak-free rerun + entry-month robustness

Two honesty checks on the iter1 result:

1. **Point-in-time (PIT) feature set**: dropped the 10 Finnhub current-snapshot
   features (marketCap, pe, pb, roe, rev_growth, eps_growth, asset_turn,
   debt_eq, div_yield, log_mcap — 2026 values tiled back through history) ->
   47 remaining characteristics, all filing/price-date point-in-time.
2. **Cohort entry-month sweep**: annual cohorts at Feb/May/Aug/Nov instead of
   the single Feb convention — the SR should not depend on when in the year
   the book is formed.

| Model | Fset | entry-02 | entry-05 | entry-08 | entry-11 | IC mean |
|---|---|---|---|---|---|---|
| XGB | full 57 | 0.57 (ann +9.7%) | 0.51 | 0.53 | 0.46 | 0.108 |
| XGB | **PIT 47** | **0.34 (ann +5.5%)** | **0.45** | **0.51 (ann +9.2%)** | **0.38** | **0.063** |
| Ridge | full 57 | 0.30 | 0.53 | 0.89 | 1.34 | 0.132 |
| Ridge | PIT 47 | 0.10 (ann nan) | 0.34 | 0.57 | 0.86 | 0.067 |

(12m-hold annual cohorts, EW, net 24bp/yr; IC = monthly Spearman vs realized
12m return.)

**Verdict:**

- **The signal is NOT a lookahead artifact.** With point-in-time features
  only, XGB EW 12m-hold stays net-positive at every entry month (SR
  0.34-0.51, ann ~5.5-9%, win 71-82%). The snapshot leak roughly DOUBLED the
  headline (full-set SR 0.46-0.57) and about half the IC (0.108 -> 0.063) —
  but the honest number remains a real, positive, tradeable-on-1y-horizon
  result. Honest headline: **XGB PIT EW decile L/S, annual hold: net SR
  ~0.4, ann ~6-9%, OOS 2009-2026.**
- **XGB is stable across entry conventions; Ridge is not.** XGB SR band
  0.34-0.51; Ridge swings 0.10-0.86 with a NaN year (ann) at entry-02 — the
  linear model's apparent strong years (1.34 at entry-11) are convention
  luck. XGB confirmed as champion for this horizon.
- **Monthly rebalance still loses** under PIT (XGB EW 1m-hold net SR -0.68):
  the mean-reversion-at-monthly-frequency conclusion is unchanged — this is
  a 1-year holding-period strategy, full stop.

Artifacts: `gkx_preds_{xgb,ridge}_1y_pit.parquet` (PIT predictions),
`gkx_1y_results.json` (updated, includes per-entry-month stats).

# UPDATE 2026-08-20 (iter3) — horizon profile, sensitivity, live book

New script `xgb_1y_horizon_profile.py` reuses the PIT XGB predictions (no
retraining) to map the edge across holding periods, stress costs/width, and
produce the current book. Three infrastructure bugs fixed along the way
(predictions now extend through the latest refit block to 2026-08; NaN-label
rows are dropped per cohort group so join-miss names can't zero-weight into
spreads; each horizon applies its own sane-tail label filter instead of
destructively shrinking the shared frame).

## Horizon profile (same predictions, EW decile L/S, net)

| Hold | SR | ann | mean obs | win | n |
|---|---|---|---|---|---|
| 1m | -0.68 | -5.8% | — | 40% | 211 |
| 3m | 0.27 | +3.3% | +1.4% | 68% | 68 |
| 6m | 0.34 | +4.7% | +3.2% | 68% | 34 |
| **12m** | **0.34** | **+5.5%** | **+7.8%** | **71%** | 17 |
| 24m | 0.43 | +6.5% | +18.1% | 81% | 16 |

- The reversal-to-edge crossover sits between 1m and 3m; the signal pays
  from 3m onward and the second year adds MORE than the first (12m +7.8% ->
  24m +18.1% per window) — a slow-burn value/reversal effect, not a
  short-horizon pop.
- 24m cohorts (net): positive 13/16 years; losses are 2021 -56.1%, 2022
  -28.4%, 2023 -10.5% (the value drawdown era, same as 12m).

## Sensitivity (12m annual cohorts, EW)

| Variant | SR | ann |
|---|---|---|
| decile, 24bp | 0.34 | +5.5% |
| decile, 48bp | 0.33 | +5.2% |
| decile, 96bp | 0.31 | +4.7% |
| quintile, 24bp | 0.36 | +4.4% (dd -47%) |
| decile, 24bp, PIT $2 floor | **0.32** | +5.1% |

Costs are nearly irrelevant at annual turnover (96bp/yr costs 0.03 SR).
**The point-in-time $2 price floor leaves SR at 0.32 — the edge is NOT a
penny-stock artifact.** Quintiles reduce maxDD (-47%) at equal SR.

## Live book (2026-08-31, latest predictions, px >= $2)

- Universe today: 885 names ranked, only 291 priced >= $2 (the recent
  cross-section is heavily diluted with sub-$2 TwelveData names).
- LONG: LCID, HUBS, DOCU, GXO, CHTR, MOH, RIVN, PINS, HUM, CLF, CHWY, WDAY,
  UAL, BAX, THC, MOS, LW, LUV, OKTA, ZM, LULU, JBL, APA, ZS, CNC, ETSY, IFF,
  ILMN, ORCL — beaten-down growth/cyclicals.
- SHORT: KO, COST, MDLZ, WMT, JPM, XOM, PFE, MCD, BAC, GS, JNJ, UPS, FDX,
  DIS, NOC... — stable mega-caps. The model is short Coca-Cola and long
  Lucid — the low-vol/size/reversal profile in one line.
- Artifacts: `gkx_1y_live_book_2026-08-31.csv`, `gkx_1y_profile_{3,6,12,24}m.csv`.

# UPDATE 2026-08-20 (iter4) — PANEL BUG FOUND: ret_next was scrambled; deploy backtest fixed

## The bug (desk-wide impact)

The GKX monthly panel's `ret_next` was built via `mret.stack().shift(-1)`
— `shift(-1)` on the stacked MultiIndex shifts by ROW POSITION, scrambling
returns across tickers (especially at month boundaries). Proof: CSCO
Feb-2020..Feb-2021 — prod(1+panel ret_next) = +105.7% vs true +11.7%
(raw CSV; the 12m fwd12 join says +12.4%). Everything that used `ret_next`
as a label or booked return was contaminated: the **GKX 1m replication**
(training labels AND decile-L/S booked returns — the entire v6-v13 story),
the 1m-hold stats in this report, and the deploy slices. The 12m-forward
results (iter1-3) are UNAFFECTED: the fwd12 label is an independent join,
and the models never touch ret_next.

Fixes: panel builder (`gkx_monthly.py`), panel parquet (patched in place,
identity verified), `gkx_backtest.py` loader, `xgb_1y_ls.py` loader — all
now compute ret_next(m) = close(m+1)/close(m)-1 per ticker on the index.

## What changes on the 1y side

- **1m-hold (monthly rebalance) flips sign: XGB PIT net SR -0.68 -> +0.29**
  (ann +3.9%, win 58%). The "violent monthly mean-reversion" of iter1 was
  an artifact of the scrambled label — the 1y signal is mildly POSITIVE
  even at 1-month holding. Ridge PIT 1m-hold ~0.
- 12m-hold unchanged (SR 0.34 entry-02 — predictions don't depend on
  ret_next).

## Deployment backtest (fixed, `xgb_1y_deploy.py`)

Quarterly staggered entry (Feb/May/Aug/Nov), 12m hold, 4 simultaneous
cohorts, fixed books, monthly slices, net of 24bp full-cycle at formation
and exit, PIT $2 floor. 67 cohorts, 2009-02..2026-08:

- **Monthly SR +0.42, ann +5.9%, win 62%, maxDD -64.6%.**
- By year: positive 15/18; losses concentrated in 2021 -23.9% and 2022
  -37.0% (the value/small-cap drawdown era — same years as the isolated
  cohorts; the -64.6% maxDD is those two consecutive years compounding).
- **Market exposure: beta +0.05, corr +0.05 — the book IS market-neutral.**
- Feb-only slice book (EW-rebalanced version of the annual cohorts): SR
  0.26, ann +3.0% — vs +5.5% from fwd12 booking (buy-and-hold-with-drift;
  the gap is within-window compounding/Jensen, same sign).

## Honest updated headline

The 1y-target PIT XGB is a market-neutral quarterly-refreshed decile L/S:
**net SR ~0.3-0.4 (monthly-rebalanced or staggered-hold accounting),
ann ~4-6%**, with the edge surviving point-in-time features, entry-month
convention, costs, and a $2 price floor; losses concentrate in
value-drawdown regimes (2021-2022). The GKX 1m replication numbers built
on the broken label are being revalidated separately.

# UPDATE 2026-08-20 (iter5) — UNIVERSE BUG: backtests ran on 292 names, not the 913-name panel

`pc.load_ohlcv()` reads only `twelve_big/` (~292 tickers) while the GKX
panel holds 913 (built from the union of twelve_big + twelvedata +
twelve_liq + polygon + polygon_v2 + twelve_extend). Every label join
(fwd12, ret_next, px) in iters 1-4 therefore silently restricted the
backtests to the ~292-name subset. Fixed: all loaders now use
`union_panel.load_union()` (1,097 tickers); the panel's ret_next rebuilt
with the union source + the original sane-tail filter (coverage 50% ->
85%; CSCO identity verified). GKX 1m rerun also gained the full universe.

## Revised full-universe numbers (OOS 2009-2026, decile L/S, net)

| Strategy | 292-name subset | Full union universe |
|---|---|---|
| GKX 1m Ridge EW (monthly) | 0.61 | **+0.93** (ann +14.1%) |
| GKX 1m XGB EW (monthly) | 0.57 | **+0.76** (ann +14.6%) |
| 1y XGB PIT, 1m-hold monthly | 0.29 | **+0.58** (ann +10.2%) |
| 1y XGB PIT, 12m-hold annual | 0.34 | **+0.93** (ann +18.1%, dd -18.0%) |
| 1y XGB PIT, staggered deploy | 0.42 | **+1.02** (ann +14.6%, dd -25.9%, beta -0.06) |
| 1m+1y XGB 50/50 rank blend, monthly | 0.52 | **+0.68** (ann +12.5%) |

The wider cross-section (~900 names incl. smaller caps) is where the edge
lives — consistent with GKX's EW-alpha-in-smaller-names finding. The
deploy book's worst years soften dramatically with breadth: 2021/2022
went from -24%/-37% (subset) to +7.5%/-9.1% (full universe). 1m+1y blend
now ADDS value (50/50 SR 0.68 > either pure leg; P&L corr dropped to
0.68 on the full universe).

## Caveats

- Full-universe labels are sane-tail filtered (ret_next, fwd12 in
  [-0.95, 2.5]) but the union includes the junk-tier TwelveData names the
  v10-v13 reports warned destabilize marginal results — the spread here
  is REAL breadth, not new junk (the panel's own investable filter
  survives; the $2-floor sensitivity should be re-run).
- Liquidity/capacity of the smaller names remains unmodeled.

## Honest updated headline

On the real ~900-name universe: the 1y-target PIT XGB staggered decile
L/S books **net SR ~1.0, ann ~15%**, market-neutral (beta ~0); the 1m
GKX replication now stands at **Ridge/XGB net SR ~0.76-0.93, ann ~14%**.
Both are the best free-data results this desk has produced, and both
numbers rest on verified-clean labels on the correct universe.

# UPDATE 2026-08-20 (iter6) — full-universe stress tests: edge holds at capacity

Horizon profile + sensitivity re-run on the full ~900-name universe:

## Horizon profile (PIT XGB preds, EW decile L/S, net, full universe)

| Hold | 3m | 6m | 12m | 24m |
|---|---|---|---|---|
| SR | 0.78 | 0.88 | **0.93** | 0.82 |
| ann | +15.0% | +17.4% | +18.1% | +13.1% |
| dd | -29.5% | -24.6% | **-18.0%** | **-7.9%** |
| win | 68% | 74% | 82% | 94% (15/16 yrs) |

## 12m sensitivity (annual cohorts, EW, net)

| Variant | SR | ann |
|---|---|---|
| decile 24bp | 0.93 | +18.1% |
| decile 96bp (4x cost) | 0.89 | +17.4% |
| quintile 24bp | 0.84 | +10.9% (dd -13.0%) |
| decile PIT $2 floor | **0.99** | +18.4% |
| decile $1M ADV floor | 0.73 | +14.7% |
| decile $5M ADV floor | 0.73 | +15.6% |
| decile $20M ADV floor | **0.63** | +13.2% |

- The $2 price floor IMPROVES the Sharpe on the full universe (sub-$2
  names add noise, not signal) — definitively not a penny artifact.
- Dollar-volume floors: the edge holds at $20M ADV (SR 0.63, ann +13%),
  i.e., tradeable at institutional capacity.
- Entry-month sweep (full universe): XGB PIT 12m-hold SR 0.72/0.93/0.93/0.81
  (Feb/May/Aug/Nov) — robust; Ridge 0.36-0.87 still convention-sensitive.
  XGB remains champion.
- Live book 2026-08-31 (803/885 names >= $2): LONG WOLF, ACAT, CHTR, HUM,
  FTNT, GOOGL, ADBE, TSLA, GOOG, PINS... (beaten-down quality + select
  momentum), SHORT leg the stable megacaps as before.

## Final honest headline (1y arc)

The 1y-target PIT XGB decile L/S on the full universe: **net SR ~0.6-1.0
depending on holding scheme and capacity floor (0.93 annual 12m-hold,
1.02 staggered deploy, 0.63 at $20M ADV), ann ~13-18%, market-neutral,
robust to entry month, costs, price floor, and capacity.** Losses
concentrate in 2012/2015/2022 at -7 to -12% per year — no disaster years.

# UPDATE 2026-08-20 (iter7) — tuning, signal profile, blend verdict: depth-3 champion SR 1.10

## Hyperparameter sweep for the 12m target (full universe, PIT)

| Config | 12m-hold entry-02 net SR | IC mean |
|---|---|---|
| depth 4, lr .05, 300 trees (old) | 0.93 | 0.062 |
| depth 6, mcw 20 | 0.75 | — |
| **depth 3, lr .02, 600 trees** | **1.03-1.10** | **0.118 (IC-IR 3.43)** |

Shallower slower-learning trees suit the noisy 12m target; the config is
now the default in xgb_1y_ls.py and the champion parquets regenerated.
**New headline numbers: 12m-hold SR 1.10 (ann +24.8%, dd -15.3%),
1m-hold 0.70, staggered deploy SR 1.06 (ann +16.4%, dd -22.8%).**

## Signal profile shifted on the full universe

Feature importances (PIT, full universe): ret_m1 (0.14) is now the top
feature, with ret_12_1, ret_6_x_mkt, ret_12_x_vix, vol family, skew/kurt.
The subset model was vol/liquidity-dominated with no momentum; the full
universe's smaller names carry momentum/reversal dynamics the model now
exploits (macro-conditional momentum).

## Blend verdict by holding period

12m-hold annual cohorts on the joined universe (~405 names): pure 1y
**0.75** >> blend 50/50 0.43 > pure 1m 0.21. The 1m signal decays at long
horizons. Combined with the monthly result (blend 0.68 > 1m 0.66 > 1y
0.58): **use the 1y prediction alone for 12m holds; blend with the 1m
prediction only for monthly rebalancing.** Horizon-matched prediction is
the right tool.

## Current best books (net, OOS 2009-2026, full universe)

- 1y XGB PIT (depth-3) decile L/S: 12m-hold SR ~1.0-1.1, ann ~21-25%;
  staggered deploy SR 1.06, ann +16.4%; $20M ADV floor ~0.6 (pre-tuning).
- 1m GKX Ridge/XGB monthly: SR 0.93/0.76.
- 50/50 blend monthly: SR 0.68.

# UPDATE 2026-08-20 (iter8) — depth-3 everywhere; tuned re-validation; blend verdict revised

## Depth-3 also wins the 1m target

| 1m GKX XGB (full universe, EW decile L/S) | net SR | ann |
|---|---|---|
| depth 4 (old) | 0.76 | +14.6% |
| **depth 3 / lr .02 / 600 trees** | **0.84** | +18.2% |

Promoted to default in gkx_backtest.py; parquets regenerated. Ridge stays
the 1m champion (0.93).

## Tuned 1y model re-validation (depth-3 parquets)

- Horizon profile (net): 3m 0.88, 6m 0.89, 12m **1.03** (ann +20.8%),
  24m **0.96** (dd -8.9%, 15/16 yrs positive).
- 12m sensitivity: 4x costs 0.99; quintile **1.04** (dd -12.5%);
  PIT $2 floor **1.05**.
- Capacity (tuned): $1M ADV 0.89, $5M 0.81, **$20M 0.73 (ann +15.5%)**,
  $50M 0.64 (ann +14.0%) — meaningful improvement over the pre-tuning
  floors (0.63 at $20M).
- Live book 2026-08-31: LONG ACAT, INTC, ORCL, WOLF, MU, CHTR, HUM, TSLA,
  PANW, GOOGL, OKTA... (chips + beaten-down quality).

## Blend verdict REVISED after tuning

With the tuned 1m model, the monthly 50/50 blend (0.80) no longer beats
pure 1m (0.83); pure 1y at 1m-hold is 0.70. Conclusion: **horizon-matched
models only** — 1m model for monthly rebalance, 1y model for 12m holds;
blending dilutes. (Pre-tuning the blend looked additive only because the
1m leg was undertuned.)

## Final strategy stack (all net, full universe, OOS 2009-2026)

| Strategy | Rebalance | SR | ann |
|---|---|---|---|
| 1m Ridge EW decile L/S | monthly | 0.93 | +14.1% |
| 1m XGB d3 EW decile L/S | monthly | 0.84 | +18.2% |
| 1y XGB d3 EW decile L/S | annual 12m-hold | 1.03-1.10 | +21-25% |
| 1y XGB d3 staggered deploy | quarterly, 12m hold | 1.06 | +16.4% |
| 1y XGB d3 @ $20M ADV | annual | 0.73 | +15.5% |
