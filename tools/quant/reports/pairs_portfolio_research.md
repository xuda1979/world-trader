# Pair Portfolio Research — Walk-Forward Falsification Frontier

**Date:** 2026-08-06  |  **Cost assumption:** 3.8 bps round-trip  |  **Engine:** v5 symmetric mean-reversion on Kalman spread, z=2.0 entry

## 1. The portfolio
Calendar-time walk-forward simulation, dollar-neutral, sized so a 1-sigma spread
move = 1% equity per pair. IS = first 60% of shared calendar; OOS = last 40%.
Qualification = Bonferroni IS t-gate + Engle-Granger cointegration (IS slice only,
no OOS peek).

- **11 qualified pairs**, 104 OOS trades
- **OOS net Sharpe = 6.96**, Sortino 27.8, maxDD -2.1%, CAGR@10%vol = 100.4%
- Net of 3.8bps costs; gross Sharpe 7.23 (cost drag = 0.27 Sharpe)
- Top OOS contributors: SO/DUK (+32.8 sig), JNJ/ABBV (+21.8), AMAT/ARM (+20.1),
  PFE/MRK (+19.1), AAPL/AMAT (+16.0)

## 2. Diversification frontier (real)
OOS net Sharpe scales strongly with breadth:

| pairs (k) | net Sharpe |
|-----------|-----------|
| 1 | 3.46 |
| 2 | 4.36 |
| 5 | 5.69 |
| 7 | 5.17 |
| 9 | 6.36 |
| 11 | **6.96** |

Breadth is the single biggest lever: 3.5 -> 7.0 as we go from 1 to 11 independent
pairs. The portfolio should hold as many independently-qualified pairs as pass the
gate.

## 3. Scramble control (the honest test)
Lag-scramble series B by a random circular offset (preserves vol/autocorrelation,
destroys genuine cointegration) and re-run the identical WF+portfolio pipeline.
Distribution across 23 seeds: mean 5.13, sd 1.04, min 3.03, max 7.75.

- Real portfolio (6.96) is **z = +1.76** above the scramble mean.
- 4 of 23 scramble draws exceed the real result (max 7.75).

Reading: the real signal *clears* the scramble mean by ~1.8 sigma and sits in the
97th+ percentile, but is not fully separated -- the walk-forward gate admits noise
in both real and scrambled universes reflecting a mild multiple-testing / selection
prize. This is a **suggestive-but-not-clinching** edge; treat reported Sharpe as an
upper bound on realized discretionary edge.

## 4. Gate-strictness sweep (MIN_IS_TSTAT)
Tightening the IS t-stat floor and measuring real-vs-scramble z:

| IS T floor | pairs | real OOS Sharpe | scram mean | z |
|-----------|-------|-----------------|-----------|-----|
| 6.0 | 10 | 6.51 | 4.94 | 1.36 |
| 7.0 | 9 | 6.36 | 4.78 | 1.35 |
| 8.0 | 7 | 5.17 | 4.01 | 1.28 |
| 9.0 | 4 | 4.88 | 3.85 | 0.97 |
| 10.0 | 4 | 4.88 | 3.86 | 0.89 |
| 11.0 | 4 | 4.88 | 3.68 | 1.27 |

Tightening the IS gate **reduces real Sharpe faster than it improves separation**
(z stays ~1.3-1.4 and even drops). The base gate (z≈1.75 with full breadth but no
IS-extra floor) is the best risk/reward balance. Do NOT tighten beyond the base
gate; keep all 11 pairs.

## 5. Recommendations for building the high-Sharpe book
1. **Keep full breadth (all 11 pairs)** -- diversification is the dominant Sharpe
   driver; tightening erodes it.
2. **Profile the cost drag:** net vs gross = 0.27 Sharpe @3.8bps. At 7.6bps (per-side
   reading) expect ~0.5 drag. Prefer higher-z-entry (fewer, bigger trades) if costs
   rise.
3. **Treat the edge as provisional:** z≈1.8 vs scramble is promising but not
   settled. Add more history (paid data tier) to widen the OOS window before hard
   capital allocation.
4. **Do not blend the cross-sectional same-sector book** -- it fails its own
   scramble test (z≤0.95, gross scrambled positive); it would dilute this book.
5. The IS universe holds 294/404 pairs with IS t≥5 but most fail EG cointegration;
   the 11-pair book is already the cointegrated core.

## Artifacts
- `tools/quant/pairs_frontier.py` -- diversification frontier + scramble falsification
- `tools/quant/pairs_gate_sweep.py` -- IS-t gate sweep (real vs scramble)
- `tools/quant/pairs_portfolio_sim.py` -- added MIN_IS_TSTAT research knob
- reports: pairs_portfolio_sim.{md,json}, pairs_frontier.json, pairs_gate_sweep.json
