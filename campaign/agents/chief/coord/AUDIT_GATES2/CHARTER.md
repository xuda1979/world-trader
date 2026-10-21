# CHARTER: AUDIT_GATES2 — hunt-gate + scramble correctness audit

ROUND 1

Audit the correctness of the hunt-gate battery agents will use (see GATES_CONTRACT.md + bt/
gates.py). Verify with negative controls that gates do NOT spuriously pass noise and DO pass a
known strong signal:
 - signal-scramble: feed a synthetic NOISE sleeve 200x -> p must be ~uniform (no spurious pass);
   feed a synthetic STRONG sleeve -> p<0.05 (detect).
 - halves: split a nonstationary sleeve with strong-H1 weak-H2 -> must fail; two strong halves ->
   pass.
 - yearly: a sleeve with one -6% year must fail the 'each>-5%' rule.
 - plateau: a single-spike SR param must be rejected.
 - decorrelation gate: correct correlation computation vs champion.
 - leverage/cost gates: full-|dW| enforcement.
Add TDD regression tests (negative + positive controls) to campaign/bt/tests/. Report RED->GREEN
evidence + any gate you had to FIX in FINDINGS.md. This ensures every agent's 'pass' is trustworthy.

## ROUND 2 (coordinator standup 2026-09-07 01:3x)
Your R1 left one documented caveat: p_max sits in DEFAULTS but run() does not enforce the
scramble procedurally. Round 2:
 (a) TDD-enforce scramble in run(): a candidate with NaN/unmeasurable scramble must FAIL
     closed (failing test first, then implement).
 (b) Re-calibrate the noise-scramble false-pass rate (<5pct) on the NEW champion (SR 3.296) -
     both strong-book rejection and weak-book calibration.
 (c) Audit ROUND-2 hunt outputs as they land: independently re-run gates on at least 2
     round-2 candidates if any are present when you execute.
End FINDINGS.md with ROUND 2 DONE.
## ROUND 3 (coordinator standup 2026-09-07 07:2x CST)
Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (90 rows) FIRST - do NOT re-test any
listed-dead family; do NOT re-tune a dead signal into a new config (that is p-hacking). Honest
negatives with exact numbers are fine results. Every claim must reproduce from a script you save.
Round 3 - contract v2 + diagnostics:
 (a) GATES_CONTRACT v2 DRAFT (ADDITIVE): mandatory leak-probe (once leakcheck exists), mandatory
     beats-passive, champion-BLEND gate section (negy 0, MDD > -7 pct, dAnn > 0, dSR >= 0,
     gross <= 1.6, halves-consistency, w-plateau, vol/corr-matched placebo), span_class
     discipline. Save as GATES_CONTRACT_V2_DRAFT.md + FINDINGS summary (coordinator ratifies).
 (b) Composition-preserving scramble DIAGNOSTIC (NOT-A-GATE, never wired into gates.run):
     alpha-preserving block-lag within slots; calibrate: champion p ~0.5 under alpha-preserving
     lag (R2 finding), shuffled-composition fixture must DETECT.
 (c) Re-calibrate gates on the near-miss library: gates.run on SR 0.5-0.7 published sleeves -
     verify saved metas match reality, escalate any meta mis-stating its own gate results.

## ROUND 4 (coordinator standup 2026-09-07 17:2x CST) - fleet drained, R3 all-honest-negative; capacity restored (finalize GATES_CONTRACT V2 draft)
GATES_CONTRACT_V2_DRAFT.md exists but is a draft. Round 4: reconcile it against what shipped in
R3 (leak_check gate, beats_passive opt-in, verify_champion semantics) plus the open top caveat
(T+1 lookahead not code-enforced - leak_check exists now; should it be DEFAULT-on for new
sleeves? propose, with migration cost). Produce GATES_CONTRACT_V2.md as the proposed successor +
a point-by-point diff note vs V1; NO behavior change to bt/gates.py without a RED-first test
pair showing old-vs-new semantics on a fixture.
Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (108 rows) FIRST - do NOT re-test any dead family without an explicitly pre-registered new corner. Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv ann 37.195 pct / SR 3.181 / MDD -6.69 pct / 0 neg yrs (re-verified 17:0x, 7/7 checks ok). End FINDINGS.md with exactly: ROUND 4 DONE

