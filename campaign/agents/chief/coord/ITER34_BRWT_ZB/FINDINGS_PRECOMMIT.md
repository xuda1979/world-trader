# ITER34 FINDINGS PRECOMMIT - BRWT Z-THRESHOLD SCALAR zb (SIGNAL-PARAMETER AXIS, LARGEST-WEIGHT SLEEVE FAMILY 31.08 PCT)

Sealed 2026-09-19 morning CST, session 16, BEFORE any candidate computation. The driver
hard-asserts this file sha16. Provenance: anchor A1 was re-run BEFORE sealing (disclosed
per the 09-19 re-seal precedent): re-typed generator brwt_build(lb, zb=1.0, min_start) vs
saved sleeve bytes dev 9.9991e-17 (brwt10, inner n=6567), 9.9855e-17 (brwt7, n=4580),
9.9963e-17 (brwt5, n=4580); saved tails 2026-08-28 all three (champion-frame horizon);
regen tails 2026-09-01 (EIA splice) reindexed down to the frozen frame - re-type faithful,
FRED brent/wti + EIA spot-daily splices byte-equivalent to the sleeve-emission vintage on
every row. This also proves the Sep-17 re-emission of brwt10_2000/brwt7 costfix bytes
(mtime 2026-09-17 10:54, smaller files) is content-identical on the whole builder frame.

# THESIS
ITER33 (#125) closed the signal-parameter axis for the C5ng family (30.16 pct committed
weight; incumbent k=2.5 freeze OOS-vindicated, G7 kill). The LARGEST committed exposure
is NOW the brwt family: brwt10 9.9772 pct + brwt7 9.1924 pct + brwt5 10.8304 pct =
30.0000 pct of book weight - sitting EXACTLY at the 0.30 brwt-block relw-share cap (the
fit wants more; the cap binds). All three emitted by ONE generator (Brent-WTI log-spread
z mean-reversion; FULL |dW| 6.4bps; vol_target) with ONE frozen scalar zb=1.0 (z entry
threshold) shared by all three variants (lb in 10/7/5 and min_start 2000/2008 are variant
identity, not family scalars), inherited frozen from the CAMP_COST R3 candidate era. The
acceptance-era report (E1 idea3) printed a STANDALONE sleeve-SR plateau over bz in
{1.0, 1.5, 2.0} (on the older rev15 config: lb 15, half-turn 6e-4, 2001+ standalone
objective); the BOOK-LEVEL pool-fit IS-SR under the current operator objective
(Sharpe-max s.t. ann >= 20 pct, gross <= 1.6) has NEVER been measured over zb. This cell
closes the signal-parameter axis for the largest-weight sleeve family.

# GRID (pre-committed)
zb in {1.0, 1.25, 1.5, 1.75, 2.0} - the acceptance-print bz points {1.0, 1.5, 2.0} plus
their midpoints (deterministic rule: acceptance points plus midpoints, symmetric around
the anchor; no point outside the printed envelope [1.0, 2.0]); anchor zb=1.0. SHARED
across all three variants: the generator has one zb and the incumbent state has 1.0 for
all three; independent per-variant grids would be a 125-cell mining surface, not the
one-scalar family axis (ITER33 convention). zb=1.0 regenerates ALL THREE streams.

# FROZEN (byte-verbatim)
Generator (re-typed into the driver from the CAMP_COST R6 refresh_sleeves documented
convention - importing is avoided because the sweep must not execute any emitter; anchor
A1 proves the re-type): FRED brent/wti (tools/quant/hedge_fund_strats/data_fred,
dedup keep-last, sorted) spliced with EIA brent/wti spot dailies
(tools/quant/data/eia_weekly) strictly AFTER the FRED last index; sp = log(BR) - log(WT)
dropna; truncated at min_start (2000-01-01 brwt10, 2008-01-01 brwt7 and brwt5); mean/std
rolling(lb, min_periods=lb), sd zero-replaced with NaN; z = (sp - m) / sd; pos +1.0 where
z < -zb, -1.0 where z > zb, else 0.0; T+1 gross = pos * sp.diff().shift(-1); sleeve cost
FULL |pos.diff()| * 6.4e-4; vol_target from campaign.agents.B2_highfreq.gates (same code
object as every committed emitter); arms move TOGETHER (one shared scalar).
Pool/fit/build (identical to ITER32/33): 12-slot pool B.PATHS byte-frozen; frame from
2008-03-31; IS before 2017-01-01; fit_relw shrink 0.70 diagonal, SLSQP 3-start, W_MAX 2.0
then capped bounds; apply_cap brwt-block (brwt10/7/5) share cap 0.30 pro-rata; CFX4
pinned 0; project_wmax water-filling at k_covered 11 (scale-free Wmax invariant);
build_book gear 1.0, BPS 6.4 FULL |dW|, RATE 4.5 pct on max(gear-1, 0).

