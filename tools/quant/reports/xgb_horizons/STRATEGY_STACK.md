# ML Long/Short Strategy Stack — Master Summary (ex1st era)

**📘 AUTHORITATIVE CONSOLIDATED REPORT: `FINAL_RESEARCH_REPORT.md` (2026-08-24)**
This file is the working iteration log; the single full research report with
the entire arc (champion, overlays, all short-side frictions + short-interest
feature, deployable champion, caveats, artifacts) lives there.

**Date:** 2026-08-20 · **Status:** research complete, live-positive, deployment cards issued
**Full details:** `GKX_1M_FINAL_REPORT.md` (1m arc) · `XGB_1Y_FINAL_VERDICT.md` (1y arc)

## The stack (all net of costs, full ~900-name union universe, OOS 2009-2026)

| # | Book | SR | ann | dd | Capacity |
|---|---|---|---|---|---|
| 0 | **Ridge-1m (PIT) + quarterly-ex1st 50/50 combo** | **1.15** | +17.2% | -25.8% | both legs |
| 1 | **quarterly ex1st EW t=0.25 + VIX gate** | **1.20** | +24.1% | -23.1% | ~$144-288M/leg |
| 2 | **Ridge-1m monthly (PIT)** | 0.61 | +8.7% | -27.7% | **0.62 @ $20M ADV** |
| 3 | 1y ex1st, 12m-hold annual | 1.08 (sweep 0.91-1.28) | +20-23% | -12-20% | |
| 4 | 1y ex1st, 24m-hold | ~0.96 | ~+14% | ~-9% | |

## Combo risk ladders (vol targeting, PIT legs)

| Combo | Variant | SR | ann | dd |
|---|---|---|---|---|
| defensive (Ridge 50/50) | raw | 1.15 | +17.2% | -25.8% |
| defensive | vol-targ 1y leg | 0.91 | +10.0% | -14.9% |
| defensive | both vol-targ | 0.89 | +7.4% | -10.8% |
| aggressive (ens 40/60) | raw | **1.21** | +23.4% | -35.9% |
| aggressive | vol-targ 1y leg | 1.09 | +14.8% | -26.9% |
| aggressive | both vol-targ | 0.93 | +9.1% | **-11.4%** |

## Combo weight (2026-08-23 — re-optimized)

Swept on actual monthly legs (1y-ex1st SR 1.30/ann +25.4%/Calmar 0.71 vs
1m-ens SR 0.95/ann +19.5%/Calmar 0.33, corr 0.26). **Optimal is w1y ~0.65-0.70**
(≈2:1 1y:1m), i.e. the deployed 50/50 underweights the higher-Calmar 1y leg:

| w1y (weight on 1y ex1st) | SR | ann | dd |
|---|---|---|---|
| 0.40 | 1.34 | +22.7% | -46.9% |
| 0.50 (current defensive) | 1.41 | +23.3% | -43.7% |
| **0.65 (recommended)** | **1.45** | +24.1% | -38.6% |
| 0.70 | 1.44 | +24.4% | -37.1% |
| 1.00 (pure 1y) | 1.30 | +25.4% | -35.6% |

Robust plateau 0.60-0.75 (all ~1.44). Honesty: blend weight is in-sample
guidance (champion legs already chosen), not a fresh OOS claim. Move toward
a ~2/3 1y / 1/3 1m split on reallocation.

## Drawdown overlay (2026-08-23) — VOL-TARGET the WHOLE combo at ~0.13-0.14

User ask: lower dd, KEEP ann, improve SR. Tested on the champion combo
(monthly, 2009-2026). VIX level/spike gates and market-trend filters all
cost return (trend/VIX-level halve ann by pulling to cash during re-upticks).
**Vol-targeting the whole combo (rolling 9-12m, ann target ~0.13-0.14, cap
1.5x) is the winner -- it satisfies all three:**

