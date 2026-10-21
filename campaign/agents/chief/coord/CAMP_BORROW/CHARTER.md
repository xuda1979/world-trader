# CHARTER: CAMP_BORROW — IBKR call-rate + borrow-cost audit

ROUND 1

Audit and, where needed, correct the cost model for IBKR reality:
 1. Call rate: verify the champion charges 4.5%/yr margin on (gross-1) — confirm this is a
    reasonable IBKR call-rate proxy (current fed funds + margin spread) and stress the margin
    drag if call rate rises to 5.5%/6.5% (report ann/SR/MDD sensitivity).
 2. Borrow: verify borrow 0.5%/yr short-notional is charged on EVERY short sleeve; where
    hard-to-borrow instruments exist (e.g., natgas LEAPS?, equity books), model a higher borrow tier.
 3. Reconciliation: confirm the champion's margin + borrow algebra exactly reconcile to the
    TRADE_RECORD_STANDARD ledgers (qty_notional=|dW|, cost_bps=6.4, borrow, margin).
 4. TDD: add/extend campaign/bt tests for margin-call-rate stress + borrow-tier correctness.
 Produce an honest sensitivity table (call rate 4.5/5.5/6.5, borrow 0.5/2/5%) -> champion
 ann/SR/MDD. Deliver findings in FINDINGS.md.

## ROUND 2 (coordinator standup 2026-09-07 01:3x)
R1 verified margin on the LEAKED champion. Round 2 re-audits the NEW CAUSAL champion
(re-emit 2026-09-07 00:45, ann 39.85pct, SR 3.296):
 (a) Recompute margin drag on (gross-1)=0.6 at 4.5pct/yr - expect 2.70pct/yr unchanged;
     verify gross equals 1.600000 daily in the new weight stream.
 (b) Call-rate stress ladder 4.5->5.5->6.5->8 pct/yr on the new headline; publish the table.
 (c) Fail-closed: if gross deviates from 1.6 by >1e-9 any day, FLAG LOUDLY (re-emit regression).
End FINDINGS.md with ROUND 2 DONE.
## ROUND 3 (coordinator standup 2026-09-07 07:2x CST)
Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (90 rows) FIRST - do NOT re-test any
listed-dead family; do NOT re-tune a dead signal into a new config (that is p-hacking). Honest
negatives with exact numbers are fine results. Every claim must reproduce from a script you save.
Round 3 - financing stress runbook v2 + blend support:
 (a) Call-rate path scenarios on the champion via bt/borrow.py: sustained 12 pct call rate for 90d
     (2008-style), 8 pct for 30d (2020-style), sustained 6 pct for 1y; report ann/MDD/neg_years
     per scenario. Extend the CAMP_BORROW ops JSON with a rate_paths block + pin tests.
 (b) Blend support: bt helper blending levered champion + unlevered sleeve - exact margin-delta
     algebra when gross changes, TDD RED fixture first (wrong-margin-sign test fails), then GREEN.

## ROUND 4 (coordinator standup 2026-09-07 17:2x CST) - fleet drained, R3 all-honest-negative; capacity restored (productize the R3 ladder)
Your R3 JSON ladder is scenario-anchored. Round 4: extract it into campaign/bt/financing_stress.py
- a reusable tool: given a sleeve/champion net series + gross path, emit the IBKR call-rate /
borrow-tier stress table (per +1pp rung: ann/SR/MDD delta) as JSON + TDD
campaign/bt/tests/test_financing_stress.py (RED first). Validate: tool output on the committed
champion reproduces your R3 numbers to 1e-12 and CAMP_BORROW R1 4.5/5.5/6.5 pct table
(-0.84pp ann per +1pp). Fail-closed on missing inputs.
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
 (a) Freshness audit of the financing stack vs published IBKR rates:
 call 4.5 pct on (gross-1) => margin drag 2.70 pct/yr (re-derive); borrow 0.5 pct/yr on shorts
 (verify which sleeves actually carry short legs + their gross share). (b) Flag any drift > 10
 pct relative vs the modeled numbers with exact citations. No new signals; no champion edits.

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

 (a) DOCS-ONLY (charter-named file): append the 4 rate-drift flags + the both-directions reading
 from your R5 (4.5 pct flat conservative vs today DFF+1.5pp = 5.13; period-path mean 2.93+1.5
 understates by +1.30pp) to campaign/GOAL100_CHAMPION.md under a new section '## FINANCING
 CONVENTION DISCLOSURE (2026-09-08)'. Do not touch results/ or bt/.
 (b) FRAUD-CATCH: reproduce DATA_FREDMORE's R5 verdicts from published artifacts.

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
 (a) AUDIT (own code): HUNT_FXCARRY2-R6 - re-run their
 r6_treasfut_repro_scorecard.json path; confirm all 19 books x cells and the DEFECT-#3 conclusion
 (TREASFUT-R5 row absent from ALL historical states, not just the deduped one). (b) Borrow lane:
 your 4 drift flags stay open - re-measure against current curves and re-pin 0.2195
 bps/yr embedded at champion level. The DATA_ORGANIZE remediation path you delivered is ASSIGNED
 to DATA_FREDMORE/DATA_ETF_MORE this round - verify their landing NEXT round; do not implement it
 yourself (tools/ stays outside your charter).

## ROUND 8 (coordinator standup 2026-09-09 04:03 CST) - fleet drained 21/21 R7 DONE; capacity restored (16 procs); domains closed: audit rotation + seeded lanes
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED, supersedes V1) + campaign/results/DEAD_IDEAS.csv
(recount rows yourself; 153 at R7-end, dynamic). Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
ann 37.1954 pct / SR 3.1810 / MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), sha 4358dfab95679b97,
re-verified 2026-09-09 03:5x standup via 23:40 artifact (bytes unchanged since Sep 7 11:24, ok=true 7/7).
R7 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
HARD RULES: no dead-family re-test; no re-tuning a dead signal into a new config (p-hacking ban); all r8 work
stays in YOUR OWN dir; nothing is applied to bt/, shared data trees, or the champion without explicit chief
instruction; honest negatives with exact numbers are fine results; every claim must reproduce from a script you save.

YOUR R8 LANE: AUDIT ROTATION (R4 pattern): (i) pick 6 DEAD_IDEAS.csv rows from families OTHER THAN borrow-campaign that carry saved scripts; independently reproduce each from its CITED script; report reproduced / diverged (exact numbers) / unreproducible per row - IBKR call-rate/borrow assumptions in cited configs must match the recorded values. (ii) 2 OWN-family rows: rebuild missing scripts if derivable; tag upgraded-evidence.
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
