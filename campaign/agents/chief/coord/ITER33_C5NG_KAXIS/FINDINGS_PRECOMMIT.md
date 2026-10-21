# ITER33 FINDINGS PRECOMMIT - C5NG CALM-FILTER SCALAR k (SIGNAL-PARAMETER AXIS, LARGEST-WEIGHT SLEEVE FAMILY)

Sealed 2026-09-19 morning CST, session 15, BEFORE any candidate computation. The driver
hard-asserts this file sha16. Provenance: anchor A1 was re-run BEFORE sealing (disclosed
per the 09-19 re-seal precedent): re-typed generator run(summer, k=2.5) vs saved sleeve
bytes dev 9.9747e-17 (C5ng) and 9.9963e-17 (C5ngsum), n=7381 both, tails 2026-08-24 both
- re-type faithful, DHHNGSP input byte-equivalent to the sleeve-emission vintage on every
row, so the Sep-8 data-file mtime is proven content-irrelevant on this axis.

# THESIS
ITER32 (#124) closed the signal-parameter axis for the a6r7 stream (8.0 pct committed
weight): incumbent DUR=1.9 is the interior IS-argmax of its own family. The LARGEST
committed exposure is the C5ng family: C5ng 16.47 pct + C5ngsum 13.69 pct = 30.16 pct of
book weight, both emitted by ONE generator with ONE frozen scalar k=2.5 (calm filter:
position zeroed when the absolute log-return exceeds k times the trailing-90d sigma
shift(1)), inherited frozen from the C5_newdata acceptance era. The acceptance-era report
printed a STANDALONE sleeve-SR k-plateau on the 1998+ eval window under the acceptance
objective; the BOOK-LEVEL pool-fit IS-SR under the current operator objective (Sharpe-max
s.t. ann >= 20 pct, gross <= 1.6) has NEVER been measured over k. This cell closes the
signal-parameter axis for the largest-weight sleeve family.

# GRID (pre-committed)
k in {1.5, 2.0, 2.5, 3.0, 3.5} - the same 5-point grid the acceptance-era plateau printed
(continuity), anchor k=2.5. SHARED across both variants: the generator has one k and the
incumbent state has 2.5 for both; independent per-variant grids would be a 25-cell mining
surface, not the one-scalar family axis. k=2.5 regenerates BOTH streams.

# FROZEN (byte-verbatim)
Generator: DHHNGSP close-to-close log return; weekday map Wed/Thu short -1, Fri long +1
(dayofweek 2/3/4); summer variant months Apr-Oct; calm threshold thr = rolling(90) std
shift(1) times k, mask to 0.0; T+1 execution gr = pos times lr.shift(-1); sleeve cost
6e-4 per unit absolute position change; vol_target(vt_ann=0.10, min_days=60, cap 3.0)
expanding - imported from campaign.agents.B2_highfreq.gates (same code object; the
generator run() itself is RE-TYPED into the driver because importing
e1_idea1_ng_detrunc.py would execute its module-level save_sleeve side effects and
rewrite live sleeve bytes; anchor A1 proves the re-type).
Pool/fit/build (identical to ITER32): 12-slot pool B.PATHS byte-frozen; frame from
2008-03-31; IS before 2017-01-01; fit_relw shrink 0.70 diagonal, SLSQP 3-start, W_MAX 2.0
then capped bounds; apply_cap brwt-block (brwt10/7/5) share cap 0.30 pro-rata; CFX4
pinned 0; project_wmax water-filling at k_covered 11 (scale-free Wmax invariant, the
2026-09-19 convention); build_book gear 1.0, BPS 6.4 FULL absolute-dW, RATE 4.5 pct on
max(gear-1, 0).

# COVERAGE LAW (asserted per cell)
Scalar k changes values only, never the NaN pattern (mask writes 0.0 in place; dropna
sites structural). Assert: dfc index equals the frozen frame index; fit rows == 1809;
k_covered == 11; CFX4 column untouched.

# ANCHORS (all must hold before any verdict; fail means STOP, no candidates)
A1 (done, pre-seal): both arms dev below 1e-12 - PASSED at 9.97e-17 and 1.00e-16.
A2: projection identity on incumbent exactly 0.0; relw12 vs committed weights dev below
1e-12 (expected 8.3e-17); book bytes vs champion dev below 1e-12 (expected 9.996e-17);
fit rows 1809; k_covered 11; incumbent IS-SR 4.198632 within 5e-6; Wmax_sf at k=11
equals 1.8115x.
Anchor cell k=2.5 in-sweep: weights dev vs committed below 1e-6 (SLSQP boundary jitter
around 5.5e-9, disclosed in the ITER30 repair, tolerated); book dev vs champion below
1e-9.

# ADMISSION (per cell)
Wmax_sf at most 2.0 plus 1e-9, AND IS-MDD at least -6 pct, AND 0 IS-negative years, AND
IS-SR above 4.198632 plus 1e-4 (jitter tolerance per the 2026-09-19 convention).

# SELECTION AND STOP RULE (sealed)
If no cell admitted: HONEST NEGATIVE, no reveal, no candidate CSV, done. Else ONE global
argmax over admitted cells ranked by (-is_sr, abs(k-2.5), k); ONE reveal. If the reveal
fails ANY gate: REJECT, no second reveal, no other cell revealed regardless of its IS or
FS numbers.

# REVEAL GATES (verbatim ITER32)
G1 cagr >= 20 pct or arith >= 20 pct; G2 gross <= 1.6; G3 FS MDD >= -7 pct; G4 zero FS
negative years; G5 CFX4 relw == 0; G6 Wmax_sf <= 2.0x at k=11; G7 OOS police: at least
4/5 positive bin dSR AND min bin dSR >= -0.10 AND FS-SR above 3.751429; G8 fit-window
shrink <= 2 pct. Bins 2017-18, 2019-20, 2021-22, 2023-24, 2025-26 vs the incumbent book.
All 8 must pass for ADOPTABLE; anything else is REJECT.

# DISCLOSED RISKS AND PRE-ANALYSIS
(a) Smaller k zeroes more days: the filter binds more; sleeve vol_target re-scales the
survivors; both effects live INSIDE the frozen generator and are measured, not modeled.
(b) The k-to-infinity limit (no filter) is NOT on the grid: the grid is the finite
pre-committed family, not a limit study.
(c) k moves 2 of the 11 covered names; if small-k gas sleeves improve, the fit may
re-concentrate into gas - G6 plus the ITER26 water-filling repair bound it.
(d) Candidate streams are regenerated from the CURRENT DHHNGSP bytes; A1 proved these
identical at 1e-16 to the sleeve-emission vintage on all 7381 rows, so no vintage drift
is possible on this axis.
(e) The champion is untouched throughout: read-only sweep; champion and weights sha16
asserted equal pre and post.
