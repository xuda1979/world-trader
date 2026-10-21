> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
# GOAL100 ITER31 - COVARIANCE-TARGET AT THE INVARIANT CAP (2026-09-19, session '13)

Operator objective (verbatim, unchanged): "keep improving. the leverage must be <=1.6.
Maximize Sharpe ratio. The annual return cannot be smaller than 20 percent."
Champion of record UNCHANGED: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16
8559fa55ee9a3417 / weights d2d11c92a98683df / ann 23.6054 pct / SR 3.751429 / MDD
-3.6130 pct / gross 1.0 exact / 0 neg yrs. Gauntlet ok 7/7 pre-run
(coord/verify_champion_r3_last_session13.json).

## THE CELL
#121 closed the covariance-TARGET axis by INADMISSIBILITY: A3 constvar (IS-SR 4.2444,
Wmax_sf 2.0966x) and A4 diag-LW04 (s*=0.0293, IS-SR 4.2274, Wmax_sf 2.0837x) beat the
IS bar but sat past the 2.0x concentration wall, unrevealed. #119 established (credit,
ITER26) that an inadmissible bar-beater gets ONE invariant-legal completion: water-fill
to the largest allocation the EXISTING invariant permits, re-adjudicate, ONE reveal.
The estimator axis had never received it. ITER31 = that cell. No new data, no operator
rule change (legal basis identical to ITER26). Wmax convention: k_covered = 11
(#120 canonical; disclosed divergence from ITER26's literal x13 form, which
post-dated correction would fail the incumbent itself).

## RESULT (driver_iter31.log; precommit 70c776c7f82a96c8 sealed pre-run)
- Anchors: projection-identity 0.0 exact; weights 8.327e-17; bytes 9.996e-17; incumbent
  IS-SR 4.198632 exact; REPRO vs ITER29 saved arms 6.939e-17 (machinery bit-exact).
- ADMITTED 2/2 at the cap: A3 4.2443 / A4 4.2261 (projection cost 0.0001/0.0013 - the
  wall was costing ~nothing in IS terms); Wmax_sf 2.0000x exactly both.
- ARGMAX A3. REVEAL: FS SR 3.787991 = +0.0366 over the incumbent - STRONGEST REJECTED
  CANDIDATE ON RECORD - with ALL operator gates PASS (cagr 23.7438 pct >= 20; gross 1.0;
  MDD -3.8237 >= -7; 0 neg yrs; CFX4 0; G8 0.0000 pct).
- G7 OOS police: [+0.0452, +0.0336, -0.0031, -0.0788, -0.0179] = 2/5 positive
  (needs >=4/5) => FAIL => REJECT per sealed stop rule. A4 unrevealed by law.
  Shape: gains front-loaded 2017-20, erosion 2021-26 - the ITER17-law vintage shape.
  This is ITER17-law kill '7.

## DECISION ITEM FOR THE OPERATOR (recorded, NOT acted on - no self-relax precedent)
For the first time a candidate dominates the incumbent on the operator's literal
objective (higher SR at ann 23.7 pct, gross 1.0, every operator-stated gate green) and
dies ONLY on the internal 5-bin OOS-consistency gate (G7). The G7 police is 5-for-5 on reveals it has judged
(bund_02y, credit-at-cap, xly_etf, recipe-argmax, A3-at-cap; seliccary died the G5
window-confirm and RB_hobr the OOS-ann arm), every one with the same front-loaded-gain
shape; the campaign reading is
that the 2021-26 erosion is the honest signal and 3.788 would not have represented
out-of-sample. Keeping G7 as-is is RECOMMENDED. If the operator ever wants to relax it
(e.g. >=3/5 bins or min-dSR-only), that is a RULE CHANGE to be sanctioned explicitly,
with this memo as its price tag: +0.0366 FS-SR claimed, 3/5 windows negative.

## FRONTIER AFTER ITER31
NINE axes measured-closed: gear (ITER21), weights (ITER22), grid edges (ITER23), census
data (ITER24/#117b/27/28), 8c-era ledger (ITER25), credit-at-cap (ITER26),
covariance-target (ITER29), covariance-target-AT-CAP (ITER31), recipe (ITER30).
Remaining levers unchanged: purchased data or operator rule change. Landed:
coord/ITER31_FITTARGET_CAPFIT/ (precommit+findings+driver+log+arm CSVs+candidate CSV),
test_iter31_fittarget_capfit.py 6 pins (mutation-checked RED -> byte-exact restore ->
GREEN).