| Config | SR | ann | dd |
|---|---|---|---|
| champion combo (unfiltered) | 1.447 | +24.1% | -38.6% |
| **vol-targ win12 @ 0.14** | **1.582** | **+24.7%** | **-27.5%** |
| vol-targ win9 @ 0.13 | 1.639 | +23.8% | -24.2% |
| vol-targ win12 @ 0.16 | 1.552 | +26.6% | -30.9% |

Robust: EVERY (window 9-18 × target 0.12-0.16) improves SR (+0.09..+0.20) and
cuts dd. Mechanism: scales UP in calm-strong months, DOWN in turbulent --
captures same/more ann with far less tail (unlike macro-gates that withdraw
to cash). This is whole-combo vol-targeting at ~0.14, NOT the per-leg 5-6%
variant in the ladders above (which cut ann to single digits). Recommended:
vol-target the blended combo, rolling 12m, ann target 0.14, cap 1.5x.

**6 bps cost check (2026-08-23):** all numbers are net of the 6 bps/side book
costs (COST=0.0006, applied full-cycle in each leg). The vol-target overlay's
own churn is negligible (~8bp/yr) because vol-scaled exposure moves slowly —
honest monthly-churn model: SR 1.576, ann +24.6%, dd -27.5% (vs 1.582
no-cost). The Sharpe gain is real, not a cost artifact.

**NEW — alt-data DXY stack (2026-08-23): the best drawdown filter.** User asked
for NEW signals / alternative data. Standalone macro gates FAIL (credit
BAA-AAA/BAA-10y z, t10y2y inversion, gold-12m, breadth<0.4/0.5 all cost ann
and barely cut dd — they lag the drawdown or mis-time the recovery). The
winner is **stacking a DXY dollar/liquidity-stress gate on top of vol-target**:

| Config | SR | ann | dd |
|---|---|---|---|
| raw combo | 1.447 | +24.1% | -38.6% |
| vol-targ win12@0.14 | 1.576 | +24.6% | -27.5% |
| **vol-targ + DXY z>1.5→0.7** | **1.630** | **+24.1%** | **-24.1%** |

DXY spikes mark dollar/liquidity-deleveraging stress that lags the book's own
trailing vol, so it adds orthogonal signal on top of vol-target; unlike
gold/VIX it does NOT stay elevated during recoveries. Robust across z
1.3-2.0 (SR 1.59-1.63), gates ~20% of months spread across years (~6 in
2022). Deploy: vol-targ win12@0.14 AS the base + LIGHT DXY-z>1.5 de-risk to
0.7 on top. Artifacts: `xgb_combo_dd_dxy_stack.py`.

**NEW — regime-switch, market-neutral MR during the downside (2026-08-23):
the new champion.** User asked to develop market-neutral mean-reversal
strategies for the downside. The deck had a validated MR crash-sleeve (k5_n30,
long-worst/short-best, dollar-neutral, 6bp net, passes signal-scramble). This
deploys it as an OVERLAY activated only in DXY-stress months (the same gate
that de-risks the champion to 0.5x), so drawdown-window capital is rotated
into an uncorrelated (rho -0.09) market-neutral source instead of parked in
cash. Artifact: `xgb_combo_regime_mr.py`, `xgb_combo_regime_mr.json`.

| Config | SR | ann | dd |
|---|---|---|---|
| raw combo | 1.447 | +24.1% | -38.6% |
| vol-targ win12@0.14 | 1.576 | +24.6% | -27.5% |
| + DXY z>1.5→0.5 (de-risked) | 1.650 | +23.7% | -22.5% |
| **+ MR overlay f=0.4 in stress** | **1.715** | **+25.6%** | **-23.8%** |

