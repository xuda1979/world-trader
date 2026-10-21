# ITER48 FINDINGS_PRECOMMIT - C5NG FAMILY VOL-TARGET AXIS (vt_ann), session 28, 2026-09-19

SEALED BEFORE ANY CANDIDATE COMPUTATION. sha16 of this file is asserted by driver_iter48.py at run start.

## Operator objective (verbatim, unchanged)
"keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be smaller than 20%."

## Verified-first (pre-seal)
- Canonical gauntlet ok=true 7/7 fresh (coord/verify_champion_r3_last_session28.json): weights_repro 8.327e-17 /
  byte_repro 1.041e-16 / half-turn rejected 1.62e-5 / gross 1.0000000000006 n_over 0 / 0 negy / MDD -3.7012 /
  SR 3.7840994002 / cagr 23.7668.
- Champion triple re-hashed fresh: champion 3c456aa53193eb89 / weights 8313bee1ad8a72fe / vt024 sleeve 7ec85336e7f7d00f.
- Baseline suite 630 passed / 0 failed OWN RUN 69.87s (python3 -m pytest from repo root).
- Coord quiet (latest writes = session-27 landing, 36-39 min old); STANDUP tail = session-27 entry; no live writer.

## THE CELL
C5ng family harness vol_target (vt_ann), the emission-harness scalar of the LARGEST book family:
C5ng 17.2624 pct + C5ngsum 14.3495 pct = 31.61 pct of committed book weight (vt024 book). vt_ann=0.10 frozen
since the acceptance era (gates.vol_target default; .meta 'harness expanding vt10 min60 cap3'); the value itself
was NEVER measured at book level under the current objective. Shared across BOTH variants = ONE generator scalar
(per-variant vt = mining surface, REFUSED, same law as the #125 k treatment).

## LEGALITY (enumerated, not asserted)
- Ledger scan: no prior C5ng-VT axis exists (33 swept the calm-filter k; acceptance plateau print was k-only;
  C5_newdata docs contain no vt grid - 'vt series' in CHARTER_2.md means the vol-targeted return series).
- The two-slice standard (established 38/39, applied 44/45): 33 consumed slice 1 (k); THIS seal is slice 2.
- ANTI-DOG-CHASE BINDING: this is the LAST seal on the C5ng family - the grid below is measured end-to-end
  REGARDLESS of outcome; a rising IS edge is recorded, NOT chased. Remaining family constants (90d calm window,
  vol_target min_days=60, weekday map, COST_SLEEVE, MONTHS) = identity/refused classes (no printed grids -
  same standard as dualmom FRAC=1/3 in #130).

## GRID (deterministic, zero free choice)
ARMS = (0.10 anchor, 0.06, 0.09, 0.12, 0.15). Novel points = the EXACT mirror of the sealed ITER43 A5r2-VT
grid (0.06/0.09/0.12/0.15) bracketing the anchor on both sides - precedent-referenced arithmetic.

## A1 PRE-SEAL (run BEFORE this seal; coord/anchor_a1_probe.log)
- A1a C5ng regen-vt010-vs-committed ok=True maxdev=9.975e-17 inner=7381 committed_nonnan=7381 FULL.
- A1b C5ngsum regen-vt010-vs-committed ok=True maxdev=9.996e-17 inner=7381 committed_nonnan=7381 FULL.
- Committed sha16: C5ng 3d2b80691ef7a448 / C5ngsum ccfe3a4bc8706161 (untouched Sep-07 vintages).
- CLIP-REGIME PROBE (disclosed, result-aware): scale=(vt/rcum).clip(upper=3.0). C5ng pre-scale rcum 44.5-85.6 pct
  ann -> clip NEVER binds (frac 0.0000 at every grid point), stream(vt) = (vt/0.10) x stream(0.10) to 3.7e-15 of
  stream std. C5ngsum clip binds on 1-3 expanding-warmup days (rcum min 2.33 pct, 1997-98), ALL BEFORE the
  2008-03-31 book frame -> ON-FRAME BOTH VARIANTS ARE PURE-SCALE.
- READING (honest EV): with the clip off-frame, the first-order fit response is a 1/c share rescale that the
  mean-variance fit largely undoes; the LIVE channels are (i) diag-shrink mismatch (Sig_jk scales c, Sig_jj c^2),
  (ii) WALL-SHADOW: down-scale arms raise wanted C5ng/C5ngsum shares ~1/c across the 2/11 wall (committed C5ng
  17.26 pct at 1.8989x; vt=0.09 wants ~19.2 pct, vt=0.06 ~28.8 pct vs wall 18.18 pct), forcing a genuinely
  different book, (iii) build_book nav-drift second-order. ADOPTION EV HONESTLY LOW; the seal's content is the
  wall-shadow + second-order measurement and frontier-airtightness of the largest-weight family.

## ADMISSION (pre-registered)
- Frame: committed 12-pool via rawew13v2_build (A5r2 -> vt024 post-47), rows 1809, k_covered 11.
- BAR = 4.207736 (committed vt024 book IS-SR, exact digits from driver_iter47.log ARM VT=0.24).
- Candidate admitted iff: is_sr > BAR + 1e-4 (47's STRICTER margin form) AND is_mdd >= -0.06 AND 0 IS neg years
  AND Wmax_sf <= 2.0 + 1e-9. Anchor arm (0.10) ineligible by construction.
- A2 committed-frame continuity: projid 0.0, weights maxdev < 1e-12 vs committed weights file, bytes maxdev
  < 1e-12 vs champion CSV, committed IS-SR within 5e-6 of BAR - fail-closed.
- A2b regen-vs-committed fit-landing jitter is LOGGED and disclosed (43-class SLSQP landing gap); the 1e-4
  admission margin must exceed it by orders of magnitude or the arm is denied (47 precedent: margin 308x jitter).

## STOP RULE (verbatim, re-sealed)
ONE reveal = the IS-argmax of admitted non-anchor arms. If no arm is admitted: honest negative, no reveal, no
candidate CSV, no operator gate consumed. If the reveal fails ANY gate: REJECT, no second reveal, NO extension,
NO second seal on this family (anti-dog-chase binding above). Champion bytes must be sha-identical pre==post run.

## REVEAL GATES (verbatim, D18-corrected percent form)
G1 (cagr >= 20.0 pct) OR (arith >= 20.0 pct); G2 grossmax <= 1.6 + 1e-9; G3 FS MDD >= -7 pct; G4 0 FS neg years;
G5 CFX4 = 0; G6 Wmax_sf <= 2.0x (k=11); G7 OOS police = bins-positive >= 4/5 AND min bin dSR >= -0.10 AND
f_sr > FS_BAR = 3.784099 (current champion FS SR); G8 fit-window shrink <= 2 pct.

## MACHINERY (pre-registered)
- driver_iter48.py = driver_iter47.py via asserted-exactly-once substitutions + graft of driver_iter33's
  re-typed C5ng run() (A1-proven 1e-16 class in #125) with the single parameterization vol_target(net, vt_ann=vt);
  py_compile gate before run; frozen four-block AST text-identity vs driver_iter41 AND driver_iter36 at run start.
- D17 panel() pre-patch retained (inert safety). Novel arms use regenerated streams; the anchor cell is on SAVED
  committed bytes (A1a/A1b recons). Stream calendars are vt-invariant (net is pre-scale; scaled.dropna() pattern
  identical across vt) - rows 1809 / k 11 asserted per arm.
