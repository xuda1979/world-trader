> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
# GOAL100 ITER34 - BRWT Z-THRESHOLD FAMILY SCALAR zb (SIGNAL-PARAMETER AXIS, LARGEST-WEIGHT SLEEVE FAMILY 30.00 PCT) - HONEST NEGATIVE (2026-09-19, session 16)

Operator objective (unchanged verbatim): keep improving; leverage <= 1.6; maximize
Sharpe; annual return >= 20 pct. Champion of record UNCHANGED:
GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 8559fa55ee9a3417 / weights
d2d11c92a98683df / ann 23.6054 pct / SR 3.751429 / MDD -3.6130 / gross 1.0 /
0 neg yrs. Gauntlet ok 7/7 fresh pre-run this session
(coord/verify_champion_r3_last_session16.json: weights 8.327e-17 / bytes 1.032e-16 /
gross 1.0000000 / SR 3.751428690 / cagr 23.6054).

# THE CELL
ITER33 closed the signal-parameter axis for the C5ng family (k=2.5, 30.16 pct book
weight, freeze OOS-vindicated). The LARGEST committed exposure is NOW the brwt FAMILY:
brwt10 9.9772 pct + brwt7 9.1924 pct + brwt5 10.8304 pct = 30.0000 pct of book weight,
sitting EXACTLY at the 0.30 brwt-block relw-share cap (the fit wants more; the cap
binds). All three are emitted by ONE generator (Brent-WTI log-spread rolling-z
mean-reversion; long when z < -zb, short when z > zb; FULL |dW| 6.4bps sleeve cost;
vol_target; lb in 10/7/5 and min_start 2000/2008 are variant identity) with ONE frozen
scalar zb=1.0 shared by all three variants, inherited frozen from the CAMP_COST R3
candidate era. The acceptance-era report (E1 idea3) printed a STANDALONE sleeve-SR
plateau over bz in {1.0, 1.5, 2.0} on the older rev15 config; the BOOK-LEVEL pool-fit
IS-SR under the current operator objective was never measured over zb. Grid zb in
{1.0, 1.25, 1.5, 1.75, 2.0} = the acceptance-print points plus their midpoints,
deterministic, SHARED across all three variants (one generator scalar; per-variant grids
would be a 125-cell mining surface). Precommit sealed b9b9539c7dbe41ef BEFORE any
candidate (driver hard-asserts the sha); A1 anchor re-run pre-seal and disclosed inside
per the 09-19 re-seal precedent. Generator RE-TYPED into the driver from the CAMP_COST
R6 refresh_sleeves documented convention (importing emitters is refused); A1 proves the
re-type - and the same anchors prove the Sep-17 re-emission of the brwt costfix bytes
(mtime 2026-09-17 10:54, smaller files) content-identical on the whole builder frame
(saved tails 2026-08-28 all three).

# RESULT (driver_iter34.log)
- Anchors ALL EXACT: A1 regen-vs-saved 9.999e-17 (brwt10, n=6567) / 9.986e-17 (brwt7,
  n=4580) / 9.996e-17 (brwt5, n=4580). A2 projection identity 0.0 exact / weights
  8.327e-17 / bytes 9.996e-17 (n=4806) / fit rows 1809 / k_covered 11 / incumbent IS-SR
  4.198632 / Wmax_sf 1.8115x. Anchor cell zb=1.0: weights dev 8.903e-09 / book dev
  4.044e-10 / block share 0.300000 exact.
- ADMITTED 0/5: IS-SR FALLS MONOTONICALLY from the anchor: 4.198632 (zb=1.0 = the bar)
  -> 4.060778 (1.25) -> 3.884666 (1.5) -> 3.477293 (1.75) -> 3.230354 (2.0); IS-ann
  18.122 -> 11.812 pct. Cells LIVE (regen-dev 0.129-0.187: the scalar moves real
  signal; the decline is a curve, not jitter).
- NO reveal per the sealed stop rule (bar = incumbent IS-SR + 1e-4; nothing admitted).
  No candidate CSV exists. Wmax_sf rises toward the 2.0x wall as zb rises (1.9867x at
  zb=2.0) while block share falls to 0.2819 - sparser z-entries concentrate the book
  elsewhere; a second structural reason the fit never wants higher zb.
- Champion sha16 pre==post True. ITER17-law closure 9 by monotone dominance.

# READINGS
1. THIRD closure shape in the signal-parameter class: DUR interior-max (ITER32), k
   OOS-vindicated freeze (ITER33), zb monotone-from-freeze (ITER34). Here IS itself
   certifies the freeze - every interior cell strictly worse by 0.14 to 0.97 IS-SR;
   no police needed. Strongest negative type; the acceptance-era freeze is load-bearing
   in the direction IS cares about.
2. zb < 1.0 (lower envelope) is UNMEASURED - disclosed pre-seal as outside the
   acceptance envelope. The costfix-era history already walked zb DOWN 1.5 -> 1.0 (with
   lb changes). A lower-envelope extension is the only remaining legal direction on
   this axis; EV bounded by, but not zero from, the monotone right side. Next-seal
   decision, not this one.
3. The brwt trio is one bet expressed three times (block share pinned at the 0.30 cap
   in every cell); sweeping the ONE shared scalar was the correct family granularity.
   Per-variant lb grids remain refused (125-cell mining surface).

# FRONTIER AFTER ITER34
TWELVE axes measured-closed: gear (21), weights (22), grid edges (23), census data
(24/117b/27/28), 8c-era ledger (25), credit-at-cap (26), covariance-target (29),
covariance-target-AT-CAP (31), recipe (30), signal-parameter DUR (32), signal-parameter
C5ng-k (33), signal-parameter brwt-zb (34). Remaining second-tier cells: diescrack
L40/Z20 (10.83 pct, two-scalar single sleeve), QAxasts tsmom189 (7.59 pct), dualmom
band121 (5.72 pct), brwt per-variant lb (refused, mining surface), brwt zb<1.0 lower
envelope (only unmeasured direction, disclosed). Three signal-parameter closures
(interior-max / OOS-vindicated freeze / monotone-from-freeze) progressively confirm the
acceptance-era freezes are load-bearing. Remaining levers UNCHANGED: purchased data or
operator rule change (G7 price tag +0.0366 stands; ITER33 +0.0075 second priced point).

Landed: coord/ITER34_BRWT_ZB/ (FINDINGS_PRECOMMIT b9b9539c7dbe41ef + anchor_iter34.py +
driver_iter34.py + driver_iter34.log + FINDINGS + 5 arm weights CSVs for-the-record),
test_iter34_brwt_zb.py 6 pins (mutation-checked RED -> byte-exact restore sha
b37ea2fa6df5bacf -> GREEN), this doc, STANDUP_LOG, memory 126.
SUITE 551 passed / 0 failed (545 + 6, own run, 67.56s).
