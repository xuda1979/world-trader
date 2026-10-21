# CHARTER: AUDIT_RECON — byte-repro + no-lookahead + trade-blotter reconciliation

ROUND 1

Independently verify integrity: (a) champion CSVs are byte-reproducible from committed sleeve
inputs (run rawew13v2_build.py --verify; must be IDENTICAL); (b) every sleeve used is T+1/no
lookahead (read the four levers: signal->position shift, vol-target trailing, throttle lag,
cost on |dW|); (c) reconstruct a period of the champion's implied weight path and confirm the
portfolio return = Wg_{t-1}*r_t (no same-day leak), and that turnover charged == |dW|*6.4bps on
that reconstruction; (d) confirm any equity-family sleeve (H21/XGB1y/MHX if in a pool) is not
overstating due to unmodeled shortability (see CAMP_SHORT). Produce an integrity report with
exact reproduction hashes/numbers in FINDINGS.md. Flag any discrepancy loudly.

## ROUND 2 (coordinator standup 2026-09-07 01:3x)
Your R1 found the same-day leak (39.85 honest vs 40.84 leaked). Round 2 on the RE-EMITTED
champion (2026-09-07 00:45):
 (a) Full blotter reconciliation of the new CSV: cost charge vs dW-abs-sum x 6.4bp (expect
     4.94bp/yr), margin charge exact, no-lookahead perturbation (turnover-vs-same-day-return
     corr should be ~0.2 legitimate responsiveness, NOT the 0.34/0.78 leak signature).
 (b) DEAD_IDEAS.csv spot-audit: re-run 3 sampled dead configs (COT sw-follow lb12, TIPS
     reversion N252, intl carry lag0) - verify the dead verdict reproduces.
 (c) Lineage pin: new-vs-archived champion diff = causal mechanism only (write a test).
End FINDINGS.md with ROUND 2 DONE.
## ROUND 3 (coordinator standup 2026-09-07 07:2x CST)
Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (90 rows) FIRST - do NOT re-test any
listed-dead family; do NOT re-tune a dead signal into a new config (that is p-hacking). Honest
negatives with exact numbers are fine results. Every claim must reproduce from a script you save.
Round 3 - build the re-emit ACCEPTANCE TOOL before the wave runs:
 (a) bt/verify_champion.py: given (champion_csv, weights_csv, 13 sleeve CSVs) verify INDEPENDENTLY
     of engine internals: byte-repro from builder arithmetic; full-dW cost reconciliation from the
     WEIGHTS themselves (your own algebra, not engine.cost_turnover); causality (weights ==
     f(nav.shift(1)), your R1 mechanism); daily gross <= 1.6; negy + MDD + worst-year gates.
     Exit code 0/1, JSON report, fail-closed on missing input. TDD with a synthetic 3-sleeve
     mini-champion fixture (RED on each injected defect: half-turn cost, same-day weights,
     gross 1.7, one neg year).
 (b) Run against the CURRENT committed champion; document the expected costfix-delta result.
     The coordinator will run this tool to accept the re-emit wave.

## ROUND 4 (coordinator standup 2026-09-07 17:2x CST) - fleet drained, R3 all-honest-negative; capacity restored (integrity report for the R4 wave)
Round 4 runs concurrently with coordinator edits (GOAL100_CHAMPION.md banner, NEW
campaign/bt/verify_champion_r3_cmd.sh, fleet_keeper.py plan() fix + test, keeper supervision
logs). Produce the usual integrity report ON THE CHAMPION BYTES ONLY: sha256 of
GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv + weights CSV vs HEAD, builder --verify IDENTICAL,
and confirm champion bytes did not move during the round (they must not). Flag ANY
coordinator-file drift you find - including mine.
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
 Post-flip acceptance round (runs AFTER AUDIT_FWBUGS lands the
 section-12 flip - poll their FINDINGS.md; if not landed by your start, audit the CURRENT tree
 state instead and state which you did): (a) verify_champion_r3_cmd.sh 7/7 and champion
 UNCHANGED by the flip (champion sha 4358dfab95679b97 before == after - prove the gates flip is
 champion-neutral). (b) Re-run the 26 production call-site census yourself; any verdict change
 under default-on leak = escalation. (c) Confirm commit-wave B5 state (dirty path count + list)
 for the coordinator.

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

 (a) Reconcile the CAMP_COST CANDIDATE book vs the champion of record: cost reconciliation at
 6.4bps full-dW on the 14-sleeve build + causality/truncation probes; your own code.
 (b) Fleet-status artifact: run coord/fleet_keeper.py status (safe) + cross-check monitor_v4
 output; log the authoritative view (ROUND-mismatch BLOCKED walls are known-false alarms).

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
 (a) CENTERPIECE - blotter day-weight reconciliation row (carried r7
 queue item): reconcile the champion's daily |dW|-charged cost series against the blotter record
 at DAY granularity; publish the reconciliation row + any day-weight mismatches with exact
 numbers. R5's scalar-probe lesson applies: ship the generator script WITH the artifact.
 (b) Fleet-status snapshot as in your R6(b): keeper status + monitor_v4 ONE_SHOT cross-check +
 commit-wave state, timestamped.

## ROUND 8 (coordinator standup 2026-09-09 04:03 CST) - fleet drained 21/21 R7 DONE; capacity restored (16 procs); domains closed: audit rotation + seeded lanes
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED, supersedes V1) + campaign/results/DEAD_IDEAS.csv
(recount rows yourself; 153 at R7-end, dynamic). Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
ann 37.1954 pct / SR 3.1810 / MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), sha 4358dfab95679b97,
re-verified 2026-09-09 03:5x standup via 23:40 artifact (bytes unchanged since Sep 7 11:24, ok=true 7/7).
R7 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
HARD RULES: no dead-family re-test; no re-tuning a dead signal into a new config (p-hacking ban); all r8 work
stays in YOUR OWN dir; nothing is applied to bt/, shared data trees, or the champion without explicit chief
instruction; honest negatives with exact numbers are fine results; every claim must reproduce from a script you save.

YOUR R8 LANE: SEEDED LANE (r7 close-out, quantified 0.537 bp/yr): DRAFT the day-1 entry-cost fix for the Wg builder - TDD, failing test first, as a .patch file + test saved in YOUR OWN dir; do NOT apply to bt/ or any shared tree. Quantify the champion cost-book effect precisely (your r7 claim: reported 5.2622 bp/yr vs true ~5.80 with day-1 entry charged). Chief applies after verification. Then AUDIT ROTATION: 4 other-family DEAD_IDEAS rows reproduced from cited scripts.
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
AUDIT_RECON lane correction: quantify the day-1 entry-cost fix against the PROMOTED book - reported cost is now 5.2734 bp/yr (not 5.2622); your ~5.80 true-cost estimate must be re-derived on the n=4806 book.
