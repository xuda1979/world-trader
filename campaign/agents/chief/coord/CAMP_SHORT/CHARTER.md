# CHARTER: CAMP_SHORT — non-shortable-stock modeling + integration

ROUND 1

Build a rigorous, reusable NON-SHORTABLE-STOCK model per IBKR reality and integrate it as a
fail-closed gate for any equity L/S sleeve.
 1. Research: what fraction of US small/micro-caps are hard-to-borrow / not shortable, and the
    borrow fee schedule at IBKR (hard-to-borrow fees, locate requirements, short-sale constraints).
 2. Model: implement bt/shortability.py with a shortability_gate(weights, universe_mcap/rank):
    - drop or reweight the short leg of names below a size/borrow threshold (configurable frac),
    - charge a borrow fee on the remaining short notional (IBKR hard-to-borrow sliding fee, not the
      flat 0.5% — make it parameterizable, default calibrated to IBKR typical 0.5-20%/yr by
      borrow tier).
 3. Test (TDD): campaign/bt/tests/test_shortability.py — RED->GREEN: (a) names above threshold
    shortable, below dropped; (b) borrow fee charged correctly; (c) no-lookahead (borrow that day).
 4. Impact: run the champion's equity-family sleeves (H21_f5, XGB1y, MHX) through the model and
    report the honest ann/SR/MDD change. Determine if any is materially overstating returns.
 Deliver model + tests + impact report in FINDINGS.md. Do NOT modify committed champion CSVs.

## ROUND 2 (coordinator standup 2026-09-07 01:3x)
R1 delivered shortability.py + 5 tests; the champion has no single-name L/S slot. Round 2:
 (a) Publish the ~20-line integration snippet wiring shortability into the round-2 hunt sleeve
     template: any candidate shorting single names passes tiered-borrow + non-shortable-drop
     BEFORE gates (put it in your FINDINGS for other agents to copy).
 (b) Re-run the champion under TIERED borrow (0.5/1/3 pct ladders) - R1 flagged MHX-style
     75bps/yr tier risk; quantify champion sensitivity (expected ~0: shorts are futures/ETF/FX).
 (c) Add a borrow-stress scenario to a results/ JSON for the ops runbook.
End FINDINGS.md with ROUND 2 DONE.
## ROUND 3 (coordinator standup 2026-09-07 07:2x CST)
Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (90 rows) FIRST - do NOT re-test any
listed-dead family; do NOT re-tune a dead signal into a new config (that is p-hacking). Honest
negatives with exact numbers are fine results. Every claim must reproduce from a script you save.
Round 3 - borrow census for the integration lane:
 (a) Library stress census: top-30 campaign/results/sleeve_library sleeves by SR (+ any
     BLEND_CANDIDATE_SUBMISSION): reconstruct or FAIL-CLOSED-flag short legs (SHORT_LEG_UNKNOWN =
     cannot be integrated, loud); tier ladder 0.5/2/8 pct + NONE-tier drops; per-sleeve ann drag +
     which survive integration-grade borrow pricing. Output
     campaign/results/CAMP_SHORT_LIBRARY_BORROW_CENSUS.json + pin tests.
 (b) Publish the R2(a) pregate snippet to work_r3/BLEND_PREGATE.md for HUNT_VOL2 to consume.
 (c) If the champion re-emits mid-run: re-run the R2(b) ladder vs the NEW champion, report both.

## ROUND 4 (coordinator standup 2026-09-07 17:2x CST) - fleet drained, R3 all-honest-negative; capacity restored (fix the library bug YOU found)
strat_ls_equity.py neg branch flips already-negative weights positive: every short leg lands
long, 130/30 is really 160/0. Round 4: TDD RED->GREEN fix in
tools/quant/hedge_fund_strats/strat_ls_equity.py (neg = abs(neg)/abs(neg).sum() * short_scale
as positive short notional, or negate once - pick the convention that matches the docstring,
cite it), fixture test that short legs are actually short. Then re-run YOUR R1 MHX impact
numbers under the fixed code and state what changed. Committed champion CSVs: untouched.
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
 (a) MHX shortability re-audit (carried from the CHAMPION20Y_V2
 deprecation banner): does any CURRENT champion sleeve imply single-name short exposure
 post-costfix? The 4 regenerated sleeves moved weights (brwt15 -0.040126, diescrack -0.032070,
 QAxasts -0.007740, dualmom -0.005128). (b) Spot-check C5 shortability on the champion of record
 (harness C5) and confirm top gross shares with exact numbers. No new signals.

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

 (a) Capability verdict stands (0/62,465 slot-days net-short; borrow immaterial at champion
 level). FRAUD-CATCH cross-verification: reproduce CAMP_BORROW's AND CAMP_COST's R5 verdicts
 from published artifacts with your own code. Mismatch -> escalate.
 (b) DEAD_IDEAS curation of the short/borrow rows.

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
 (a) AUDIT (own code): AUDIT_GATES2's V2 conformance sweep - spot-recompute
 2 of their 5 lane claims (HUNT_CMDT2 and the RES_BASIS row-137 standalone-PASS) from published
 artifacts. (b) Capability lane refresh: re-run the 62,465 slot-day net-short census invariant on
 the current tree (expect 0 net-short slot-days still) and re-pin the 8 pct HTB tier arithmetic
 (3.2931 bps/yr) against CAMP_BORROW's 4 open drift flags (>10 pct rel).

## ROUND 8 (coordinator standup 2026-09-09 04:03 CST) - fleet drained 21/21 R7 DONE; capacity restored (16 procs); domains closed: audit rotation + seeded lanes
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED, supersedes V1) + campaign/results/DEAD_IDEAS.csv
(recount rows yourself; 153 at R7-end, dynamic). Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
ann 37.1954 pct / SR 3.1810 / MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), sha 4358dfab95679b97,
re-verified 2026-09-09 03:5x standup via 23:40 artifact (bytes unchanged since Sep 7 11:24, ok=true 7/7).
R7 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
HARD RULES: no dead-family re-test; no re-tuning a dead signal into a new config (p-hacking ban); all r8 work
stays in YOUR OWN dir; nothing is applied to bt/, shared data trees, or the champion without explicit chief
instruction; honest negatives with exact numbers are fine results; every claim must reproduce from a script you save.

YOUR R8 LANE: AUDIT ROTATION (R4 pattern): (i) pick 6 DEAD_IDEAS.csv rows from families OTHER THAN short-campaign that carry saved scripts; independently reproduce each from its CITED script; report reproduced / diverged (exact numbers) / unreproducible per row - borrow/non-shortable constraints in the cited configs must be honored exactly as recorded. (ii) 2 OWN-family rows: rebuild missing scripts if derivable; tag upgraded-evidence.
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
