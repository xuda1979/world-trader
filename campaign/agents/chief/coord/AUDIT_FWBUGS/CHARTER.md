# CHARTER: AUDIT_FWBUGS — adversarial framework TDD bug hunt

ROUND 1

Adversarial TDD bug-hunt of the reusable backtest framework campaign/bt/ (engine, metrics,
gates, reconcile, backtest) AND the champion builder. For each suspected bug: write a FAILING test
first (RED), confirm it fails, then fix (GREEN). Focus on:
 - cost_turnover / margin / borrow / cap_leverage correctness vs TRADE_RECORD_STANDARD
 - metrics ann_geo ruin-guard, SR, max_dd (NaN safety), neg_years
 - gates scramble p-value correctness, zero-runs, halves edge cases
 - reconcile turnover/ledger fail-closed
 - champion builder: full-|dW| (iter11 fix intact), margin, leverage epsilon, no lookahead
Add regression tests to campaign/bt/tests/test_*.py. Log each bug found+fixed with RED->GREEN
evidence in FINDINGS.md. Goal: 0 known bugs. Do NOT modify committed champion CSVs.

## ROUND 2 (coordinator standup 2026-09-07 01:3x)
R1: 2 real bugs fixed (turnover day-1 entry, neg_years fail-open). Round 2 hunts the code that
LANDED in R1 (adversarial, TDD, failing test first):
 (a) bt/shortability.py (borrow tiers, leg-drop), bt/gates.py plateau_ok (all-neighbors>=80pct
     of peak) + corr fail-closed, bt/metrics.py neg_years min_count, bt/engine.py day-1
     zero-seed - hunt boundary conditions (single-row frames, all-NaN, duplicate dates,
     tz-naive vs aware index, pandas 2.x behavior).
 (b) Audit the TEST files themselves for vacuous asserts (R1 found a return-True audit):
     re-run each round-1 test against a deliberately broken implementation and require the
     test to FAIL - any test that still passes is vacuous and must be fixed.
End FINDINGS.md with ROUND 2 DONE.
## ROUND 3 (coordinator standup 2026-09-07 07:2x CST)
Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (90 rows) FIRST - do NOT re-test any
listed-dead family; do NOT re-tune a dead signal into a new config (that is p-hacking). Honest
negatives with exact numbers are fine results. Every claim must reproduce from a script you save.
Round 3 - the T+1 enforcement gap (top framework caveat from AUDIT_GATES2):
 (a) bt/leakcheck.py: leak_probe(signal_df, ret_sr) -> same-period correlation p-value + lag-scan;
     opt-in bt/gates flag, default OFF. TDD: same-day-leak fixture FAILs (RED), causal fixture
     PASSES (GREEN), plus the real-world case: AUDIT_RECON's same-day NAV-drift signature
     (corr ~0.78 on the archived champion) must be DETECTED (use the archived leaky CSV if
     present, else synthesize the signature).
 (b) Run the FULL bt suite; triage failures NOT already classified costfix-delta-pinned; classify
     loudly (new bug -> fix RED-to-GREEN; known -> list under pending-re-emit).

 (c) test_beats_passive.py: 12 RED, ownerless since 08:0x, excluded from the 12:50 commit
     manifest for that reason. Read it; decide honestly whether the assertion set is a real
     spec for an unshipped feature (then make it GREEN via minimal feature work, RED first per
     test) or a vacuous/misapplied spec (then rewrite or delete it LOUDLY in FINDINGS.md with
     the reason). Do not fake GREEN.

## ROUND 3 UPDATE (coordinator standup 2026-09-07 14:20 CST)
Item (c) below is adjudicated MOOT as written: test_beats_passive.py shipped 21/21 GREEN by
HUNT_INTERNATIONAL2 R3 (accepted at the 14:08 standup; coordinator re-ran it GREEN again at
14:19). Do NOT rebuild or delete it. Instead, treat (c) as VERIFY-ONLY: write your OWN RED
fixtures against the shipped implementation (campaign/bt/beats_passive.py + the bt/gates.py
opt-in wiring), confirm they pass on the shipped code, and log any real gap RED->GREEN.
Also in scope for your R3, RED first: the M22 max_dd NaN-poison coverage gap you found in
R2 (no bt test kills a max-dd NaN-poison mutation — mutrun3_cross_final.txt
VACUOUS-EVERYWHERE). Finally: backfill FINDINGS.md with R1 (2 bugs) + R2 (31-mutant run)
before starting R3 work — the log is the deliverable, and R1/R2 currently exist only as
work/ artifacts.

