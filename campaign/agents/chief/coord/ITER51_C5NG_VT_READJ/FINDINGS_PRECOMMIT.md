# ITER51 FINDINGS_PRECOMMIT - C5NG FAMILY VOL-TARGET (vt_ann) STALENESS RE-ADJUDICATION
# Sealed 2026-09-20 session 31, BEFORE any candidate computation. sha16 asserted by driver_iter51.py at run start.
#
# OPERATOR OBJECTIVE (verbatim, unchanged, 6th resend)
# "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be smaller than 20%."
#
# VERIFY-FIRST STATE (this session, before sealing)
# - Canonical gauntlet ok=true 7/7 fresh (coord/verify_champion_r3_last_session31.json):
#   weights_repro 7.633e-17 / byte_repro 1.041e-16 / half-turn rejected 1.644e-5 / gross exact
#   1.0000000000006 n_over 0 / 0 negy / MDD -3.7339 / SR 3.8203573009568794 / cagr 23.92147218901779.
# - Triple shas re-hashed fresh: champion cfa9ec4d38158691 / weights a384d6b92e258fd5 /
#   A5r2 vt024 7ec85336e7f7d00f / QAxasts vt015 c40d008ddbf7c579.
# - C5ng committed vintages re-hashed: C5ng 3d2b80691ef7a448 / C5ngsum ccfe3a4bc8706161 (Sep-07 vintages, untouched).
# - Baseline suite 648 passed / 0 failed (own run 66.38s, python3 -m pytest from repo root).
# - Coord quiet (latest writes = session-30 landing 00:39; STANDUP tail = session-30 entry;
#   RAWEW15_REFRESH pair = known cron-twin deterministic refresh artifact, disclosed #133/#134,
#   champion re-hashed after it). No concurrent writer.
# - BAR exact digits source: coord/ITER50_SHRINK_READJ/driver_iter50.log A2 line
#   "IS-SR=4.218504 (bar 4.218504)" - the incumbent's committed-frame IS-SR.
#
# THE CELL (27th measured axis)
# C5ng family harness vol_target (vt_ann), STALENESS RE-ADJUDICATION at the CURRENT champion.
# C5ng 17.94 pct + C5ngsum 14.91 pct = 32.86 pct of committed book weight - the LARGEST family.
#
# MOTIVATION CLASS (the legality core, recorded AT SEAL)
# 1. Class provenance: #141 (ITER50) recorded the STALENESS RE-ADJUDICATION class - a family
#    whose scale/solver certificate predates an ADOPTED non-uniform rescale is re-adjudicated at
#    the new frame, ONE re-adjudication per family per generation, scoped. ITER50 consumed the
#    solver family's cell (re-closed this generation). This seal consumes the C5ng family's.
# 2. The generation: ITER49's adoption (rescale-2: QAxasts 7.9566 -> 5.5133 pct, the largest
#    adopted move on record; the refit moved C5ng 17.26 -> 17.94 and C5ngsum 14.35 -> 14.91,
#    family share 31.61 -> 32.86 pct) postdates ITER48's certificate. Under the #48 law (diag
#    shrink re-prices hedging under ANY non-uniform rescale) the ITER48 interior-peak certificate
#    is exactly one generation stale. Same motivation shape as ITER50, applied to the largest
#    family.
# 3. Binding reconciliation: ITER48's ANTI-DOG-CHASE text ("NO second seal on this family")
#    binds EDGE-CONTINUATION ("a rising IS edge is recorded, NOT chased" - its own words). The
#    ITER47 binding states the escape form verbatim: "Any further movement on this family
#    requires a NEW motivation class recorded in the ledger, not an edge continuation." The
#    staleness class IS the ledger-recorded new motivation class (#141). NO edge continuation is
#    involved: the grid below is the SAME 5 points verbatim; a rising IS edge at 0.15 is
#    RECORDED and NOT chased (re-binding below).
# 4. Closure shape honesty: ITER48 closed NO-ADMISSION (interior peak) - there is NO OOS police
#    verdict being re-litigated (police kills are OOS evidence about the candidate and are NEVER
#    re-run). The only question here is whether the interior peak MOVED with the covariance -
#    exactly the question ITER50 asked of the solver, where the answer was NO (ranking
#    covariance-robust).
#
# RESULT-AWARE MOTIVATION DISCLOSED (per the #139 precedent)
# Adoption EV is honestly LOW. ITER50's mechanism read: the in-admissible-set ranking is
# covariance-robust (FOURTH plateau confirmation); ITER48's own reading: on-frame pure-scale
# means the fit largely undoes a 1/c share rescale, the live channels being second-order
# (diag-shrink mismatch, wall-shadow, nav-drift). The seal's content is the FRONTIER AIRTIGHTNESS
# of the largest-weight family's scale certificate and a candidate FIFTH plateau confirmation.
# If any arm IS-admits, the ONE reveal goes to the G7 police - no self-adoption exists.
#
# GRID (deterministic, zero free choice, VERBATIM ITER48 mirror of the sealed ITER43 grid)
# ARMS = (0.10 anchor, 0.06, 0.09, 0.12, 0.15). Anchor = committed cell, ineligible by
# construction. NO upper-edge points (edge-extension class is BOUND by the re-binding below).
# One shared harness scalar across BOTH variants (per-variant vt = mining surface, REFUSED).
#
# A1 + CLIP PRE-SEAL PROBES (run BEFORE this seal; anchor_a1_probe.log in this directory)
# - A1a regen-vt010-vs-committed C5ng ok=True maxdev=9.975e-17 inner=7381 committed_nonnan=7381 FULL.
# - A1b regen-vt010-vs-committed C5ngsum ok=True maxdev=9.996e-17 inner=7381 committed_nonnan=7381 FULL.
# - CLIP-REGIME PROBE at the CURRENT data vintage, all 5 arms x both variants:
#   scale=(vt/rcum).clip(upper=3.0), rcum = expanding(60) ann vol of the PRE-SCALE stream
#   (vt-invariant). On-frame (>= 2008-03-31) rcum_min = 52.3014 pct (C5ng) / 31.8819 pct
#   (C5ngsum) - the largest bound at any arm is vt/3 = 0.05. bound_frac_onframe = 0.000000 at
#   EVERY arm for BOTH variants. ON-FRAME PURE-SCALE at every grid point, re-confirmed.
#   (ITER48 disclosed pre-scale rcum 44.5-85.6 pct incl. pre-frame history; the on-frame mins
#   at this vintage are the two values above - same conclusion, disclosed per the
#   evidence-preservation rule.)
#
# ADMISSION (IS level, all required, pre-registered)
# - Frame: committed 12-pool via rawew13v2_build (B.PATHS live = A5r2 vt024 + QAxasts vt015),
#   rows 1809, k_covered 11.
# - BAR = 4.218504 (committed champion IS-SR, exact digits from the ITER50 A2 line, above).
# - Candidate admitted iff: is_sr > BAR + 1e-4 (the 47-class STRICTER margin form) AND
#   is_mdd >= -0.06 AND 0 IS negative years AND Wmax_sf <= 2.0 + 1e-9.
# - A2 committed-frame continuity vs the LIVE pair: projid == 0.0, weights maxdev < 1e-12,
#   book bytes maxdev < 1e-12, IS-SR == BAR within 5e-6 - fail-closed.
# - A2b regen-vs-committed fit-landing jitter LOGGED and disclosed; the 1e-4 margin must exceed
#   it by orders of magnitude or the arm is denied.
#
# STOP RULE (frozen)
# ONE global IS-argmax reveal among admitted arms by IS-SR (tie-break: smaller L1 distance to
# the anchor cell, then lexicographic). If NO arm admits or argmax <= BAR + 1e-4: NO REVEAL,
# KEPT=[], honest negative, no candidate CSV beyond the for-the-record arm files.
#
# REVEAL GATES (all 8 required, verbatim D18-correct lineage)
# G1 cagr >= 20 pct OR arith >= 20 pct (percent form); G2 grossmax <= 1.6 (operator cap, builder
# gear 1.0); G3 FS MDD >= -7 pct; G4 0 FS negative years; G5 CFX4 == 0; G6 Wmax_sf <= 2.0x
# (k_covered = 11); G7 OOS police: >= 4/5 positive bin dSR (edges 2017/2019/2021/2023/2025) AND
# min bin >= -0.10 AND FS SR > 3.820357 (the incumbent); G8 fit-window shrink <= 2 pct.
# ADOPTABLE 8/8 => full Amendment-2 battery in-session BEFORE any adoption (canonicalize to
# bt/verify_champion.py's own algebra, independent gauntlet 7/7 on the canonical pair, coherence
# halves, r3 cmd + builder PATHS update, re-pin wave, 6 mutation-checked pins). ANY fail =>
# REJECT, record, STOP - no second reveal.
#
# D19 INHERITED-LITERAL GUARD (the #136/#140 class)
# The reveal log line's incumbent label MUST FORMAT FS_BAR (3.820357), not inherit a template
# string literal. The substitution list asserts this line explicitly.
#
# COVERAGE LAW / FROZEN BLOCKS
# - Per-arm asserts: rows == 1809, k == 11 (same-12-names class - the #137 new-member trap does
#   NOT apply), fail-closed.
# - fit_relw / apply_cap / project_wmax / build_book asserted AST-text-identical to
#   driver_iter41.py AND driver_iter36.py at run start.
# - Driver = driver_iter48.py with asserted-exactly-once substitutions (OUT dir, PRECOMMIT_SHA,
#   BAR, FS_BAR, header line, D19 reveal label + its arg list, log filename x2); py_compile gate
#   before the run. ~90 pct of the file byte-identical to the lineage.
# - Champion sha16 pre==post asserted by the driver (the driver must not touch the live pair).
#
# ANTI-DOG-CHASE RE-BINDING (pre-committed)
# This re-adjudication RE-SEALS the C5ng family at the CURRENT frame. REGARDLESS of outcome:
# no further C5ng measurement this generation; a rising IS edge at 0.15 is RECORDED, NOT
# chased; any further movement requires a NEW motivation class recorded in the ledger.
#
# REFUSED ALTERNATIVES (recorded at seal, before results)
# - A5r2-vt third seal: its curve was RISING at 0.24 - a staleness re-adj there is
#   indistinguishable from the edge continuation its own binding refuses. REFUSED (harder case
#   than this cell, whose certificate was interior).
# - tsmom-vt re-adjudication: tsmom IS the adopter of rescale-2; re-measuring its own grid at
#   its own adoption = chasing the adoption itself. REFUSED.
# - tsmom-MAW / DUR / C5ng-k / brwt-zb staleness cells: same class, strictly smaller materiality
#   (broad plateaus / small shares); one cell per session; C5ng is the largest and the only
#   family whose share GREW under the rescale refit.
# - Re-running police-killed cells at the new incumbent: re-litigating OOS evidence. REFUSED.
# - Solver / estimator internals: re-closed THIS generation (ITER50 single-re-adjudication
#   scope). Wmax relaxation (+0.024 IS-SR behind the wall), G7 relaxation (price-tag curve,
#   recommendation KEEP), purchased data: operator levers, unchanged, not cells.