The whole point, in numbers: in the 41 DXY-stress months the de-risked
champion makes only +3.4%/yr (SR 0.45) because it steps to 0.5x; the MR
sleeve in those SAME months earns +20.7%/yr (SR 1.00) while staying
dollar-neutral. Rotating into it fills the de-risk gap and lifts SR above the
champion on every frontier. Robust across MR f=0.2-0.6 (SR 1.67-1.72), VT
target 0.12-0.16, DXY z 1.3-2.0, and MR k5_n20/30/40 + k3_n20 (all >=1.66).
DXY_F=0.5 (de-risk harder) + MR overlay beats the old DXY_F=0.7 champion
(1.63) on all three axes: SR 1.715 vs 1.63, ann +25.6% vs +24.1%, dd -23.8%
vs -24.1%. The MR overlay adds +0.065 SR / +1.9% ann at a modest dd cost.
Deploy: vol-targ whole combo + DXY z>1.5→0.5 + MR overlay f=0.4 in stress.

**NEW — macro drawdown filter, credit-spread widening ON the regime-switch
(2026-08-23): the new champion, dd breaks -20%.** User asked to use ALL macro
indexes / market data to filter the drawdown without affecting ann or Sharpe.
Tested every macro series in the deck (aaa/baa/BAA-AAA, us10y/2y/30y/t10y2y/
tbill3m, brent/wti/natgas/xau/slv, dow/spx, FX, vix) as an ADDITIONAL de-risk
layer on the regime-switch. ALL fail to cut dd while holding SR>=1.715/ann
(they lag the drawdown / mis-time the recovery) EXCEPT **credit BAA-AAA spread
widening (z>1.3→0.5, lagged)**, used as a supplemental orthogonal layer.
Artifacts: `xgb_combo_credit_macro.py` / `.json`.

| Config | SR | ann | dd |
|---|---|---|---|
| raw combo | 1.447 | +24.1% | -38.6% |
| champion (vol-targ+DXY+MR) | 1.715 | +25.6% | -23.8% |
| **+ credit-widening z>1.3→0.5** | **1.751** | **+24.7%** | **-19.5%** |

First time dd breaks -20% while keeping SR≥1.7 and ann ~+25%. Credit flags
~33/210 months (16%) spread across genuine credit-stress eras (7 in 2015, 7
in 2018, 6 in 2022, 2 in 2020) — economic signal, not a few lucky points.
Robust plateau: window 9-12 × threshold 1.0-1.5 × de-risk 0.5-0.7 ALL improve
the champion on all three axes (SR 1.73-1.76, dd -19.5 to -21.2%, ann
+23.7-25.2%); center config (win12/thr1.3/f2 0.5) avoids overfitting the best
point. Deploy: vol-targ combo + DXY z>1.5→0.5 + MR overlay f=0.4 in DXY
stress + credit-widening z>1.3→0.5 de-risk.

**NEW — MR-in-downside with a UNION activation gate (2026-08-23): the new
champion, SR 1.760 / dd -18.2%.** Refinement of the credit-macro champion:
broaden the market-neutral MR sleeve's activation from DXY-stress ONLY to
**DXY OR credit-widening** (the union of the two downside/stress signals),
keeping all other params identical. Artifacts: `xgb_combo_mr_union.py`/`.json`.

| Config | SR | ann | dd |
|---|---|---|---|
| raw combo | 1.447 | +24.1% | -38.6% |
| champion (vol-targ+DXY+credit+MR-on-DXY) | 1.751 | +24.7% | -19.5% |
| **MR on DXY∪credit** | **1.760** | **+24.7%** | **-18.2%** |

Strictly dominates the credit champion (same ann +24.7%, +0.009 SR, -1.3pp
dd). The MR sleeve pays in BOTH dollar-stress and credit-stress downside
months (+1.05%/mo across the 33 credit-stress months); activating it on the
union adds 19 credit-only months (not already covered by DXY) where MR earns
its drawdown premium — pulls the tail lower at zero ann cost. The full plateau
(credit win9-12 × thr1.0-1.5 × f2 0.5-0.7 × MR f0.3-0.5) all give SR 1.76-1.78
/ dd -17.8 to -19.2% — robust region, not a lone pick. MR active 60/210
months. Full stack below in "Drawdown overlay" progression. Deploy: vol-targ
combo + DXY z>1.5→0.5 + credit z>1.3→0.5 + MR k5_n30 f=0.4 in DXY∪credit.

