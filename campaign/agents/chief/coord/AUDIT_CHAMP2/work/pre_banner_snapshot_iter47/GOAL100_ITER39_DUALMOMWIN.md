> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
# GOAL100 ITER39 - DUALMOM GATE MA-WINDOW (WIN) AXIS AT FROZEN BAND=0.03 - FAMILY CLOSURE
Session 19 cont., 2026-09-19 ~13:3x CST. Operator objective verbatim unchanged. CHAMPION UNCHANGED:
campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 8559fa55ee9a3417 / weights
d2d11c92a98683df / ann 23.6054 pct / SR 3.751429 / MDD -3.6130 / gross 1.0 (sha pre==post).

## THE SECOND SEAL AND ITS DISCLOSED TENSION
ITER38 (same session) measured the FULL acceptance-printed BAND axis; the curve left NO open
direction on that axis. Seal #1 had pre-named the WIN slice as "the natural SECOND seal if this
one leaves a one-sided open direction" - that literal condition did NOT fire, and this seal
proceeds ON ITS OWN DETERMINISTIC MOTIVATION, disclosed at seal time rather than papered over:
WIN is the OTHER axis of the same 2-D acceptance plateau grid (r2_scan5.py), fully
acceptance-printed (150, 175, 200, 225, 250), sweep rule = mirror of seal #1
(window-at-frozen-threshold), covering the win axis ENTIRELY; dualmom carries 5.7226 pct of the
book. Precommit 207c3aa37640db1d sealed BEFORE any candidate; it also records that FRAC=1/3 has
NO printed acceptance grid (sweeping it needs NEW points = mining-adjacent) and stays refused
absent a pre-committed deterministic convention. min_periods COUPLED to win (derived, not a
second scalar). After this run the dualmom gate family is FULLY measured on both printed axes.

## DISCIPLINE TRAIL
anchor_iter39.py: win-parameterized re-type (per-win MA from the cached FF market; BAND frozen
0.03 constant) - A1 vs committed CSV maxdev 9.996344e-17, INDEX IDENTICAL (identical digits to
seal #1 = same re-type). Driver derived from driver_iter38.py by 27 asserted-exactly-once
substitutions; frozen pool blocks ast-text-identity vs driver_iter36+37+38; anchors ALL EXACT
(identity 0.0 / weights 8.327e-17 / bytes 9.996e-17 / rows 1809 / k 11 / IS-SR 4.198632 /
Wmax_sf 1.8115x / share 5.7226 pct; anchor cell 7.527e-09 / 4.468e-10). Coverage law held
(identical calendar, cells LIVE regen-dev 0.036-0.082).

## RESULT: 2/5 ADMITTED - REVEAL PASSED THE FS BAR AND EVERY OPERATOR GATE, KILLED BY G7
(ITER17-LAW CLOSURE 14)
Win axis (IS-SR) falls STRICTLY MONOTONE across the whole printed envelope: 150 -> 4.218613
ADMITTED (bar + 0.019981 = the LARGEST second-tier IS gradient on record) / 175 -> 4.201254
ADMITTED (UNREVEALED by law) / 200 -> 4.198632 (anchor) / 225 -> 4.184679 / 250 -> 4.175950.
The incumbent WIN=200 sits on the LEFT SLOPE; the acceptance envelope EDGE is the IS-argmax
(the 2003-07 bull made short gate windows look better in-sample).
REVEAL (WIN=150, one per stop rule): **FS SR 3.754857 = +0.003428 over 3.751429 - PASSES the FS
bar**, and EVERY operator gate PASSES: cagr 23.5867 (>=20), gross 1.000000000 (<=1.6), MDD
-3.5869 (BETTER than the champion's -3.6130), 0 neg yrs, CFX4 0, Wmax_sf 1.7926x, G8 0.0000.
G7 bins: 2017-18 +0.0145 / 2019-20 -0.0090 / 2021-22 +0.0051 / 2023-24 +0.0054 / 2025-26 -0.0029
= **3/5 positive** (needs >=4) with min bin -0.0090 (>= -0.10) => FAIL => REJECT.
**OPERATOR RULE-CHANGE DATA POINT (recorded, recommendation KEEP stands)**: WIN=150 is the
strongest "3/5 relaxation" exhibit on record - under a >=3/5-bin rule this book would have been
ADOPTED on the operator's literal objective (higher FS-SR AND better MDD at gross 1.0, ann
23.59). It is killed purely by the internal consistency police; 2/5 windows negative with tiny
magnitudes (<=0.0145) = structure noise, the same family as every prior kill. The G7 price-tag
curve gains a 3/5 point: +0.0366 (31, 2/5) / +0.0075 (33, 2/5, floor breach) / +0.0073 (36, 2/5)
/ **+0.0034 (39, 3/5, no floor breach)** / +0.0026 (30, 2/5). Champion sha pre==post.
Artifacts: coord/ITER39_DUALMOM_WIN/ complete (precommit 207c3aa37640db1d, anchor_iter39.py+log,
driver_iter39.py 00a94c310f527aa6 + log 026de367e0556dad, 5 arm_WIN weights CSVs,
candidate_WIN150_daily.csv c5ea472591886d82 + _weights for-the-record). Pins:
campaign/bt/tests/test_iter39_dualmom_win.py 6 pins (incl. the cross-ITER family-closure pin),
mutation-checked RED (fake FS-SR caught by 2 tests) -> byte-exact restore (026de367e0556dad) ->
GREEN.
