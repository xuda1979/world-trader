# ITER55 FINDINGS_PRECOMMIT (2026-09-20, session 35, interactive - operator prompt verbatim:
# "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can
# not be smaller than 20 pct."). SEALED BEFORE any candidate computation. Driver hash-asserts
# this seal. Pins suite: campaign/bt/tests/test_iter55_brwt_zb_readj.py.

# THE CELL (31st measured axis - the LAST remaining staleness cell)
# The brwt trio (brwt10 + brwt7 + brwt5) shares ONE generator scalar zb=1.0 (Brent-WTI
# log-spread rolling-z mean-reversion: pos = +1 when z < -zb, -1 when z > zb, else flat;
# lb 10/7/5 with min_start 2000/2008 = variant identity). Trio share recomputed fresh this
# session from the committed weights: 9.9772 + 9.1924 + 10.8304 = 30.0000 pct - EXACTLY at
# the 0.30 brwt-block cap (unchanged from the cert frame). The certificate is ITER34+ITER35
# (session 16, 2026-09-19): right side MONOTONE FALLING from the anchor (1.25 4.060778 /
# 1.50 3.884666 / 1.75 3.477293 / 2.00 3.230354) and left side MONOTONE RISING INTO it
# (0.25 3.897552 / 0.50 4.057100 / 0.75 4.175140) - STITCHED FULL INTERIOR-MAX at zb=1.0,
# the strongest closure shape (IS itself certifies the freeze; NO reveal was consumed, NO
# police verdict exists on this axis). That certificate predates THREE adopted non-uniform
# rescales (ITER43 A5r2-vt015, ITER47 A5r2-vt024, ITER49 tsmom-vt015) - none touched the
# brwt files, so the staleness runs entirely through the FIT covariance per the #48 law.
# The rescaled fit is WALL-ADJACENT (Wmax_sf 1.9736x vs 1.8115x at the cert frame), and
# ITER34 measured Wmax_sf RISING toward the wall with zb (1.9867x at zb=2.0 from 1.8115x),
# so the wall-shadow geometry that held ITER52/53 arms captive may bind on the right side.

# LEGALITY AT SEAL
# 1. The brwt vt scalar is the HARNESS DEFAULT (vol_target(net) = vt_ann 0.10, min 60,
#    clip upper 3.0 - signature re-read at source this session and identical to the iter34
#    call form). The #131/#142 coverage audits recorded the trio as FULLY covered: zb
#    (sealed 34/35), per-variant lb (REFUSED mining surface - stays refused), vt (design
#    treatment). Sweeping vt or lb here = re-running sealed/refused cells = ILLEGAL.
# 2. Grid = ITER34 UNION ITER35 stitched VERBATIM: zb in {1.0 anchor, 0.25, 0.50, 0.75,
#    1.25, 1.50, 1.75, 2.00} - all 8 cert-frame points, anchor-FIRST presentation (calendar
#    assert), ZERO new points, zero free choice. NO envelope extension: the degenerate zb=0
#    always-in limit stays OUTSIDE the family (iter35 construction); zb beyond 2.0 / below
#    0.25 and finer pitch NOT run (anti-dog-chase).
# 3. Frozen in every arm: default vol_target; sleeve cost 6.4bp FULL |dW| inside the
#    generator (never re-priced - the brwt15 cost-meta law); pool 12 slots byte-frozen
#    (B.PATHS LIVE); gear 1.0; SHRINK 0.70; brwt-cap 0.30; CFX4 pinned 0; Wmax_sf <= 2.0;
#    k_covered 11; BAR 4.218504 (fresh-grepped driver_iter52.log line 11 this session);
#    FS_BAR 3.820357 (fresh gauntlet stats.sr this session).
# 4. ADMISSION ADDENDUM (pre-registered BEFORE the run, disclosed): admission additionally
#    requires projid == 0.0 EXACTLY. A projected arm = wall breach = INADMISSIBLE per the
#    ITER50 convention recorded in #141 (a wall breach is an inadmissible cell, NOT a
#    rescue; the ITER26 repair class is refused here). project_wmax stays in the pipeline
#    solely as the identity-on-feasible check - the anchor arm MUST read projid 0.000e+00,
#    proving the projection never rescues anything on feasible vectors. This term is inert
#    at the cert frame (max 1.9867x) but pre-registered because the current fit is
#    wall-adjacent and the cert-frame geometry says the right side pushes toward the wall.
# 5. D17 SCOPE: the brwt chain is r6lib-FREE (generator re-typed in-driver = pandas +
#    FRED/EIA CSVs; rawew13v2_build loads committed sleeve CSVs; no data.panel call). The
#    iter51-form single-identity harness patch is RETAINED as the documented inert safety
#    patch; the D17 runtime-patch law stays LOAD-BEARING for r6lib-resolving chains.
# 6. Driver derivation: make_driver_iter55.py builds driver_iter55.py from a byte-copy of
#    driver_iter54.py (sha16 c5c7855346fbd31c) via asserted-exactly-once substitutions;
#    the brwt generator block is spliced VERBATIM from driver_iter34.py source. Run-start
#    frozen-block AST check: fit_relw/apply_cap/project_wmax/build_book text-identical to
#    driver_iter41.py AND driver_iter36.py (the iter54 form, kept verbatim).

