# CHARTER: AUDIT_CHAMP2 — independent champion replica-audit vs all constraints

ROUND 1

INDEPENDENT adversarial re-verification of champion campaign/results/GOAL100_RAWEW13v2_
WEIGHTED_GEAR16_daily.csv from RAW sleeve files + builder (campaign/scripts/rawew13v2_build.py).
Do NOT trust the committed CSV or any doc. Recompute from the sleeve files and verify EVERY:
 1. 6.4bps one-side FULL |dW| (no 0.5x)  2. IBKR 4.5% margin on (gross-1)  3. leverage<=1.6
    (0 overshoot)  4. 0 negative calendar years  5. fungible-short pool (no single-name equity
    short, or model it)  6. T+1 no lookahead (perturbation)  7. byte reproducibility (maxdev<1e-12).
Independently recompute ann_geo/SR_d/MaxDD/neg-years and compare to the committed champion numbers.
If ANY check fails, add a failing TDD test first, then fix (you may fix the builder but NOT silently
alter committed champion semantics). Log exact PASS/FAIL numbers in FINDINGS.md. Reuse
campaign/audit_harness_newconstraints.py as a starting point (already 7/7 PASS) but audit it too.

## ROUND 2 (coordinator standup 2026-09-07 01:3x)
Your R1 C6 FAIL forced the coordinator-approved causal re-emit (2026-09-07 00:45): builder
nav.shift(1), committed ann 39.85pct vs archived leak 40.84pct
(archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_SAMEDAYLEAK_ann40.84.csv). Round 2 = fresh C1-C7
audit of the NEW champion:
 (a) C1-C7 all re-run against the current tree (expect 7/7, C6 PASS at honest 39.85pct).
 (b) Byte-repro builder + committed CSV; verify RAWEW13v2_IS_SR_weights.csv unchanged
     (relw never depended on nav - weights must be identical pre/post re-emit).
 (c) PROVENANCE: campaign/results/GOAL100_TRUTH20Y files are untracked (Sep 1 mtime) - find
     their builder, verify their stats, flag any stale-claim risk in results/.
 (d) Verify new-vs-archived champion differs by EXACTLY the causal-vs-leak mechanism
     (max dev ~3.96e-3, corr 0.99988) - pin with a test.
End FINDINGS.md with ROUND 2 DONE.
## ROUND 3 (coordinator standup 2026-09-07 07:2x CST)
Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (90 rows) FIRST - do NOT re-test any
listed-dead family; do NOT re-tune a dead signal into a new config (that is p-hacking). Honest
negatives with exact numbers are fine results. Every claim must reproduce from a script you save.
Round 3 - docs integrity + weights audit:
 (a) Stale-claim lint (TDD): grep campaign docs for 40.84 quoted as CURRENT headline and TRUTH20Y
     quoted as current champion. RED first (the iter11 memo main-table title is a known hazard),
     then ADDITIVE supersede banners to offending docs (never rewrite history), then GREEN. Show
     before/after grep evidence.
 (b) Weights-vs-builder cross-check: champion weights CSV vs 13 sleeve builders' weights (max dev
     per column, pin tol 1e-10; any drift = costfix-delta, documented not new-bug).
 (c) CHAMPION_CARD.md generated from the builder + pin test regenerating it byte-identical.

## ROUND 4 (coordinator standup 2026-09-07 17:2x CST) - fleet drained, R3 all-honest-negative; capacity restored (stale-prose hygiene + card sync)
(a) Re-run verify_champion via campaign/bt/verify_champion_r3_cmd.sh (NEW canonical wrapper -
    the docstring usage block is a template and fails closed on partial sleeve maps; the 15:2x
    and 17:0x standups both hit this). Confirm 7/7 ok + regenerate campaign/CHAMPION_CARD.md.
(b) Stale-number sweep: R3 found prose quoting superseded headlines (39.6873 pct,
    CHAMPION20Y_V2). GOAL100_CHAMPION.md section 11 now carries a coordinator banner (step-3
    verify DIFFs 3.1e-3..6.2e-3). Sweep campaign top-level markdown for remaining un-bannered
    stale headline quotes; banner them (insert-only, never delete history), list every file.
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
 (a) CHAMPION20Y_V2 rebuild-or-drop EXECUTION (chartered by the
 coordinator's 03:1x deprecation banner): rebuild the 20y table from POST-costfix sleeves with
 fresh builder --verify IDENTICAL + MHX shortability re-audit, OR complete the quarantine doc on
 why it stays deprecated. Either is an honest outcome; a rebuild that cannot reach IDENTICAL is
 a DROP with numbers. (b) Fix the champion_card.py PYTHONPATH footgun (one-line sys.path insert
 or wrapper script, TDD). (c) GOAL80_FINAL_REPORT.md: coordinator leaned CONFIRM (self-scoped
 prior-campaign history) - independently verify its 43.2 pct best-honest claim is self-consistent
 with its own artifacts; confirm or flag with numbers.

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

 (a) Independently verify CAMP_COST's 14-sleeve CANDIDATE when it lands (your own code, their
 artifacts): 7/7 checks + cost reconciliation + causality/truncation probes ON THE CANDIDATE;
 verdict in FINDINGS; do NOT edit their files.
 (b) Confirm the champion_card.py sys.path fix + your round5b pins remain green on the current
 tree (both UNCOMMITTED - re-flag for the commit wave).
 (c) NO campaign doc edits this round.

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
 (a) AUDIT: AUDIT_FWBUGS-R6 census - spot-check 20 randomly-seeded paths
 from their manifest for existence + classification correctness (record the seed in FINDINGS);
 verify both escalations reproduce (fresh-clone ModuleNotFoundError; the 1140 verify-JSON citation
 is a 145-byte ok:false failed invocation). (b) Your R6 pins (round5/round5b/round6 test files +
 champion_card.py fix) land in this standup's commit wave - re-run your full suite on the TRACKED
 state and confirm green; flag any test that behaves differently tracked vs untracked.

## ROUND 8 (coordinator standup 2026-09-09 04:03 CST) - fleet drained 21/21 R7 DONE; capacity restored (16 procs); domains closed: audit rotation + seeded lanes
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED, supersedes V1) + campaign/results/DEAD_IDEAS.csv
(recount rows yourself; 153 at R7-end, dynamic). Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
ann 37.1954 pct / SR 3.1810 / MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), sha 4358dfab95679b97,
re-verified 2026-09-09 03:5x standup via 23:40 artifact (bytes unchanged since Sep 7 11:24, ok=true 7/7).
R7 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
HARD RULES: no dead-family re-test; no re-tuning a dead signal into a new config (p-hacking ban); all r8 work
stays in YOUR OWN dir; nothing is applied to bt/, shared data trees, or the champion without explicit chief
instruction; honest negatives with exact numbers are fine results; every claim must reproduce from a script you save.

YOUR R8 LANE: AUDIT ROTATION (R4 pattern): (i) pick 6 DEAD_IDEAS.csv rows from OTHER families that carry saved scripts; independently reproduce each from its CITED script; report reproduced / diverged (exact numbers) / unreproducible per row. (ii) re-confirm champion sha 4358dfab95679b97 bytes unchanged at r8 start and note any divergence.
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
AUDIT_CHAMP2 lane correction: your R8 item (ii) becomes - confirm champion bytes UNCHANGED at sha 8d7e711e6d05a2b1 since the 19:03 promotion; bytes equal to that sha = PASS, not divergence.
