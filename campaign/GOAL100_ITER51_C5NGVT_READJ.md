# GOAL100 ITER51 - C5NG FAMILY VOL-TARGET STALENESS RE-ADJUDICATION AT THE CURRENT CHAMPION

Session 31, 2026-09-20. Honest negative, NO ADOPTION. Champion of record UNCHANGED:
campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 cfa9ec4d38158691 /
weights a384d6b92e258fd5 / FS SR 3.820357 / cagr 23.92 pct / gross 1.0 / MDD -3.7339 pct /
0 neg yrs / Wmax_sf 1.9736x.

## The cell (27th measured axis)
The C5ng family harness vol_target vt_ann - the LARGEST book family (C5ng 17.94 pct +
C5ngsum 14.91 pct = 32.86 pct, share GREW from 31.61 pct under the ITER49 refit) - was
last certified at the vt024-era champion (ITER48: interior peak EXACTLY at the anchor
vt 0.10). The ITER49 adoption rescale (QAxasts 7.9566 to 5.5133 pct, the largest adopted
move on record) postdates that certificate, and the #48 mechanism law states diag
shrinkage re-prices hedging under ANY non-uniform rescale. The STALENESS RE-ADJUDICATION
class (#141, ledger-recorded; one re-adjudication per family per generation; ITER50
consumed the solver family's cell) supplies this generation's C5ng cell. Legality vs the
ITER48 binding ("NO second seal on this family"): that binding binds EDGE-CONTINUATION
("a rising IS edge is recorded, NOT chased" - its own words); the ITER47 binding states
the escape form verbatim ("Any further movement on this family requires a NEW motivation
class recorded in the ledger, not an edge continuation"). The staleness class IS the
ledger-recorded new motivation class; NO edge continuation is involved (same grid
verbatim). Precommit 020a8e69de643117 sealed BEFORE any candidate computation; grid =
the ITER48 mirror of the sealed ITER43 grid VERBATIM (anchor 0.10 + 0.06/0.09/0.12/0.15;
zero free choice; NO upper-edge points - edge extension stays bound).

## Verify-first (pre-seal)
Gauntlet ok=true 7/7 fresh (verify_champion_r3_last_session31.json: weights 7.633e-17 /
bytes 1.041e-16 / half-turn rejected 1.644e-5 / gross exact n_over 0 / 0 negy / MDD
-3.7339 / SR 3.8203573009568794 / cagr 23.92147218901779); triple shas re-hashed (incl.
vt024 7ec85336e7f7d00f + vt015 c40d008ddbf7c579); C5ng vintages intact (3d2b80691ef7a448
/ ccfe3a4bc8706161); baseline suite 648 passed / 0 failed (own run 66.38s); coord quiet.
A1 anchors PRE-seal (anchor_a1_probe.log): regen-vt010-vs-committed C5ng 9.975e-17 /
C5ngsum 9.996e-17, inner 7381 FULL both. CLIP-REGIME PROBE at the current vintage:
bound_frac_onframe = 0.000000 at ALL 5 arms x BOTH variants (on-frame rcum_min 52.3014 /
31.8819 pct ann vs the largest bound 0.05) - ON-FRAME PURE-SCALE at every grid point.

## Result: single clean run, NO-ADMISSION, honest negative
A2 anchor continuity EXACT: rebuild from live B.PATHS reproduces the committed pair to
7.633e-17 (weights) / 9.991e-17 (bytes), IS-SR 4.218504 = bar exactly, projid 0.0, rows
1809, k 11. A2b fit-landing jitter 5.484e-09 weights / 7.868e-10 IS-SR - the sealed
1e-4 admission margin is ~127x the jitter. THE CURVE (5 cells):
- ANCHOR VT=0.10: IS-SR 4.218504 = the measured IS-argmax of the whole grid EXACTLY
  (interior peak at the committed cell, at the CURRENT frame).
- VT=0.09: 4.207912 THROUGH the wall (projid 7.658e-03, Wmax_sf 2.0000x) - the ITER48
  wall-shadow channel (down-scale raises wanted C5ng share past 2/k) firing at the new
  covariance exactly as predicted.
- VT=0.06: 4.053512, projid 3.579e-02, Wmax_sf 2.0000x (wall-bound, deepest down-arm).
- VT=0.12: 4.184495 and VT=0.15: 4.021775 - admissible (projid 0, Wmax_sf 1.7843x /
  1.5595x) but IS-DOMINATED, monotone falling above the anchor.
IS admission list EMPTY (bar 4.218504 + 1e-4). Per the sealed stop rule: NO reveal, NO
candidate CSV, champion sha16 pre equals post (driver-asserted). The ITER48 interior-peak
certificate SURVIVES the rescale - the staleness hypothesis is REFUTED for the largest
family, exactly as ITER50 found for the solver: the in-wall ranking is covariance-robust.

## Frontier consequence: FIFTH independent plateau confirmation
ITER22 weights / ITER29 estimator / ITER30 recipe / ITER50 solver-grid /
ITER51 C5ng-vt-at-current-champion. TWO post-adoption staleness re-adjudications
(solver + largest family) both return the incumbent as the argmax; the plateau is not an
artifact of any single family's seal. C5ng family RE-SEALED at the current frame
(anti-dog-chase re-binding: no further C5ng measurement this generation; a rising IS
edge at 0.15 would have been RECORDED, not chased - the measured curve FALLS from the
anchor on both sides, so no edge exists to chase). 27 axes measured under the current
objective. Operator levers UNCHANGED = purchased data / rule change (Wmax-relaxation
door re-priced at ITER50: up to +0.024 IS-SR behind the wall; G7 price-tag curve:
police approved 2 of 11 reveals, KEEP). Remaining staleness cells of the class (tsmom-MAW,
DUR, C5ng-k, brwt-zb - all interior-max closures at pre-rescale frames) are strictly
smaller materiality; one cell per session discipline leaves them to future generations
if any future adoption re-stales them.

## Landing
coord/ITER51_C5NG_VT_READJ complete (FINDINGS_PRECOMMIT.md 020a8e69de643117, probe
script + anchor_a1_probe.log, driver_iter51.py 586ad73d251a2ac9 (derived from
driver_iter48.py by 8 asserted-exactly-once substitutions incl. the D19 reveal-label
guard formatting FS_BAR), driver_iter51.log 717fb13980a137e3, 15 arm files, NO candidate
CSV). test_iter51_c5ng_vt_readj.py 6 pins mutation-checked RED (fake bar-beating arm +
fake admission caught by 4 pins incl. the log-sha immutability pin) -> byte-exact
restore (717fb13980a137e3) -> GREEN. Three test-authoring defects caught fail-closed
PRE-GREEN (regex unpack arity x2 + tuple index after the arity fix - all in test code,
no log/pin tolerance touched; #136 inherited-literal class cousin). This memo landed
BEFORE the suite (lint validated in-run).
