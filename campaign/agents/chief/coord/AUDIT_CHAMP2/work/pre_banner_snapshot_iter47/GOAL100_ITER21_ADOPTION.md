> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
# ITER21 ADOPTION — THE GEAR DIMENSION: SR-MAX CHAMPION AT GROSS 1.0 (2026-09-18, coordinator)

## Objective (operator, verbatim, unchanged from 2026-09-18)
> "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return
> can't be smaller than 20%."

ITER20 adopted the SR-max weight vector under the family assumption gross == 1.6. But the
operator's constraint is a **CAP** (<= 1.6), not a target. This iteration releases that pin
and examines the gear dimension itself.

## The structural fact (cost-structure identity, not an estimate)
rawew13v2_build.py charges `margin = max(gear-1, 0) * 4.5%/252` inside the net series while
turnover and borrow scale exactly ~ gear. Therefore **net SR is EXACTLY flat on (0, 1.0]**
(every cost proportional) **and STRICTLY DECREASING on [1, 1.6]** (the margin term bites).
Consistent with the #109 record: gear 1.705 made SR FALL 3.2358 -> 3.2084. The SR argmax
under `gross <= 1.6, ann >= 20%` is therefore the SMALLEST admissible gear, not the cap.

## New champion of record
campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
- sha256 8559fa55ee9a3417d3068579b24fd5609815b605a6600387e0efd5c5cf37dbe8 (n=4806)
- **weights UNCHANGED from ITER20**: RAWEW13v2_IS_SR_weights.csv sha16 d2d11c92a98683df
  (shrink 0.70 + brwt-cap 0.30, CFX4 = 0, Wmax 1.9762x <= 2.0x)
- **ann 23.6054% / SR 3.751429 / MDD -3.6130% / 0 neg years (0/19) / worst year +7.3488%**
- gross 1.0 exact every day (operator cap 1.6: 0 days over, 37.5% headroom)
- turnover 4.03 bp/yr (was 6.45); margin drag 0.00%/yr (was 2.70%)

| metric | ITER20 (gear 1.6) | **ITER21 (gear 1.0)** | delta |
|---|---|---|---|
| **SR (THE objective)** | 3.455068 | **3.751429** | **+0.296361** |
| ann | 36.4150% | 23.6054% | -12.81pp (floor 20% kept, 18% headroom) |
| MDD | -5.9284% | -3.6130% | +2.32pp better |
| worst year | +8.8898% | +7.3488% | still positive |
| neg years | 0/19 | 0/19 | = |
| gross | 1.6 exact | 1.0 exact | further inside the cap |
| margin cost | 2.70%/yr | 0 | removed |
| OOS dSR (5 2-yr bins) | - | +0.362/+0.155/+0.411/+0.328/+0.274 | 5/5 positive |

The OOS result is ANALYTIC, not statistical: removing a constant per-day drag raises SR in
every sub-window by construction. This is stronger than the ITER15 "positive in all
windows" sampling gold standard.

## Why the same weights win again
The gear lever multiplies whatever the weight vector earns; it cannot substitute for it.
The committed ITER20 vector remains the IS-SR argmax of its family at ANY gear <= 1.6, so
the SR-max book is that vector at the plateau edge. The pre-committed alternative (uniform
equal-weight EW12v2, zero fitted parameters) was built and LOST at every gear
(FS SR 3.6665 vs 3.7514 on the flat plateau; OOS bin 2 negative) -- the correlation-aware
fit genuinely dominates naive de-concentration.

## Pre-commit disclosure (campaign/agents/chief/coord/ITER21_SRMAX_EW_GEAR/FINDINGS_PRECOMMIT.md)
Written BEFORE the reveal: 2-point family {EW12v2, committed ITER20 vector} x gear,
admissibility list, anchor requirement, selection rule. Two deviations, both disclosed:
1. The pre-commit fixed g = 1.05 "outside the flat zone does no SR work" -- WRONG on its own
   terms (1.05 > 1.0 pays margin for nothing; SR(1.05) = 3.7138 < SR(1.0) = 3.7514). The
   operating point was moved to the plateau's argmax edge g = 1.0 by the pre-committed
   objective (maximize SR; max-ann tie-break within the flat set). The ADOPTION decision is
   identical at either point (both dominate the incumbent by > +0.25 SR).
2. g = 1.0 was chosen over smaller gears by max-ann tie-break inside the SR-flat set
   [0.88, 1.0] (floor + headroom), not by SR peeking -- SR is bit-identical across the set
   (pinned by test: plateau invariance < 1e-9).

## Independent verification (coordinator, from raw bytes)
1. **Anchor**: build() with the committed vector at gear 1.6 reproduced the ARCHIVED ITER20
   bytes at 1.110e-16 BEFORE any candidate was built (mechanics-exact proof).
