# ML Long/Short Strategy Stack — Master Summary (ex1st era)

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
