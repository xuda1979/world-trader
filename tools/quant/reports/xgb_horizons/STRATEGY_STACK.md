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

## Combo risk ladder (vol targeting)

| Variant | SR | ann | dd |
|---|---|---|---|
| raw 50/50 | 1.15 | +17.2% | -25.8% |
| vol-targeted 1y leg | 1.11 | +12.3% | -14.2% |
| both legs vol-targeted | 1.01 | +9.1% | -8.9% |

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
