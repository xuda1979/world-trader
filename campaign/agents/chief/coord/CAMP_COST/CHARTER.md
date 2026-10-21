# CHARTER: CAMP_COST — full-|dW| @ 6.4bps one-side universal audit

ROUND 1

Audit EVERY rebalancing path for cost honesty (one-side FULL |dW| @ 6.4bps, TRADE_RECORD_STANDARD):
 1. Verify the champion builder charges FULL |dW| (not 0.5x) — confirm the iter11 fix is intact by
    re-running the regression test; also confirm no OTHER builder (campaign/scripts/*.py,
    C4_construct, champion_build, champion20y_build) still uses a 0.5 half-turn on its weight diffs.
 2. Grep for '0.5' cost patterns across campaign/scripts and campaign/agents (flag any 0.5*|dW|).
 3. Verify vol-target rebalances and throttle switches also charge full 6.4bps (no free rebalances).
 4. TDD: one regression test asserting NO builder undercharges turnover < full|dW|*6.4bps.
 Report each builder's cost-convention + any discrepancy with exact numbers. Deliver in FINDINGS.md.

## ROUND 2 (coordinator standup 2026-09-07 01:3x)
R1 found 2 slot-level half-turn offenders (dualmom ~0.1bps/yr, diescrack ~2.2bps/yr). Round 2:
 (a) Open the diescrack and dualmom sleeve builders, verify whether their INTERNAL cost models
     under-charge vs 6.4bps FULL dW (TDD: failing test first on a synthetic 2-day stream).
 (b) If confirmed, re-emit corrected sleeve net CSVs (byte-reproducible, report before/after
     sleeve ann) - do NOT touch the champion composite (coordinator will re-emit).
 (c) Sweep ALL 13 champion sleeves for the same defect class; publish a per-sleeve charge table.
End FINDINGS.md with ROUND 2 DONE.
## ROUND 3 (coordinator standup 2026-09-07 07:2x CST)
Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (90 rows) FIRST - do NOT re-test any
listed-dead family; do NOT re-tune a dead signal into a new config (that is p-hacking). Honest
negatives with exact numbers are fine results. Every claim must reproduce from a script you save.
Round 3 - re-emit readiness + cost attribution (committed champion untouched until the
coordinator's re-emit wave):
 (a) Finish R2 sweep (all-13 per-sleeve charge table) if incomplete. Byte-repro the CURRENT
     committed champion and DOCUMENT the expected 12 pin failures as costfix-delta PENDING-REEMIT
     (do not soften the pins - they keep teeth).
 (b) Turnover attribution: per-sleeve share of champion turnover cost, annual bps, top-5 drivers;
     work_r3/turnover_attribution.csv + tests.
 (c) IF the all-13 costfixed pool is byte-reproducible by your generators (incl. brwt10/brwt7/brwt5):
     emit a RE-EMIT CANDIDATE champion CSV + weights into work_r3 (NOT results, NOT committed) with
     exact before/after headline deltas + full-gate table. The coordinator performs the actual
     re-emit in a later standup from your candidate.

## R3 AMENDMENT (coordinator standup session 2, 2026-09-07 07:5x CST)
The re-emit ALREADY HAPPENED: coordinator ran rawew13v2_build.py --emit at 07:28 from the
4 costfixed sleeves (verified: builder --verify byte-exact 9.996e-17; fresh stats ann
39.69% / SR 3.289 / MDD -6.79% / 0/19 neg years; four-corner identity champion-archived =
shift + costfix verified to 9.996e-17 using your __prefix.csv archives; pins updated and
full suite 191 pass / 1 fail = your intentional brwt10/7/5 fail-closed gate).
Therefore, for YOUR round 3, replace (a) and (c) above with:
 (a') Skip the PENDING-REEMIT documentation (done). Instead: independent re-verification of
      the 07:28 emit from your own generators; report any residual vs the committed CSV.
 (c') PRIMARY MANDATE unchanged and now URGENT: brwt10/7/5 have NO committed generator in
      the repo (coordinator re-verified: only consumers reference them). Rebuild them TDD
      (failing test first, FULL |dW| @ 6.4bps), quantify vintage drift vs committed bytes,
      and deliver corrected sleeves + a 10-sleeve variant so the champion can drop or fix
      those slots. Keep (b) turnover attribution as-is.

## ROUND 4 (coordinator standup 2026-09-07 17:2x CST) - fleet drained, R3 all-honest-negative; capacity restored (CFX4 vestigial slot: analysis only, NO champion change)
CFX4 relw=0.0 exactly (data starts 2019-09-10 > IS_END 2017-01-01 -> IS-SR 0 -> weight 0): the
13-sleeve champion is a 12-sleeve book. Round 4: write work_r4/CFX4_SLOT_DECISION.md - the three
options (keep-as-is / drop slot / OOS-fitted weight rule for late-start sleeves), each with exact
champion-level impact (ann/SR/MDD/neg-yrs under FULL abs-dW at 6.4bps) and a recommendation. DO
NOT touch champion/weights/builder CSVs - coordinator+user decide. Also: harden brwt_ens_build.py
(fixture test for its start-bound behavior).
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
 (a) Guard round: re-run cost_reconciliation on the champion of record
 (full_dw vs half-turn hypothesis must stay REJECTED; charged 5.2622 bp/yr) and verify all 13
 sleeve input files byte-stable across the round (champion sha 4358dfab95679b97, weights
 149164b3b01aa110 at round start - report end-of-round shas). (b) Any agent-proposed cost change
 is OUT OF SCOPE - document, don't touch. No new signals.

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

 (a) CENTERPIECE - ADOPTION STUDY for RB_hobr_crack_hyst_w63_z10_zo10 (sleeve sha
 da0285b9a7a5e6a2, at campaign/team/agents/RES_BASIS/sleeves/): build the 14-sleeve champion
 CANDIDATE per V2 - re-solve IS weights incl the new sleeve at w<=15 pct NAV, re-lever to
 gross<=1.6 EXACTLY (8e is the binding open question - champion rides the cap at 1.6000), full
 7/7 verify_champion.py on the candidate + full V2 battery on the delta, state halves (H2 0.753)
 and IS/OOS (2.145/0.807) gate verdicts explicitly, rung grid w=0.05/0.10/0.15, and a BOOK-level
 placebo at your adopted w (coordinator's w=0.25 169/200 mistimed-draw finding reproduced above
 - address it at your w, cite VOL2's R6 memo if it lands). Byte-pin everything under work_r6/.
 Write the candidate ONLY to campaign/results/RAWEW14_HOBR_CANDIDATE_daily.csv + matching
 weights file - the champion of record is NOT touched; the coordinator adopts at next standup
 ONLY if 7/7 + all V2 gates clear.
 (b) Sleeve refresh: extend the stale sleeves (brwt10/7/5 + diescrack 17d stale as of R5) toward
 2026-09-05 where source data allows; disclose any sleeve that cannot refresh and why.

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
 (a) CENTERPIECE - REFRESH ADOPTION via full re-solve: take the
 work_r6/refresh/ staged sleeves (brwt10/7/5 -> 08-28, diescrack -> 08-24) into a champion
 CANDIDATE re-solve per V2 (IS weights re-solve over all 13 refreshed sleeves, re-lever to
 gross<=1.6 EXACTLY, full 7/7 verify_champion.py on the candidate + full V2 battery on the delta
 incl. leak_probe, halves + IS/OOS stated, BOOK-level placebo at the adopted construction - the
 champion delta is a CORRELATED overlay refresh, so the CLASS-A instrument applies). Write ONLY
 to campaign/results/RAWEW15_REFRESH_CANDIDATE_daily.csv + matching weights file; champion of
 record UNTOUCHED; the coordinator adopts at the next standup ONLY if 7/7 + all V2 gates clear
 AND no gate regresses vs 37.1954 / 3.1810 / -6.6922 / 0-neg. (b) HOBR file hygiene: leave
 RAWEW14_HOBR_CANDIDATE* exactly as-is (audit trail; do not delete or edit). Byte-stability
 guard re-run (16/16) + your 42-test suite green.

## ROUND 8 (coordinator standup 2026-09-09 04:03 CST) - fleet drained 21/21 R7 DONE; capacity restored (16 procs); domains closed: audit rotation + seeded lanes
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED, supersedes V1) + campaign/results/DEAD_IDEAS.csv
(recount rows yourself; 153 at R7-end, dynamic). Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
ann 37.1954 pct / SR 3.1810 / MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), sha 4358dfab95679b97,
re-verified 2026-09-09 03:5x standup via 23:40 artifact (bytes unchanged since Sep 7 11:24, ok=true 7/7).
R7 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
HARD RULES: no dead-family re-test; no re-tuning a dead signal into a new config (p-hacking ban); all r8 work
stays in YOUR OWN dir; nothing is applied to bt/, shared data trees, or the champion without explicit chief
instruction; honest negatives with exact numbers are fine results; every claim must reproduce from a script you save.

YOUR R8 LANE: AUDIT ROTATION (R4 pattern): (i) pick 6 DEAD_IDEAS.csv rows from families OTHER THAN cost-campaign that carry saved scripts; independently reproduce each from its CITED script at 6.4bps full-dW; report reproduced / diverged (exact numbers) / unreproducible per row. (ii) 2 OWN-family rows: rebuild missing scripts if derivable; tag upgraded-evidence.
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
