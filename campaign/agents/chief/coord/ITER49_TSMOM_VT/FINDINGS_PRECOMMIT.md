# ITER49 FINDINGS_PRECOMMIT - TSMOM (QAxasts) HARNESS VOL-TARGET AXIS (vt_ann)
# Sealed 2026-09-19 session 29, BEFORE any candidate computation. Driver hard-asserts this sha16.
#
# ENUMERATION (the 38/39 two-slice standard, applied uniformly): the tsmom family has consumed
# exactly ONE slice - MAW (ITER37, grid {126,157,189,220,252}, anchor=argmax, no reveal consumed).
# The ONE remaining owed cell is the harness vol_target vt_ann of the SAME generator - never
# measured at book level (the ITER37 sweep froze vt=0.10; QA_xasts_tsmom189.py printed an MAW
# plateau only - no vt grid was ever printed, so the sealed-mirror rule supplies the grid, as in
# ITER48). This seal is the family's SECOND and LAST slice: after this run the tsmom family is
# CLOSED end-to-end.
#
# GRID: {0.06, 0.09, 0.12, 0.15} + anchor 0.10 = EXACT mirror of the sealed ITER43 A5r2-VT grid
# reused by ITER48 (zero free choice). Per-variant vt REFUSED (one shared harness scalar,
# #125 law). ANTI-DOG-CHASE BINDING AT SEAL: this is the LAST seal on the tsmom family
# REGARDLESS of outcome. Remaining constants - panel composition, RET_PAN, Wed/T+1 cadence,
# 0.20/leg EW, sign(px-MA) rule, sleeve COST, vol_target min_days=60, clip upper=3.0 - are
# refused no-printed-grid / strategy-identity classes (#130 FRAC standard).
#
# GENERATOR: graft of driver_iter37.py's A1-proven re-type of e1_idea5_xasts_detrunc.py
# (module-level save_sleeve law: never import the source), MAW=189 FROZEN, the only change
# being vol_target(net.dropna(), vt_ann=vt). D17 panel pre-patch applied BEFORE the
# r7_idea5_breadth import (ordering preserved from driver_iter37).
#
# PRE-SEAL DISCLOSURES (per #117/#125/#138/#139 precedent, all measured BEFORE this seal,
# probe log = anchor_a1_probe.log in this directory):
# (1) A1 regen-vt010 vs committed E1_QAxasts_tsmom189_2006.csv (sha16 664d01fa126902c0):
#     maxdev 9.996344e-17, inner 4947 = committed_nonnan 4947 FULL; spans identical
#     2006-12-13..2026-08-12. The re-type is byte-faithful (same digits as ITER37's A1).
# (2) CLIP-REGIME PROBE: gates.vol_target scale = (vt/rcum).clip(upper=3.0) with
#     rcum = expanding(60) ann vol of the PRE-SCALE stream. On-frame (>=2008-03-31, n=4565)
#     pre-scale rcum min = 19.8341 pct ann (max 32.4469) - an order of magnitude above every
#     clip bound vt/3 (max bound 5.0 pct at vt=0.15). The clip NEVER binds on-frame at ANY
#     arm -> ON-FRAME PURE-SCALE. RESULT-AWARE MOTIVATION DISCLOSED: under the #48
#     shrink-distortion law (diag shrink credits variance at c^2 but hedge value at c, so any
#     non-uniform rescale misprices hedging) the adoption EV of a pure-scale axis is honestly
#     LOW and the anchor is the certified-optimum prior. The seal's content is therefore the
#     FRONTIER-AIRTIGHTNESS of the last vt cell (the two-slice standard's owed measurement)
#     and a THIRD confirmation of the #48 law, not an alpha hunt.
# (3) WARMUP: vol_target rcum needs 60 obs -> first 59 rows NaN -> dropna() cuts them; the cut
#     is vt-INVARIANT (NaN comes from rcum, not from scale). 382 pre-frame rows exist; the fit
#     frame starts 2008-03-31 so none are reachable. Calendar equality across arms is a
#     structural consequence, asserted per arm anyway (fail closed).
#
# COVERAGE LAW (sealed asserts): every arm - regen calendar EQUALS the vt=0.10 regen calendar;
# frame coverage count EQUALS the committed stream's; fit rows == 1809; k_covered == 11;
# projection identity on the incumbent == 0.0 exactly; A2 committed-frame continuity
# weights <1e-12 AND book bytes <1e-12 AND IS-SR == BAR within 5e-6 (BAR = 4.207736, the
# ITER47 vt024 champion's committed IS-SR). A2b fit-landing jitter is measured and logged;
# the admission margin is BAR + 1e-4 (jitter measured 1.465e-09 at ITER48, 4 orders below).
#
# ADMISSION (IS level, all required): is_sr > 4.207736 + 1e-4 ; is_mdd >= -6 pct ; 0 IS
# negative years ; Wmax_sf <= 2.0 (k_covered=11). Anchor arm ineligible by construction.
# STOP RULE: ONE global IS-argmax reveal among admitted, then STOP - fail => no second reveal,
# no candidate CSV under no-admission (law). REVEAL GATES (all 8 required):
# G1 cagr >= 20 pct OR arith >= 20 pct (D18-correct percent form) ; G2 grossmax <= 1.6 (the
# operator cap; builder gear is 1.0) ; G3 FS MDD >= -7 pct ; G4 0 FS negative years ;
# G5 CFX4 == 0 ; G6 Wmax_sf <= 2.0x ; G7 OOS police: >= 4/5 positive bin dSR AND min bin
# >= -0.10 AND FS SR > 3.784099 (the incumbent) ; G8 fit-window shrink <= 2 pct.
# ADOPTABLE 8/8 => full battery per the #43 Amendment-2 protocol (canonicalize to the
# verifier's own algebra before any adoption); else REJECT.
#
# FROZEN BLOCKS: fit_relw / apply_cap / project_wmax / build_book asserted AST-text-identical
# to driver_iter41.py AND driver_iter36.py at run start. Driver = driver_iter48.py with
# asserted-exactly-once substitutions + the tsmom graft; py_compile gate before the run.
# Champion sha16 pre==post asserted by the driver.

