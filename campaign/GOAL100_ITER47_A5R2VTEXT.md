> SUPERSEDED (ITER61, 2026-10-12, ITER61_DDCON): the champion of record moved to the
> NG-block (C5ng+C5ngsum) relw cap 0.28 construction (A_cap28; sha16 a8ed233bd0f6fd5d /
> weights 2b0f5fbc43113149; current headline ann 23.86% at 2dp = 23.860978% precise,
> SR 3.7845, MDD -3.30%, 0 neg yrs, sealed vintage window to 2026-08-28). The ITER49
> vt015 champion below (ann 23.92% / sha16 cfa9ec4d38158691 / weights a384d6b92e258fd5)
> is SUPERSEDED history — preserved byte-exact as the archive_*_SUPERSEDED_by_ITER61_DDCON
> pair (reproducible via build(ng_cap=None)). All figures below are frozen at the ITER49
> adoption state.

> SUPERSEDED (ITER49, 2026-09-19): the champion of record moved again - the tsmom
> (QAxasts) harness vol-target vt=0.15 adoption (8/8 gates, G7 4/5 positive bins min
> -0.0092, FS SR 3.820357 = +0.0363). New headline ann 23.92% (sha16 cfa9ec4d38158691 /
> weights a384d6b92e258fd5 / canonical sleeve E1_QAxasts_tsmom189__vt015.csv). The vt024
> book below (ann 23.77 pct, SR 3.784099, sha16 3c456aa53193eb89) is preserved byte-exact
> in campaign/agents/chief/coord/ITER49_TSMOM_VT/prior_champion_backup/. History preserved
> verbatim below.

# ITER47_A5R2VTEXT - A5r2 VT upper-edge extension: ADOPTION (session 27, 2026-09-19 ~21:2x-22:0x CST)

Champion of record: campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
sha16 3c456aa53193eb89 / RAWEW13v2_IS_SR_weights.csv sha16 8313bee1ad8a72fe.
FS SR 3.7840994002149047 (incumbent 3.7647642016866434, +0.0193355) / cagr 23.7668 pct
(arith 21.4908) / MDD -3.7012 pct / 0 neg years / worst year +7.6671 pct / n 4806
(2008-03-31..2026-08-28) / gross 1.0 EXACT / turnover 4.1841 bp/yr / margin 0.
All operator constraints satisfied: leverage 1.0 <= 1.6; ann 23.77 pct >= 20; SR maximized
vs the incumbent under the sealed gates. Canonical A5r2 sleeve: A5_r2_contango_rateshock__vt024.csv
sha16 7ec85336e7f7d00f (+ .meta); the vt015 vintage (901eebdd3abef617) untouched on disk;
prior champion pair byte-exact in coord/ITER47_A5R2_VTEXT/prior_champion_backup/.

## VERDICT: ADOPTION - champion MOVED (second adoption; ITER43 was the first since ITER21)

### THE CELL (23rd measured axis)
A5r2 per-sleeve VT UPPER-EDGE extension. ITER43's sealed grid {0.06..0.15} ended AT the
then-adopted cell 0.15 with IS-SR monotone RISING into the edge and the argmax AT the edge;
extension inside THAT seal was forbidden by its stop rule. This session sealed the fresh
legal instrument (ITER35 lower-envelope second-seal precedent): precommit 2aafd014c7521ebe
sealed BEFORE any candidate, A1 anchors run PRE-seal and disclosed inside (A1a regen-vt010
vs module 0.000e+00 EXACT; A1b regen-vt015 vs committed sleeve 9.996344e-17, inner 4249 FULL).
Grid {0.18, 0.21, 0.24} = equal-step 0.03 continuation; anchor 0.15 = committed champion cell,
bar-ineligible by construction. ANTI-DOG-CHASE BINDING (pre-committed): LAST seal on this
family - the bracket 0.06..0.24 is now measured end-to-end and the still-rising curve at the
0.24 edge is recorded, NOT chased.