# COVERAGE LAW (asserted per cell)
Scalar zb changes values only, never the NaN pattern (z-NaN prefix is set by lb, frozen;
pos stays 0.0 on NaN z; dropna sites structural). Assert: dfc index equals the frozen
frame index; fit rows == 1809; k_covered == 11; CFX4 column untouched.

# ANCHORS (all must hold before any verdict; fail means STOP, no candidates)
A1 (done, pre-seal): all three arms dev below 1e-12 - PASSED at 9.9991e-17, 9.9855e-17,
9.9963e-17.
A2: projection identity on incumbent exactly 0.0; relw12 vs committed weights dev below
1e-12 (expected 8.3e-17); book bytes vs champion dev below 1e-12 (expected 1.032e-16);
fit rows 1809; k_covered 11; incumbent IS-SR 4.198632 within 5e-6; Wmax_sf at k=11
equals 1.8115x.
Anchor cell zb=1.0 in-sweep: weights dev vs committed below 1e-6 (SLSQP boundary jitter
class, tolerated per ITER30 repair); book dev vs champion below 1e-9.

# ADMISSION (per cell)
Wmax_sf at most 2.0 plus 1e-9, AND IS-MDD at least -6 pct, AND 0 IS-negative years, AND
IS-SR above 4.198632 plus 1e-4 (jitter tolerance per the 2026-09-19 convention).

# SELECTION AND STOP RULE (sealed)
If no cell admitted: HONEST NEGATIVE, no reveal, no candidate CSV, done. Else ONE global
argmax over admitted cells ranked by (-is_sr, abs(zb-1.0), zb); ONE reveal. If the reveal
fails ANY gate: REJECT, no second reveal, no other cell revealed regardless of its IS or
FS numbers.

# REVEAL GATES (verbatim ITER32/33)
G1 cagr >= 20 pct or arith >= 20 pct; G2 gross <= 1.6; G3 FS MDD >= -7 pct; G4 zero FS
negative years; G5 CFX4 relw == 0; G6 Wmax_sf <= 2.0x at k=11; G7 OOS police: at least
4/5 positive bin dSR AND min bin dSR >= -0.10 AND FS-SR above 3.751429; G8 fit-window
shrink <= 2 pct. Bins 2017-18, 2019-20, 2021-22, 2023-24, 2025-26 vs the incumbent book.
All 8 must pass for ADOPTABLE; anything else is REJECT.

# DISCLOSED RISKS AND PRE-ANALYSIS
(a) Larger zb enters fewer states: the sleeve runs sparser and vol_target re-scales the
survivors; both effects live INSIDE the frozen generator and are measured, not modeled.
(b) The brwt block sits EXACTLY at its 0.30 share cap. A candidate fit wanting MORE block
mass is bounded by the cap plus the ITER26 water-filling repair; a fit wanting LESS frees
mass to non-block names under the Wmax_sf invariant. Either direction is measured.
(c) zb moves 3 of the 11 covered names SIMULTANEOUSLY and they are +0.62..+0.84 mutually
correlated (one Brent-WTI bet expressed three times): the IS response is effectively
one-dimensional, which is the point of a family axis, but it also means a bad zb is
triply bad - G3/G4/G7 bound the damage.
(d) The zb -> 0 limit (always-in) and zb > 2 are NOT on the grid: the grid is the finite
pre-committed family inside the acceptance envelope, not a limit study.
(e) Candidate streams are regenerated from the CURRENT FRED+EIA bytes; A1 proved these
identical at 1e-16 to the sleeve-emission vintage on every row, so no vintage drift is
possible on this axis.
(f) The champion is untouched throughout: read-only sweep; champion and weights sha16
asserted equal pre and post.