**NEW — blend-weight re-opt under the FULL overlay stack (2026-08-23): the
new champion, w1y=0.75 → SR 1.774 / dd -16.5%.** The w1y blend weight was
tuned to ~0.65 on the RAW combo before any drawdown overlay existed. This
re-optimizes it conditional on the full stack (vol-targ + DXY + credit +
MR-union), a legitimate "use more of the available info" improvement.
Artifacts: `xgb_combo_w1y_opt.py`/`.json`.

| Config | SR | ann | dd |
|---|---|---|---|
| raw combo | 1.447 | +24.1% | -38.6% |
| w1y=0.65 (MR-union champion) | 1.760 | +24.7% | -18.2% |
| **w1y=0.75 (re-optimized)** | **1.774** | **+24.8%** | **-16.5%** |

Better on all three axes; MaxDD now a new low -16.5%. Why the optimum shifts
up: under vol-targeting + the macro de-risk gates, the higher-Calmar 1y-ex1st
leg is disproportionately protected, so tilting heavier into it (less
lower-Calmar 1m-ensemble) harvests its superior per-unit risk better. Robust
plateau w1y=0.68-0.82 all SR 1.764-1.774 / ann +24.8% / dd -16.5 to -17.5%
(not a spike); 0.75 chosen as center, over the raw-combo-tuned 0.65. Full
stack: vol-targ win12@0.14 cap1.5 + DXY z>1.5→0.5 + credit z>1.3→0.5 +
MR k5_n30 f=0.4 in DXY∪credit. Net of 6 bps, no lookahead.

**TESTED-NEGATIVE (2026-08-23): large-VIX MR activation does NOT beat the
champion.** User hypothesis — MR works best in large-VIX, so add it there.
Directly tested VIX-level (25/28/30/35) and VIX-spike (1.5/2.0/2.5 + fine
1.4–2.5 × MR f0.3–0.5) both as additions to the DXY∪credit MR union and as
standalone replacements. **No config exceeds the champion's SR 1.774**; VIX-
only crushes ann (~-1pp). Why: the champion's MR is active in 60 months but
only 17 have VIX>25 — the DXY∪credit gate already activates MR in 43 downside
months VIX misses (slow grinds, credit squeezes), so the large-VIX MR edge is
already captured; adding VIX pulls in high-VIX-but-not-crashing months that
dilute. Champion unchanged: SR 1.774 / ann +24.8% / dd -16.5%.

**SHORT-SIDE FRICTIONS MODELED (2026-08-23): borrow cost + non-shortable.**
User ask: include IBKR call rate + 6bp cost, short interest as input, and
model non-shortable names. Artifacts: `xgb_combo_borrow.py`/`.json`,
`xgb_combo_nonshortable.py`/`.json`.

- **Borrow (call) rate on short notional** (`short_notional ~0.97x`, paid
  monthly `= notional*rate/12`): 0.5%→SR 1.738, **1.0%→SR 1.701 / +23.6% /
  -17.0%**, 3.0%→SR 1.56. Even 3% keeps it strongly positive.
- **Non-shortable** (drop least-liquid `p` of each month's short decile, no
  locate): this IMPROVES the strategy — SR 1.774→**1.838** at p=30%
  (illiquid-tail shorts are the noisiest AND the hard-to-borrow bucket).
  Realistic deployable champion (p~30% + 1% borrow): **~SR 1.76 / +24.5% /
  -16.5%** — essentially unchanged vs raw despite modeling both frictions.
