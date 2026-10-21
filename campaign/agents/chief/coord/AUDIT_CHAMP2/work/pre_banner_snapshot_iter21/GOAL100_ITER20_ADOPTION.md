# ITER20 ADOPTION — SHARPE-MAX CHAMPION OF RECORD (2026-09-18, coordinator)

## Objective change (operator, 2026-09-18, direct instruction, quoted verbatim)
> "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return
> can't be smaller than 20%."

The campaign objective moved from **ann-max (subject to gates)** to
**Sharpe-max subject to ann >= 20% and gross <= 1.6**. Under that objective the ann-max
champion (ITER19, sha16 7559e82b022c6236, 39.4995% / SR 3.2176 / MDD -6.5232%) is no
longer the argmax; it is archived **byte-exact** and stays reproducible.

## New champion of record
campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
- sha256 766fc0ce9926d793dd582b028558f29b7cf1e5ad4d86475cd8c46507175fd393 (n=4806)
- weights RAWEW13v2_IS_SR_weights.csv sha16 d2d11c92a98683df
- **ann 36.4150% / SR 3.455068 / MDD -5.9284% / 0 neg years (0/19) / worst year +8.89% (2013)**
- gross exactly 1.600000000000 on every day, 0 days over the 1.6 cap (operator hard cap PASS)
- ann 36.42% >= 20% floor PASS (1.8x headroom)
- turnover 6.4493 bp/yr (charged in net, FULL |dW| @6.4bps; margin 4.5%/yr on (1.6-1))

Construction: fit_relw(IS, shrink_d=0.70) + brwt-block (brwt10/7/5) relw-share cap 0.30,
excess redistributed pro-rata on the committed non-block shares, CFX4 pinned 0 -- now the
builder DEFAULT (build()), selected by argmax IS-SR over the pre-committed admissible
grid (same epistemic status as the champion's own shrink selections; the plateau is flat,
FS SR 3.42-3.47 across neighbours -- no cherry-pick edge). The superseded vintage is
reproducible: build(shrink_d=0.98, brwt_cap=None).

## Independent verification (coordinator, 2026-09-18) -- NOT the builder's own report
1. Anchor: canonical builder reproduced the PRIOR champion bytes at 9.996e-17 before any edit.
2. **Rebuild**: the real build() with the ITER20 weight vector (monkeypatched fit) emits
   bytes IDENTICAL to the candidate file at 1.041e-16 -> costs/margin/T+1-causal mechanics
   are genuinely charged; not a cost artifact (the HT_TAIL trap class).
3. Weights provenance: independent reproduction of fit(0.70)+cap(0.30, pro-rata, s=0)
   matches the committed vector at 8.327e-17; raw brwt-block share 0.4605 -> capped 0.3000.
4. CFX4 = 0.0 exactly (the discredited twelvedata vendor feed stays out -- champion invariant).
5. W_MAX: largest weight 0.164682 = 1.976x equal (cap 2.0x) PASS.
6. OOS (>=2017) dSR vs prior champion across the five 2-yr bins:
   **+0.292 / +0.364 / +0.232 / +0.320 / +0.425 -- 5/5 POSITIVE**; dAnn -0.39 / +1.59 /
   +3.48 / +5.27 / +2.68 pp. (The 09-18 frontier memo's own 5-window split showed
   3 positive / 2 flat-to-negative; this 2-yr split is stronger. Both are broad.)
7. Admissibility (pre-committed): IS MDD -4.11% >= -6% PASS, IS ann 29.75% >= 20% PASS,
   0 IS neg years PASS, FS MDD wall -5.93% >= -7% PASS.

## Why adoption is correct under the stated objective
| metric | prior (ann-max) | new (SR-max) | delta |
|---|---|---|---|
| **Sharpe** | 3.2176 | **3.4551** | **+0.2375 -- THE objective** |
| ann | 39.4995% (archived prior vintage) | 36.4150% | -3.08pp (floor 20% not binding) |
| MDD | -6.5232% | -5.9284% | +0.59pp better |
| worst year | +5.6250% | +8.8898% | better |
| OOS ann | 43.15% | 42.76% | -0.39pp |
| gross | 1.6 exact | 1.6 exact | = |

