# ITER53 FINDINGS_PRECOMMIT - A6R7 (bond2y trend) DUR SCALAR STALENESS RE-ADJUDICATION
# Sealed 2026-09-20 session 33, BEFORE any candidate computation. sha16 asserted by driver_iter53.py at run start.
#
# OPERATOR OBJECTIVE (verbatim, unchanged)
# "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be smaller than 20%."
#
# VERIFY-FIRST STATE (this session, before sealing)
# - Canonical gauntlet ok=true 7/7 fresh (coord/verify_champion_r3_last_session33.json):
#   weights_repro 7.632783294297951e-17 / byte_repro 1.0408340855860843e-16 / half-turn rejected
#   1.644349418787801e-05 / gross 1.0000000000005784 n_over 0 / 0 neg years worst +7.9063 pct /
#   MDD -3.733938034777473 pct / SR 3.8203573009568794 / cagr 23.92147218901779 /
#   turnover 4.331113668256489 bp/yr / n_days 4806 (2008-03-31..2026-08-28). EVERY digit
#   identical to the session-32 artifact - the champion chain is byte-stable.
# - Shas re-hashed fresh, ALL OK: champion cfa9ec4d38158691 / weights a384d6b92e258fd5 /
#   a6r7 sleeve E1_a6r7_bond2y_trend_1990.csv e281e8c4cc5682fb / DGS2 source 6e86215a92bd0973
#   (span 1990-01-02..2026-08-27, n=9170 - unchanged window) / derivation parent
#   driver_iter52.py 3d3ab315d44f04cc / frozen-block extract sources driver_iter41.py
#   9e95eb2b7a0684ba + driver_iter36.py 3458f0b1e1c16573.
# - Baseline suite 660 passed / 0 failed (own run 68.17s, python3 -m pytest from repo root).
# - BAR exact digits source: coord/ITER52_TSMOM_MAW_READJ/driver_iter52.log line 11
#   fresh-grepped this session: "A2 committed-frame continuity: projid=0.000e+00 weights
#   maxdev=7.633e-17 bytes maxdev=9.991e-17 n=4806 rows=1809 k=11 IS-SR=4.218504 (bar 4.218504)";
#   ITER52 A2b jitter 3.249e-09 weights / 1.151e-10 IS-SR.
# - COORD QUIET + STRAY-WRITER DISCLOSURE: latest coord write before this session = the
#   session-32 landing (STANDUP_LOG 02:34). The cron-twin stray RAWEW15_REFRESH_CANDIDATE pair
#   re-emitted 02:38:49 with sha16 14e5bca370bbc30a / 93fbb268c2935b7e - this re-emit DIFFERS
#   from the #123/ITER32-era bytes (dc3d7c9e / 8c19ef22): the pair is a DEAD-vintage artifact
#   whose re-emits have varied before (line 15079 records 8d7e711e / 8c19ef22); it sits OUTSIDE
#   the champion pin graph; champion pair re-hashed AFTER it, UNAFFECTED (digits above). Also
#   disclosed: 6 unrelated claude --bare procs alive at seal time (no coord writes); the driver
#   asserts champion-pair pre==post regardless.
#
# THE CELL (29th measured axis)
# a6r7 (DGS2 bond2y trend, legacy generator) ONE generator scalar DUR=1.90 - the coefficient
# of -dy in the legacy total-return proxy tr = (-DUR * y.diff() + y / 252) - family book share
# 8.6961 pct at the current frame (recomputed fresh from RAWEW13v2_IS_SR_weights.csv; matches
# the session-31 audit figure 8.70; 7th of 12; LARGER than the tsmom family whose cell ITER52
# consumed at 5.5133 pct). The a6r7 family's signal certificate.
#
# MOTIVATION CLASS (the legality core, recorded AT SEAL)
# 1. Class provenance: #141 (ITER50) recorded the STALENESS RE-ADJUDICATION class - a family
#    scalar whose certificate predates an ADOPTED non-uniform rescale is re-adjudicated at the
#    new frame, ONE re-adjudication per family-scalar-cell per generation. Solver consumed by
#    ITER50, C5ng-vt by ITER51, tsmom-MAW by ITER52. The session-31 police enumerated exactly
#    this queue ("tsmom-MAW / DUR / C5ng-k / brwt-zb staleness cells: same class, strictly
#    smaller materiality; one cell per session") and the ITER52 memo frontier carried it:
#    "Remaining staleness-class cells: DUR (iter32 anchor 1.90), C5ng-k (iter33), brwt-zb
#    (iter34/35)". This seal consumes the DUR cell - the LARGEST-remaining-materiality of the
#    three (family share 8.6961 pct) and the DEEPEST-aged remaining certificate.
# 2. Depth of staleness: the DUR certificate is ITER32 (session 14: IS-SR concave in DUR with
#    the interior max EXACTLY at the incumbent 1.90, bar 4.198632, at the 8559fa55 frame,
#    FS 3.751429 vintage). THREE adopted non-uniform rescales postdate it: ITER43 (A5r2 vt015),
#    ITER47 (A5r2 vt024), ITER49 (tsmom vt015 - the largest adopted move on record). NONE
#    touched the a6r7 sleeve file itself (sha e281e8c4cc5682fb unchanged; the A1 probe below
#    reproduces the committed stream at 9.975e-17 = the ITER32 A2 digit EXACTLY, so the
#    generator AND its DGS2 vintage are bit-stable) - the staleness runs entirely through the
#    FIT: the neighbor rescales moved the pool covariance, and under the #48 law (diag shrink
#    re-prices hedging under ANY non-uniform rescale) the DUR-conditional fit curve may have
#    moved with it. The question: did the interior peak survive the covariance change.
# 3. Refusal reconciliation: the a6r7-VT cell is POLICE-KILLED (ITER30 90-cell sweep; the
#    session-31 audit records "a6r7-vt = ITER30 90-cell sweep, police-killed"). This seal does
#    NOT touch vt: VT frozen 0.12 in every arm - and the probe shows the vt machinery is
#    DEGENERATE at current vintages anyway (cap-satiated 99.35 pct of days in EVERY arm - see
#    probes). DUR is a DIFFERENT frozen scalar whose certificate predates the rescales;
#    re-measuring it chases no adoption (the rescale adopters are OTHER families) and no edge.
# 4. Binding reconciliation: the ITER47 escape form governs ("a NEW motivation class recorded
#    in the ledger, not an edge continuation") - the #141 staleness class IS that class. No
#    DUR-specific anti-dog-chase binding exists beyond the standard one-cell-per-session law.
#    The grid below is the SAME 5 points VERBATIM; NO envelope extension.
#
# RESULT-AWARE MOTIVATION DISCLOSED (per the #139 precedent)
# Adoption EV is honestly LOW: all THREE prior staleness re-adjudications (ITER50 solver,
# ITER51 C5ng-vt, ITER52 tsmom-MAW) returned the incumbent as argmax; the ITER32 DUR curve was
# FLAT near its peak (anchor 4.198632 vs worst arm 4.192924 - a 0.0057 IS-SR spread across the
# whole +/-0.5 grid); and the incumbent sits wall-ADJACENT at the current frame (1.9736x),
# which mostly THREATENS candidates (wall-shadow) rather than helping them. The seal's content
# is the FRONTIER AIRTIGHTNESS of the a6r7 signal certificate and a candidate SEVENTH
# independent plateau confirmation. If any arm IS-admits, the ONE reveal goes to the G7 police
# - no self-adoption exists.
#
# GRID (deterministic, zero free choice, VERBATIM ITER32 grid)
# ARMS = (1.90 anchor, 1.40, 1.65, 2.15, 2.40). Provenance (ITER32 precommit, sealed
# 2026-09-19): "5 cells, 4 novel, symmetric +/-0.25 and +/-0.50 around the incumbent
# coefficient". Presentation order anchor-FIRST (the per-arm calendar-law assert compares each
# arm to the anchor arm, so the anchor must register first; the SET is identical to the sealed
# grid - zero free choice). One sleeve, one scalar; NO coupled derived quantity (unlike the
# tsmom min_periods coupling): every stateful window (K=378 rolling mean, CAD=42 stride,
# expanding(60) vt) is FROZEN identically in all arms.
#
# FROZEN (byte-frozen for every arm, verbatim ITER32)
# K=378, CAD=42, T+1 (W.shift(1)); sleeve-internal cost = LEGACY 6.0bp FULL |dWsig| (NOT the
# 6.4bp transplant: this axis lives INSIDE the legacy sleeve own convention; the brwt15
# cost-meta law holds - never re-price from meta prose; A1 byte-faithfulness pins the
# convention); expanding(60) VT=0.12 CAP=5.0; DGS2 source
# tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv; pool = the 12 committed slots
# (rawew13v2_build NAMES/PATHS LIVE = A5r2 vt024 + QAxasts vt015) byte-frozen; gear 1.0;
# SHRINK 0.70 diag; brwt-cap 0.30; CFX4 relw pinned 0; Wmax_sf <= 2.0 at k_covered=11;
# IS_END 2017-01-01; START 2008-03-31.
#
# PRE-SEAL PROBES (anchor_a1_probe.log sha16 94de62a99a074538, probe_iter53_a1.py
# sha16 5ae071fe64ad6ee7; run BEFORE this seal)
# - A1 regen-dur1.90-vs-committed a6r7 ok=True maxdev=9.975e-17 inner=9168
#   committed_nonnan=9168 FULL - byte-faithful; the digit is EXACTLY ITER32's A2 number.
# - CALENDAR: all 5 DUR arms produce an IDENTICAL index (n=9168 each) - coverage law holds;
#   the driver re-asserts it per arm, fail-closed.
# - CAP-REGIME PROBE: bound_frac_at_CAP5 = 0.993455 at ALL 5 arms - the inline VT=0.12 NEVER
#   binds (rcum_ann_max 1.3766..2.2976 pct << 12 pct); lev is pinned at CAP=5.0 on 99.35 pct
#   of days in EVERY arm, so arm streams differ ONLY through the dur-scaled net_g under one
#   constant 5.0x scale. The a6r7 vt scalar is DEGENERATE at current vintages (consistent with
#   the session-31 audit: inline VT=0.12/CAP5.0 are frozen constants). HONESTY RECORD: the
#   probe verdict line was corrected IN-PLACE pre-seal - the first draft wrongly concluded
#   "no cap satiation" from the same numbers; the corrected script + log are what the shas
#   above pin.
#
# ADMISSION (IS level, all required, pre-registered)
# - Frame: committed 12-pool via rawew13v2_build, B.PATHS LIVE (= A5r2 vt024 + QAxasts vt015),
#   rows 1809, k_covered 11.
# - BAR = 4.218504 (committed champion IS-SR, exact digits from the ITER52 A2 line, above).
# - Candidate admitted iff: is_sr > BAR + 1e-4 (the 47-class STRICTER margin form) AND
#   is_mdd >= -0.06 AND 0 IS negative years AND Wmax_sf <= 2.0 + 1e-9.
# - A2 committed-frame continuity vs the LIVE pair: projid == 0.0, weights maxdev < 1e-12,
#   book bytes maxdev < 1e-12, IS-SR == BAR within 5e-6 - fail-closed.
# - A2b regen-vs-committed fit-landing jitter LOGGED and disclosed; the 1e-4 margin must
#   exceed it by orders of magnitude or the arm is denied.
#
# STOP RULE (frozen)
# ONE global IS-argmax reveal among admitted arms by IS-SR (tie-break: smaller |DUR - 1.90|,
# then lexicographic label). If NO arm admits or argmax <= BAR + 1e-4: NO REVEAL, honest
# negative, no candidate CSV beyond the for-the-record arm files.
#
# REVEAL GATES (all 8 required, verbatim D18-correct lineage)
# G1 cagr >= 20 pct OR arith >= 20 pct (percent form); G2 grossmax <= 1.6 (operator cap,
# builder gear 1.0); G3 FS MDD >= -7 pct; G4 0 FS negative years; G5 CFX4 == 0; G6 Wmax_sf
# <= 2.0x (k_covered = 11); G7 OOS police: >= 4/5 positive bin dSR (edges 2017/2019/2021/
# 2023/2025) AND min bin >= -0.10 AND FS SR > 3.820357 (the incumbent); G8 fit-window shrink
# <= 2 pct. ADOPTABLE 8/8 => full Amendment-2 battery in-session BEFORE any adoption
# (canonicalize to bt/verify_champion.py own algebra, independent gauntlet 7/7 on the
# canonical pair, coherence halves, r3 cmd + builder PATHS update, re-pin wave, 6
# mutation-checked pins). ANY fail => REJECT, record, STOP - no second reveal.
#
# D19 INHERITED-LITERAL GUARD (the #136/#140 class)
# Every inherited tsmom label is truthfully renamed (ARM DUR=%.2f, REVEAL arm DUR=%.2f,
# A1 regen-dur1.90, arm_dur/candidate_dur file stems, arm_maw%d_stream_tsm -> arm_dur%.2f_
# stream_a6r7); the reveal incumbent label FORMATS FS_BAR (3.820357). The make-driver asserts
# no ANCHOR_MAW / build_tsmom / TSM / MAW / VT_FROZEN / vol_target / QAxasts / vt015 / ITER52 /
# driver_iter52 token survives.
#
# COVERAGE LAW / FROZEN BLOCKS / D17 SCOPE NOTE
# - Per-arm asserts: calendar equality vs the anchor arm (LOAD-BEARING, retained even though
#   the probe shows dur-invariance), frame coverage equality, rows == 1809, k == 11 - all
#   fail-closed.
# - fit_relw / apply_cap / project_wmax / build_book asserted AST-text-identical to
#   driver_iter41.py AND driver_iter36.py at run start.
# - Driver = driver_iter52.py with asserted-exactly-once substitutions (OUT dir, PRECOMMIT_SHA,
#   header line, constants block, D17+r6lib generator block -> legacy_a6r7, A1 block, arm loop,
#   anchor-continuity block, admission block, reveal label/argmax/candidate name, log filename
#   x2); py_compile gate before the run.
# - D17 SCOPE NOTE (truthful): the ITER53 chain is r6lib-FREE - legacy_a6r7 needs only pandas
#   + DGS2, and rawew13v2_build loads the committed sleeve CSVs directly (no data.panel call),
#   so the driver_iter52 DUAL-IDENTITY D17 patch is substituted OUT as NOT-APPLICABLE with an
#   explicit log line. This is the documented non-r6lib case (the ITER51 "inert safety patch"
#   note is true only for non-r6lib chains - this cell IS one). The D17 runtime-patch law
#   remains LOAD-BEARING for every r6lib-resolving chain and is untouched by this note.
# - Champion sha16 pre==post asserted by the driver (the driver must not touch the live pair).
#
# ANTI-DOG-CHASE RE-BINDING (pre-committed)
# This re-adjudication RE-SEALS the a6r7-DUR cell at the CURRENT frame. REGARDLESS of outcome:
# no further a6r7-DUR measurement this generation; any dominated near-miss arm (e.g. a rising
# edge at 2.15/2.40) is RECORDED, NOT chased; 1.15/2.65 and any finer pitch are NOT run; any
# further movement requires a NEW motivation class recorded in the ledger.
#
# REFUSED ALTERNATIVES (recorded at seal, before results)
# - a6r7-vt re-adjudication: POLICE-KILLED (ITER30 90-cell sweep). This seal does not touch
#   vt; vt is FROZEN at 0.12 in every arm (and the probe shows it is degenerate anyway).
# - C5ng-k (iter33) / brwt-zb (iter34/35) staleness cells: same class, strictly smaller
#   materiality, one cell per session - left to future sessions/generations.
# - Re-running police-killed cells at the new incumbent: re-litigating OOS evidence. REFUSED.
# - Solver / estimator internals: re-closed THIS generation (ITER50 single-re-adjudication
#   scope). Wmax relaxation (+0.024 IS-SR behind the wall), G7 relaxation (price-tag curve,
#   recommendation KEEP), purchased data: operator levers, unchanged, not cells.