# STOP RULE (sealed)
# Arm admission: IS-SR > BAR + 1e-4 AND IS-MDD >= -6 pct AND 0 IS neg-years AND
# Wmax_sf <= 2.0 (+1e-9 tol) AND projid == 0.0 (addendum 4). Anchor arm ineligible by
# construction (IS-SR = BAR). NO admission -> HONEST NEGATIVE, no reveal. Admission ->
# ONE reveal = IS-argmax of the admitted list ONLY (no second reveal, no police-shopping).
# Reveal adjudicated on 8 gates; G7 OOS police (current 3-prong form) = bins >= 4/5
# positive AND min bin >= -0.10 AND FS SR > FS_BAR. ADOPT only at 8/8 (champion files
# rewritten by the outboard adoption procedure, never by the driver); anything less =
# REJECT, candidate kept for-the-record. Champion sha16 pre==post driver-asserted in ALL
# branches.

# PRE-SEAL PROBES (probe_iter55_a1.py / probe_iter55_a1.log, run 04:37 CST pre-seal)
# Champion pair re-hashed intact: cfa9ec4d38158691 / a384d6b92e258fd5.
# A1 regen-zb1.0-vs-committed brwt10 ok=True maxdev=9.999e-17 inner=6567 FULL
# A1 regen-zb1.0-vs-committed brwt7  ok=True maxdev=9.986e-17 inner=4580 FULL
# A1 regen-zb1.0-vs-committed brwt5  ok=True maxdev=9.996e-17 inner=4580 FULL
#   - EXACTLY the ITER34/35 A1 digits: generator re-type AND brent/wti vintages bit-stable
#   since the cert frame (fred mtimes 08-12, eia mtimes 09-06/09-07 both pre-date the cert
#   and are proven content-identical by the 1e-16 devs). Regen tails reach 2026-09-01 vs
#   committed emission cut 2026-08-28: post-frame rows, unreachable by the fit (the iter36
#   disclosure class; inner join = FULL committed coverage).
# Calendar-vs-zb probe: brwt10 zb=2.0 index IDENTICAL to zb=1.0 (zb moves only the
#   threshold mask, never the index) - coverage law holds by construction.
# vt-clip probe: bound_frac=0.000000 ALL THREE variants (scale never pinned at 3.0) - the
#   default-vt treatment is nowhere near its clip (the iter54 C5ng clean case, not the
#   iter53 a6r7 CAP-saturation case).
# Trio share recomputed: 9.9772 + 9.1924 + 10.8304 = 30.0000 pct (block cap exact); max
#   non-CFX4 share C5ng 17.9422 pct -> Wmax_sf 1.9736x (matches the #144/#145 record).
# Fresh verification this session: gauntlet ok=true 7/7 (verify_champion_r3_last_session35
# .json, EVERY digit identical to s32/s33/s34); baseline suite 672/0 own run 74.81s.
# Stray-writer disclosure: 16 claude-ish procs at probe time = this session --print +
#   OTHER-repo prompts (quantum, independent_papers, cmri wrappers, 6 --bare) - NO
#   world-trader coord-writing fleet batch; champion pair intact pre-seal.
