# ITER31 FINDINGS - COVARIANCE-TARGET ARMS AT THE INVARIANT CAP (2026-09-19, session #13)

Pre-commit: FINDINGS_PRECOMMIT.md sha16 70c776c7f82a96c8, SEALED before any candidate
computation (driver asserts the hash; mutation aborts). Cell: #121 closed the
estimator-target axis by INADMISSIBILITY (A3/A4 bar-beating but past the Wmax wall);
the #119 repair precedent (credit at-cap) had never been applied to this axis. This
iteration measured it: A3/A4 water-filled to the invariant at k_covered=11 (#120
canonical convention; ITER26's literal x13 denominator NOT reused - disclosed in the
pre-commit; the incumbent itself is feasible under the corrected invariant at 1.8115x).

## PRE-RUN DEFECTS FOUND AND FIXED (all BEFORE the first execution; run #1 clean)
1. winner-gross defect: the reveal block read Wg_p (last loop iteration = A4) instead
   of the argmax winner's gross weights; fixed to rebuild the winner's book (G2
   correctness).
2. placeholder collision: ''13'-style header tokens produced stray apostrophes
   (syntax error caught by py_compile fail-closed); fixed pre-run.
3. anchor nrows hack replaced by proper capture of the anchor fit's (rows, k).
COSMETIC, SEALED: the pre-commit contains one 'session #13' apostrophe typo from the
same collision class; the file stays byte-sealed (hash stability beats a blemish).

## Anchors (all PASS pre-candidate)
projection-identity on incumbent = 0.0 exactly; weights 8.327e-17; bytes 9.996e-17
(n=4806); grossmax 1.000000000 / 0 days over 1.6; incumbent Wmax_sf(x11) 1.8115x;
incumbent IS-SR 4.198632 exact (continuity); fit rows 1809, k_covered 11.
REPRO: both arms re-fit vs ITER29 saved arm vectors maxdev 6.939e-17 (need <1e-9) -
machinery bit-exact.

## RESULT: ADMITTED 2/2 at the cap -> argmax A3 -> REVEAL -> G7 FAIL -> REJECT
- A3 constvar s=0.70: unprojected IS-SR 4.2444 -> AT-CAP 4.2443 (projection cost
  0.0001 - shadow-pricing scale, same pathology family as ITER22/26/30); Wmax_sf 2.0000x
  exactly (the cap binds; moved mass 0.0176); IS-ann 18.49 pct, IS-MDD -2.32, 0 neg IS yrs.
- A4 diag-LW04 s*=0.0293: unprojected 4.2274 -> AT-CAP 4.2261 (cost 0.0013); Wmax_sf
  2.0000x (moved mass 0.0152); IS-MDD -2.51, 0 neg IS yrs.
ARGMAX = A3 (higher IS-SR). A4 UNREVEALED by the sealed stop rule.

REVEAL (first estimator-family reveal ever fired), 12-pool refit at the cap, gear 1.0,
n=4806 (2008-03-31..2026-08-28):
  FS SR = 3.787991 vs incumbent 3.751429 (+0.0366) - THE STRONGEST REJECTED CANDIDATE
  ON CAMPAIGN RECORD (recipe argmax +0.0026, xly -0.0013, credit -0.0435).
  Operator gates: ann cagr 23.7438 pct (>=20 PASS) / arith 21.4716 / MDD -3.8237
  (>=-7 PASS) / 0 neg yrs (PASS) / gross 1.000000000 (<=1.6 PASS) / CFX4 0 (PASS) /
  Wmax_sf 2.0000x (PASS) / G8 shrink 0.0000 pct (PASS).
  G7 OOS police: bins [+0.0452, +0.0336, -0.0031, -0.0788, -0.0179] = 2/5 positive
  (needs >=4/5) => FAIL. Gains front-loaded 2017-20; erosion 2021-26 - the ITER17-law
  vintage shape (IS-fit gain transfers early, decays late).
VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per pre-commit).
Champion sha16 pre==post: 8559fa55ee9a3417 / d2d11c92a98683df.

## STRATEGIC CONSEQUENCE
1. The estimator axis is now closed at the cap TOO (unprojected #121 + at-cap here):
   the at-cap completion buys back essentially ALL of the unprojected IS gain
   (4.2444 -> 4.2443), i.e. the wall was costing almost nothing in IS terms - the
   rejection was never about the invariant, it is the OOS police.
2. NEW OPERATOR ITEM (no self-relax per #109/#116/#118 precedent): for the first
   time a candidate DOMINATES the incumbent on the operator's literal objective
   (SR +0.0366 at ann 23.74 pct, gross 1.0, every operator-stated gate green) and dies
   ONLY on the internal 5-bin OOS-consistency gate. Relaxing G7 to >=3/5 positive bins
   (or a min-dSR-only form) would admit it. That gate has killed 7 candidates, all of
   which look exactly like this one (front-loaded gains); the campaign prior is that
   3.788 does not representable out-of-sample. The decision belongs to the operator:
   keep the police as-is (recommended; champion stands) or charter a sanctioned
   G7-relaxation reveal (would be a rule change, not an iteration).
3. Frontier after ITER31: NINE axes measured-closed (gear, weights, grid edges, census
   data, 8c ledger, credit-at-cap, covariance-target, covariance-target-at-cap, recipe).
   Remaining levers unchanged: purchased data or operator rule change - now with a
   CONCRETE priced rule-change candidate (G7) on the table for the first time.

## Landed
driver_iter31.py + driver_iter31.log + arm_A3/A4_atcap_weights.csv +
candidate_A3_atcap_daily.csv (for-the-record) + this FINDINGS; pins
campaign/bt/tests/test_iter31_fittarget_capfit.py (6, mutation-checked RED ->
byte-exact restore -> GREEN); memo campaign/GOAL100_ITER31_FITTARGET_CAPFIT.md;
STANDUP_LOG append; memory sub-entry #123.