2. **Round-trip**: the canonical CLI `--emit-candidate ITER21_SRMAX_GEAR10 --gear 1.0`
   (untouched fit path) emitted the adopted bytes; `--verify` now reports IDENTICAL at
   9.996e-17 with gross 1.000000 exact, margin 0.00%/yr.
3. Weights blob byte-IDENTICAL to the ITER20 vintage (restored from
   ITER20_SRMAX_c30_s70_weights.csv after the emit's float-formatting rewrite; numeric
   maxdev 8.3e-17, sha16 d2d11c92a98683df preserved).
4. CFX4 = 0.0 exactly; Wmax 1.9762x <= 2.0x; 0 neg years; worst year +7.35%.
5. Independent 4-knob identity (test_audit_champ2_round2): champion - archived-leak ==
   shift + costfix + weight-rule + GEAR, telescoping to 1.8e-16.
6. Admissibility: ann 23.61% >= 20% PASS; gross 1.0 <= 1.6 PASS; FS MDD -3.61% >= -7% PASS;
   0 neg years PASS; Wmax 1.98x PASS; CFX4 0 PASS.

## What changed in the repo (all additive; history preserved)
- champion CSV -> ITER21 bytes; prior bytes archived byte-exact as
  archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily_SUPERSEDED_by_ITER21_gear10.csv
  (sha16 766fc0ce9926d793), reproducible via `build(gear=1.6)` / `--gear 1.6`.
- rawew13v2_build.py: GEAR 1.6 -> 1.0 (canonical), ITER21 docstring section,
  ann-max escape hatch now `build(shrink_d=0.98, brwt_cap=None, gear=1.6)`.
- TDD: new campaign/bt/tests/test_iter21_srmax_gear_champion.py (8 tests, RED first --
  5 failed pre-adoption -- then GREEN) pinning bytes/stats/gates/plateau-invariance/
  margin-monotonicity/weights-purity/vintage-repro.
- Re-pin wave (46 RED -> 0): rawew13v2, iter19, iter20 (3), audit_champ2 r1/r2 (4-knob
  identity)/r3/r4/r5/r6, audit_recon_lineage, auditrecon_r2_lineage, camp_borrow r2
  (call-rate-immunity + geared teeth)/r3, camp_cost full_dw/r6/r7, camp_short_r3_census
  (census re-run), energy_family_filter, financing_stress, fwbugs_audit_r3,
  iter17_sleeve_addition (RB_hobr rejection re-anchored: IS +0.32 SR but OOS -1.13pp ann /
  -0.015 SR -- still rejected, now on the objective's own metric).
- CAMP_BORROW_FINANCING_R3.json re-priced per its own fail-closed protocol (new frozen
  extract champion_committed_8559fa55.csv): the gear-1.0 book is CALL-RATE-IMMUNE -- every
  scenario delta is exactly 0.00pp. That degeneracy is the honest result, and the geared
  (1.6) rate ladder retains its teeth in test_camp_borrow_round2 (0.60pp/pp verified).
- CHAMPION_CARD.md regenerated by its generator; 16 gated docs gained additive ITER21
  SUPERSEDE banners (originals snapshotted in AUDIT_CHAMP2/work/pre_banner_snapshot_iter21/);
  STALE_HEADLINES lint extended with the 36.41-generation spellings (current headline is
  computed from the CSV at test time: 23.61%).

## Honest caveats -- READ BEFORE DEPLOYING
1. **THE TRADE**: this book gives up 12.81pp of annualized return (36.42% -> 23.61%) to buy
   +0.296 SR and 2.32pp of MDD. That is what the stated objective (SR-max s.t. ann >= 20%,
   gross <= 1.6) demands -- the 20% floor is met with 18% relative headroom -- but if the
   operator's intent was "run at 1.6 unless told otherwise", the ITER20 vintage is archived
   byte-exact and one command (`--emit --gear 1.6 --force` + re-pin wave) restores it.
2. The champion FILENAME still says GEAR16 (historical path; content is the gear-1.0 book).
   Renaming would break the pin graph -- proposed as follow-up, not done additively here.
3. margin-insensitivity means the financing stress runbook loses its discriminating power
   on THIS book (all scenarios tie). The geared ladder teeth remain pinned; if the operator
   re-gears, the JSON must be re-priced again (the sha gate enforces this).
4. The ann floor now binds in exactly one place: IS-window ann at gear 1.0 is 19.75% (< 20%
   IS, 23.61% FS). The operator floor is a FULL-SAMPLE statement and is met; the IS number
   is recorded here for transparency.
5. Suite state at adoption: 478 baseline + 8 new = 486; 46 re-pin REDs taken to 0 (final
   count below).

## Final suite count
**486 passed, 0 failed** (2026-09-18/19 post-adoption full run, 131s; baseline was 478,
+8 new ITER21 pins; all 46 re-pin REDs resolved).