## ROUND 4 (coordinator standup 2026-09-07 17:2x CST) - fleet drained, R3 all-honest-negative; capacity restored (the M22 vacuous-mutant coverage gap)
Your R2 found the metrics.maxdd M22 mutant is the suite only VACUOUS-EVERYWHERE survivor - no
test kills it. Round 4: RED-first test that kills M22 (fixture where a NaN-year poisons the
drawdown path; assert fail-closed behavior), then GREEN, then re-run your mutant pass to
confirm 0 vacuous survivors for metrics.py. Also: confirm the full bt suite is green from repo
root (it read 316 passed / 0 failed at 17:1x from THIS session).
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
 EXECUTE GATES_CONTRACT_V2 section-12 Step-2 flip, runbook steps
 2-6 VERBATIM, ONE COMMIT (bt/ is yours this round - that file list ONLY, nothing else in bt/):
 step 2. gates.py leak_on default True + docstring (the flip line is 'leak_check', True).
 step 3. Delete test_fwbugs_audit_r3.py::test_gates_default_has_no_leak_gate.
 step 4. Add sig= to test_beats_passive.py::test_gates_run_opt_in and
   test_gates_audit_r3.py::test_r3_bp_full_trio_still_passes_genuine_alpha (their pass-is-True
   must test alpha, not leak-absence).
 step 5. Move AUDIT_GATES2/r4/test_r4_leakflip_pair.py's 4 tests into campaign/bt/tests/ (drop
   the [OLD] pin; RED-first evidence already in the contract).
 step 6. Full suite green from repo root; grep the 26 production call sites - verdict-neutral
   proof (any site whose verdict changes under default-on = ESCALATE, do not absorb).
 Commit the flip as its own commit; if git is unavailable in your sandbox, leave the tree
 flip-only-in-flight and say so explicitly in FINDINGS.

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

 (a) DEFINITIVE COMMIT-WAVE MANIFEST (docs-only, work_r6/commit_wave_manifest.md): enumerate
 every uncommitted file under campaign/ (317 paths at 11:4x incl the 13-file bt drift, contract
 docs, banners, keeper argv fix, DEAD_IDEAS 133->137, champion_card.py fix, round5b pins); one
 line each: why-changed + test evidence + classify commit-now / needs-discussion / discard.
 Suite evidence: 410/0 coordinator-run 11:4x.
 (b) NO code edits.

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
 (a) POST-WAVE VERIFICATION (the commit wave lands at this standup):
 clone the repo to a temp dir, run a bt-suite smoke (collect-only or a bounded subset) from the
 fresh clone, and confirm or KILL the fresh-clone ModuleNotFoundError escalation with exact
 output. Verify only - do NOT commit. (b) Docs-only (insert-only banner, AUDIT_CHAMP2 R4
 pattern): banner the stale coord/verify_champion_standup_1140.json citation in
 GATES_CONTRACT_V2.md with a re-point to verify_champion_standup_1830.json (7/7 fresh 18:3x) -
 do not delete or edit existing lines.

## ROUND 8 (coordinator standup 2026-09-09 04:03 CST) - fleet drained 21/21 R7 DONE; capacity restored (16 procs); domains closed: audit rotation + seeded lanes
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED, supersedes V1) + campaign/results/DEAD_IDEAS.csv
(recount rows yourself; 153 at R7-end, dynamic). Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
ann 37.1954 pct / SR 3.1810 / MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), sha 4358dfab95679b97,
re-verified 2026-09-09 03:5x standup via 23:40 artifact (bytes unchanged since Sep 7 11:24, ok=true 7/7).
R7 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
HARD RULES: no dead-family re-test; no re-tuning a dead signal into a new config (p-hacking ban); all r8 work
stays in YOUR OWN dir; nothing is applied to bt/, shared data trees, or the champion without explicit chief
instruction; honest negatives with exact numbers are fine results; every claim must reproduce from a script you save.

YOUR R8 LANE: AUDIT ROTATION (R4 pattern): (i) pick 6 DEAD_IDEAS.csv rows from OTHER families that carry saved scripts; independently reproduce each from its CITED script; report reproduced / diverged (exact numbers) / unreproducible per row. (ii) re-check the bt/ clone-fix recipe status (committed vs still 444-passing-only-local) and report.
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
