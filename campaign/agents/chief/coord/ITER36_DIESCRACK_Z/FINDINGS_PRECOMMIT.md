ITER36 FINDINGS PRECOMMIT - DIESCRACK GATE-Z AXIS AT FROZEN L=40 (SIGNAL-PARAMETER AXIS, LARGEST REMAINING SECOND-TIER CELL)

Sealed 2026-09-19 ~10:45 CST, session 17, BEFORE any candidate computation. The driver
hard-asserts this file sha16. Provenance: anchor A1 re-run BEFORE sealing (disclosed per
the 09-19 re-seal precedent): re-typed generator diescrack_build(gate=2.0) vs the
committed sleeve bytes maxdev 9.980081e-17 (inner n=4615 = the full saved stream
2008-03-28..2026-08-24; saved sha16 c7d19f5bd0b2a603; index identical on the saved span).
Disclosure: the re-typed stream retains 59 leading vol-target warmup rows
(2008-01-02..2008-03-27) that the committed emission drops; they precede the pool frame
start 2008-03-31 and cannot reach the fit; frame-window coverage is asserted per cell.

# THESIS AND MOTIVATION
The brwt-zb axis is FULLY closed (#126/#127: single-peaked interior-max EXACTLY at the
incumbent zb=1.0 at 30.00 pct book weight). The largest remaining legal second-tier cell
is diescrack L40/Z20 - 10.83 pct of book weight per the #126/#127 frontier table, a
SINGLE sleeve with TWO frozen scalars (lookback L=40, gate Z=2.0), acceptance-era
freezes from HUNT_BASIS2 (delivered 7/8 gates, scramble-gate degenerate as written; the
sibling L15/Z1.5 was dominated: 2017 neg-yr -6.48 pct breached the sleeve floor). The
book-level pool-fit IS-SR under the operator objective was never measured over either
scalar. A 2-D (L,Z) sweep is a 25-cell mining surface and is REFUSED. The pre-committed
1-D slice rule is: sweep the trigger Z at frozen L=40 - the same generator class as
brwt-zb (#126/#127) and C5ng-k (#125), and the scalar the HUNT_BASIS2 acceptance work
itself varied (delivered gates Z=2.0 at L40 and Z=1.5 at L15).

# GRID (pre-committed)
Z in {1.5, 1.75, 2.0, 2.25, 2.5}. Deterministic rule: acceptance-adjacent point 1.5 (the
family's second delivered gate), anchor 2.0, midpoint 1.75 of {1.5, 2.0}, equal-step
extensions 2.25/2.5 balancing both sides (the ITER34 midpoints-plus-extension
convention). Anchor Z=2.0 regenerates the committed stream. One sleeve, one scalar, five
cells - no per-variant ambiguity. L is NOT swept (disclosed refusal; L=40 is the
champion's own freeze). Z below 1.5 is NOT on the grid: the acceptance-era sibling at
Z=1.5 already breached the sleeve neg-yr floor, so looser gates start OUTSIDE the
family's acceptance envelope (same treatment as ITER35's degenerate zb=0 exclusion).

# FROZEN (byte-verbatim)
Generator re-typed from the CAMP_COST R6 refresh_sleeves diescrack_build (the committed
bytes' proven source; A1 proves the re-type): DJFUELUSGULF (tools/quant/data/newdata,
dedup keep-last sorted) x 42.0 gal/bbl vs wti_full (FRED harness) spliced with EIA
wti_spot_daily strictly AFTER the FRED last index; sp = log(diesel*42) - log(wti)
dropna, truncated at 2008-01-01; rolling(40, min_periods=40) mean/std, sd zero-replaced
NaN; z = (sp - m) / sd; pos +1.0 where z < -Z, -1.0 where z > Z, else 0.0; T+1 gross =
pos * sp.diff().shift(-1); sleeve cost FULL |pos.diff()| x 6.4e-4; borrow 0.005/252
charged where pos or lagged pos nonzero (frozen mask); vol scale
(0.08 / (expanding(60).std() * sqrt(252))) clip upper 3.0.
Pool/fit/build identical to ITER32/33/34/35: 12-slot pool B.PATHS byte-frozen; frame
from 2008-03-31; IS before 2017-01-01; fit_relw shrink 0.70 diagonal, SLSQP 3-start,
W_MAX 2.0 then capped bounds; apply_cap brwt-block share cap 0.30 pro-rata; CFX4 pinned
0; project_wmax water-filling at k_covered 11; build_book gear 1.0, BPS 6.4 FULL |dW|,
RATE 4.5 pct on max(gear-1, 0). The four frozen functions (fit_relw, apply_cap,
project_wmax, build_book) are asserted AST-text-identical to driver_iter34.py pre-run.

# COVERAGE LAW (asserted per cell)
Scalar Z changes values only, never the calendar (the stream index is the Z-invariant
spread-dropna index). Assert per cell: frame-window notna count of the diescrack column
unchanged; dfc index equals the frozen frame index; fit rows == 1809; k_covered == 11;
CFX4 column pinned 0.

# ANCHORS (all must hold before any verdict; fail means STOP, no candidates)
A1 (done, pre-seal): 9.980081e-17 - PASSED.
A2: projection identity on incumbent exactly 0.0; relw12 vs committed weights dev below
1e-12; book bytes vs champion dev below 1e-12; fit rows 1809; k_covered 11; incumbent
IS-SR 4.198632 within 5e-6; Wmax_sf at k=11 equals 1.8115x.
Anchor cell Z=2.0 in-sweep: weights dev vs committed below 1e-6; book dev vs champion
below 1e-9.

# ADMISSION (per cell)
Wmax_sf at most 2.0 plus 1e-9, AND IS-MDD at least -6 pct, AND 0 IS-negative years, AND
IS-SR above 4.198632 plus 1e-4 (jitter tolerance per the 2026-09-19 convention).

# SELECTION AND STOP RULE (sealed)
If no cell admitted: HONEST NEGATIVE, no reveal, no candidate CSV, done. Else ONE global
argmax over admitted cells ranked by (-is_sr, abs(Z - 2.0), Z); ONE reveal. If the
reveal fails ANY gate: REJECT, no second reveal, no other cell revealed regardless of
its IS or FS numbers.

# REVEAL GATES (verbatim ITER32/33/34/35)
G1 cagr >= 20 pct or arith >= 20 pct; G2 gross <= 1.6; G3 FS MDD >= -7 pct; G4 zero FS
negative years; G5 CFX4 relw == 0; G6 Wmax_sf <= 2.0x at k=11; G7 OOS police: at least
4/5 positive bin dSR AND min bin dSR >= -0.10 AND FS-SR above 3.751429; G8 fit-window
shrink <= 2 pct. Bins 2017-18, 2019-20, 2021-22, 2023-24, 2025-26 vs the incumbent
book. All 8 must pass for ADOPTABLE; anything else is REJECT.

# DISCLOSED RISKS AND PRE-ANALYSIS
(a) Looser gates trade more dislocation days; the L15/Z1.5 sibling failed the SLEEVE
neg-yr floor in 2017 - 2017 is inside the IS window, so the IS filters are the natural
catch.
(b) The 2021-22 energy-crisis regime is the known G7 fragility bin for crack exposure
(ITER33 gas analog: the inherited freeze was OOS-PROTECTIVE against its own IS
gradient). If IS wants Z other than 2.0, G7 arbitrates. Stated BEFORE the run as the
primary risk, not after the fact.
(c) The sleeve is a FRED spot PROXY for the HO-CL calendar spread (roll/basis risk
disclosed at acceptance); the convention is frozen and Z-invariant across cells.
(d) The 2020-04-20 negative WTI print log()-gap bridge is frozen in the generator and
Z-invariant.
(e) Candidate streams are regenerated from CURRENT newdata/FRED/EIA bytes; A1 pins the
vintage at 1e-16 against the sleeve-emission bytes.
(f) The champion is untouched throughout: read-only sweep; champion and weights sha16
asserted equal pre and post.
