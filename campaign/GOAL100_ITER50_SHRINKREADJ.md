# GOAL100 ITER50 - BOOK-SOLVER (SHRINK, BRWT-CAP) RE-ADJUDICATION AT THE CURRENT CHAMPION

Session 30, 2026-09-20. Honest negative, NO ADOPTION. Champion of record UNCHANGED:
campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 cfa9ec4d38158691 /
weights a384d6b92e258fd5 / FS SR 3.820357 / cagr 23.92 pct / gross 1.0 / MDD -3.7339 pct /
0 neg yrs / Wmax_sf 1.9736x.

## The cell (26th measured axis)
The solver grid (shrink_d, brwt_cap) was last adjudicated at the PRE-adoption champion
(ITER22 15-pt argmax, ITER23 7 edge points all wall-inadmissible, ITER29 estimator fixed
point). Since then TWO admitted NON-UNIFORM rescales moved the covariance the shrink acts
on (ITER47 A5r2 vt010 to vt024, share 3.78 to 2.41 pct; ITER49 QAxasts vt010 to vt015,
share 7.9566 to 5.5133 pct), and the #48 mechanism law states diag shrinkage re-prices
hedging under any non-uniform rescale. No anti-dog-chase seal existed on the book-solver
family. Precommit e9eaf0183cb2072c sealed BEFORE any candidate computation; grid = the
ITER22 15-pt + ITER23 7-pt families VERBATIM (zero free choice; s in 0/0.25 dropped per
ITER22's sealed disclosure).

## Sealed pipeline deviation (disclosed pre-run)
Builder-native convention (fit_relw then apply_cap), NO water-filling projection: the
frozen project_wmax hard-asserts block mass <= 0.30 (valid only at the incumbent cap) and
the projection is IDENTITY on the incumbent (projid 0.000e+00 on every ITER48/49 arm), so
no-projection is exactly the committed path at the anchor; elsewhere a wall breach is a
FILTER-INADMISSIBLE cell (the ITER23 "last admissible point" reading), not a rescue.

## Result: single clean run, NO-ADMISSION, honest negative
A2 anchor continuity EXACT: rebuild (0.70, 0.30) from live B.PATHS reproduces the
committed pair to 7.633e-17 (weights) / 9.991e-17 (bytes), IS-SR 4.218504 = bar exactly,
projid 0.0, rows 1809, k 11. THE CURVE (22 cells):
- EVERY bar-beating cell breaches the Wmax 2.0x invariant: best 4.242558 at
  (shrink 0.40, cap 0.30) but Wmax_sf 2.0932x; (0.50, 0.30) 4.235334 at 2.0516x;
  (0.70, 0.27) 4.227197 at 2.0582x; (0.70, 0.28) 4.226649 at 2.0300x; (0.60, 0.30)
  4.227365 at 2.0125x; (0.70, 0.29) 4.223676 at 2.0018x; (0.70, 0.26/0.25) 2.0864x/2.1146x.
- EVERY wall-admissible non-anchor cell sits BELOW the bar: best admissible
  (0.98, 0.25) 4.194032 at 1.9671x; (0.85, 0.30) 4.202808 at 1.9104x.
IS admission list EMPTY (bar 4.218504 + 1e-4 jitter margin, disclosed, ~48x the measured
landing jitter). Per the sealed stop rule: no reveal, no candidate CSV, champion sha
pre equals post (asserted by the driver). ITER23's structure REPLICATED EXACTLY at the
new covariance: the incumbent is the admissible argmax of its solver neighborhood - the
staleness hypothesis (post-rescale re-fitting could beat the anchor inside the wall) is
REFUTED BY MEASUREMENT. Fourth independent plateau confirmation (weights ITER22,
estimator ITER29, recipe ITER30, solver-grid-at-current-champion ITER50).

## Frontier consequence
26 axes measured under the current objective; the book-solver family now RE-CLOSES at
the CURRENT champion (sealed single-re-adjudication scope - no further solver-grid
measurement is possible this generation). Operator levers UNCHANGED: purchased data /
rule change (relaxing Wmax 2.0x remains the only measured door to the IS-attractive
concentrations, priced at roughly +0.02 FS-SR at the old edge and now up to +0.024
IS-SR at the new edge - still operator-only, still evidence-contradicted OOS on its
best historical axis). The 20 pct ann floor and the 1.6 gross cap are NOT binding on
the champion (23.92 pct ann, gross 1.0). Landed: coord/ITER50_SHRINK_READJ complete
(precommit, driver_iter50.py sha16 1db4b29c9077989d, log sha16 1a92e365c279c80a,
22 arm weight files, NO candidate), test_iter50_shrink_readj.py 6 pins mutation-checked
RED (fake wall-admissible bar-beater caught by 4 pins incl. log-sha immutability) then
byte-exact restore then GREEN; one test-authoring defect caught fail-closed pre-GREEN
(no-projection pin matched the def line - repaired to call-site check).