The -3.08pp ann is the price of de-concentration (brwt block 76% -> ~58% of gross) and is
the objective-relevant trade the operator asked for. The 09-17 memos had already identified
brwt-cap de-concentration as the only legitimate lever left (RESEARCH_AGENDA 2a) and the
09-17 multi-agent hunt sweep confirmed no decorrelated alpha exists on disk (all REJECTs).

## What changed in the repo (all additive, history preserved)
- campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv + RAWEW13v2_IS_SR_weights.csv
  -> ITER20 bytes (prior bytes archived as archive_*_SUPERSEDED_by_ITER20_srmax.csv,
  daily sha16 7559e82b022c6236 / weights be2265ff026dafb3).
- campaign/scripts/rawew13v2_build.py: SHRINK_D 0.98->0.70, new W_BRWT_CAP=0.30 +
  apply_brwt_cap(), build(..., brwt_cap=None) escape hatch, --brwt-cap CLI,
  emit-safety extended (non-canonical cap needs --force). --verify = IDENTICAL
  (bytes 1.1e-16 / weights 8.3e-17) -- the champion has a checked-in repro path again
  (closes the D15-class gap for this vintage).
- TDD: new campaign/bt/tests/test_iter20_srmax_champion.py (7 tests, RED first, then GREEN)
  pins bytes/stats/gross/floor/CFX4/Wmax/vintage-repro/objective-dominance.
- Re-pinned: iter19 (shrink + stats), iter17_wmax (composite), round2 (independent fit
  composite + weights sha d2d11c92 + ann/SR/MDD/corr pins + two-sided weight-rule
  materiality), round6 (exact stats + blend deltas + 8e delta -0.1265pp),
  recon_lineage (ann pin), auditrecon_r2_lineage + pin_mutations (composite),
  camp_borrow_round3 (sha16/BASE_ANN/BASE_SR_D/BASE_MDD), financing_stress (ann/sr_d),
  energy_family_filter (champion + brwt-screen pins -- NOTE the brwt-only screen now lands
  at MDD -7.53%, OUTSIDE the -7 wall: screen artifact, NOT a candidate),
  iter17_walkforward (rejection re-anchored to the objective: WF raises ann +2.51pp via
  uncapped concentration but LOWERS SR -0.167/-0.191 on both arms -> still rejected),
  rawew13v2 (IS-only pin flows through the composite).
- Regenerated artifacts: CHAMPION_CARD.md (generator), CAMP_BORROW_FINANCING_R3.json
  (re-anchored per its own fail-closed protocol; new frozen extract
  champion_committed_766fc0ce.csv; reprice_history appended; closed-form scenario pins
  unchanged), census JSON re-run.
- Docs: 15 gated docs prefixed with the additive ITER20 SUPERSEDE banner (originals
  snapshotted in AUDIT_CHAMP2/work/pre_banner_snapshot_iter20/); STALE_HEADLINES gained
  the 38.11/39.50 generations; round3 a4 headline pin -> 36.414968%.

## Honest caveats
1. The gain is broad but not uniform: the frontier memo's own 5-window OOS split showed
   3 positive / 2 flat-to-slightly-negative dSR windows (its dSR -0.155 window is dAnn
   +5.88pp). The 2-yr-bin split is 5/5 positive dSR. This is NOT the ITER15
   "positive in all windows" gold standard on every slicing.
2. Selection is IS-SR argmax on a flat plateau -- the point chosen is not special among
   admissible neighbours (that IS the robustness claim).
3. verify_champion.py:65 still hard-codes SHRINK_D=0.62 (pre-existing defect D15/#111);
   it is now stale for the new champion in a DIFFERENT way (the champion family is
   shrink 0.70 + cap). The authoritative repro path is rawew13v2_build.py --verify
   (IDENTICAL) and test_iter20_srmax_champion.py; fixing verify_champion.py remains
   open follow-up work.
4. Suite state at adoption: 471 baseline green -> 33 red post-swap -> all re-pinned;
   final full-suite count recorded in the standup log of 2026-09-18.
