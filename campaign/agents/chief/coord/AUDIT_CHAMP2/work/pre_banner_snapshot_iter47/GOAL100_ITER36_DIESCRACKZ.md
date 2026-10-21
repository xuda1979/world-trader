> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
GOAL100 ITER36 - DIESCRACK GATE-Z AXIS AT FROZEN L=40 (SIGNAL-PARAMETER AXIS, LARGEST REMAINING SECOND-TIER CELL 10.83 PCT) - HONEST NEGATIVE; REVEAL FIRED AND DIED ON G7 (ITER17-LAW CLOSURE 11) (2026-09-19, session 17)

Operator objective (unchanged verbatim): keep improving; leverage <= 1.6; maximize
Sharpe; annual return >= 20 pct. Champion of record UNCHANGED:
GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 8559fa55ee9a3417 / weights
d2d11c92a98683df / ann 23.6054 pct / SR 3.751429 / MDD -3.6130 / gross 1.0 /
0 neg yrs. Gauntlet ok 7/7 fresh this session
(coord/verify_champion_r3_last_session17.json; fail-closed first on a coordinator
path typo - the gauntlet rejected a wrong sleeve path before anything ran).

# THE CELL
The brwt-zb axis is FULLY closed (#126/#127). The largest remaining legal second-tier
cell is diescrack L40/Z20 - measured 10.8293 pct book share at the A2 anchor - a SINGLE
sleeve with TWO acceptance-era frozen scalars (lookback L=40, gate Z=2.0, HUNT_BASIS2
delivered 7/8 gates; sibling L15/Z1.5 dominated: 2017 neg-yr -6.48 pct). A 2-D (L,Z)
sweep is a 25-cell mining surface and was REFUSED at seal time. Pre-committed 1-D slice
rule: sweep the trigger Z at frozen L=40, grid {1.5, 1.75, 2.0, 2.25, 2.5} =
acceptance-adjacent 1.5 + anchor 2.0 + midpoint 1.75 + equal-step extensions 2.25/2.5
(the ITER34 midpoints-plus-extension convention); Z below 1.5 excluded (outside the
family acceptance envelope, same treatment as ITER35 degenerate zb=0). Precommit sealed
946c617d868816e8 BEFORE any candidate. A1 pre-seal: re-typed generator (from the
CAMP_COST R6 refresh_sleeves diescrack_build, the committed bytes proven source) vs
saved sleeve maxdev 9.980081e-17, inner n=4615, saved sha16 c7d19f5bd0b2a603; disclosed:
the re-type keeps 59 vt-warmup leading rows the committed emission drops - all before
the frame start 2008-03-31. NEW fail-closed tooling: the four frozen pool functions
(fit_relw/apply_cap/project_wmax/build_book) are asserted AST-text-identical to
driver_iter34.py at run start.

# RESULT (driver_iter36.log)
- Anchors ALL EXACT (A2 identity 0.0 exactly / weights 8.327e-17 / bytes 9.996e-17 /
  rows 1809 / k_covered 11 / IS-SR 4.198632 / Wmax_sf 1.8115x; anchor cell weights
  6.450e-09 = the known SLSQP boundary-jitter class, book 8.494e-10, block share
  0.300000).
- Sweep 5/5 cells LIVE (regen-dev 0.034-0.092, real curves): Z=1.50 -> 4.189526,
  Z=1.75 -> 4.204030 (ADMITTED, the ONLY one), Z=2.00 -> 4.198632 (anchor),
  Z=2.25 -> 4.173041, Z=2.50 -> 4.175864. IS-MDD flat (-2.39..-2.61), Wmax_sf falls
  with Z (1.8630x -> 1.7073x), block share 0.3000 everywhere (cap pinned by brwt).
- REVEAL (Z=1.75, one per stop rule): FS SR 3.758736 = +0.007307 over 3.751429 - THIRD-
  STRONGEST REJECTED CANDIDATE ON RECORD (ITER31 +0.0366, ITER33 +0.0075, ITER36
  +0.007307, ITER30 +0.0026). ALL operator gates PASS (cagr 23.6420 / arith 21.3904 /
  gross 1.000000000 / MDD -3.6273 / 0 neg yrs / CFX4 0 / Wmax_sf 1.8366x / G8 0.0000)
  but G7 bins [-0.0012, +0.0117, -0.0036, -0.0060, +0.0080] = 2/5 positive => FAIL
  => REJECT per sealed stop rule. No second reveal; no other cell was admitted.
  Champion sha16 pre==post True.

# VERDICT AND READING
HONEST NEGATIVE (reveal fired and died on the OOS police), ITER17-law closure 11. The
incumbent Z=2.0 is NOT the IS-interior argmax of its own family (contrast DUR 32 and
brwt-zb 34/35): a real interior competitor exists at Z=1.75 (+0.0054 IS-SR). But the
OOS profile is structure noise, not alpha: the bin dSR magnitudes are TINY
(|dSR| <= 0.012) and window-inconsistent (2/5), while dsr_full is nominally +0.0073 -
the police binds on CONSISTENCY, not magnitude (same verdict family as ITER30, where a
nominally positive full-sample delta split 2/5 across windows). The acceptance-era
freeze Z=2.0 is OOS-VINDICATED against its own IS gradient - the second closure shape
(#125 C5ng-k class) on the diesel-crack family: loosing the gate to 1.75 buys IS-SR
that does not survive windows; tightening to 2.25/2.5 loses IS outright. The crack
sleeve joins gas as an energy-crisis-regime sleeve whose inherited scalar is
load-bearing.

# FRONTIER AFTER ITER36
THIRTEEN axes measured-closed (gear 21, weights 22, grid edges 23, census data
24/117b/27/28, 8c-era ledger 25, credit-at-cap 26, covariance-target 29, recipe 30,
cov-target-AT-CAP 31, signal-params DUR 32 / C5ng-k 33 / brwt-zb 34+35 / diescrack-Z 36).
Five signal-parameter closures on record across four shapes (interior-max 32 /
OOS-vindicated freeze 33+36 / monotone-from-freeze 34 / FULL interior-max 35).
Remaining second-tier cells: QAxasts tsmom189 (7.59 pct), dualmom band121 (5.72 pct),
brwt per-variant lb (refused mining surface). Remaining levers UNCHANGED: purchased
data or operator rule change - now with a THIRD priced G7 data point (+0.007307,
2/5 windows negative): the G7 price-tag curve is +0.0366 (31), +0.0075 (33),
+0.0073 (36), all police-killed, recommendation KEEP stands.

Landed: coord/ITER36_DIESCRACK_Z/ (FINDINGS_PRECOMMIT 946c617d868816e8 + driver_iter36.py
+ driver_iter36.log + FINDINGS + 5 arm weights CSVs + candidate_Z1.75_daily/_weights.csv
for-the-record), test_iter36_diescrack_z.py 6 pins (mutation-checked RED 3 failed ->
byte-exact restore 3fed7fe5b05a32b4 -> GREEN), this doc, STANDUP_LOG, memory 128.
SUITE 563 passed / 0 failed (557 + 6, own run, 70.84s).