# AMENDMENT 1 (2026-09-19 session 29, BEFORE the corrected run; run-1 log preserved as
# driver_iter49_run1_identity_defect.log): D17 patch extended to BOTH module identities.
# Run-1 died fail-closed at the graft import BEFORE any arm/A1/verdict: the driver_iter48-
# inherited patch wrapped only the short-path identity (sys.modules['data']) and was inert
# there (C5ng never calls panel()); the tsmom chain reaches panel() via r6lib's
# 'from campaign.harness import data as D' = the full-path identity. Repair: the SAME
# _panel_d17 function is assigned to BOTH DH.panel and campaign.harness.data.panel BEFORE
# the r7_idea5_breadth import. Nothing else changes: grid, admission, stop rule, gates,
# anti-dog-chase binding all stand verbatim. Precommit sha16 after amendment is recorded in
# the driver's PRECOMMIT_SHA constant (asserted at run start).

# AMENDMENT 2 (2026-09-19 session 29, BEFORE the corrected re-run; run-2 log preserved as
# driver_iter49_run2_stale_incumbent_label.log): D19-class INHERITED-LITERAL defect, caught
# fail-closed by the pin suite pre-GREEN. The reveal log line's incumbent LABEL was a
# hardcoded string inherited from the driver_iter48 template ("incumbent 3.764764", the
# ITER43-era value) while the sealed FS_BAR gate constant is 3.784099 - the G7 GATE MATH
# used the correct constant (its PASS is valid; the bin lines print live incumbent SRs), so
# the VERDICT is unaffected; only the printed label is stale. Repair: the label now formats
# FS_BAR. The run is deterministic - the corrected re-run must reproduce every ARM/A2/reveal
# number byte-identically (asserted by the pins) with only the label changing. Log sha16
# changes; the pins pin the NEW sha.

# AMENDMENT 3 (2026-09-19 session 29, BEFORE the corrected re-run): ERA RECONSTRUCTION PIN.
# The first corrected-re-run attempt (post-adoption-swap builder) died FAIL-CLOSED at the A2
# assert: B.PATHS["QAxasts"] had already been repointed to the adopted tsm-vt015 sleeve, so
# the driver's "committed frame" was the NEW champion's pool. That crashed attempt's printed
# A2 row is recorded here as POST-ADOPTION CONTINUITY EVIDENCE: rebuild-vs-adopted-weights
# maxdev 7.633e-17, rebuild-vs-adopted-bytes 9.991e-17, rebuilt IS-SR 4.218504 = the sealed
# vt0.15 arm value EXACTLY - the default builder now reproduces the adopted champion at
# 1e-17 (no log written; evidence disclosed here per the campaign's evidence-preservation
# rule). The corrected re-run era-pins PATHS["QAxasts"] to the pre-ITER49 vt0.10 vintage so
# the SEALED experiment is reconstructed exactly as sealed (bar 4.207736, vt024-era frame);
# every ARM/A2/reveal number must reproduce run-2 byte-identically, only the D19 label and
# the first-line sha16 change. Precommit sha16 after this amendment is in the driver.

# AMENDMENT 4 (2026-09-19 session 29, BEFORE the corrected re-run): A2 ADJUDICATED AGAINST
# THE ERA PAIR. Attempt-2 of the corrected re-run died fail-closed at A2 (weights maxdev
# 2.443e-02): the A2 block read the LIVE committed files, which the ADOPTION has since
# replaced (cfa9ec4d38158691 / a384d6b92e258fd5) - the vt024-era frame rebuild cannot and
# must not reproduce the ADOPTED weights. Repair: the sealed experiment's continuity
# targets are the ERA pair preserved byte-exact in this directory's prior_champion_backup/
# (3c456aa53193eb89 / 8313bee1ad8a72fe = the exact bytes A2 reproduced in run-2); the
# driver's pre==post champion-sha assert now guards the LIVE ADOPTED pair (the driver must
# not touch it). Determinism expectation unchanged: every ARM/A2/reveal number byte-equal
# to run-2; deltas = the D19 label + the first-line sha16 only.
