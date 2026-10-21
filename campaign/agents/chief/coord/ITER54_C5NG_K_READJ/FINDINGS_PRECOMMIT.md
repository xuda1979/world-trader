# ITER54 FINDINGS_PRECOMMIT (2026-09-20, session 34, interactive - operator prompt verbatim:
# "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can
# not be smaller than 20 pct."). SEALED BEFORE any candidate computation. Driver hash-asserts
# this seal. Pins suite: campaign/bt/tests/test_iter54_c5ng_k_readj.py.

# THE CELL (30th measured axis)
# The largest committed exposure is the C5ng family: C5ng 17.9422 + C5ngsum 14.9146 =
# 32.8568 pct of book relw (recomputed fresh this session from the committed post-projection
# weights; largest family, holding ranks 1+2 of 12). Both variants are emitted by ONE
# generator with ONE frozen scalar k=2.5 (calm filter: position flat when absolute log-return
# exceeds k times trailing-90d sigma shift(1); shared across variants - a per-variant grid
# would be a 25-cell mining surface and is refused). The certificate is ITER33 (session 15,
# 2026-09-19): at the 8559fa55 frame the incumbent k=2.5 was a LOCAL IS DIP - k=2.0/3.0/3.5
# admitted above bar 4.198632, argmax k=3.5 (4.227429) revealed and REJECTED at G7 (2/5 bins,
# min -0.2537) - the frozen value OOS-vindicated. That certificate predates THREE adopted
# non-uniform rescales (ITER43 A5r2-vt015, ITER47 A5r2-vt024, ITER49 tsmom-vt015) - none
# touched the C5ng files themselves, so the staleness runs entirely through the FIT covariance
# per the #48 law. The rescaled fit is now WALL-ADJACENT (Wmax_sf 1.9736x vs 1.8115x at
# ITER33 frame), so the wall-shadow geometry may bind differently than at the certificate
# frame. This is the third of the four staleness cells enumerated by the session-31 police
# (tsmom-MAW done s32, DUR done s33; brwt-zb remains).

# LEGALITY AT SEAL
# 1. The C5ng-VT scalar is RE-SEALED (ITER51, session 31: incumbent vt=0.10 = measured
#    IS-argmax EXACTLY at the current frame, curve falls on both sides, no admission) and is
#    FROZEN at 0.10 in EVERY arm. Sweeping vt here = re-running a sealed cell = ILLEGAL.
# 2. The a6r7-VT scalar is POLICE-KILLED (ITER30) and not in this chain at all.
# 3. Grid = ITER33 VERBATIM: k in {2.5 anchor, 1.5, 2.0, 3.0, 3.5} (the acceptance-print
#    points), anchor-FIRST presentation (calendar assert), zero free choice. NO envelope
#    extension: k<1.5 or k>3.5 NOT run (anti-dog-chase: the ITER33 k=3.5 IS-fact 4.227429 is
#    RECORDED, NOT chased; finer pitch NOT run).
# 4. Frozen in every arm: VT_FROZEN 0.10 harness vol_target; COST_SLEEVE 6.0bp sleeve-internal
#    (never re-priced - the brwt15 cost-meta law); pool 12 slots byte-frozen (B.PATHS LIVE);
#    gear 1.0; SHRINK 0.70; brwt-cap 0.30; CFX4 pinned 0; Wmax_sf <= 2.0; k_covered 11;
#    BAR 4.218504 (fresh-grepped driver_iter52.log line 11 this session); FS_BAR 3.820357.
# 5. D17 SCOPE: the C5ng chain is r6lib-FREE (build_c5ng re-typed in-driver = pandas +
#    DHHNGSP only; rawew13v2_build loads committed sleeve CSVs; no data.panel call). The
#    iter51-form single-identity harness patch is RETAINED as the documented inert safety
#    patch; the D17 runtime-patch law stays LOAD-BEARING for r6lib-resolving chains.

# STOP RULE (sealed)
# Arm admission: IS-SR > BAR + 1e-4 AND IS-MDD >= -6 pct AND 0 IS neg-years AND
# Wmax_sf <= 2.0 (+1e-9 tol). Anchor arm ineligible by construction (IS-SR = BAR).
# NO admission -> HONEST NEGATIVE, no reveal. Admission -> ONE reveal = IS-argmax of the
# admitted list ONLY (no second reveal, no police-shopping). Reveal adjudicated on 8 gates;
# G7 OOS police (current 3-prong form) = bins >= 4/5 positive AND min bin >= -0.10 AND
# FS SR > FS_BAR. ADOPT only at 8/8 (champion files rewritten by the outboard adoption
# procedure, never by the driver); anything less = REJECT, candidate kept for-the-record.
# Champion sha16 pre==post driver-asserted in ALL branches.

# PRE-SEAL PROBES (anchor_a1_probe.log sha16 9270aee97b7854be, run 04:11:59 CST pre-seal)
# A1a regen-k250-vs-committed C5ng ok=True maxdev=9.975e-17 inner=7381 FULL (committed_nonnan 7381)
# A1b regen-k250-vs-committed C5ngsum ok=True maxdev=9.996e-17 inner=7381 FULL
#   - EXACTLY the ITER33 A1 digits and the ITER51 A1a/b digits: generator re-type AND DHHNGSP
#   vintage bit-stable across all three sessions (its Sep-8 mtime proven irrelevant on this axis).
# Calendar identical ALL 5 arms (k moves only the mask, never the index): C5ng n=7381, C5ngsum n=7381.
# Clip regime (vt FROZEN 0.10): bound_frac_onframe=0.000000 at ALL 5 arms x BOTH variants
#   (rcum_min 47.84..54.55 pct ann C5ng / 29.22..33.35 pct C5ngsum vs bound 0.0333) - unlike the
#   a6r7 CAP-saturation class (ITER53), the C5ng vt scalar is NOWHERE NEAR its clip at any k.
# Family share recomputed fresh: C5ng 17.9422 + C5ngsum 14.9146 = 32.8568 pct (matches the
#   session-31 record 32.86; largest family).
#
# Stray-writer disclosure: 6 unrelated claude --bare procs + this session --print (PID 48114)
# live at probe time; no coord-writing fleet batch; champion pair re-hashed intact pre-seal.
