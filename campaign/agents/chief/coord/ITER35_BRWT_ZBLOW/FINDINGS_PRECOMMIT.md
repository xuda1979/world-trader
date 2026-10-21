# ITER35 FINDINGS PRECOMMIT - BRWT Z-THRESHOLD LOWER-ENVELOPE EXTENSION (SIGNAL-PARAMETER AXIS, LARGEST-WEIGHT SLEEVE FAMILY 30.00 PCT)

Sealed 2026-09-19 midday CST, session 16, BEFORE any candidate computation. The driver
hard-asserts this file sha16. Provenance: anchor A1 re-run BEFORE sealing (disclosed per
the 09-19 re-seal precedent): re-typed generator brwt_build(lb, zb=1.0, min_start) vs
saved sleeve bytes dev 9.9991e-17 (brwt10, inner n=6567), 9.9855e-17 (brwt7, n=4580),
9.9963e-17 (brwt5, n=4580), identical to the ITER34 pre-seal run one hour earlier (same
data vintages, same session).

# THESIS AND MOTIVATION (disclosed)
ITER34 (#126) swept the brwt family z-threshold zb over the acceptance envelope
{1.0, 1.25, 1.5, 1.75, 2.0}: IS-SR falls MONOTONICALLY from the anchor
(4.198632 -> 3.230354), 0/5 admitted. The monotone RIGHT side certifies the freeze
against zb-increases but says NOTHING about zb < 1.0 - the lower envelope is UNMEASURED
and was disclosed as outside the ITER34 grid at seal time. Two independent structural
facts point DOWN: (a) the costfix-era construction history already walked zb from 1.5
(rev15 config) down to 1.0 (champion config, with lb changes), i.e. the family's own
acceptance evolution moved toward MORE activity; (b) IS-ann RISES as zb falls (18.122
pct at the anchor vs 11.812 at zb=2.0 on the measured side), and under a max-Sharpe
objective more activity is not automatically worse. This cell measures the ONLY
remaining legal direction of the largest-weight family's one-scalar axis (30.0000 pct
of book weight, EXACTLY at the 0.30 brwt-block share cap).

# GRID (pre-committed)
zb in {0.25, 0.5, 0.75, 1.0} - the reflection of the ITER34 novel cells
{1.25, 1.5, 1.75, 2.0} about the anchor 1.0, EXCLUDING the degenerate reflected point
zb=0 (the always-in limit: pos = sign(-z) every day, no filter - a different strategy,
not a cell of this family). Deterministic rule: reflection minus degenerate endpoint;
anchor zb=1.0. SHARED across all three variants (one generator scalar; per-variant
grids remain a refused 125-cell mining surface). zb=1.0 regenerates ALL THREE streams.

# FROZEN (byte-verbatim - identical to ITER34)
Generator (re-typed into the driver from the CAMP_COST R6 refresh_sleeves documented
convention; anchor A1 proves the re-type): FRED brent/wti (dedup keep-last, sorted)
spliced with EIA brent/wti spot dailies strictly AFTER the FRED last index; sp =
log(BR) - log(WT) dropna; truncated at min_start (2000-01-01 brwt10, 2008-01-01 brwt7
and brwt5); mean/std rolling(lb, min_periods=lb), sd zero-replaced with NaN;
z = (sp - m) / sd; pos +1.0 where z < -zb, -1.0 where z > zb, else 0.0; T+1 gross =
pos * sp.diff().shift(-1); sleeve cost FULL |pos.diff()| * 6.4e-4; vol_target from
campaign.agents.B2_highfreq.gates; arms move TOGETHER.
Pool/fit/build (identical to ITER32/33/34): 12-slot pool B.PATHS byte-frozen; frame
from 2008-03-31; IS before 2017-01-01; fit_relw shrink 0.70 diagonal, SLSQP 3-start,
W_MAX 2.0 then capped bounds; apply_cap brwt-block share cap 0.30 pro-rata; CFX4 pinned
0; project_wmax water-filling at k_covered 11; build_book gear 1.0, BPS 6.4 FULL |dW|,
RATE 4.5 pct on max(gear-1, 0).

# COVERAGE LAW (asserted per cell)
Scalar zb changes values only, never the NaN pattern (z-NaN prefix set by lb, frozen;
dropna sites structural). Assert: dfc index equals the frozen frame index; fit rows ==
1809; k_covered == 11; CFX4 column untouched.

# ANCHORS (all must hold before any verdict; fail means STOP, no candidates)
A1 (done, pre-seal): all three arms dev below 1e-12 - PASSED at 9.9991e-17, 9.9855e-17,
9.9963e-17.
A2: projection identity on incumbent exactly 0.0; relw12 vs committed weights dev below
1e-12; book bytes vs champion dev below 1e-12; fit rows 1809; k_covered 11; incumbent
IS-SR 4.198632 within 5e-6; Wmax_sf at k=11 equals 1.8115x.
Anchor cell zb=1.0 in-sweep: weights dev vs committed below 1e-6; book dev vs champion
below 1e-9.

# ADMISSION (per cell)
Wmax_sf at most 2.0 plus 1e-9, AND IS-MDD at least -6 pct, AND 0 IS-negative years, AND
IS-SR above 4.198632 plus 1e-4 (jitter tolerance per the 2026-09-19 convention).

# SELECTION AND STOP RULE (sealed)
If no cell admitted: HONEST NEGATIVE, no reveal, no candidate CSV, done. Else ONE global
argmax over admitted cells ranked by (-is_sr, abs(zb-1.0), zb); ONE reveal. If the
reveal fails ANY gate: REJECT, no second reveal, no other cell revealed regardless of
its IS or FS numbers.

# REVEAL GATES (verbatim ITER32/33/34)
G1 cagr >= 20 pct or arith >= 20 pct; G2 gross <= 1.6; G3 FS MDD >= -7 pct; G4 zero FS
negative years; G5 CFX4 relw == 0; G6 Wmax_sf <= 2.0x at k=11; G7 OOS police: at least
4/5 positive bin dSR AND min bin dSR >= -0.10 AND FS-SR above 3.751429; G8 fit-window
shrink <= 2 pct. Bins 2017-18, 2019-20, 2021-22, 2023-24, 2025-26 vs the incumbent
book. All 8 must pass for ADOPTABLE; anything else is REJECT.

# DISCLOSED RISKS AND PRE-ANALYSIS
(a) Lower zb trades MORE mild-dislocation days: turnover and sleeve cost rise inside
the frozen generator; vol_target re-scales. All measured, not modeled.
(b) The 2021-22 energy-crisis regime is the known fragility bin (ITER33 G7 kill): at
lower zb the spread sleeve held MORE exposure through 2021-22 - if the incumbent freeze
is OOS-protective the same way zb=2.5 was for gas, G7 is the gate that catches it.
This is stated BEFORE the run as the primary risk, not after the fact.
(c) The brwt block sits EXACTLY at its 0.30 share cap; both directions of fit response
are bounded by the cap plus the water-filling repair, as in ITER34.
(d) zb = 0.25 is the densest cell (filter barely binds); it is the mirror of ITER34's
1.75, not a new minimum. The degenerate zb=0 is NOT on the grid.
(e) Candidate streams are regenerated from the CURRENT FRED+EIA bytes; A1 proved these
identical at 1e-16 to the sleeve-emission vintage on every row.
(f) The champion is untouched throughout: read-only sweep; champion and weights sha16
asserted equal pre and post.
