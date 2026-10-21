# ITER52 FINDINGS_PRECOMMIT - TSMOM (QAxasts) MAW SCALAR STALENESS RE-ADJUDICATION
# Sealed 2026-09-20 session 32, BEFORE any candidate computation. sha16 asserted by driver_iter52.py at run start.
#
# OPERATOR OBJECTIVE (verbatim, unchanged)
# "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be smaller than 20%."
#
# VERIFY-FIRST STATE (this session, before sealing)
# - Canonical gauntlet ok=true 7/7 fresh (coord/verify_champion_r3_last_session32.json):
#   weights_repro 7.632783294297951e-17 / byte_repro 1.0408340855860843e-16 / half-turn rejected
#   1.644349418787801e-05 / gross 1.0000000000005784 n_over 0 / 0 neg years worst +7.9063 pct /
#   MDD -3.733938034777473 pct / SR 3.8203573009568794 / cagr 23.92147218901779 /
#   turnover 4.331113668256489 bp/yr / n_days 4806 (2008-03-31..2026-08-28).
# - Nine shas re-hashed fresh, ALL OK: champion cfa9ec4d38158691 / weights a384d6b92e258fd5 /
#   QAxasts vt015 c40d008ddbf7c579 / A5r2 vt024 7ec85336e7f7d00f / C5ng 3d2b80691ef7a448 /
#   C5ngsum ccfe3a4bc8706161 / ITER49 prior pair 3c456aa53193eb89 + 8313bee1ad8a72fe /
#   driver_iter51.py 586ad73d251a2ac9 (the derivation parent).
# - Baseline suite 654 passed / 0 failed (own run 72.29s, python3 -m pytest from repo root).
# - BAR exact digits source: coord/ITER51_C5NG_VT_READJ/driver_iter51.log line 12 fresh-grepped
#   this session: "A2 committed-frame continuity: projid=0.000e+00 weights maxdev=7.633e-17
#   bytes maxdev=9.991e-17 n=4806 rows=1809 k=11 IS-SR=4.218504 (bar 4.218504)"; A2b jitter
#   5.484e-09 weights / 7.868e-10 IS-SR.
# - Coord quiet for repo writes (latest writes = session-31 landing 01:2x). DISCLOSED: a 4-agent
#   headless fleet batch (claude --print PIDs 4540-4543) started ~01:56 CST, one carrying this
#   session's own operator prompt; no coord writes by them in the first 30 min; champion pair
#   re-hashed at seal; the driver asserts pair pre==post regardless.
#
# THE CELL (28th measured axis)
# QAxasts tsmom ONE generator scalar MAW=189 (signal moving-average window), family book share
# 5.5133 pct at the current frame (recomputed fresh from RAWEW13v2_IS_SR_weights.csv; matches
# the ITER49 landing figure 7.9566 -> 5.5133 pct). The tsmom family's signal certificate.
#
# MOTIVATION CLASS (the legality core, recorded AT SEAL)
# 1. Class provenance: #141 (ITER50) recorded the STALENESS RE-ADJUDICATION class - a family
#    scalar whose certificate predates an ADOPTED non-uniform rescale is re-adjudicated at the
#    new frame, ONE re-adjudication per family-scalar-cell per generation. The solver cell was
#    consumed by ITER50, the C5ng vt cell by ITER51. This seal consumes the tsmom-MAW cell -
#    FIRST of the four remaining cells enumerated by the session-31 police (ITER51 precommit,
#    REFUSED-ALTERNATIVES section: "tsmom-MAW / DUR / C5ng-k / brwt-zb staleness cells: same
#    class, strictly smaller materiality; one cell per session").
# 2. Depth of staleness - the DEEPEST of the remaining cells: the MAW certificate is ITER37
#    (interior peak EXACTLY at the anchor 189, bar 4.198632, at the 8559fa55ee9a3417 frame).
#    THREE adopted non-uniform rescales postdate it: ITER43 (A5r2 vt015), ITER47 (A5r2 vt024),
#    ITER49 (tsmom vt015 - the largest adopted move on record, AND structural: it replaced the
#    canonical sleeve file itself, vt 0.10 vintage -> E1_QAxasts_tsmom189__vt015.csv). Under the
#    #48 law (diag shrink re-prices hedging under ANY non-uniform rescale) the question is
#    whether the interior peak MOVED with the covariance AND with the in-family vt change -
#    the MAW x vt015 interaction at book level was NEVER measured (ITER37 ran at vt10).
# 3. Refusal reconciliation: the session-31 police REFUSED a "tsmom-vt re-adjudication" because
#    "tsmom IS the adopter of rescale-2; re-measuring its own grid at its own adoption = chasing
#    the adoption itself" - that refusal binds the vt SCALAR (the adopted quantity itself, whose
#    certificate IS the ITER49 measurement at the current frame, and whose 0.15 edge was still
#    rising). MAW is a DIFFERENT frozen scalar with a THREE-generation-old interior-peak
#    certificate; re-measuring it chases no adoption and no edge.
# 4. Binding reconciliation: #140/ITER49 "LAST seal on the tsmom family - no extension seal is
#    possible" binds EDGE-CONTINUATION (the rising vt 0.15 grid edge). The ITER47 escape form
#    governs: "Any further movement on this family requires a NEW motivation class recorded in
#    the ledger, not an edge continuation." The staleness class IS that class (#141); the grid
#    below is the SAME 5 points VERBATIM; no envelope extension (315/378 NOT run - the
#    anti-dog-chase re-binding below).
#
# RESULT-AWARE MOTIVATION DISCLOSED (per the #139 precedent)
# Adoption EV is honestly LOW: the family share is small (5.5133 pct), the acceptance-era MAW
# plateau was BROAD (9/9 within 20 pct of peak standalone), and BOTH prior staleness
# re-adjudications (ITER50 solver, ITER51 largest-family vt) returned the incumbent as argmax
# - the in-wall ranking has been covariance-robust every time it was tested. The seal's content
# is the FRONTIER AIRTIGHTNESS of the tsmom family's signal certificate and a candidate SIXTH
# independent plateau confirmation. If any arm IS-admits, the ONE reveal goes to the G7 police
# - no self-adoption exists.
#
# GRID (deterministic, zero free choice, VERBATIM ITER37 grid)
# ARMS = (189 anchor, 126, 157, 220, 252). Provenance (ITER37 precommit, sealed 2026-09-19):
# 157/252 = acceptance-PRINTED plateau neighbors (157:0.97, 252:1.10 standalone on the truncated
# vintage), 126 = printed outer neighbor (0.93), 220 = midpoint of the 189..252 gap (220.5 -> 220,
# integer rounding disclosed then), all inside the acceptance scan envelope 42..378 (no envelope
# extension now). min_periods = maw // 2 is a DERIVED quantity, swept COUPLED (not a second
# scalar). vt FROZEN at 0.15 = the CURRENT committed anchor (sweeping it would BE the refused
# tsmom-vt cell). One sleeve, one scalar.
#
# A1 + CALENDAR + CLIP PRE-SEAL PROBES (run BEFORE this seal; anchor_a1_probe.log in this dir)
# - A1 regen-maw189-vt015-vs-committed QAxasts ok=True maxdev=9.996e-17 inner=4947
#   committed_nonnan=4947 FULL - byte-faithful at the CURRENT frame (the vt015 vintage).
# - CALENDAR: all 5 MAW arms produce an IDENTICAL index (n=4947 each) - coverage law holds;
#   the driver re-asserts it per arm, fail-closed.
# - CLIP-REGIME PROBE: scale=(vt/rcum).clip(upper=3.0), rcum = expanding(60) ann vol of the
#   PRE-SCALE stream. bound_frac_onframe = 0.000000 at ALL 5 arms; rcum_min pct ann =
#   23.3663 (189) / 23.8756 (126) / 23.5116 (157) / 21.5788 (220) / 20.1336 (252) vs the
#   largest bound vt/3 = 0.05. The vt machinery is a clean trailing vol-target at every arm.
# - PROBE RUN-1 DISCLOSURE (honesty record): the first probe invocation died fail-closed
#   PRE-A1 at the r6lib import - a single-identity D17 patch is INSUFFICIENT for this chain
#   (r6lib resolves the FULL-PATH campaign.harness.data identity); fixed to the Amendment-1
#   DUAL patch (driver_iter49 form) patching BOTH module objects BEFORE the import chain.
#   Runtime fact re-verified this session: manifest.csv (mtime Sep 8 14:40) STILL sits in
#   tools/quant/data/twelve_big/ and campaign/harness/data.py panel() still has NO skip logic
#   - the D17 runtime-patch law remains LOAD-BEARING for every r6lib-resolving chain (the
#   ITER51 "retained inert safety patch" note is true only for non-r6lib chains).
#
# ADMISSION (IS level, all required, pre-registered)
# - Frame: committed 12-pool via rawew13v2_build, B.PATHS LIVE (= A5r2 vt024 + QAxasts vt015),
#   rows 1809, k_covered 11.
# - BAR = 4.218504 (committed champion IS-SR, exact digits from the ITER51 A2 line, above).
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
# honest negative, no candidate CSV beyond the for-the-record arm files.
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
# Every inherited VT label is truthfully renamed (ARM MAW=%d, REVEAL arm MAW=%d, A1 maw189-vt015,
# arm_maw%d / candidate_maw%d file stems); the reveal incumbent label FORMATS FS_BAR (3.820357).
# The make-driver asserts no ANCHOR_VT / build_c5ng / C5NG / ARM VT / ITER51 token survives.
#
# COVERAGE LAW / FROZEN BLOCKS
# - Per-arm asserts: calendar equality vs the anchor arm (ADDED BACK from driver_iter49 -
#   driver_iter51 had dropped it; LOAD-BEARING here because MAW moves min_periods), frame
#   coverage equality, rows == 1809, k == 11 - all fail-closed.
# - fit_relw / apply_cap / project_wmax / build_book asserted AST-text-identical to
#   driver_iter41.py AND driver_iter36.py at run start.
# - Driver = driver_iter51.py with asserted-exactly-once substitutions (OUT dir, PRECOMMIT_SHA,
#   header line, constants block, generator+import block, A1 block, arm loop, admission block,
#   reveal label/argmax/candidate name, log filename x2, champion-pair pre-assert ADDED BACK
#   from driver_iter49); py_compile gate before the run. ~80 pct of the file byte-identical
#   to the lineage.
# - Champion sha16 pre==post asserted by the driver (the driver must not touch the live pair).
#
# ANTI-DOG-CHASE RE-BINDING (pre-committed)
# This re-adjudication RE-SEALS the tsmom-MAW cell at the CURRENT frame. REGARDLESS of outcome:
# no further tsmom-MAW measurement this generation; a rising IS edge at 252 (the ITER37 curve
# ticked UP there, bar-0.0058) is RECORDED, NOT chased; 315/378 are NOT run; any further
# movement requires a NEW motivation class recorded in the ledger.
#
# REFUSED ALTERNATIVES (recorded at seal, before results)
# - tsmom-vt re-adjudication: REFUSED by the session-31 police (the adoption itself; still-rising
#   edge). This seal does not touch vt; vt is FROZEN at 0.15 in every arm.
# - DUR / C5ng-k / brwt-zb staleness cells: same class, strictly smaller materiality, one cell
#   per session - left to future sessions/generations.
# - Re-running police-killed cells at the new incumbent: re-litigating OOS evidence. REFUSED.
# - Solver / estimator internals: re-closed THIS generation (ITER50 single-re-adjudication
#   scope). Wmax relaxation (+0.024 IS-SR behind the wall), G7 relaxation (price-tag curve,
#   recommendation KEEP), purchased data: operator levers, unchanged, not cells.
