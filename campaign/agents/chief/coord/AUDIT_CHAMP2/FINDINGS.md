# FINDINGS — AUDIT_CHAMP2 (independent champion replica-audit)

Agent: AUDIT_CHAMP2 · Round 1 · 2026-09-06/07
Scope per charter: adversarial re-verification of campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv from the 13 RAW sleeve files + builder (rawew13v2_build.py), all 7 constraints, auditing audit_harness_newconstraints.py itself too. Nothing trusted: committed CSV, docs, and the prior "7/7 PASS" harness all re-derived from first principles.

## Verdict

**6 of 7 gates PASS. C6 (T+1 no lookahead) FAILS** — a real, quantified same-day leak in the committed champion construction (-0.99pp/yr of ann when made causal). Byte-repro, leverage, margin, 0-neg-years, costs, and shortability all verified clean by independent reconstruction. The prior harness's C2 was proven vacuous and C6 was proven to test nothing — both now replaced with real fail-closed checks (TDD).

## What was tried, with exact numbers

### 1. Independent from-scratch rebuild (work/rebuild_indep.py)
Re-implemented the documented construction (IS-SR^0.55 rel weights, NAV-drift row-normalized slot weights, FULL |dW| turnover, 6.4bps, margin 4.5% on (1.6-1)) WITHOUT importing builder code.
- Pool aligned: 4805 days x 13 sleeves, 2008-03-31..2026-08-27; 5634 NaN cells (sparse sleeves earn 0 on foreign calendar days — documented behavior); min daily ret -0.2179 (NAV never breaks sign).
- **C7 byte repro PASS**: max|rebuilt - committed| = 9.996e-17 < 1e-12 over all 4805 rows; weights file maxdev 2.220e-16. Builder's own `--verify` independently says IDENTICAL (9.996e-17 / 2.220e-16).
- Metrics recomputed: **ann_geo 40.8413%**, **SR_d 3.3390**, **MaxDD -6.80%** (arith/log-approx variant -6.94%), **neg years 0/19**, worst year +8.89% (2013), vol 10.42%.
  - Doc reconciliation: iter10 memo's "40.88%" is the STALE pre-iter11 number (half-turn cost); the iter11 memo's 40.84% matches my rebuild exactly. The 0.04pp gap compounds exactly from the +2.468bp/yr full-|dW| cost fix. Claim reconciled, not an error.
- **C1 PASS**: charged cost = FULL |dW| x 6.4bps — cumulative 94.10bp over 4805 days = 4.935bp/yr avg; half-turn variant would differ by 2.468bp/yr, absent. No 0.5 factor anywhere (verified in builder source + reconstruction residual 0). Note: builder `--verify` prints "turnover 0.0494 bps/yr" — that number is in PERCENT/yr (its format string multiplies by 100); true figure is 4.935bp/yr. The iter10 doc's "0.02" is the stale half-turn equivalent. Cosmetic labeling bug, flagged to coordinator.
  - Minor: first-row entry turnover (10.2bp one-time) uncharged because `Wg.diff()` row 0 is NaN->0 — consistent with committed semantics, disclosed.