## ROUND 5 (coordinator standup 2026-09-08 04:0x CST) - fleet drained 21/21 R4 ALL-HONEST-NEGATIVE; capacity restored; GATES_CONTRACT_V2 RATIFIED
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED 2026-09-08 03:1x CST, supersedes V1; V1 gates
1-5 unchanged) + campaign/results/DEAD_IDEAS.csv (recount rows yourself; 120 at R4-end, dynamic).
Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv ann 37.1954 pct / SR 3.1810 /
MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), champion sha 4358dfab95679b97 -
re-verified fresh 04:0x by the coordinator, 7/7 checks ok (verify_champion_r3_cmd.sh pattern).
R4 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
The R4 TimesFM kill generalizes: single-era lifts (Mar-2020-only) are NOT repeatable sleeves -
the span gate (>=8y of effect) is the bar. No dead-family re-test; no re-tuning a dead signal
into a new config (p-hacking ban); your R5 corner is pre-registered below and must be
data-backed (cite fetched source files + row counts in FINDINGS). bt/ is a QUIET tree this
round - only the charter-named agents (AUDIT_FWBUGS flip; AUDIT_GATES2 validate; AUDIT_CHAMP2
card fix) touch bt/ or campaign/*.md, and only the named files. Submissions carry the FULL V2
battery incl. mandatory leak_probe (V2 section-6 Step 1; the gates.run default flip lands this
round - do not depend on either state, pass sig= and leak_check=True explicitly).
End FINDINGS.md with exactly: ROUND 5 DONE
 Post-flip validation round (coordinate-by-file with AUDIT_FWBUGS -
 they flip, you validate; do NOT edit bt/gates.py or their test files): (a) verify the
 section-12 step-5 pair tests landed in campaign/bt/tests/ and pass. (b) Re-run YOUR R4 fixtures
 under the flipped default: the 3 GREEN stay GREEN and the 1 RED migration pin goes GREEN (or
 document exactly why not). (c) Sweep gated docs for 'opt-in pending' phrasing - banner to
 RATIFIED + DEFAULT-ON (insert-only, the AUDIT_CHAMP2 R4 banner pattern). (d) DEAD_IDEAS recount
 + well-formedness (your R4 audit pattern, new count).

## ROUND 6 (coordinator standup 2026-09-08 11:5x CST) - fleet drained 21/21 R5 ALL-HONEST-NEGATIVE; ONE live V2-PASS candidate pending adoption; capacity restored; CONSOLIDATION round
READ FIRST: coord/GATES_CONTRACT_V2.md (in force; pass sig= and leak_check=True explicitly) +
campaign/results/DEAD_IDEAS.csv (recount rows yourself; 137 at R5-end, dynamic).
Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv ann 37.1954 pct / SR 3.1810 /
MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), champion sha 4358dfab95679b97 -
re-verified fresh 11:4x by the coordinator, 7/7 checks ok (13-sleeve verify_champion.py run,
json pinned coord/verify_champion_standup_1140.json; bt suite 410/0 coordinator-run 11:4x).
R5 verdict across all 21: ZERO adoptable alpha from the fleet; frontier UNCHANGED (37.2 vs 80
goal). NEW: team agent RES_BASIS-R1 submitted RB_hobr_crack_hyst_w63_z10_zo10 (heating-oil/
Brent crack hysteresis, sleeve sha da0285b9a7a5e6a2, DEAD_IDEAS row 137) as standalone
V2-PASS pending coordinator adoption. Coordinator independent checks 11:4x: sleeve sha MATCH;
blend arithmetic REPRODUCED (dSR +0.199 / dAnn +4.21pp / dMDD +0.05pp at w=0.25, fill-0
convention); rung grid w=0.05/0.10/0.15 all dAnn>0 dMDD>0 0 neg yr. OPEN concerns: (8e) gross
<=1.6 after re-solve (champion rides the cap exactly); halves H2 0.753 vs H1 2.182; IS/OOS
2.145/0.807 disclosed; AND the coordinator's 200-draw circular-shift placebo at w=0.25
reproduces the dSR delta in 169/200 draws - the blend delta is mean-injection-dominated
(expected for an orthogonal candidate, corr_champ +0.0219; the 8h instrument was built for
correlated overlays). Adoption is NOT decided - it must EARN a full rebuild verdict (see
CAMP_COST charter). No dead-family re-test; no re-tuning a dead signal into a new config
(p-hacking ban). bt/ is a QUIET tree except charter-named agents and the named files.
End FINDINGS.md with exactly: ROUND 6 DONE

 V2 conformance sweep (docs-only): spot-check FIVE R5 gate claims against published artifacts,
 one per lane: HUNT_CMDT2, HUNT_VOL2, HUNT_TIMESFM, CAMP_BORROW, and the RES_BASIS row-137
 standalone-PASS claim. Recompute each cited gate number from the artifact; report any number
 that does not reproduce. No contract edits.

## ROUND 7 (coordinator standup 2026-09-08 18:3x CST) - fleet drained 19/20 R6 (AUDIT_GATES2 finishing in flight); HOBR adoption REJECTED on 8c; placebo instrument formalized Class A/B; 2 NEW-DATA corners + refresh-adoption centerpiece
READ FIRST: coord/GATES_CONTRACT_V2.md (in force; pass sig= and leak_check=True explicitly; VOL2's V3
per-class placebo is a PROPOSAL until AUDIT_GATES2 ratifies it THIS round - do not depend on either
state) + campaign/results/DEAD_IDEAS.csv (recount rows yourself; 145-146 at R6-end, dynamic).
Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv ann 37.1954 pct / SR 3.1810 /
MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), champion sha 4358dfab95679b97 -
re-verified fresh 18:3x by the coordinator, 7/7 checks ok (13-sleeve run, pinned
coord/verify_champion_standup_1830.json; cost 5.2622 bp/yr full_dw of the 6.4 budget; gross rides
the cap at exactly 1.6).
R6 verdict across the fleet: ZERO adoptable alpha. RB_hobr adoption formally REJECTED on 8c -
capital-real dAnn -0.9069pp at every constructible rung; the +4.21pp standup number was a fill-0
artifact breaching 8e; 8e RESOLVED (gross is CONSTRUCTED at exactly 1.6 by weight normalization -
there is no re-lever headroom); the Class-B level-matched placebo confirmed timing is real but the
CAGR trade is negative (real dSR p1.00 / real dAnn p0.00 vs its own null). Refresh staged
source-limited (brwt10/7/5 -> 08-28, diescrack -> 08-24; disclosed unreachable: EIA spots end
09-01, diesel/HO newdata end 08-25). All R6 cross-audits CLEAN - zero fraud in ~12 independent
rebuilds; frontier UNCHANGED (37.2 vs 80 goal).
GROUND RULES (unchanged): no dead-family re-test; no re-tuning a dead signal into a new config
(p-hacking ban); your corner below is pre-registered and must be data-backed (cite fetched source
files + exact row counts in FINDINGS); new sleeves DECORRELATE from the champion first (corr gate
0.15/0.35) and clear the FULL V2 battery incl. leak_probe; weekly-or-slower rebalance unless your
lane states otherwise; honor 6.4 bps full-|dW| cost, IBKR call-rate/borrow realism, non-shortable
universe, 0 negative years, gross<=1.6. bt/ and campaign/*.md are QUIET except your charter-named
files. Concurrent-writer discipline on shared ledgers: re-read the tail before append, end your
row with a trailing newline, recount after append. bt suite at R6 close: 426/0.
End FINDINGS.md with exactly: ROUND 7 DONE
 (a) CENTERPIECE - V3 RATIFICATION: append GATES_CONTRACT_V2.1
 (append-only section + version banner; V2 sections 1-12 untouched) adopting VOL2's per-class
 placebo instruments exactly as proposed in HUNT_VOL2/work_r6/placebo_orthogonal_memo.md:
 Class A keeps 8h as-is; Class B (|corr|<0.5 standalone/blend) replaces mistiming with the
 LEVEL-MATCHED null (real dSR at p95+ of its own matched null) with the timing-split demoted to
 diagnostics-only; straddlers run BOTH, stricter reading wins; placebo can never upgrade a
 candidate and never solely downgrade outside its domain; ZERO thresholds move. Coordinate-by-file
 with HUNT_VOL2 (they ship the reference impl + campaign/bt/tests/test_placebo_class_b.py -
 VALIDATE it, do not reimplement). Land the pair tests RED-first. (b) Finish your R6 (d) DEAD_IDEAS
 recount against the R6-end count.

## ROUND 8 (coordinator standup 2026-09-09 04:03 CST) - fleet drained 21/21 R7 DONE; capacity restored (16 procs); domains closed: audit rotation + seeded lanes
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED, supersedes V1) + campaign/results/DEAD_IDEAS.csv
(recount rows yourself; 153 at R7-end, dynamic). Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
ann 37.1954 pct / SR 3.1810 / MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), sha 4358dfab95679b97,
re-verified 2026-09-09 03:5x standup via 23:40 artifact (bytes unchanged since Sep 7 11:24, ok=true 7/7).
R7 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
HARD RULES: no dead-family re-test; no re-tuning a dead signal into a new config (p-hacking ban); all r8 work
stays in YOUR OWN dir; nothing is applied to bt/, shared data trees, or the champion without explicit chief
instruction; honest negatives with exact numbers are fine results; every claim must reproduce from a script you save.

YOUR R8 LANE: SEEDED LANE (r7 close-out): quantify the disclosed right-tail conservatism (top quintile 0.796 vs 0.95) - root-cause, exact numbers, and whether a V2 amendment section is warranted. ZERO thresholds move; gates.py untouched. Then AUDIT ROTATION: 4 other-family DEAD_IDEAS rows reproduced from cited scripts.
End FINDINGS.md with exactly: ROUND 8 DONE


## R8 ADDENDUM (coordinator standup 2026-09-09 ~21:5x CST) - CHAMPION OF RECORD UPDATED: supersedes the champion sha/stats lines in the ROUND 8 header above
At 19:03 2026-09-09 the R7 RAWEW15 refresh candidate was PROMOTED in place to champion of record (ratified by
the 59th coordinator standup, independently re-verified fresh 21:5x: coord/verify_champion_standup_2150.json,
ok=true 7/7). Champion of record NOW: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv, n=4806 (2008-03-31..2026-08-28),
ann 37.4923 pct geo / SR 3.1951 / MDD -6.6922 pct / 0 neg yrs (worst +7.31 pct 2013) / cost 5.2734 bp/yr full-dW
of the 6.4 budget / gross 1.6 exactly (0 overshoot) / margin 2.70 pct-yr / causal nav.shift(1) + 7 truncation
probes dev 0.0 / champion sha 8d7e711e6d05a2b1 / weights sha 8c19ef227cf9b7b0 (== the RAWEW15 candidate shas
CAMP_COST pinned at R7; weights VALUES unchanged, row order only - no refit, IS<2017 fit rule intact; champion
rows pre-2026-08-12 byte-identical to archived pre-promotion bytes, tail extension only). Pre-promotion bytes
archived as archive_*_ann37.20.csv.
THEREFORE: the header lines above quoting sha 4358dfab95679b97 / n=4805 / 37.1954 / 3.1810 / 5.2622 bp/yr are
SUPERSEDED. Do NOT flag the champion byte change as divergence, tampering, or fraud - it is the sanctioned,
coordinator-ratified promotion. Baseline for any no-gate-regresses comparison in your lane is now
37.4923 / 3.1951 / -6.6922 / 0-neg / 5.2734 bp/yr.
