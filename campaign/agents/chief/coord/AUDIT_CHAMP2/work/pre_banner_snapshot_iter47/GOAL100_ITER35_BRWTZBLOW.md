> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
# GOAL100 ITER35 - BRWT Z-THRESHOLD LOWER-ENVELOPE EXTENSION (SIGNAL-PARAMETER AXIS, LARGEST-WEIGHT SLEEVE FAMILY 30.00 PCT) - HONEST NEGATIVE; AXIS FULLY CLOSED AS INTERIOR-MAX (2026-09-19, session 16)

Operator objective (unchanged verbatim): keep improving; leverage <= 1.6; maximize
Sharpe; annual return >= 20 pct. Champion of record UNCHANGED:
GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 8559fa55ee9a3417 / weights
d2d11c92a98683df / ann 23.6054 pct / SR 3.751429 / MDD -3.6130 / gross 1.0 /
0 neg yrs. Gauntlet ok 7/7 fresh this session
(coord/verify_champion_r3_last_session16.json).

# THE CELL
ITER34 (#126) swept the brwt family scalar zb over the acceptance envelope
{1.0, 1.25, 1.5, 1.75, 2.0} and found IS-SR falling MONOTONICALLY from the anchor
(0/5 admitted), disclosing zb < 1.0 as the only unmeasured direction. Two structural
facts pointed down and were disclosed at seal time: the family's acceptance-era
evolution already walked zb from 1.5 (rev15 config) to 1.0 (champion config), and
IS-ann rises as zb falls. This seal measured the lower envelope: grid
{0.25, 0.5, 0.75, 1.0} = the REFLECTION of the ITER34 novel cells about the anchor,
EXCLUDING the degenerate zb=0 always-in limit (pos = sign(-z) every day = a different
strategy, not a cell of this family). Precommit sealed 3c8c6083b33fb3b8 BEFORE any
candidate; A1 re-run pre-seal, identical to ITER34's (9.999e-17 / 9.986e-17 / 9.996e-17,
n=6567/4580/4580). Generator/pool/fit/build byte-identical to ITER34. Primary pre-stated
risk: lower zb holds MORE 2021-22 energy-crisis exposure (the known G7 fragility bin).

# RESULT (driver_iter35.log)
- Anchors ALL EXACT (A2 identity 0.0 / weights 8.327e-17 / bytes 9.996e-17 / rows 1809 /
  k_covered 11 / IS-SR 4.198632 / Wmax_sf 1.8115x; anchor cell weights 8.903e-09 / book
  4.044e-10 / block share 0.300000 exact).
- ADMITTED 0/4: the LEFT side RISES MONOTONICALLY INTO the anchor:
  3.897552 (zb=0.25) -> 4.057100 (0.5) -> 4.175140 (0.75) -> 4.198632 (anchor = bar).
  IS-MDD degrades steeply as zb falls: -2.56 -> -3.04 -> -3.70 -> -4.36 pct. Cells LIVE
  (regen-dev 0.179-0.205).
- NO reveal per the sealed stop rule; no candidate CSV. Champion sha16 pre==post True.

# VERDICT AND READING
HONEST NEGATIVE (NO-ADMISSION). Stitched with ITER34, the FULL measured curve over
zb in {0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0} is SINGLE-PEAKED with the INTERIOR
PEAK EXACTLY AT THE INCUMBENT zb=1.0 (left rises 3.898 -> 4.199; right falls
4.199 -> 3.230). The incumbent freeze is the IS-INTERIOR-ARGMAX of its own one-scalar
family at 30.00 pct book weight - upgrading the ITER34 edge-max reading to the strongest
possible closure shape. ITER17-law closure 10. The pre-stated crisis-fragility risk never
reached the police: the IS-MDD gradient (-2.56 -> -4.36 pct as zb falls) already prices
it. Closest miss: zb=0.75 at bar - 0.0235 - a real competitor, honestly below the 1e-4
jitter bar, unrevealed by law. The zb axis is now FULLY CLOSED on both sides of the
anchor; the degenerate zb=0 remains outside the family by construction.

# FRONTIER AFTER ITER35
TWELVE axes measured-closed (gear 21, weights 22, grid edges 23, census data
24/117b/27/28, 8c-era ledger 25, credit-at-cap 26, covariance-target 29,
covariance-target-AT-CAP 31, recipe 30, signal-parameter DUR 32, signal-parameter
C5ng-k 33, signal-parameter brwt-zb 34+35 FULLY closed interior-max). Remaining
second-tier cells: diescrack L40/Z20 (10.83 pct, TWO-scalar single sleeve - needs a
pre-committed 1-D slice rule), QAxasts tsmom189 (7.59 pct), dualmom band121 (5.72 pct),
brwt per-variant lb (refused: 125-cell mining surface). Four signal-parameter closures
now on record (interior-max 32 / OOS-vindicated freeze 33 / monotone-from-freeze 34 /
FULL interior-max 35) - the acceptance-era freezes are load-bearing without exception.
Remaining levers UNCHANGED: purchased data or operator rule change (G7 price tag
+0.0366 stands; ITER33 +0.0075 second priced point).

Landed: coord/ITER35_BRWT_ZBLOW/ (FINDINGS_PRECOMMIT 3c8c6083b33fb3b8 + anchor_iter35.py
+ driver_iter35.py + driver_iter35.log + FINDINGS + 4 arm weights CSVs for-the-record),
test_iter35_brwt_zblow.py 6 pins (mutation-checked RED -> byte-exact restore -> GREEN),
this doc, STANDUP_LOG, memory 127. SUITE 557 passed / 0 failed (551 + 6, own run).