- **C2 PASS** (by independent reconstruction, not the harness's tautology — see #3): gross port reconstructed from sleeve frame + weights; net == port - |dW|*6.4bps - (1.6-1)*4.5%/252 with residual 0.00e+00. Margin drag 2.7000%/yr.
- **C3 PASS**: gross = 1.600000000000 every day (mean = max = 1.6 exactly), 0 days > 1.6, min slot weight 0.0000 (no negative slots, so |.| never inflates gross).
- **C4 PASS**: 0/19 negative calendar years; min year +8.89% (2013); all 19 years positive, range +8.89%..+172.62% (2020).
- IS/OOS claims verified: IS ann 36.9470% (doc 37.0%), OOS ann 44.4712% (doc 44.5%), halves SR 3.78/3.10 (doc 3.78/3.11).
- **C6b PASS** (weight-fitting honesty): scaling ALL post-IS returns x0.5 changes no rel weight (max|d relw| = 0.00e+00) — the IS-SR weights are genuinely IS-only; no OOS leakage into weight fitting. relw: brwt10 1.888, brwt7 1.918, brwt5 1.889, brwt15 1.698, C5ng 1.600, C5ngsum 1.384, QAxasts 0.990, dualmom 0.994, diescrack 0.948, A5r2 0.864, a6r7 0.750, carryv2 0.651, CFX4 0.000.

### 2. C6 — REAL T+1 perturbation test: **FAIL** (the material finding)
Injected deltas into single sleeve/day returns; under T+1 the only allowed response of port_t is Wg_{t-1,i}*delta.
- Committed construction responds MORE: perturbation ratios 0.9798-1.0473 across 5 (sleeve, delta) probes (want 1.000000). Excess-response metric: 1.518e-02 weight-units (want <1e-6).
- **corr(dW_t, r_t) = 0.7846** cross-day (0 expected under T+1) — day-t weights chase day-t returns.
- Cause (builder line 67-71): nav = cumprod(1+r) INCLUDES r_t; Wg_t = f(nav_t); port_t = Wg_t * r_t.
- Economic size (causal rebuild with nav.shift(1), all else identical): **ann 40.8413% -> 39.8510% (-0.99pp), SR 3.339 -> 3.296, MaxDD -6.80% -> -6.84%, neg years 0/19 unchanged**; same-day-weight PnL term = +0.7815%/yr. No constraint-gate outcome flips (still 0 neg, MDD < -7% wall, lev 1.6), so this is a DOCUMENTED OVERSTATEMENT, not a champion-killer.
- **C6b confirms the leak is confined to the drift stream**, not the SR fitting.
- Cross-validation: an independent prior audit (AUDIT_RECON R1) had already xfail-documented the same leak at the same magnitude (test_rawew13v2.py::test_champion_portfolio_return_uses_lagged_weights_auditrecon, "ann 39.85% vs committed 40.84%"). Two independent reconstructions agree to 4 decimal places.
- NOT FIXED in the builder: fixing it re-emits the committed champion CSV (a semantics change), which the charter reserves to the coordinator. Instead the failing property is pinned as an xfail(STRICT) test, so any builder fix without lifting the marker fails the suite (fail-closed). COORDINATOR DECISION REQUESTED: re-emit wave (honest ann 39.85%) vs keep committed (disclosed overstatement).

### 3. Auditing the auditor — audit_harness_newconstraints.py had 2 vacuous gates (FIXED, TDD)
Prior state claimed "7/7 PASS". Both defects proven with counterexamples before fixing:
- **C2 was a tautology**: it reconstructed port FROM net itself (port := net + costs + margin_const), so the residual is margin_const for ANY series. Counterexample: a builder charging ZERO margin passed with residual 3.52e-19. The "margin verified" claim was empty. FIXED: independent gross reconstruction from raw sleeve frame + weights (residual now 0.00e+00 on the real builder, either admissible weight construction accepted).
- **C6 was `return True`**: the T+1 gate tested nothing and blessed the leaking construction with the false comment "T+1 verified". FIXED: real perturbation test (excess-response metric in weight units, handles zero-weight sleeves fail-closed) + corr(dW_t,r_t) + auto-detects which weight construction the builder uses by matching its returned turnover stream. On the real builder it now reports FAIL (see #2) — the harness's "7/7 PASS" was partly an artifact of these two vacuous gates.
- **C5 strengthened** (was name-substring matching): now asserts 13/13 instrument classes with evidence, dualmom LONG-ONLY, min slot weight >= 0, and materiality (top gross shares brwt10 23.7%, brwt7 20.8%, brwt5 18.2%).
- TDD evidence: new test file campaign/bt/tests/test_audit_champ2_round1.py — RED phase 3 failed (C2 accepts no-margin builder; C6 accepts same-day-weight builder; C6 blesses the real leaking champion builder) -> after harness fix GREEN 5 passed + 1 xfailed. Full suite: **79 passed, 2 xfailed** (baseline before this round: 72 passed, 1 xfailed; +7 tests, 1 new xfail).

### 4. C5 shortability — PASS (substantively verified, not just name-matched)
Inspected every sleeve generator/meta:
- brwt15/10/7/5 (Brent-WTI futures spread), diescrack (HO-CL crack spread), CFX4 (FX crosses; weight exactly 0), a6r7 (2Y treasury TR), QAxasts (oil/gold/UST/USD/VIX), C5ng/C5ngsum (Henry Hub), carryv2 (GLD/brent), A5r2 (SPY LONG/flat only): all futures/ETF/commodity/rates/FX = fungible-short instruments.
- dualmom is a 298-name SINGLE-NAME EQUITY panel, but its construction is LONG-ONLY top tercile (long when FF-gate on, else flat) — no single-name short is ever required, so the constraint "no unmodeled single-name short exposure" holds.
- Portfolio-level: all slot weights >= 0 every day (min 0.0000) — no net-short slots; the only shorting is inside sleeves, on fungible instruments (borrow 0.5%/yr already charged inside sleeve net files per TRADE_RECORD_STANDARD).
- Disclosed residual: QAxasts' VIX leg is SHORT VIX on 35.1% of days via a SYNTHETIC spot-VIX return (roll-free, zero roll carry) — fungible via VIX futures per its meta, conservative for the short side, and only 2.16% of portfolio gross (sleeve gross shares: brwt10 23.66%, brwt7 20.75%, brwt5 18.17%, brwt15 13.10%, C5ng 7.85%, C5ngsum 5.97%, dualmom 2.47%, QAxasts 2.16%, diescrack 1.71%, A5r2 1.63%, a6r7 1.43%, carryv2 1.10%, CFX4 0.00%).
- Note: brwt/diescrack/C5ng trade FRED spot proxies (roll-free) rather than actual futures strips; roll/basis risk disclosed in sleeve metas — tradeable-as-futures-spread, so C5 passes on fungibility, with the proxy caveat carried from the sleeve docs.

## Files touched (this round)
- work/rebuild_indep.py (new) — independent rebuild + 7-gate evidence.
- campaign/bt/tests/test_audit_champ2_round1.py (new) — 6 tests (RED->GREEN), incl. xfail(STRICT) pinning the C6 leak.
- campaign/audit_harness_newconstraints.py — C2/C6 replaced with real fail-closed checks; C5 strengthened. NO committed champion file touched; builder untouched; champion semantics unchanged.
- Committed champion CSV + RAWEW13v2_IS_SR_weights.csv: byte-identical to git HEAD (b722736); unmodified.

## Coordinator decisions requested
1. C6 re-emit wave: causal (nav.shift(1)) champion = ann 39.85%, SR 3.30, MDD -6.84%, 0/19 neg, all gates still pass. Committed champion currently overstates ann by +0.99pp (and +0.04pp of that predates iter11's fix). Until then the xfail(STRICT) keeps the leak fail-closed in CI.
2. Cosmetic: builder --verify prints turnover in percent/yr labeled "bps/yr" (0.0494 vs 4.935bp/yr); iter10 memo still carries stale pre-fix numbers (40.88% ann, 0.5|dW|, 0.02).

## Bottom line
The champion is NOT a fabrication: all hard constraints (costs, margin, leverage, 0-neg-years, byte-repro, shortability) survive an adversarial independent rebuild at 1e-16 tolerance. But its headline 40.84% ann embeds a +0.99pp same-day lookahead in the weight-drift stream that the previous harness's vacuous C6 ("return True") and tautological C2 failed to catch; honestly lagged, it is a 39.85% ann / 0/19 neg / -6.84% MDD champion. All gates now have teeth.

ROUND 1 DONE

---

# ROUND 2 (2026-09-07) — fresh C1-C7 audit of the RE-EMITTED causal champion

Scope per charter R2: (a) re-run C1-C7 on the post-re-emit tree (commit 8f98da1, champion re-emitted 2026-09-07 00:45 with builder nav.shift(1)); (b) byte-repro + weights-file identity pre/post re-emit; (c) provenance of the untracked GOAL100_TRUTH20Y files + stale-claim sweep; (d) pin new-vs-archived champion difference to EXACTLY the causal-vs-leak mechanism. Nothing trusted: both reconstructions (work/rebuild_r2.py, work/r2_audit_fresh.py) re-implement the construction WITHOUT importing the builder.

## Verdict

**R2 = PASS across the board. (a) 7/7 gates PASS with C6 now genuinely causal; (b) byte-repro to 1e-16 and the weights file byte-identical pre/post re-emit; (c) TRUTH20Y provenance FLAGGED (no builder in tree, pool files missing, breaches -7% MDD + 1 neg year, JSON convention gap); (d) mechanism pin PROVEN at |diff-of-diffs| = 2.5e-17.** The re-emitted champion is the honest construction: ann_geo 39.8510%, SR_d 3.2964, MaxDD -6.84% (geometric NAV), 0/19 negative years, worst year +8.61% (2013), IS 35.95% / OOS 43.49% (OOS>IS, no overfit).

## (a) C1-C7 on the current tree — exact numbers

- **C7 byte-repro PASS**: my from-scratch causal rebuild vs committed CSV: 4805/4805 rows, maxdev **9.996e-17**; weights file maxdev **2.220e-16**. Builder's own `--verify` agrees (9.996e-17 / 2.220e-16) — and its turnover line now prints the corrected unit: **4.9398 bp/yr** (R1's percent/yr mislabel fixed in builder line 112).
- **C1 FULL |dW| @ 6.4bps PASS**: charged turnover mean|dW|/day 0.003063 -> 4.9398 bp/yr; independent full-identity residual (my port - my |dW|*6.4bp - margin vs committed) = **9.996e-17**. Half-turn counterfactual would lift ann 39.8510% -> 39.8854% (+3.445bp/yr) — absent from the committed file. Disclosed residual: day-1 entry turnover 0.00bp charged (Wg.diff() row0 NaN->0; with shift(1) the day-1 weights are the no-history init, so nothing is traded into them — cleaner than R1's 10.2bp question).
- **C2 margin PASS, now discriminating (not tautological)**: residual @4.5% on (1.6-1) = **0.000e+00**; controls DETECT wrong hypotheses: @0% margin residual = 1.071e-04, @9% = 1.071e-04 (exactly the daily drag 1.0714e-04 = 0.6*0.045/252). C2 VERDICT requires all three, so a zero/wrong-margin builder now fails.
- **C3 leverage PASS**: gross mean = max = min = **1.600000000000** exactly, 0 days > 1.6+1e-9, min slot weight 0.000000 (no negative slots).
- **C4 PASS**: 0/19 negative calendar years; range +8.61% (2013) .. +167.17% (2020).
- **C5 shortability PASS** (harness): 13/13 instrument classes, dualmom LONG-ONLY, top gross shares brwt10 23.7% / brwt7 20.7% / brwt5 18.2%, CFX4 weight 0.00. All 13 sleeve input files verified clean vs git HEAD (no silent sleeve swap in the re-emit).
- **C6 T+1 PASS — the headline fix**: 15-probe perturbation (5 sleeves x 3 days) max excess response **7.047e-16** weight-units (R1 leak was ~1e-2; requirement <1e-6); single-probe examples: brwt15 +0.010 -> obs 2.305781e-03 = exp exactly; CFX4 -0.020 -> obs 0 (zero-weight sleeve handled); A5r2 +0.050 -> obs = exp to 0. **corr(dW_t, r_t) = -0.0277** (R1 leak was +0.7846; 0 expected under T+1). The champion's day-t weights are now a function of data through t-1 only.
- Harness summary MDD -6.99% vs my -6.84%: convention difference, not an error — harness prints cumsum-approx DD (overstates vs geometric NAV); both sides disclosed here.

## (b) Byte-repro + weights identity pre/post re-emit

- Champion CSV blob changed across the re-emit commit 8f98da1 (927c837 -> ca7a4da, 4805/4805 lines rewritten); working tree clean vs HEAD.
- **RAWEW13v2_IS_SR_weights.csv byte-identical pre/post re-emit**: sha256 `8107aab3...` at b722736 = current tree = measured in work/; git diff across 8f98da1 = empty. As charter reasoned: relw = max(IS_SR,0)^0.55 on <2017-01-01 data, never a function of nav. Pinned in test_audit_champ2_round2.py::test_d_weights_file_unchanged_by_reemit against the b722736 blob hash.
- Archive integrity: archived leak CSV blob 927c837 is EXACTLY the pre-re-emit champion blob — git preserved the old champion byte-for-byte as the archive; archive sha256 prefix 0516e543 matches the re-emit addendum's claim.

## (d) The re-emit differs by EXACTLY nav.shift(1) — pinned (charter d)

Four-corner identity, all from independent rebuilds (same 13 raw sleeve files, same relw, only lag differs):
- rebuilt CAUSAL (lag=1) vs committed champion: maxdev **9.996e-17** -> committed IS the causal construction.
- rebuilt LEAKY (lag=0) vs archived leak CSV: maxdev **9.996e-17** -> archive IS the leaked construction.
- rebuilt LEAKY vs committed champion: maxdev **3.962e-03** (DIFF, as required) — matches charter's pin ~3.96e-3.
- corr(committed, archived) = **0.999881** — matches charter's ~0.99988.
- **|diff of diffs| = 2.515e-17**: (my causal - my leaky) == (committed - archived) to machine zero. The ONLY knob that moved in the re-emit is the 1-day shift. Pinned with mutation evidence (shift(2), P 0.55->0.60, BPS 6.4->5.0 all detected) in test_audit_champ2_round2.py::test_d_mechanism_is_exactly_nav_shift_1.
- Economics: leak ann 40.8413% vs causal 39.8510% = **-0.99pp**; annualized same-day-weight PnL advantage of the leak = **+0.7142%/yr**; mean daily dev +2.834e-05. R1's numbers reproduced to 4 decimals by the fresh code path.

## (c) TRUTH20Y provenance + stale-claim sweep — FLAGGED (the round's one adverse finding)

- **Builder NOT in tree**: `grep -rln GOAL100_TRUTH20Y --include=*.py` over the repo matches only my own R2 test. G4_detrun/FINDINGS.md describes the *concept* (honest max span 2006-10-02..2026-08-28 = 19.8y, "0.2y short, disclosed") but the writing script is absent — the 3 CSVs + JSON (all untracked, Sep 1 16:07) are NOT reproducible from the current tree.
- **Pool files missing**: JSON pool lists 14 sleeves incl. A5r7, A1credit, XGB1y and six "E" de-truncated variants (a6r7E, QAxastsE, carryv2E, C5ngE, C5ngsumE, brwt15E) — NONE exist on disk under any name pattern I could find (searched campaign/agents + repo-wide). XGB1y_deploy.csv in results/sleeve_library correlates only **+0.2106** with TRUTH20Y BAL, so it is not the same series. The "E" variants are unverifiable.
- **Stats reconcile with its OWN JSON** (test_c_truth20y_json_bal_reconciles_with_its_csv): BAL ann arith 53.0327% vs JSON 53.0, SR 5.5635 vs 5.56, MDD geo -7.88% vs -7.9, negy 1 (2006) vs 1 — all within tolerance. AGGRESSIVE 59.58/5.59/-7.86/1, SAFE 46.49/5.51/-7.91/1. Span 2006-10-02..2026-08-28, n=4990 = 19.90y, matching G4's claim.
- **BUT it is not a constraint-passing champion**: geometric ann is **69.09%** (the 53.0 headline is simple arithmetic ann — a +16.1pp convention gap), and it **breaches the -7% MaxDD wall (-7.88%) and has 1 negative year (2006)**. Correlation to the champion on 4616 overlap days = 0.5750 — a different animal. New pin test_c_truth20y_bal_is_not_a_constraint_passing_champion locks all of this.
- **Stale-claim risk in results/-adjacent docs**: campaign/GOAL100_ITER11_COORDINATOR.md's main table still bills 40.84% as "HONEST CHAMPION" — BUT its own ADDENDUM (2026-09-07) supersedes it with the correct 39.85% headline, archive sha, and builder fix. My grep sweep found no post-re-emit doc quoting 40.84% as the current champion; every remaining 40.84 occurrence is properly framed (archive/leak/prior). blend_report.md (Aug 28) predates the champion and claims nothing about it. Risk is LOW but the iter11 main-table title remains a future-misquote hazard for anyone reading only the top half.

## Files touched (this round)

- work/rebuild_r2.py + work/r2_audit_fresh.py (pre-existing, re-run fresh) — independent rebuilds + all-gate evidence.
- campaign/bt/tests/test_audit_champ2_round2.py — 7 tests now (was 6): added test_c_truth20y_bal_is_not_a_constraint_passing_champion (RED-first reasoning documented in its docstring; measured values pinned: mdd -7.88%, negy>=1, geo 69.09%, arith 53.03%, pool corr 0.575).
- Committed champion CSV, weights CSV, archive CSV, builder, all 13 sleeve files: **unmodified** (verified clean vs HEAD 8f98da1).

## Test state

Full suite: **149 passed** (R1 end state 148; +1 new R2 pin). R2 charter items: (a) 7/7 PASS, (b) PASS, (d) PASS pinned, (c) FLAGGED — coordinator decision requested on TRUTH20Y (builder + pool files are unreproducible from tree; treat as external/legacy artifact, do not quote as champion) and optionally on relabeling the iter11 memo main table.

ROUND 2 DONE


---

# ROUND 3 (2026-09-07) — docs integrity + weights audit (charter a/b/c)

Scope per charter R3: (a) stale-claim lint TDD (RED first, ADDITIVE supersede banners, GREEN with
before/after grep evidence); (b) champion weights CSV vs 13 sleeve builders' weights (max dev per
column, tol 1e-10, drift = costfix-delta not new-bug); (c) CHAMPION_CARD.md generated from the
builder + byte-identical pin test. GATES_CONTRACT.md + DEAD_IDEAS.csv read FIRST; no dead family
re-tested, no dead signal re-tuned (this round touches construction/docs only, zero new signals).

## Environment finding first (material for the coordinator)

The working tree is AHEAD of HEAD 8f98da1 with an UNCOMMITTED costfix re-emit wave (mtimes
06:10-07:28): 4 sleeve inputs regenerated (brwt15/QAxasts/dualmom/diescrack), champion + weights
re-emitted 07:28, and multiple other agents' uncommitted work in flight (test_beats_passive.py
expects a bt/beats_passive module not yet written: 12 of its tests RED pre-module). Also, a
CONCURRENT agent session inserted the iter10/iter11 SUPERSEDE banners at 10:16, mid-my-round.
I verified their work rather than duplicating it: diffs vs HEAD are insertions-only
(GOAL100_ITER10_WEIGHTED_CHAMPION.md +5/-0, GOAL100_ITER11_COORDINATOR.md +24/-0), banner numbers
match my independent computation exactly, and I rebuilt TRUE pre-banner snapshots (git HEAD blob +
the 00:48 uncommitted addendum; both snapshots verified to contain 0 "SUPERSEDE" occurrences) in
agents/chief/coord/AUDIT_CHAMP2/work/pre_banner_snapshot/ (sha256:16 iter10 c673d89de5a85426,
iter11 583d0d0fa3943ad8; the 10:20 first-cut snapshots were polluted and were replaced).

## (a) Stale-claim lint — PASS (RED -> additive banners -> GREEN)

- RED evidence (before banners, exact test output): 3 offender lines in 2 gated docs —
  GOAL100_ITER10_WEIGHTED_CHAMPION.md:11 "| **ann (geo)** | 28.89% | **40.88%** |" (main table);
  GOAL100_ITER11_COORDINATOR.md:24 "| ann (geo) | 40.84% |" (the R2-flagged future-misquote hazard,
  now realized as a lint RED); GOAL100_ITER11_COORDINATOR.md:97 "NEW HONEST HEADLINE: ann 39.85%"
  (the 00:45 causal re-emit itself, superseded by the 07:28 costfix re-emit). 3 failed / 5 passed.
- Lint design: gated docs = campaign/*.md + campaign/results/*.md; history paths (FINDINGS/
  STANDUP/CHARTER/LOG) exempt. A stale headline (40.84/40.88/40.8413/39.85) is an offender only if
  the line lacks framing AND the doc lacks a SUPERSEDE banner naming the CURRENT headline — which
  is COMPUTED from the champion CSV at test time (test_a4 pins 39.687317), so any future re-emit
  auto-REDS every stale banner. TRUTH20Y rule: any mention without provenance/breach framing REDs
  (it is not a champion: MDD -7.88% breaches -7%, 1 neg year 2006, no builder in-tree — R2).
- After banners: 8/8 GREEN. After-grep: every remaining stale mention is banner-exempt
  (iter10:3, iter11:3-4) or a lineage disclosure; TRUTH20Y appears in ZERO gated docs.
- Charter compliance: banners are ADDITIVE (verified insertions-only vs HEAD); history not rewritten
  (originals preserved in pre_banner_snapshot/).

## (b) Weights-vs-builder cross-check — PASS (drift = costfix-delta, attribution EXACT)

- claim1: committed RAWEW13v2_IS_SR_weights.csv vs builder relw(): max dev **2.220e-16** across all
  13 columns (tol 1e-10) — worst column brwt7 at 0.000000000000 printed; identity to machine zero.
- claim2: vs git-HEAD (8f98da1) weights blob, movers = exactly {brwt15 -0.040126, diescrack
  -0.032070, QAxasts -0.007740, dualmom -0.005128}; the other 9 columns are EXACTLY 0 delta.
  Mechanism: the 4 regenerated sleeves have lower IS-SR (brwt15 2.6198->2.5084, diescrack
  0.9077->0.8526, QAxasts 0.9818->0.9679, dualmom 0.9896->0.9803; all others unchanged), so
  relw = max(IS_SR,0)^0.55 drops only in those columns.
- claim3 (attribution, not just correlation): rebuilding the champion with ONLY the 4 git-HEAD
  sleeve blobs substituted reproduces the HEAD champion to **9.996e-17** (ann 39.8510% both sides)
  — i.e. 100% of the champion drift 39.8510% -> **39.6873%** (-0.164pp) is the 4-sleeve costfix;
  zero new knobs. Evidence script: work/r3_costfix_attribution.py (saved, rerunnable).
- Current champion stats (recomputed, also on CHAMPION_CARD.md): ann_geo 39.6873%, SR_d 3.2887,
  MaxDD -6.7894% (inside -7% wall), 0/19 neg years (worst +8.34% 2013), turnover 4.9615 bp/yr,
  margin 2.70%/yr, gross 1.6 exact / 0 overshoot days, builder --verify IDENTICAL (9.996e-17).

## (c) CHAMPION_CARD.md — PASS (generated + byte-identical pin with teeth)

- RED first: both card tests failed on the pre-fix tree ("card generator missing" /
  FileNotFoundError) — captured before implementation.
- New campaign/scripts/champion_card.py: renders the card from build() + committed files. FAILS
  CLOSED: refuses to emit if builder-vs-committed champion maxdev >= 1e-12. Deterministic (no
  timestamps; two --stdout runs byte-identical). Includes sha256:16 of champion (511f384fe53b60ce),
  weights (4e83acfb12599b61), archive (0516e543615c0fc6 — matches the R2-verified archive sha).
- Card content: CURRENT headline (39.69% / 3.2887 / -6.79% / 0 neg / 1.6x / 4.9615bp/yr / 2.70%
  margin; IS 35.66% vs OOS 43.45%, OOS>IS) + SUPERSEDED lineage table (40.84 leak -> 39.85 causal
  pre-costfix -> 39.69 current) + per-sleeve relw + input paths + reproduce commands.
- Pin test (test_c_card_exists_and_is_byte_reproducible_from_its_generator): regenerates via
  --stdout and requires byte-identity with the committed card, plus determinism across runs.
  TEETH VERIFIED BY MUTATION: hand-editing the card's ann ("39.69%"->"40.00%") -> test RED;
  restoring the generated bytes -> GREEN. 8/8 round-3 tests GREEN; all 30 tests across
  test_audit_champ2_round{1,2,3} + test_rawew13v2 GREEN together.

## Honest negatives / flags for the coordinator

1. FULL bt suite is NOT green on this tree: 13 failed / 236 passed. 12 failures =
   test_beats_passive.py (another agent's TDD-first RED phase: imports bt/beats_passive, module
   not yet written — mtime 08:22, after the 07:28 re-emit); 1 = test_camp_cost_r2.py
   ::test_champion_pool_has_no_unreemitted_half_turn_sleeves FAILING BY DESIGN (CAMP_COST's own
   fail-closed flag: brwt10/5/7 are still half-turn cost convention, byte-reconstruction fails at
   maxdev 1.3e-01 vintage drift, coordinator must rebuild from generator). None of the 13 read my
   files or the champion; my 8 + all prior audit pins are GREEN. But the coordinator should know
   the campaign suite is red on this tree, and WHY.
2. CHAMPION-SPECIFIC (the 3 sleeves above are IN the champion pool): brwt10/brwt7/brwt5 = 62.4%
   of gross (23.7+20.7+18.2%) still charge 0.5*|dW| @ 6.0bps inside their sleeve net files. If
   rebuilt at full |dW| @ 6.4bps, the champion headline will drop a bit further — the current
   39.69% is therefore still an UPPER BOUND, not a floor. Flagged; fix belongs to CAMP_COST/
   coordinator (not my charter to re-emit).
3. DEAD_IDEAS.csv: charter says 90 rows; file has 95 data rows (post-wave; coordinator-added rows
   landed mid-round). Contains 1 exact duplicate row ("overnight/intraday decomposition harvesting
   (twelve_big)" x2, present in HEAD too). Hygiene flag only, not altered by me.
4. The 07:28 costfix re-emit (champion+weights+sleeves) is still UNCOMMITTED. Everything in this
   round audits the working tree; a git revert/checkout would silently flip the champion back to
   the 39.85% blob while test_a4 (pinned to 39.687317) would RED — fail-closed, but the wave
   should be committed.

## Files touched (this round)

- campaign/scripts/champion_card.py (NEW, generator) + campaign/CHAMPION_CARD.md (NEW, generated).
- campaign/agents/chief/coord/AUDIT_CHAMP2/work/r3_costfix_attribution.py (NEW, evidence script).
- campaign/agents/chief/coord/AUDIT_CHAMP2/work/pre_banner_snapshot/{iter10,iter11}.md (NEW, true
  pre-banner states; replaces the polluted 10:20 first cut).
- campaign/bt/tests/test_audit_champ2_round3.py: pre-existing untracked file authored by a prior
  AUDIT_CHAMP2 session (09:23, before my round); I verified its RED faces, its teeth (mutation
  test on the card pin), and drove it to GREEN. Not modified.
- GOAL100_ITER10_WEIGHTED_CHAMPION.md / GOAL100_ITER11_COORDINATOR.md: banners inserted by a
  CONCURRENT agent at 10:16 (insertions-only vs HEAD, verified); I did not edit them.
- Committed champion CSV, weights CSV, builder, 13 sleeve files: untouched by me (verified:
  builder --verify IDENTICAL pre/post round).

ROUND 3 DONE
---

# ROUND 4 (2026-09-08) — fleet drained; stale-prose hygiene + card sync (charter a/b)

Scope per charter R4: (a) re-run verify_champion via the NEW canonical wrapper
verify_champion_r3_cmd.sh + regenerate CHAMPION_CARD.md; (b) sweep campaign top-level
markdown for remaining un-bannered stale headline quotes and banner them (insert-only).
GATES_CONTRACT.md + DEAD_IDEAS.csv (120 data rows, 0 dups; charter said 108 — coordinator
rows landed since; includes the 2026-09-08 HUNT_FXCARRY2-R4 provenance-note row) read FIRST.
No dead family re-tested; no new signals; docs-only round.

## (a) verify_champion via canonical wrapper — 7/7 PASS + card byte-identical

- `bash campaign/bt/verify_champion_r3_cmd.sh /tmp/vc_r4.json` -> EXIT 0, "ok": true,
  errors []. ALL 7 checks ok: weights_repro (maxdev 2.220e-16), byte_repro (1.110e-16,
  tol 1e-12), cost_reconciliation (full_dw; implied/full ratio 1.0000000000008158; charged
  5.2622 bp/yr; max_dev_half 1.680e-05 => half-turn hypothesis REJECTED), causality
  (nav.shift(1) matched; sameday dev 4.927e-03 confirms the old leak is absent; truncation
  7/7 probes dev 0.0), gross (max 1.6000000000007, 0 days > 1.6, margin 2.70%/yr exact),
  yearly (0 neg, worst +7.310%), mdd (-6.6922% inside -7% wall).
- Headline confirmed against charter of record: ann_cagr 37.1954% / SR 3.1810 /
  MDD -6.6922% / 0 neg years / n=4805 (2008-03-31..2026-08-27). IS/OOS: 33.48%/40.65%
  per card; OOS > IS.
- CHAMPION_CARD.md regenerated via champion_card.py (PYTHONPATH=campaign needed; bare run
  ModuleNotFoundError 'scripts' — footgun, not a bug): byte-identical across regen AND
  identical to committed HEAD; card sha 356e40d682c5ec72; card's embedded sha pins match
  live files (champion 4358dfab95679b97, weights 149164b3b01aa110, archive 0516e543615c0fc6).
- Builder --verify (rawew13v2_build.py): champion 9.996e-17 IDENTICAL / weights 2.220e-16
  IDENTICAL / turnover 5.2622 bp/yr / margin 2.70%/yr.

## (b) Stale-number sweep — 4 docs bannered (insert-only), lint GREEN, plus 1 lint GAP fixed

Pre-state (test_audit_champ2_round4.py, authored 02:41 by the prior R4 session TDD-first,
found RED on the current tree — I verified its faces before acting): 2 failed / 3 passed.
test_a offenders (legacy generation billed current, no banner naming 37.20%):
  GOAL100_FINAL_REPORT.md:16,124 (55.5%/62.4% V1, "FINAL STATE: champion BALANCED 55.5%");
  GOAL100_FINAL_STATE.md:108,109 (47.9%/80.5% HONEST11 frontier);
  GOAL100_TRUTH_MEMO.md:111 (49.4% STRICTTRADE "FINAL MAXIMALLY-DEFENSIBLE").
test_b[honest11_build.py] offender: GOAL100_FINAL_STATE.md:93 claims byte-for-byte repro;
  measured --verify DIFFs (independently re-measured by me, match test docstring EXACTLY):
  champion_build.py CHAMPION 1.130e-03 / BALANCED 2.069e-03 / AGGRESSIVE 4.099e-03;
  champion20y_build.py 3.107e-03 / 6.160e-03 / 6.206e-03; honest11_build.py
  1.942e-03 / 2.247e-03 / 3.869e-03 — all DIFF, all > 1e-12.
- Banners added (SUPERSEDE BANNER 2026-09-08 at each doc head, + naming 37.195% champion
  of record + the measured DIFF numbers; GOAL100_CHAMPION.md got a section-12 runbook
  banner for its steps 2-3 IDENTICAL claims): insertions-only vs HEAD verified per file —
  FINAL_REPORT +14/-0, FINAL_STATE +14/-0, TRUTH_MEMO +12/-0, CHAMPION +12/-0 (mine;
  coordinator's concurrent 03:1x CHAMPION20Y-DEPRECATION banner +24/-0 already present,
  kept, not duplicated). Pre-edit snapshots (== HEAD blobs, sha-verified):
  work/pre_r4_snapshots/{GOAL100_FINAL_REPORT,GOAL100_FINAL_STATE,GOAL100_TRUTH_MEMO}.md.
- Lint gap the R4 test cannot see (found by manual sweep, fixed TDD): a NUMBER-LIST lint
  is blind to generation-billing PHRASING. GOAL100_PROGRESS.md:7 bills the 48.2% 16-pool
  config as "CURRENT champion" (2026-09-01 prose, 3 generations stale). New
  campaign/bt/tests/test_audit_champ2_round4b.py: RED on exactly that line (billing
  phrasing without naming RAWEW13v2/37.20%), then ADDITIVE banner (+10/-0 to
  GOAL100_PROGRESS.md), then GREEN + teeth test.
- After state: test_audit_champ2_round4.py 5/5 PASS; round4b 2/2 PASS; remaining legacy
  numbers in gated docs are all banner-scoped or lineage-framed (verified by grep:
  CHAMPION_CARD lineage table, CHAMPION sections under coord/R4 banners, FINAL_STATE
  under my banner). TRUTH20Y appears in gated docs ONLY inside the coord §11 banner
  pointing at the quarantine doc. GOAL80_FINAL_REPORT.md left unbannered BY DESIGN: it is
  the prior campaign's own final report (self-scoped history), flagged here for the
  coordinator to confirm.

## Environment / suite state

- Full bt suite: 398 passed, 0 failed (R3's 13 reds — test_beats_passive TDD stubs +
  CAMP_COST fail-closed — have since gone green from other agents' work; nothing of mine
  depends on that).
- Concurrent-session note: GOAL100_CHAMPION.md was edited by the coordinator mid-round
  (03:1x, CHAMPION20Y_V2 DEPRECATED FOR QUOTING, rebuild chartered as R5). My section-12
  banner was written around theirs; both insertions-only; no conflicts.
- Champion artifacts untouched all round (sha 4358dfab / 149164b3 pre == post; builder
  --verify IDENTICAL before and after).

## Files touched (this round)

- campaign/GOAL100_FINAL_REPORT.md (+14 banner), GOAL100_FINAL_STATE.md (+14),
  GOAL100_TRUTH_MEMO.md (+12), GOAL100_CHAMPION.md (+12, section-12 runbook banner),
  GOAL100_PROGRESS.md (+10) — ALL ADDITIVE, no deletions vs HEAD.
- campaign/bt/tests/test_audit_champ2_round4b.py (NEW): billing-phrasing lint, 2 tests.
- work/pre_r4_snapshots/ (NEW): 3 pre-edit doc snapshots.
- NOT touched by me: champion CSV, weights CSV, builder, card generator, all 13 sleeve
  files, test_audit_champ2_round4.py (pre-existing from prior R4 session; driven to GREEN,
  not modified).

## Flags for the coordinator

1. GOAL80_FINAL_REPORT.md quotes 43.2% as that campaign's best-honest — left alone
   (self-scoped prior-campaign history); confirm or overrule.
2. champion_card.py needs PYTHONPATH=campaign (bare invocation crashes with
   ModuleNotFoundError) — wrapper-script or sys.path fix suggested, one-line.
3. LEGACY DIFF status is now LINTED, not FIXED: all 3 legacy builders still DIFF their
   committed CSVs post-costfix (numbers above). If any legacy generation is to be rebuilt
   (CHAMPION20Y_V2 is chartered R5), the lint auto-resolves when --verify goes IDENTICAL.
ROUND 4 DONE

---

# ROUND 5 (2026-09-08) — CHAMPION20Y_V2 rebuild-or-drop EXECUTION; card footgun verified-fixed; GOAL80 43.2% verified + byte-repro'ed

Scope per charter R5: (a) rebuild the 20y table from POST-costfix sleeves with fresh builder
--verify IDENTICAL + MHX shortability re-audit, OR complete the quarantine doc on why it stays
deprecated; (b) fix the champion_card.py PYTHONPATH footgun (TDD); (c) independently verify
GOAL80_FINAL_REPORT's 43.2% best-honest claim against its own artifacts. GATES_CONTRACT_V2
(RATIFIED) + DEAD_IDEAS.csv read FIRST: recounted **130 data rows, 0 exact dups** (charter
context said 120 at R4-end; 10 more landed — dynamic per V2 preamble, all consistent). No dead
family re-tested; no new signal. Champion of record re-verified fresh this round via
verify_champion_r3_cmd.sh: ok=true 7/7 (byte_repro 1.110e-16, weights 2.220e-16, cost ratio
1.0000, MDD -6.6922, 0 neg yrs) — unchanged sha 4358dfab lineage.

## Verdict summary

(a) **CHAMPION20Y_V2 = DROP (rebuild executed in sandbox and REJECTED; stays deprecated).**
The rebuild ran through the UNMODIFIED builder on the post-costfix tree and DIFFs its committed
books at exactly the coordinator-banner numbers (BAL 3.107e-03 / SAFE 6.160e-03 / AGGR
6.206e-03); but a faithful re-emit would stamp IDENTICAL on a **gate-2-violating cost model**
(0.5|dW| @ 6bps — retired with iter11/costfix) and on an **uncosted pool member** (B3momhml,
its own meta: "no-cost-here ... Kept as reference only", worth +3.47pp CAGR uncosted). Every
convention-repaired variant still breaches the champion track (MDD >= -7% and 0-neg both fail;
1 neg year 2006 in ALL variants). (b) **Already fixed on the tree by a prior R5 session
(08:37-08:38, before my 08:44 start); verified rather than duplicated**: RED face reproduced on
the HEAD blob (ModuleNotFoundError 'scripts'), 3/3 GREEN on working tree, diff is exactly the
one-line sys.path.insert — but it is UNCOMMITTED. (c) **CONFIRM with two material flags**:
43.2% reproduces from COORD_FINAL_daily.csv to the decimal (arith 43.19% / SR 4.84 / MDD -7.48%
/ 0/19), the internal tables all reconcile, AND I recovered a byte-exact repro of the artifact
(maxdev 1.015e-16) — but 43.2 is ARITHMETIC ann (CAGR is 53.36%, a +10.2pp convention gap vs
the champion-of-record's 37.20 CAGR), and the artifact embeds an UNPRICED global-vt gross of
median 2.13x (mean 2.17x, max 5.29x): pricing it at the champion's own 4.5% margin convention
costs 5.264%/yr and takes the book to arith 37.99% / MDD **-9.27%** — out of the DD<=8% envelope
the report claims. Quotable as prior-campaign self-scoped history with those two flags, not as
a comparable headline.

## (a) CHAMPION20Y_V2 rebuild-or-drop — DROP, full numbers

READ FIRST + prior art: HUNT_TREASFUT R4 (work_r3/TRUTH20Y_QUARANTINE.md + their 8/8 pins,
re-run GREEN this round) had already proven V2 reproduces exactly from c745682-era blobs; my
charter was the opposite direction — post-costfix. Pool provenance re-derived from git: exactly
**3 of 13** V2 pool sleeves drifted since the V2 build (QAxasts, dualmom, brwt[E1_brwt_rev15] —
all b268e52 09-07; other 10 byte-identical since c745682/de890d0/acd81a0/335eff0/b0a6f18 —
verified per-file via git log). Builder itself unchanged since c745682 (09-01).

- Baseline `python3 scripts/champion20y_build.py --verify`: BAL 3.107e-03 DIFF / SAFE 6.160e-03
  DIFF / AGGR 6.206e-03 DIFF — matches the coordinator banner to the digit.
- Sandbox post-costfix rebuild (work/r5/, never emitted): BAL n=5196 CAGR 89.44% / arith
  64.52% / SR 6.12 / MDD -7.21% / 1 neg yr (2006 -1.57%); SAFE CAGR 80.26% / MDD -7.90%; AGGR
  CAGR 99.07% / MDD -7.35%. Committed vintage: BAL CAGR 90.45% / arith 65.05% / SR 6.17 / MDD
  -7.15%. **The V2 JSON's "ann": 65.1 is the ARITHMETIC ann** (CAGR is 90.45%) — same +25pp
  convention gap pattern as GOAL80.
- **Cost-convention audit (the decisive finding)**: champion20y_build.py line 29/66/71 charges
  `0.5*|dW| @ 6bps` on BOTH blend turnover and throttle flips — the pre-iter11 convention,
  retired by the costfix wave. Counterfactual full-|dW| @ 6.4bps on the same pool: BAL CAGR
  89.44 -> 87.26% (-2.185pp). A faithful re-emit = IDENTICAL stamp on a retired cost model.
- **B3momhml uncosted (load-bearing disclosure)**: its meta reads "REFERENCE (NOT
  gate-passing) ... no-cost-here ... Kept as reference only". E1's costed series (6bps
  half-turn) moves BAL by **-3.47pp CAGR** (89.44 -> 85.98). Mechanism measured: uncosted
  premium 3.628bp/day at vt scale = 9.14%/yr on the sleeve (4.5% mean slot weight); the gap is
  broad-based (positive in 21/21 years, 2007-2026 range +1.05..+7.69pp/yr — not one episode).
- **MHX shortability re-audit (charter item; cited from CAMP_SHORT R5(a), not duplicated)**:
  mean |short|/NAV 0.2960 pre-vt -> borrow tiers EASY +0.148% / MEDIUM +0.592% / HARD
  +2.368%/yr on the vol-targeted book; MHX mean slot weight in the V2 blend = **3.87%** ->
  worst-case book drag ~0.09pp/yr. Disclosable, not disqualifying. Generator provenance
  intact (CAMP_SHORT R4: committed bytes reproduce from the XGB prediction cache, maxdev
  9.983e-17).
- **Compliance matrix** (work/r5/v2_compliance_matrix.json): committed-convention 89.44 CAGR /
  -7.21 MDD (gate-2 violation); full-6.4 87.26 / -7.84; costed-B3 85.98 / -7.17; **full-6.4 +
  costed-B3 83.83 CAGR / arith 61.51 / SR 5.85 / MDD -7.29 / 1 neg yr** (V3-shaped — still
  fails the champion track: MDD wall + 0-neg); drop-MHX 68.96 / -9.11; fully compliant +
  no-MHX 63.78 / -9.97. Selection invalidation: the A/B configs were picked under the
  pre-costfix numbers' MDD>=-8 envelope — repairing the convention invalidates the selection.
- **Gearing disclosure (new, measured)**: V2's global vt applies median **2.52x** amplification
  to a raw EW blend that is only 3.95% vol (raw blend arith 24.52%/yr -> post-vt 61.45%/yr;
  cap 8.0x). The 65.1 headline is a geared construction, not a sum-1 book.
- Leak probe (V2 §6 Step-1 discipline, run anyway): post-costfix rebuild dW_t vs r_t wide probe
  same_period_corr **+0.0056, p 0.264, leak=False** (lag argmax -1 — causal drift signature).
- Charter disposition: both halves of (a) executed — rebuild run (REJECTED) + quarantine doc
  COMPLETED with an R5 addendum in
  agents/chief/coord/HUNT_TREASFUT/work_r3/TRUTH20Y_QUARANTINE.md (append-only; includes
  recommended quoting language + the V3-shaped 83.83/-7.29 numbers for the coordinator's call).
  NOTHING in campaign/results/ was touched.

## (b) champion_card.py PYTHONPATH footgun — verified FIXED (prior R5 session's work), not duplicated

- Concurrent-work check (charter discipline): bt/tests/test_audit_champ2_round5.py (mtime
  08:37) + champion_card.py fix (08:38) landed minutes before my session start (08:44). I
  verified their work instead of re-doing it: (i) RED face reproduced on the HEAD blob —
  `env -u PYTHONPATH python3 /tmp/head_champion_card.py --stdout` -> rc=1, "ModuleNotFoundError:
  No module named 'scripts'"; (ii) working tree 3/3 GREEN (bare run from repo root, bare run
  from /tmp cwd, clean-env stdout byte-identical to committed card); (iii) `git diff` = exactly
  the one-line `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))` + import — no
  artifact change. **UNCOMMITTED — flag for the coordinator to include in the next commit.**

## (c) GOAL80_FINAL_REPORT.md 43.2% — CONFIRMED self-consistent + BYTE-EXACT repro recovered; 2 material flags

- **Every headline number reproduces from its own CSV** (results/COORD_FINAL_daily.csv,
  n=4696, 2008-09-01..2026-08-28): arith ann **43.19%** (claim 43.2), SR_d **4.84** (4.84),
  SR_m **3.30** (3.3), vol **8.93%** (8.9), MDD geo **-7.48%** (-7.5), 0/19 neg years worst
  +7.1% (2008) — exact. IS/OOS: arith 37.96/47.71 vs claimed 38.0/47.7 — exact. Sub-period
  MDDs -5.1/-7.5/-6.3/-3.9/-5.2/-7.4 — exact vs section 3. Yearly table vs COORD_FINAL.json:
  max |dev| 0.049pp (2014). Internally airtight.
- **Convention flag #1**: 43.2% is the ARITHMETIC ann; geometric CAGR = **53.36%**. The
  champion of record's 37.1954% is a CAGR. Comparing "GOAL80 43.2" to "GOAL100 37.2" mixes
  conventions (arith-vs-arith: 43.2 vs 43.6 arith-equivalent of 37.2 — nearly equal!).
- **Byte-exact provenance RECOVERED (better than the report's own repro section)**: the
  surviving builder does NOT document its recipe — `coord_goal100_v2.py::blend()` defaults
  TGT=0.075 and computes per-sleeve vt scales on NaN-ALIGNED DataFrame columns, landing arith
  19.99% (nowhere near 43.19; pinned). The artifact was actually built with **raw-first vt
  (each sleeve on its own index) @ TGT=0.08** (the JSON's "vt": 0.08) + DD-throttle 4% FR 0.5 +
  6bps half-turn blend costs; with the single pre-costfix dualmom blob (b268e52~1) the rebuild
  is **BYTE-EXACT: maxdev 1.015e-16, n=4696, arith 43.19% / CAGR 53.36%** (work/r5/
  goal80_coordfinal_repro_TGT08_predualmomfix.csv; pinned in
  test_audit_champ2_round5b.py::test_goal80_coordfinal_byte_repro). The other drifted sleeves
  (A5r7/a6r7/QAxasts/A1credit re-emitted 09-01, 5 days after the artifact) turn out to have
  byte-identical content in the relevant span (only dualmom matters at 1e-12).
- **Convention flag #2 (leverage claim)**: the report says "NO leverage". The construction
  applies a global vol-target multiplier to a sum-1 book — realized gross multiplier median
  **2.13x** (mean 2.17x, p90 2.98x, max 5.29x, code cap 8.0x). This is vol-amplification =
  economically a financing-backed exposure dial. Unpriced in the artifact. Pricing at the
  champion's own 4.5%-on-(gross-1) convention: drag **5.264%/yr** -> arith 37.99% / CAGR 45.60%
  / SR 4.26 / MDD **-9.27%** — outside the DD<=8% envelope the report claims. Verdict: the 43.2
  is internally honest and exactly reproducible, but it is an ARITHMETIC, financing-unpriced,
  pre-costfix-convention (6bps half-turn, B3 uncosted: costed-B3 costs -1.24pp arith) number;
  with financing priced it does not clear its own DD envelope. Correct to keep GOAL80 and
  GOAL100 lineages quarantined from each other's headlines.
- B3 cost effect under the exact confirmed recipe: arith 43.19 -> 41.95% (-1.24pp) —
  material, not cosmetic (the E1 note "costed variant saved separately: 34.9%" refers to the
  E1 12-pool frontier book, not COORD14).
- Charter discipline: coordinator leaned CONFIRM; I confirm with numbers + two flags. GOAL80
  doc itself NOT edited (self-scoped prior-campaign history; R4 decision stands). All pins in
  campaign/bt/tests/test_audit_champ2_round5b.py (NEW, 7 tests, RED-first logic documented in
  docstrings; suite run below).

## Files touched (this round)

- campaign/bt/tests/test_audit_champ2_round5b.py (NEW, 7 pin tests — V2 post-costfix DIFF
  pins, retired-cost pin, B3-premium pin, COORD_FINAL byte-repro pin, convention pins).
- campaign/agents/chief/coord/HUNT_TREASFUT/work_r3/TRUTH20Y_QUARANTINE.md (APPEND-only R5
  addendum completing the quarantine per charter (a)).
- work/r5/ (NEW evidence: sandbox rebuilds r5_rebuild_*, r5_*_full64, r5_BAL_costedB3_noMHX,
  rebuild_vs_committed.json, v2_compliance_matrix.json, goal80_coordfinal_verify.json,
  goal80_coordfinal_repro_TGT08_predualmomfix.csv, dualmom_pre_costfix.csv pinned blob).
- NOT touched by me: champion CSV/weights/archive, champion_card.py + its R5 test (prior
  session's uncommitted work, verified only), all campaign/results/*, GOAL80_FINAL_REPORT.md,
  champion20y_build.py, coord_goal100_v2.py.

## Suite state + flags for the coordinator

- Full bt suite AFTER my inserts: **410 passed / 0 failed** (includes my 7 new pins, the prior
  session's 3 R5 card tests, HUNT_TREASFUT's 8 V2 pins; run 2026-09-08 ~10:05).
- 1. R5(b)'s fix + test are UNCOMMITTED on the tree — commit them with my round5b pins.
- 2. champion20y_build.py + coord_goal100_v2.py both carry retired/absent cost conventions;
  if a V3 20y book is ever wanted, build it full-|dW|@6.4 + costed B3 + MHX-borrow disclosure
  (83.83 CAGR / -7.29 MDD / 1 neg yr — non-champion-track) and re-pick configs IS-only.
- 3. coord_goal100_v2.py::blend() defaults do not reproduce its own committed artifact
  (TGT 0.075 vs 0.08; aligned-vs-raw-first vt) — anyone re-running it cold gets 19.99% arith.
  Pinned so the drift is loud.
- 4. My earlier in-round confusion (documented for audit honesty): two of my first swap
  experiments disagreed because blend() uses NaN-aligned vt columns (4.10% raw blend) vs
  raw-first (20.20%) — root-caused to construction convention, NOT nondeterminism; resolved
  before any verdict relied on it.

ROUND 5 DONE


## ROUND 6 (2026-09-08, session started 15:20 CST) - charter: (a) independent verify of CAMP_COST's 14-sleeve CANDIDATE with own code; (b) re-verify champion_card fix + round5b pins; (c) NO campaign doc edits

READ-FIRST done: coord/GATES_CONTRACT_V2.md re-read in full (Step-2 flip banner noted:
leak_check default-ON since commit 539f50e; I pass explicit sig/leak semantics in my probes).
DEAD_IDEAS.csv recounted MYSELF: **145 data rows** (146 lines incl header; charter said 137 at
R5-end - 8 rows landed since; dynamic by design). Row for RB_hobr (RES_BASIS-R1) confirmed
present with status "standalone V2-PASS (pending coordinator adoption)". No dead family
re-tested; RB_hobr is NOT dead-listed (it is the pending candidate, explicitly in scope).

Champion of record unchanged on the tree: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
sha256[:16] **4358dfab95679b97**; weights 149164b3b01aa110; RB_hobr sleeve sha256[:16]
**da0285b9a7a5e6a2** (matches the meta's pinned sha exactly). Fresh canonical 13-sleeve
verify_champion.py run this session (my work/r6_verify_champ13.json): **ok=true 7/7** -
weights_repro max_dev 2.2e-16, byte_repro 1.1e-16, cost model full_dw ratio 1.0000000000008
(half_dw diagnoses 1.68e-05 away - rejected), causality nav.shift(1) sameday-dev 4.93e-03,
truncation 7/7 probes dev 0.0, gross max 1.6000000000007 (0 days over), 0 neg years worst
+7.3104%, MDD -6.6922%. Baseline clean.

## (a) CAMP_COST 14-sleeve candidate RAWEW14_HOBR_CANDIDATE - VERIFIED 7/7 with own code; THE ADOPTION ARITHMETIC FLIPS SIGN WITH THE GROSS-CAP CONVENTION

Artifacts consumed (CAMP_COST's, read-only, nothing of theirs edited):
results/RAWEW14_HOBR_CANDIDATE_daily.csv (sha 4a662985a408129b, n=4805,
2008-03-31..2026-08-27) + RAWEW14_HOBR_CANDIDATE_weights.csv (dc0dc87fea2ef4b0, 14 rows).

1. **Canonical tool on the candidate triple: ok=true 7/7** (my work/r6_verify_candidate14.json;
   I re-derived the full 14-sleeve CLI map from the builder PATHS + RB_hobr, NOT from their
   stdout): weights_repro 2.2e-16 (is_end 2017-01-01 inferred, P=0.55), byte_repro 1.01e-16,
   cost_reconciliation **full_dw** ratio 1.0000000000014 (half_dw 1.97e-05 away - rejected),
   day-1 entry 4.05e-14 bp, causality causal 1.01e-16 vs sameday 4.81e-03, truncation 7/7
   probes 0.0, gross max 1.6000000000006 (0 over), yearly 0 neg / worst +7.8443%, MDD
   -6.2354% > -7% wall. Turnover 5.4972 bp/yr (champion 5.2622 -> +0.235 bp/yr).
2. **My own independent verifier** (work/r6_audit_champ2_candidate14.py - own algebra mirroring
   the recipe from its docstring, NO import of rawew13v2_build/bt/CAMP_COST modules):
   **ALL 7 CHECKS OK** - byte 9.996e-17, cost full_dw 1.0002e-16, truncation 0.0,
   weights_max 1.6000000000000012, financing-implied gross 1.60000000000056, 0 neg,
   MDD -6.2354. Candidate stats: CAGR **36.2885** / arith 31.4261 / SR **3.2719** / MDD -6.2354.
3. **THE DECISIVE FINDING - convention root-cause, exact numbers (work/r6_blend_probes.json +
   pins in bt/tests/test_audit_champ2_round6.py):** every adoption-positive number in the
   11:4x standup is the **fill-0 native-units blend** (champ + w*hobr on the champion's
   4805-day index), NOT the emitted re-solve:
   - fill-0 w=0.25: dSR **+0.1989** (=standup +0.199), dAnn CAGR **+4.2128pp** (=+4.21),
     dMDD **+0.0508pp** (=+0.05), blend MDD -6.64% (reproduces RES_BASIS's meta to the
     digit; w=0.5 -> MDD -7.96%, breaks the wall, also as their meta says).
   - fill-0 rung grid: dAnn +0.838 / +1.679 / +2.521pp at w=0.05/0.10/0.15 - all positive,
     reproducing the standup's "rung grid all dAnn>0".
   - **The emitted re-solve candidate**: dAnn **-0.9069pp**, dSR +0.0909, dMDD +0.4568pp.
     My own re-solve rung grid (own code): dAnn **-0.7858 / -1.5936 / -2.4233pp** at the same
     rungs - ALL NEGATIVE. The sign flips exactly at the funding mechanism.
   - **Why**: the champion rides gross **exactly 1.6 every day** (weights_max
     1.6000000000000012, 0 days over). Any additive overlay pushes gross ABOVE the cap:
     fill-0 w=0.25 blend gross = 1.6 + 0.25*hobr_gross = **2.02-2.10x** (hobr dollar-neutral
     pre-vt gross 2.0, realized ann vol 9.55% -> implied post-vt gross ~1.67x) = a V2 8e
     breach of **+0.42..+0.50 gross**. The re-solve is the only 8e-compliant construction,
     and it funds HOBR from the other 13 sleeves -> the book's ann drops 0.9pp.
4. **V2 battery verdict on the certifiable construction** (the re-solve = what the candidate
   CSV is): 7/7 champion-track checks PASS, cost reconciliation full_dw PASS, causality/
   truncation PASS, leak probes all leak=False (below), 0 neg years, MDD improved -0.457pp.
   BUT **8c dAnn>0 HARD FAILS: -0.907pp** (and 8g plateau dAnn negative at every rung).
   8d dSR>=0 (+0.0909) and dH2>=0 (+0.0223) pass; 8f halves dSR_H1 +0.2376 / dSR_H2 +0.0223
   (positive both halves, decaying); 8i exclusion reproduces with own code: dominant dd
   window 2018-06-19..2018-07-20 (24d), dMDD excl **+0.5219pp** >= 0.5 - passes by a
   +0.0219pp hair. On the fill-0 blend the 8c passes but **8e hard fails** (2.02-2.10x).
   **No admissible construction delivers dAnn>0 within gross<=1.6.**
5. **Placebo reproduction, own code (my rng, not theirs)**: circular shift of HOBR at
   fill-0 w=0.25 reproduces the dSR delta in **188/200 draws >= real** (199/200 >= 0.9x
   real; null median 0.2149 vs real 0.1989) - mean-injection-dominated, CONFIRMING the
   coordinator's 169/200 (same regime, different seed/shift range). On the RE-SOLVE the
   same instrument gives **0/200** (CAMP_COST's battery: reproduced_frac 0.0 - matches).
   My own B1 level-matched block bootstrap (120 draws, L=20, moments re-matched, full
   re-solve machinery): real dSR 0.0909 vs null median 0.0400 / p95 0.0657 -> real at the
   100th percentile (right-tail pass) - **the SR delta on the re-solve is timing-real, not
   mean injection**; but real dAnn -0.907pp sits BELOW all 120 nulls' dAnn (percentile 0.0,
   null median -0.70pp) - HOBR's mean return drags the cap-compliant book regardless of
   timing. Both instruments agree: the SR gain is real, the ann gain does not survive the cap.
6. **Leak probes, own code (work/r6_leak_probe_own.py, no bt import; V2 6b thresholds
   |corr|>=0.20 AND p<0.05 AND lag-0-argmax)**: wide 14-col weights vs same-period sleeve
   rets (13 valid cols, CFX4 const-0 skipped): same-period corr **-0.0145**, p 0.267,
   leak=False. Scalar turnover |dWg| vs book: +0.2255, p 1.9e-56, argmax lag **-1** (the
   causal weights-chase-yesterday's-NAV signature; matches CAMP_COST's 0.22549 exactly),
   leak=False. Scalar signed dWg: +0.0089, p 0.539, leak=False. My scalar numbers match
   their battery to the digit; verdict leak=False on every construction.
7. **Sleeve-level meta claims reproduced with own code**: RB_hobr n=4604 2008-02-19..2026-08-25,
   SR 1.3498, ann 13.2499%, MDD -22.288%, 1 neg yr (worst -0.685% 2022), H1 2.1823 / H2
   0.7533 (the coordinator's halves concern VERIFIED exactly), IS SR 2.145 / OOS SR 0.8074
   (VERIFIED - real OOS decay, below the 1.0 bar OOS), corr_champ +0.0219. beats-passive
   ordering with my own trio (twelvedata SPY bh / IEF 60-40 / CTA_15vol, matched span
   n=4592): hobr 1.3405 vs best-of-trio 0.6187 (60/40) - **beats, True**. z-neighborhood
   spot-check: w63_z15 1.0834 / w63_z20 0.7840 (matches their fine-grid 1.083/0.784).
   NOT independently verifiable by me: T+1->T+2 net-stream decay claim 1.343->0.142 (shifting
   a net return stream is date-invariant - SR unchanged 1.3498/1.3499/1.3502; the claim
   requires the underlying signal-weight path, which I did not rebuild; flagged, not
   material to the verdict below). Window/z plateau grids + scramble p=0.000 accepted from
   their artifacts, not re-derived (no raw-data rebuild attempted this round).

**VERDICT (a)**: The CAMP_COST 14-sleeve candidate artifact is byte-clean, causal, honestly
costed, leak-free, and PASSES the 7/7 champion-track battery - as an artifact it is
reproducible and sound (my own algebra and the canonical tool agree to ~1e-16). **But it is
NOT the construction whose +4.21pp the standup quoted, and on it the V2 8c gate FAILS
(dAnn -0.907pp < 0, negative at every 8g rung).** The +4.21pp exists only in the fill-0
overlay that breaches 8e by +0.42..+0.50 gross (2.02-2.10x vs cap 1.6) - a HARD violation -
and that overlay's gain is mean-injection-dominated (188/200 reproduction). RB_hobr's
timing genuinely improves book SR (+0.091 re-solve, B1 100th pctile) but at the cost of
0.9pp ann once the gross cap is respected. **My recommendation to the coordinator: do NOT
adopt on the current record.** If the committee values SR over ann, the honest framing is
"cap-compliant SR-max re-solve, ann -0.9pp, MDD +0.46pp" - which 8c (dAnn>0 HARD) currently
rejects; the alternative is to re-litigate 8c, not to adopt the fill-0 numbers.

## (b) champion_card.py sys.path fix + round5b pins - GREEN; still UNCOMMITTED (re-flagged)

- `env -u PYTHONPATH python3 campaign/scripts/champion_card.py --stdout` from the repo root:
  rc=0, output **byte-identical** to committed campaign/CHAMPION_CARD.md (True).
- git diff on champion_card.py = exactly the R5b one-line sys.path.insert + Path import
  (re-verified this session) - no artifact change, no drift.
- My round5b pins: test_audit_champ2_round5b.py (7) + test_audit_champ2_round5.py (3) +
  round1 pins (7) = **17 passed** this session.
- **UNCOMMITTED, re-flagged for the commit wave**: `git status` shows campaign/scripts/
  champion_card.py modified; bt/tests/test_audit_champ2_round5.py and test_audit_champ2_
  round5b.py are still untracked (??). Commit them together with my new R6 pins (below).

## (c) Campaign doc edits - NONE (charter honored)

No campaign/*.md touched. Writes this round: my own work/r6* (verifier, probes, JSONs,
verify JSONs) + ONE new pin file campaign/bt/tests/test_audit_champ2_round6.py (4 tests,
RED-first documented: the fill-0 assertion initially pinned the inner-join variant and
FAILED 0.2045 vs 0.1989 before I split the two conventions - the failure was my pin, not
the artifact; both variants now pinned at exact values). Suite after my inserts: **422
passed / 0 failed** (up from 410 at R5-end; the +12 = HUNT agents' concurrent test files
+ my 4 R6 pins).

## Flags for the coordinator

1. Candidate disposition per (a) verdict above: 8c FAIL on the certifiable construction;
   8e FAIL (+0.42..0.50 gross) on the standup construction. No adoption path under current V2.
2. champion_card.py fix + round5 pins + round5b pins + new round6 pins: all UNCOMMITTED -
   include in the next commit wave (list: campaign/scripts/champion_card.py,
   bt/tests/test_audit_champ2_round5.py, test_audit_champ2_round5b.py,
   test_audit_champ2_round6.py).
3. CFX4 relw = 0.0 in the candidate weights (IS_SR<=0 -> relw 0): the 14th column is
   carried but contributes nothing; harmless, disclosed.
4. RB_hobr T+2 decay claim (1.343->0.142) remains artifact-unverifiable from the net CSV
   alone (needs the weight path); ask RES_BASIS to publish positions or a signal series
   per V2 10a if this family ever re-enters an acceptance track.
5. My scalar-turnover leak probe (+0.2255, p 1.9e-56) EXCEEDS the 0.20 |corr| leg with
   argmax lag -1; leak=False by the lag leg, same as CAMP_COST's own battery. Anyone
   re-running scalar probes must check the argmax leg, not just |corr| (documented in the
   pin file comments and work/r6_leak_probe_own.json).

ROUND 6 DONE
## ROUND 7 (charter a+b; executed 2026-09-08 22:4x-23:5x CST) - AUDIT_FWBUGS-R6 census spot-check + tracked-state suite re-run

Preconditions per charter: coord/GATES_CONTRACT_V2.md in force (pass sig= and leak_check=
explicitly; VOL2 V3 per-class placebo still PROPOSAL - not depended on either way this round);
campaign/results/DEAD_IDEAS.csv recounted myself with a real csv parser (quoted multi-line
fields): **152 data rows, 78 distinct sources** (charter said 145-146 at R6-end; consistent -
concurrent R7 appends landed: last 3 rows = HUNT_TREASFUT-R7, CAMP_SHORT-R7, CAMP_BORROW-R7).
No dead family touched; no campaign/*.md edited; zero bt/ source edits by this agent this round
(audit-only). Charter (b)'s premise - that my pins land in this standup's commit wave - was
tested and came back FALSE (below); that IS the (b) result.

### (a) AUDIT_FWBUGS-R6 census spot-check - CLEAN (seed 20260908, 20/20 + 31/31)

- Census internals: appendix = 2206 path rows (31 MODIFIED + 2175 UNTRACKED, footer
  "total paths: 2206" consistent). Charter said 2,202 at their census; +4 rows of live-tree
  drift by their own caveat (tree is live). Spot-check method: seeded `random.seed(20260908)`,
  sample 20 rows, verify (i) path EXISTS on disk, (ii) CURRENT git classification matches the
  appendix row. **20/20 OK, 0 mismatch** (all 20 drew UNTRACKED rows - 98.6% of the appendix
  is untracked; expected). Because a 20-row untracked sample is weak evidence about the
  MODIFIED class, I additionally verified **ALL 31 MODIFIED rows exhaustively: 31/31 are
  tracked-with-changes right now**. Census-vs-now: live tracked-modified under campaign/ = 32;
  delta = exactly ONE new file, `campaign/bt/tests/test_beats_passive.py` (+90 lines,
  DATA_ETF_MORE R6 degenerate-benchmark pins, mtime 16:20 09-08 - landed AFTER their 16:0x
  census; correctly absent from it, not an error). Repro saved: work/r7_spotcheck.py +
  work/r7_spotcheck.txt (two bugs in my own first draft caught and fixed: porcelain slice
  l[4:]->l[3:], and appendix-vs-porcelain path-prefix normalization).

- Escalation 1 REPRODUCED: `git archive HEAD -- campaign/bt | tar -x` into an empty dir, then
  a valid `gates.run` call (test_gates.py's own _r() fixture shape) =>
  **"FRESH-CLONE CRASH: ModuleNotFoundError: No module named 'bt.leakcheck'"** (bt/gates.py:135).
  All 7 wave-blocker files STILL untracked at HEAD b772958: bt/{leakcheck,beats_passive,align,
  blend,borrow,financing_stress}.py + verify_champion_r3_cmd.sh (`git ls-files
  --error-unmatch` rc=1 on each). Verified the 2 hermes/* branches are April-era and hold
  neither file - the wave exists on NO branch.

- Escalation 2 REPRODUCED: coord/verify_champion_standup_1140.json is EXACTLY a 145-byte
  record: `{"tool": "bt/verify_champion.py", "ok": false, "errors": ["missing sleeve inputs:
  no --sleeve name=path given"], "checks": {}}` - a failed invocation, correctly NOT a 7/7 pin.
  The bracketing ok:true records carry the same 7/7 headline (read verify_champion_standup_
  1830.json: ann 37.19539675684982 / sr 3.180994199561701 / mdd -6.692185534307193 / neg 0 /
  n 4805; a fresh coordinator ..._2233.json, ok:true 7 checks, mtime 22:39 tonight also
  matches). Citation re-point recommendation STANDS; champion numbers unaffected.

### (b) Tracked-state suite - the commit wave DID NOT LAND; tracked tree does NOT reproduce green

- HEAD b772958 (21:53 +0800) committed ONLY 6 team/ roster files (RES_FXSTYLE + RES_ALTDATA
  charters etc). My R6 flag list (champion_card.py, round5, round5b, round6 pins) and
  AUDIT_FWBUGS's fresh-clone blocker list are ALL still uncommitted: `git ls-files
  --error-unmatch` FAILS for bt/tests/test_audit_champ2_round5.py, round5b, round6, and the 7
  bt modules above; champion_card.py still shows its uncommitted +6 sys.path diff.
- Measured tracked state: `git archive HEAD` full tree to /tmp, run bt suite there:
  **2 collection errors (test_beats_passive.py, test_fwbugs_audit_r3.py - import the untracked
  bt.beats_passive / bt.leakcheck) + 21 failed / 80 passed** among the collectable files
  (101 collected). Failure decomposition: **19 of 21 = ModuleNotFoundError bt.leakcheck at
  gates.py:135** (test_gates 1, test_gates_audit 11, test_gates_audit_r3 4, leakflip 3);
  **2 = committed-test-vs-committed-source vintage mismatch, reproducible on pure HEAD
  without any untracked file**: (1) test_camp_cost_full_dw.py::test_no_builder_in_champion_
  pool_undercharges asserts the 0.5x pattern EXISTS in QA_dualmom_band121.py, but HEAD's
  QA_dualmom already carries the costfix (line-52 comment: "was 0.5*(neww-prev).abs().sum()")
  - the corrected test sits uncommitted on disk; (2) test_rawew13v2.py::test_sr_and_ann_
  improve_over_prior_champion asserts ann >= 1.30x EW (HEAD-era 40.9 vs 28.9); the costfix
  moved the champion to 37.195 (my measured: 0.372 vs 0.2889*1.3 - fails) - its fix is also
  only on disk. These 2 are NOT new bugs - they are the R2/R4 fixes' test-side halves, still
  uncommitted - but they mean **pure HEAD fails its own committed suite**, independent of the
  untracked-module issue.
- Live tree, same session: **444 passed / 0 failed** twice (97.17s / 91.86s; suite grew
  422->444 from concurrent R7 agents' new test files). My pins all green live:
  round1 (7) + round5 (3) + round5b (7) + round6 (4) = 21 passed; champion_card.py from a
  clean env (env -u PYTHONPATH, bare cwd=repo-root invocation) rc=0 and BYTE-IDENTICAL to
  committed CHAMPION_CARD.md (True). On the ARCHIVED tree the same bare invocation is the
  old crash: ModuleNotFoundError: No module named 'scripts' - i.e. **the sys.path fix exists
  only uncommitted; tracked-vs-untracked behavior DIFFERS for both charter-named files**
  (champion_card footgun + the pin files). No test behaves differently between my runs A/B
  on the same tree, so the flag is: tracked state is BROKEN, untracked disk state is GREEN.
- Champion of record re-verified fresh by me, this session (bash bt/verify_champion_r3_cmd.sh,
  json pinned work/r7_champver.json): **ok=True 7/7 - weights_repro 2.2e-16, byte_repro
  1.1e-16, cost_reconciliation full_dw 1.2e-16 (5.2622 bp/yr of the 6.4 budget, day-1 entry
  3.87e-13), causality nav.shift(1) causal 1.1e-16 vs sameday 4.93e-3 + truncation 7 probes
  0.0, gross max 1.6000000000006978 / n_over 0 / margin 2.70%/yr, neg_years 0 (worst
  +7.3104%), MDD -6.6922%**. Champion CSV + weights CSV tracked-clean; ALL 13 sleeve paths
  from rawew13v2_build.py PATHS verified `git ls-files --error-unmatch` rc=0 (13/13). So the
  champion lineage itself survives a fresh clone; only the GATES/test layer is clone-broken.

### Flags for the coordinator

1. **The commit wave has not happened.** Every commit-now item from AUDIT_FWBUGS R6 + my R6
   flag list is still uncommitted at HEAD b772958. Until it lands, pure HEAD (i) crashes
   gates.run on import (fresh-clone), (ii) fails its own committed suite 21/2-errors, and
   (iii) keeps the champion_card footgun. The wave is fully specified in AUDIT_FWBUGS
   work_r6/commit_wave_manifest.md (their wave order steps 1-6; my files ride step 1/2).
2. New since their census: only campaign/bt/tests/test_beats_passive.py (+90, DATA_ETF_MORE
   R6) entered tracked-modified; recommend it joins the wave's bt commit.
3. Two committed tests assert the PRE-costfix vintage of committed source (full_dw offender
   pin, rawew13v2 1.30x pin). Their disk fixes are correct and green; if the wave commits the
   disk bytes as-is, both heal. Do NOT "fix" by softening either assertion.
4. DEAD_IDEAS 152 rows / 78 sources at 23:5x (their manifest said 145 at 16:0x) - ledger
   healthy, growing from R7 appends.

Evidence artifacts (mine, all saved): work/r7_spotcheck.py, work/r7_spotcheck.txt,
work/r7_champver.json, work/r7_tracked_failures.txt, work/r7_tracked_failed_reasons.txt.
Archive of HEAD used for the tracked-state runs: /tmp/trackstate_r7 (regenerable via
`git archive HEAD | tar -x -C <dir>`).

ROUND 7 DONE
