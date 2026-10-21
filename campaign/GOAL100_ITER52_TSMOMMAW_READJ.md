# GOAL100 ITER52 - TSMOM (QAxasts) MAW SCALAR STALENESS RE-ADJUDICATION AT THE CURRENT CHAMPION

Session 32, 2026-09-20. Honest negative, NO ADOPTION. Champion of record UNCHANGED:
campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 cfa9ec4d38158691 /
weights a384d6b92e258fd5 / FS SR 3.820357 / cagr 23.92 pct / gross 1.0 / MDD -3.7339 pct /
0 neg yrs / Wmax_sf 1.9736x.

## The cell (28th measured axis)
The tsmom signal moving-average window MAW=189 - ONE generator scalar, family book share
5.5133 pct (9th of 12) - last certified by ITER37 (interior peak EXACTLY at the anchor 189,
IS-SR 4.198632 = bar, at the 8559fa55ee9a3417 frame, vt10 vintage). That certificate predates
THREE adopted non-uniform rescales: ITER43 (A5r2 vt015), ITER47 (A5r2 vt024), and ITER49
(tsmom vt015 - the largest adopted move on record AND structural: it replaced the canonical
sleeve file itself, vt 0.10 vintage -> E1_QAxasts_tsmom189__vt015.csv c40d008ddbf7c579).
Under the #48 law (diag shrink re-prices hedging under ANY non-uniform rescale) the question
was whether the interior peak moved with the covariance AND with the in-family vt change -
the MAW x vt015 interaction at book level was NEVER measured (ITER37 ran at vt10). DEEPEST
staleness of the four remaining class cells; FIRST of the four enumerated by the session-31
police (ITER51 precommit: "tsmom-MAW / DUR / C5ng-k / brwt-zb staleness cells: same class,
strictly smaller materiality; one cell per session").

## Legality (the refusal reconciliation, recorded AT SEAL)
The session-31 police REFUSED a "tsmom-vt re-adjudication" ("tsmom IS the adopter of
rescale-2; re-measuring its own grid at its own adoption = chasing the adoption itself") -
that binds the vt SCALAR, the adopted quantity itself. MAW is a DIFFERENT frozen scalar with
a THREE-generation-old interior-peak certificate; re-measuring it chases no adoption and no
edge. The #140/ITER49 "LAST seal on the tsmom family - no extension seal is possible" binds
EDGE-CONTINUATION; the ITER47 escape form governs ("a NEW motivation class recorded in the
ledger, not an edge continuation") - the #141 staleness class IS that class. Grid = the
ITER37 grid VERBATIM (anchor 189 + 126/157/220/252; zero free choice; NO envelope extension
- 315/378 not run); min_periods = maw // 2 COUPLED (derived); vt FROZEN at the current 0.15
anchor in EVERY arm (sweeping it would BE the refused cell). Precommit 0e4c271945a4be28
sealed BEFORE any candidate computation.

## Verify-first (pre-seal)
Gauntlet ok=true 7/7 fresh (verify_champion_r3_last_session32.json: weights 7.632783294297951e-17
/ bytes 1.0408340855860843e-16 / half-turn rejected 1.644349418787801e-05 / gross
1.0000000000005784 n_over 0 / 0 negy / MDD -3.7339 / SR 3.8203573009568794 / cagr
23.92147218901779); nine shas re-hashed ALL OK (incl. vt015 c40d008ddbf7c579, vt024
7ec85336e7f7d00f, ITER49 prior pair 3c456aa53193eb89 + 8313bee1ad8a72fe, derivation parent
driver_iter51.py 586ad73d251a2ac9); baseline suite 654 passed / 0 failed (own run 72.29s);
BAR digits fresh-grepped from driver_iter51.log line 12 (IS-SR=4.218504, projid 0, rows 1809,
k 11); coord quiet + the 4-agent fleet batch disclosed (PIDs 4540-4543, no coord writes).

## Pre-seal probes (anchor_a1_probe.log, before the seal)
A1 regen-maw189-vt015-vs-committed QAxasts ok=True maxdev=9.996e-17 inner=4947 FULL;
CALENDAR identical at ALL 5 MAW arms (n=4947 each); CLIP-REGIME bound_frac_onframe=0.000000
at ALL 5 arms (rcum_min 20.1336..23.8756 pct ann vs the largest bound 0.05). PROBE RUN-1
DISCLOSURE: the first invocation died fail-closed PRE-A1 - a SINGLE-identity D17 patch is
INSUFFICIENT for the tsmom chain (r6lib resolves the FULL-PATH campaign.harness.data
identity); fixed to the Amendment-1 DUAL patch. Runtime fact re-verified: manifest.csv
(mtime Sep 8 14:40) STILL sits in twelve_big and harness data.py panel() has NO skip logic -
the D17 runtime-patch law remains LOAD-BEARING for every r6lib-resolving chain.

## Result: single clean run, NO-ADMISSION, honest negative
Driver = driver_iter51.py via 16 asserted-exactly-once substitutions (make_driver_iter52.py;
sha16 3d3ab315d44f04cc; frozen blocks AST-identical to driver_iter41 AND driver_iter36;
champion-pair pre-assert + per-arm calendar/coverage asserts added back from driver_iter49).
A1 9.996e-17 inner 4947 FULL; A2 continuity EXACT (projid 0.000e+00 / weights 7.633e-17 /
bytes 9.991e-17 / rows 1809 / k 11 / IS-SR 4.218504 = bar BOTH sides); A2b jitter weights
3.249e-09 / IS-SR 1.151e-10 (the 1e-4 admission margin ~87x the weight jitter). THE CURVE
(5 cells):
- ANCHOR MAW=189: IS-SR 4.218504 = the measured IS-argmax of the whole grid EXACTLY
  (interior peak at the committed cell at the CURRENT frame, now at the vt015 vintage).
- MAW=126: 4.172832 THROUGH the wall (projid 2.032e-03, Wmax_sf 2.0000x).
- MAW=157: 4.183629 THROUGH the wall (projid 4.503e-04, Wmax_sf 2.0000x).
- MAW=220: 4.207128 and MAW=252: 4.209368 - admissible (projid 0) but IS-DOMINATED;
  the ITER37-era 252 tick-up PERSISTS at the new frame and still falls bar-0.0091 short.
IS admission list EMPTY (bar 4.218504 + 1e-4). Per the sealed stop rule: NO reveal, NO
candidate CSV, champion sha16 pre equals post (driver-asserted). NEW MECHANISM READ: unlike
ITER48/51 (down-arm wall-shadow on a scale axis), here BOTH down-arms are wall-bound because
the RESCALED fit now sits wall-ADJACENT (anchor Wmax_sf 1.9736x vs 1.8115x at ITER37's
frame) - de-windowing raises wanted tsmom concentration past 2/k at the current covariance.
The ITER37 interior-peak certificate SURVIVES all three rescales + the in-family vt change
- staleness REFUTED for the tsmom signal scalar: SIXTH independent plateau confirmation
(ITER22 weights / ITER29 estimator / ITER30 recipe / ITER50 solver / ITER51 C5ng-vt /
ITER52 tsmom-MAW-at-current-champion). THREE staleness re-adjudications run to date
(solver + largest family + deepest-scalar), ALL return the incumbent as argmax.

## Frontier consequence
27 -> 28 axes measured under the current objective. Remaining staleness-class cells: DUR
(iter32 anchor 1.90), C5ng-k (iter33), brwt-zb (iter34/35) - strictly smaller materiality,
one cell per session discipline. tsmom-MAW RE-SEALED at the current frame (anti-dog-chase
re-binding: no further tsmom-MAW measurement this generation; the admissible-but-dominated
252 arm is RECORDED, NOT chased; 315/378 stay outside the envelope). Operator levers
UNCHANGED = purchased data / rule change (Wmax-relaxation door re-priced at ITER50: up to
+0.024 IS-SR behind the wall; G7 price-tag curve: police approved 2 of 11 reveals, KEEP).
Champion of record: ITER49 tsm-vt015 book, SR 3.820357, cagr 23.9215, gross 1.0.

## Landing
coord/ITER52_TSMOM_MAW_READJ complete (FINDINGS_PRECOMMIT.md 0e4c271945a4be28, probe
script + anchor_a1_probe.log cda0954b06933750, driver_iter52.py 3d3ab315d44f04cc, driver
log badb4a960d53d785, 10 arm files, NO candidate CSV). test_iter52_tsmom_maw_readj.py
6 pins mutation-checked RED (fake bar-beating arm at 252 + fake admission + fake verdict
caught by 4 pins incl. the log-sha immutability pin) -> byte-exact restore (badb4a960d53d785)
-> GREEN 6/6. This memo landed BEFORE the suite (lint validated in-run).
