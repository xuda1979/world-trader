> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
# GOAL100 ITER38 - DUALMOM HYSTERESIS-BAND (BAND) AXIS AT FROZEN WIN=200
Session 19, 2026-09-19 ~13:1x CST. Operator objective verbatim: "keep improving. the leverage must
be <=1.6. Maximize Sharpe ratio. The annual return can't be smaller than 20%."
CHAMPION UNCHANGED: campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 8559fa55ee9a3417
/ weights d2d11c92a98683df / ann 23.6054 pct / SR 3.751429 / MDD -3.6130 / gross 1.0 (all operator
constraints met; sha pre==post asserted by the driver).

## WHAT WAS MEASURED
dualmom = QA_dualmom_band121 (A3_xs_quality r2 accepted sleeve; 5.7226 pct book share measured at
the A2 anchor) - Antonacci dual momentum: xs 12-1 top-tercile long-only + FF-market 200d-MA gate
with a +/-BAND hysteresis band, flat off; monthly T+1; 6.4bps FULL |dW|; VT 0.10 expanding60 cap5.
Its acceptance plateau was a 25-cell (win x band) standalone-SR grid on the PRE-costfix convention
(21/25 within 20 pct of peak, (200, 0.03) interior) - the book-level pool-fit IS-SR under the
current objective was never measured over any dualmom scalar. The 2-D surface REFUSED at seal
(25-cell mining); the pre-committed 1-D slice rule (diescrack class): sweep the THRESHOLD (BAND)
at frozen WINDOW (WIN=200). GRID = the acceptance-printed band axis at-bands (0.01, 0.02, 0.03,
0.04, 0.05) - zero new points, anchor centered. FRAC=1/3 and the xs 21/252 lookbacks frozen as
strategy identity (documented load-bearing / name-defining respectively).

## DISCIPLINE TRAIL
Precommit SEALED 8a1c571db36f9770 BEFORE any candidate computation; pre-seal A1 disclosed inside:
re-typed generator (campaign/scripts/QA_dualmom_band121.py NEVER imported - module-level
save_sleeve would rewrite live bytes; A3 engine spec-loaded from its path) vs committed CSV
maxdev 9.996344e-17 with INDEX IDENTICAL (n=4743, spans 2007-10-08..2026-08-12 both, head
2007-10-08=0.0 both) - byte-faithful INCLUDING calendar, and proof the D17-patched panel
(manifest.csv skipped) content-equals the original 298-name panel. Driver derived from
driver_iter37.py by 32 asserted-exactly-once substitutions; frozen pool blocks ast-text-identity
vs driver_iter36+37; anchors ALL EXACT (projection identity 0.0 / weights 8.327e-17 / bytes
9.996e-17 / rows 1809 / k 11 / IS-SR 4.198632 / Wmax_sf 1.8115x; anchor cell weights 7.527e-09 /
book 4.468e-10, SLSQP boundary-jitter class). Coverage law held: all 5 cells on the IDENTICAL
stream calendar (first eligible MES 2007-09-28 gate-ON at every band; cells LIVE, regen-dev
0.022-0.082).

## RESULT: 1/5 ADMITTED - REVEAL FIRED AND REJECTED ON G7 (ITER17-LAW CLOSURE 13)
Band axis (IS-SR): 0.01 -> 4.188768 / 0.02 -> 4.199008 ADMITTED / 0.03 -> 4.198632 (anchor) /
0.04 -> 4.193199 / 0.05 -> 4.185947. Single-peaked with the peak at 0.02 = bar + 0.000376
(shadow-price scale - the incumbent freeze sits AT the interior max within measurement
resolution). REVEAL (argmax BAND=0.02, one per stop rule): FS SR 3.750604 < 3.751429 - the IS
gain INVERTS at full sample; G7 bins -0.0006/+0.0015/-0.0059/-0.0076/-0.0005 = 1/5 positive =>
FAIL => REJECT (no second reveal). All operator gates PASS (cagr 23.6016 / gross 1.000000000 /
MDD -3.6166 / 0 neg yrs / CFX4 0 / Wmax_sf 1.8114x / G8 0.0000 pct). Bin magnitudes tiny
(<=0.0076) and window-inconsistent: the police binds on CONSISTENCY (ITER30 structure-noise
family). Champion sha pre==post.
Artifacts: coord/ITER38_DUALMOM_BAND/ complete (precommit 8a1c571db36f9770, anchor_iter38.py+log,
driver_iter38.py c294d91c2cf36f53 + log db61dfae1a9a4580, 5 arm_BAND weights CSVs,
candidate_BAND0.02_daily.csv c116230bab638c10 + _weights for-the-record). Pins:
campaign/bt/tests/test_iter38_dualmom_band.py 6 pins, mutation-checked RED (fake cell value
caught by 3 tests) -> byte-exact restore (log sha db61dfae1a9a4580) -> GREEN.