### RUN (single clean run; no amendments)
Driver derived from driver_iter43.py by 15 asserted-exactly-once substitutions; frozen blocks
(fit_relw/apply_cap/project_wmax/build_book) text-identical vs driver_iter41 AND driver_iter36
at run start; admission jitter margin BAR + 1e-4 added (stricter than 43's raw >BAR).
Arms: rows 1809 k 11 projid 0.0 everywhere; IS-SR 4.203733 [anchor] / 4.205510 / 4.206799 /
4.207736 - monotone rising, all 3 novel cells admitted (min margin +0.001777 = 308x the
disclosed 5.766e-09 landing jitter; max +0.004003). A2 committed-frame continuity 8.327e-17 /
9.991e-17 / IS-SR = bar exactly. REVEAL (argmax VT=0.24): FS SR 3.784099 = +0.0193,
G7 bins +0.0123/+0.0320/+0.0276/+0.0111/+0.0147 = 5/5 POSITIVE (min +0.0111) - THE FIRST
UNANIMOUS 5/5 OOS REVEAL ON RECORD (every prior reveal: 2/5 to 4/5; nine consecutive kills).
All 8 gates PASS (cagr 23.7668 / gross 1.000000000 / MDD -3.7012 / 0 negy / CFX4 0 /
Wmax_sf 1.8989x / G8 0).

### BATTERY (per the #43 Amendment 2 protocol, BEFORE adoption)
Driver-pair gauntlet: weights_repro FAIL 6.404e-09 (the measured driver-vs-verifier SLSQP
landing gap; all other checks GREEN; headline reproduced to 6 dp). Canonicalized to
bt/verify_champion.py's own algebra (_relw_from + _weights_gear/_net_from): canonical-vs-driver
relw delta = the measured 6.404e-09; canonical gauntlet 7/7 GREEN (weights_repro 8.327e-17,
byte_repro 1.041e-16, half-turn rejected 1.62e-5, gross 1.0000000000006 n_over 0, 0 negy).
Coherence: H1 dSR +0.0045 / H2 +0.0237 both positive; 14/19 years positive, worst-year delta
-0.154 pp; attribution - A5r2 standalone SR UNCHANGED 1.0192 at EXACTLY 1.60x scale
(= 0.24/0.15), the fit re-weights A5r2 3.78 -> 2.41 pct: covariance/weighting gain, not
sleeve alpha (same mechanism class as ITER43). Sleeve-emit identity proven in BOTH
generations (arm_vt015_stream == committed vt015 sleeve == 901eebdd; arm_vt024_stream ==
committed vt024 sleeve == 7ec85336). DISCLOSED: the vt015 .meta PROSE says window start
2009-09-16 but the FILE bytes start 2009-09-18 (identical calendars, union=inner=4249) -
meta prose is not bytes; the bytes ruled everywhere.

### MECHANISM (honest reading)
Raising the sleeve's vol target runs A5r2 bigger at unchanged risk-adjusted quality; the IS
fit buys LESS of the bigger sleeve (3.78 -> 2.41 pct book weight) and the freed weight goes
to uncorrelated sleeves - the covariance structure improves in BOTH OOS halves and 14/19
years. The +0.0193 FS SR margin is the largest adopted gain on record (ITER43 was +0.0133),
~2.9x the largest structure-noise dSR family member and ~1e6x the landing jitter. The 5/5
unanimous G7 is the first candidate the OOS police has ever agreed with in every window.

### LANDING
- verify_champion_r3_cmd.sh: A5r2 -> vt024 + ITER47 banner; builder rawew13v2_build.py
  PATHS A5r2 -> vt024; final canonical gauntlet on the ADOPTED files 7/7
  (coord/verify_champion_r3_last_session27.json).
- Re-pin wave: 40 RED -> 0 (18 champion-pin files, iter19/20/21 stats, energy filter,
  recon lineage, round2 mechanism/weights/metrics/corr (re-measured 0.9357692357), round3
  STALE_HEADLINES registry + a4 + lineage, round6 stats + convention deltas re-measured,
  iter43 era re-anchors). 35 gated docs got ADDITIVE PREPENDED ITER47 SUPERSEDE banners
  (snapshots in coord/AUDIT_CHAMP2/work/pre_banner_snapshot_iter47/); CHAMPION_CARD.md
  regenerated by its own generator (4854 bytes).
- test_iter47_a5r2_vtext.py: 6 pins, mutation-checked RED twice (fake incumbent FS-SR;
  fake champion sha) -> byte-exact restore (395fd9b0aebd3094) -> GREEN.
- Suite: 630 passed / 0 failed (624 + 6, own run) - see STANDUP entry.

### FRONTIER (23 axes measured under the current objective)
The A5r2-VT family is CLOSED end-to-end (0.06..0.24, dog-chase bound). Every other legal
axis remains measured-closed (gear/weights/grid-edges/census/8c-ledger/credit/estimator/
recipe/signal-params/overlays/pool-composition). Remaining operator levers UNCHANGED:
purchased data or rule change (G7 price-tag curve +0.0366/+0.0161/+0.0075/+0.0073/+0.0034/
+0.0026/+0.0025/+0.0013, all police-killed; KEEP recommendation stands). The campaign has
now delivered TWO adoptions in one day (ITER43 +0.0133, ITER47 +0.0193 = SR 3.751429 ->
3.784099, +0.0327 combined) with every operator constraint green.
