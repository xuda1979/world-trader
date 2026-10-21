# RES_VOL FINDINGS — volatility / options-implied engines (CBOE VIX term structure)
> Chartered to find a decorrelated volatility-surface engine (term-slope) the champion lacks.
> Honest verdict: **REJECT (all 20 candidates fail every gate).**

## Re-derived this session (run_hunt_r2.py, fresh compute)
All 20 vol books were re-run on 2026-09-09 from more_vol data (VIX 1990+, VXV 2007+, VIX3M 2009+,
VIX6M 2008+, VIX9D 2011+, RVX 2009+, VVIX 2007+; SPX spliced 1993+). Candidates:
- L1 VRP: VIX - trailing RV21 (long book on spliced SPX, lb 10/21/63): SR 0.56-0.59, 8 neg yrs,
  worst year -31.9%, corr ~ -0.05.
- L3 term-slope: VIX9D-VIX3M, 3m-6m in short/long directions: SR -0.47..+0.23, all fail.
- L2 RV-lead (VIX9D > RV21): long SR 0.70 (best), short -0.73.

## SCORECARD: 20 books | local-pass 0 | V2-pass 0
Best candidate W_9dlead_long SR=0.70 (corr -0.055), W_spx_vrp SR=0.59 (corr -0.050) — all far
below the SR>=1.5 (or even SR>=1.0) champion-eligibility floor.

## Verdict
**REJECT.** The VIX term-structure / VRP books do not clear SR>=1.0 in the costed/causal/vol-
targeted harness. This CONFIRMS the prior HUNT_VOL2 R1/R2 negative (risk-off gates + overlays
dead; A5 contango already in champion). The vol family is exhausted for standalone sleeves; vol
remains a REGIME/GATE input only.

RES_VOL DONE
