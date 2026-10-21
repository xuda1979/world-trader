# CHARTER: HUNT_TREASFUT — treasury futures curve / basis round-2

ROUND 1

Round-2 US-rates. Prior a6r7 bond2y trend + A1credit regime are champion slots. Test NEW
decoupled rates sleeves high-corr to champion would be redundant — focus on genuinely low-corr:
 (a) FRONTIER: treasury futures CURVE trade from constant-maturity FRED (DGS2/DGS5/DGS10/DGS30):
     long 2y short 10y when curve steeps, flat when flattening, vol-scaled, daily.
 (b) TIPS real-yield (DFII10/20/30) level-reversion directional.
 (c) Term-structure butterfly (2s10s30s) — if implementable with DGS series.
 (d) International yield-spread (US10 - DE/CA/JP10 from more_fred IRLTLT...) partial carry.
Costs: DGS-based trades approximate treasury futures at 6.4bps full-|dW|. All gates, |corr|<0.15 vs
champion (watch corr to a6r7/A1credit). Data more_fred (DGS*,T10Y2Y,DFII*,IRLTLT*) + newdata.
Read GATES_CONTRACT.md first.

## ROUND 2 (coordinator standup 2026-09-07 01:3x)
R1: curve/fly/intlcarry/tipsrev honest negatives (the R1 repro-test FAIL was the champion
re-emit landing mid-session; current tree is green, 81 passed - ignore that env note).
Round 2 on FRED cash-yields (DGS2/DGS10/DGS30 on disk):
 (a) Duration-matched cash-yield engine: convert DGS yield changes to futures-comparable
     returns via modified duration (DUR 4.4/7.7/15.5 for 2y/10y/30y proxies), then rerun the
     R1 momentum/curve machinery with 2008+ depth and REAL vol-targeting.
 (b) Steepener kink-trade: 2s10s + 10s30s combos, vol-targeted, cost-honest.
 (c) Yield LEVEL momentum with regime filter (T5YIFR direction) - long-duration when real
     yields falling, tested as overlay AND standalone.
Gates/costs per contract. End FINDINGS.md with ROUND 2 DONE.
## ROUND 3 (coordinator standup 2026-09-07 07:2x CST)
Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (90 rows) FIRST - do NOT re-test any
listed-dead family; do NOT re-tune a dead signal into a new config (that is p-hacking). Honest
negatives with exact numbers are fine results. Every claim must reproduce from a script you save.
Rates momentum DEAD (R1+R2). Round 3 - champion-integrity duty:
 (a) GOAL100_TRUTH20Y reconstruction attempt: AUDIT_CHAMP2 verified the 3 CSVs+JSON reconcile with
     their OWN json but the BUILDER is absent from the tree. Read G4_detrun/FINDINGS.md concept,
     attempt reconstruction from the described mechanism; if you reproduce BAL/AGGRESSIVE/SAFE to
     <=1e-12: save builder + TDD tests and report. If not: write work_r3/TRUTH20Y_QUARANTINE.md
     (what was attempted, exact max dev) and recommend quarantine. Either way add a lint test that
     FAILS if any campaign doc quotes TRUTH20Y as current champion (RED first - a passing lint
     test is a fine result; show the grep evidence).
 (b) Cross-verify HUNT_CREDIT2's round-2 negative rows from saved CSVs; escalate mismatches.

## ROUND 4 (coordinator standup 2026-09-07 17:2x CST) - fleet drained, R3 all-honest-negative; capacity restored (close the V2 provenance break YOU found)
Your R3 proved champion20y_build.py --verify now DIFFs (coordinator re-confirmed 17:0x: BAL
3.107e-03 / SAFE 6.160e-03 / AGGR 6.206e-03) after the costfix wave touched its feeding sleeves,
and TRUTH20Y is a provenance-orphan. Round 4: (a) produce the corrected CHAMPION20Y_V2 rebuild
path - which sleeve set reproduces it EXACTLY today (git-historical sleeves vs __costfix sleeves;
try a worktree of the pre-costfix commit if needed) - or prove it unreproducible and extend the
quarantine memo to CHAMPION20Y_V2 itself; (b) 4-row DEAD_IDEAS audit rotation (non-treasury
families). Champion RAWEW13v2 bytes: untouched.
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
 (a) NEW CORNER (pre-registered): TreasuryDirect auction data
 (keyless, live per altdata5) - auction-cycle positioning family (pre/post-auction drift in
 futures or a6r7-adjacent tenors WITHOUT re-testing a6r7's dead configs). Document fetch spans +
 gap structure. Full V2 battery; honest negative expected.

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

 (a) FRAUD-CATCH cross-verification: reproduce AUDIT_CHAMP2's GOAL80 byte-exact repro
 (coord/AUDIT_CHAMP2/work_r5/goal80_coordfinal_repro_TGT08_predualmomfix.csv + the pins in
 bt/tests/test_audit_champ2_round5b.py) with YOUR OWN builder code. The 43.19 arith / 53.36 CAGR
 / 2.13x median gross / financing-unpriced verdict is consequential - confirm or refute it.
 (b) TRUTH20Y_QUARANTINE.md: append-only R6 note ONLY if you find a discrepancy.

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
 (a) NEW CORNER (pre-registered; NEW data source): ECB SDMX
 (keyless, live per the altdata6 2026-09-08 roster) euro-area yield-curve family - slope /
 curvature factor sleeves at WEEKLY or slower rebalance from the SDMX yield-curve dataflow, PIT
 by publication calendar. Must DECORRELATE from a6r7 bond-2y trend (corr gate 0.15/0.35) and
 survive the era-table discipline that closed your FX-carry sibling: MANDATORY sub-span stability
 pre/post-2010 (an effect that only exists post-2013 is a FAIL with that number stated). Cite
 dataflow + fetched row counts. Full V2 battery; honest negative expected. (b) TRUTH20Y_QUARANTINE
 duty: append ONLY on a real discrepancy in the 7 pins (zero found R6).

## ROUND 8 (coordinator standup 2026-09-09 04:03 CST) - fleet drained 21/21 R7 DONE; capacity restored (16 procs); domains closed: audit rotation + seeded lanes
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED, supersedes V1) + campaign/results/DEAD_IDEAS.csv
(recount rows yourself; 153 at R7-end, dynamic). Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
ann 37.1954 pct / SR 3.1810 / MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), sha 4358dfab95679b97,
re-verified 2026-09-09 03:5x standup via 23:40 artifact (bytes unchanged since Sep 7 11:24, ok=true 7/7).
R7 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
HARD RULES: no dead-family re-test; no re-tuning a dead signal into a new config (p-hacking ban); all r8 work
stays in YOUR OWN dir; nothing is applied to bt/, shared data trees, or the champion without explicit chief
instruction; honest negatives with exact numbers are fine results; every claim must reproduce from a script you save.

YOUR R8 LANE: AUDIT ROTATION (R4 pattern): (i) pick 6 DEAD_IDEAS.csv rows from families OTHER THAN treasury-futures that carry saved scripts; independently reproduce each from its CITED script (not FINDINGS prose); report reproduced / diverged (exact numbers) / unreproducible per row. (ii) pick 2 rows from your OWN family lacking a saved script and rebuild the script from FINDINGS description if derivable; tag the row upgraded-evidence.
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