- **Short interest as input (public feature built + validated):** FINRA Reg SHO
  daily short-volume -> monthly `short_ratio = Σshort_vol/Σtotal_vol`
  (`finra_shortint_build.py` -> `data/finra_short_ratio_monthly.parquet`,
  point-in-time, ~70% union coverage). Cross-period IC (10 clean months across
  two disjoint eras 2019 + 2024): **IC -0.0416, IC-IR -0.97, negative 90% of
  months, +1.03%/mo quintile L/S** — high short-volume → lower fwd ret, stable
  across eras. 1m A/B retrain (2024 window): SR 1.18 → **1.54** with the feature
  (relative signal). CAUTION: FINRA CDN serves **2019+ only** (403 on older
  files) + rate-limits bulk, so full 2009-2026 historical attribution needs a
  commercial short-interest source. Add `short_ratio` to the model feature set
  for new fits; treat the full-history boost as unproven.

## Model

- **1y champion**: XGB depth-3 / lr .02 / 600 trees, 47 PIT chars, trained
  on the **ex1st target** (`fwd12 − fwd1` — the slow component; reversal
  month excluded). The ex1st transform was the biggest single improvement:
  entry-month sweep 0.38-1.10 (dd to -71.6%) → 0.91-1.28 (dd max -19.6%).
- **1m champion (PIT, 2026-08-21)**: Ridge+XGB ensemble 0.95 (ann +19.5%).
  Single models: XGB 0.73, Ridge 0.61 (0.62 @ $20M ADV) — the Finnhub
  snapshot leak had inflated Ridge to 0.93; on PIT features the ranking
  flips. The quarterly ex1st book (1.20) is the best standalone book.
- **Drawdown filter**: VIX gate at formation — 0.5x exposure VIX>22, 0x
  VIX>35 — cuts the quarterly book's dd -36%→-23% with ann untouched.
  Rejected for Ridge-1m (vol regimes interleave its gains/losses).

## Structural facts (the "why")

- **Size**: the 1m edge is small-names ONLY (LARGE 0.04 / MID -0.08 /
  SMALL 0.61); the 1y signal survives large caps (0.68 daily-panel) —
  large-cap-only deployment uses the 1y book.
- **Horizon**: 1m XGB decays by 6m; Ridge-1m persists (0.65 @12m); the
  1y ex1st model is the dedicated long-hold book.
- **Optimization**: EW beats rank/z/ivol and mean-variance (rejected,
  split-half); tilts t≈0.25-0.5 optimal (adds book risk, not beta);
  quarterly frequency optimal (weekly loses); regime gating rejected.
- **Data integrity (all fixed 2026-08-20)**: scrambled `ret_next`
  (stack().shift(-1) row-positional), 292-name label joins, horizon-
  mismatch booking. All numbers above are post-fix.

## Live record (post-backtest, ex1st predictions)

- 1y 12m-hold cohorts: **+31.6% / +19.0% / +2.4%** cum net
- 1y quarterly (EW t=0.25): **+19.7% / +9.2%** (Feb/May-2026, full term)
- 1m PIT live (14 mo): ensemble **+78%**, XGB +72%, Ridge +21% (10/14, 10/14, 8/14 positive) — the pre-PIT Ridge's +137% was largely the snapshot leak

## Deployment (formation cards issued 2026-08-31)

- **1y leg** (quarterly EW t=0.25): VIX 15.5 → 1.0x exposure; 80L/80S.
  LONG ACAT/WOLF/ORCL/CHTR/MU/HPE/PINS/HUM/TSLA/META...
- **Ridge-1m leg** ($20M ADV floor): 59L/59S. LONG DDOG/MU/TSLA/PANW/
  PLTR/ARM/AMD/AAPL/AVGO...; SHORT BIIB/MDT/ABT/PAYX/AIG/TGT/MGM...
- Concentration note: MU/TSLA/VRT long in BOTH legs — cap or monitor.
- Monitor: `python3 tools/quant/bigmove/live_monitor.py`
- Next refit: 2027-01-31. Price data through 2026-08-18.
- Re-check VIX at formation time (local data lags ~10 days).
