# Pair Portfolio Sharpe 6.96 — Independent Verification Report

**Verified:** 2026-08-06  |  **Cost:** 3.8 bps RT  |  **Engine:** v5 mean-reversion, z=2.0
**Result under audit:** OOS net Sharpe = **6.96** (Sortino 27.8, maxDD -2.1%, 204 OOS days)

## Is it TRUE? — Four independent checks

### 1. Arithmetic reproduction — PASS (exact)
Recomputed the OOS Sharpe from the raw daily net P&L series with an independent
implementation (mean_daily / stdev_daily × √252, population stdev):
- Sim's own value: 6.9609
- Independent recomputation: 6.9609  → **bit-for-bit identical**
The 6.96 is a faithful product of the documented arithmetic, not a reporting bug.

### 2. Lookahead / leakage audit — PASS (clean)
- **Entry z-score** uses a strictly trailing window `spread[i−lookback : i)` that
  EXCLUDES day `i`; verified per-trade (entry z = −4.39, −2.44, −2.05 on real
  trades) — no future data in the entry trigger.
- **P&L accrues from day `ei+1` onward** (entry 2025-10-17 → first P&L day
  2025-10-20) — no same-bar fill advantage.
- **Qualification** (EG cointegration + Bonferroni IS t-gate) uses only the first
  60% IS slice; lookback/horizon estimated from IS half-life only. OOS dates never
  enter selection.

### 3. Cost model — PASS (conservative, small drag)
- Cost per round-trip = `2 × 3.8e-4 / entry_spread_sd`, charged at entry and exit.
- Median cost 0.044 sigma/trade vs median gross 1.75 sigma/trade → **costs eat
  only ~2.9% of gross P&L**. Cost drag = 0.27 Sharpe (gross 7.23 → net 6.96).
- Cost robustness: 0→7.23, 3.8→6.96, 7.6→6.68, 11.4→6.38 bps. Monotonic, saturating.

### 4. Concentration / fragility — HEALTHY-DIVERSIFIED but RIGHT-SKEWED (CAVEAT)
- **All 11 pairs profitable OOS** (net sigma +9.1 to +32.8). No single-pair driver.
- P&L spread over window: **every ~20-day block is positive** (+2% to +38.7% eq).
- But the daily distribution is **sharply right-skewed** (skew 4.4, kurtosis 31);
  top-1 day = 9.7%, top-5 days = 28%, top-10 days = 40% of total OOS P&L.
- The biggest day (+0.180, 5.4% of total) was decomposed: driven by **5 pairs
  reverting concurrently** (semis AAPL/AMAT/ARM + pharma PFE/TMO/MRK) — a real
  broad mean-reversion day, not a data artifact.

## Statistical context (falsification)
Against a 24-seed lag-scramble control (identical pipeline, scrambled cointegration):
- Real OOS Sharpe 6.96 vs scramble mean 5.13 (sd 1.04), **z = +1.76**, 97th percentile.
- The signal likely carries some real edge (clears the noise floor) but is not
  fully separated from the selection/rounding prize. **Treat 6.96 as an optimistic
  upper bound** on discretionary, live-traded Sharpe.

## Bottom line
The 6.96 is **mathematically true to the pipeline, free of lookahead, honest
about costs, and genuinely diversified**. The genuine caveat is its **right-skewed,
fat-tailed daily P&L** (Sharpe a winner-take-big-days strategy) and a **~1.8σ edge
over noise** that needs more OOS history to confirm before hard capital allocation.
Skew/kurtosis imply the drawdown tail is larger than a normal Sharpe suggests.
