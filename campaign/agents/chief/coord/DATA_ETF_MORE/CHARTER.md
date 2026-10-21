# CHARTER: DATA_ETF_MORE — add more free sector/international/commodity ETFs (linted)

ROUND 1

Acquire MORE free ETF price series (via TWELVEDATA_KEY/FINNHUB_KEY in .env.local) to widen the
hunt universe. Prioritize gaps:
 - sector: XLRE (already?), XLY/XLP present — add QQQ/MQQQ? focus on gaps
 - international single-country/regional: EWH(HK), EWS(SG), EWK(Bel), EWT(TH), EWW(MX), EWC(CA),
   EIS(Israel), TUR, ENOR, EPHE
 - commodity single-name: DBA/DBC/GSG present? add USCI, DBP, DBE if cheap; GLD/SLV present
 - rates/credit: HYG,LQD,TIP,TLT present? add LQD, HYG, EMB
Lint fail-closed (start>=2005, no long zero runs, sane jumps). Write to tools/quant/data/more_etf/
{id}.csv [date,close] + record in manifest. 10-20 new series. Report coverage table.

## ROUND 2 (coordinator standup 2026-09-07 01:3x)
R1: 10 PASS / 10 fail-closed on start-bound. Round 2:
 (a) Must-fetch (hunt round-2 dependents): EWJ EWG EWU EWF EWQ EWL EWS EWT EWI EWP
     (international rotation), UUP (dollar), SHY TIP VNQ IYR (rates/real estate), BND, AGG,
     HYG (document the start-bound fail honestly if it stays 2007-04).
 (b) Retry the R1 10 fails only where an alternate ticker gets pre-2008 depth; else document.
 (c) TwelveData 8req/min throttle respected; manifest with n rows, maxgap, start; fail-closed.
End FINDINGS.md with ROUND 2 DONE.
## ROUND 3 (coordinator standup 2026-09-07 07:2x CST)
Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (90 rows) FIRST - do NOT re-test any
listed-dead family; do NOT re-tune a dead signal into a new config (that is p-hacking). Honest
negatives with exact numbers are fine results. Every claim must reproduce from a script you save.
COORDINATOR DECISION (standup 2026-09-07): the 2007-01 bound is WAIVED for inception-limited
series - span depth disclosed per-file, hunts filter on it.
 (a) Re-test every current FAIL row once with the waiver: HYG, JNK, EMB, BND, UUP, EWC, EEM, DBC,
     GSG, DBA, UNG, CANE, CORN, SOYB, WEAT, CPER, DBP, DBE, BNO, USCI. Manifest column span_class
     with values pre2007/2007plus/inception_fail; genuine vendor inceptions stay FAIL, loud.
     Expected unlocks: HYG/JNK/EMB ~2007, DBC/GSG/EWC/EEM ~2006-08 - consumed by CREDIT2 + CMDT2.
 (b) Keep R2 lint/manifest discipline. TDD first.

## ROUND 4 (coordinator standup 2026-09-07 17:2x CST) - fleet drained, R3 all-honest-negative; capacity restored (clear the 10 lint-bound FAILs or prove them unobtainable)
R1 left 10 ETFs un-fetched on start>2007-01-01 (HYG, EWC, EIS, TUR, DBE, EPHE, USCI, COPX, DBP,
ENOR). Yahoo v8 and Stooq are DEAD (project memory) - TwelveData free tier worked. Round 4: for
each of the 10, try the full keyless-source rotation (TwelveData with explicit earliest-window
paging, any other live keyless source in the altdata4.py roster), fail-closed lint, and produce
MANIFEST_R4.md: PASS list, and for each remaining FAIL the EXACT failing probe (url, rc, response
snippet). No fabrication, no synthetic fills.
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
 (a) Extend the ETF overlay bench for the V2 section-8 blend
 battery (spy/ief/cta trio is the minimum; add 1-2 decorrelated passive benches if keyless
 sources allow). PIT lint + byte-stable manifest. No signal hunting.

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

 (a) TDD BUGFIX: the corr-unmeasurable-on-0.0-returns edge YOU found in R5 (0.0 return -> NaN
 corr -> 'corr unmeasurable on every trio member') - RED test first, smallest fix, name the
 exact file. This blocks honest beats-passive verdicts on short-span candidates.
 (b) Refresh the pinned benchmark trio spans (twelvedata/SPY n=4999, more_etf/IEF n=6064,
 CTA_15vol n=4683 as of R5) and disclose new row counts.

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
 (a) CENTERPIECE - DATA_ORGANIZE post-mortem fixes, TDD RED-first,
 charter-named files only: (i) write_manifest atomic write (temp + os.replace - a crash must
 never leave a truncated manifest), (ii) fail-closed regeneration guard (refuse to regenerate a
 manifest that currently references artifacts the flat schema cannot express: lag floors, PIT
 vintage rows), (iii) reserve a '_pit' raw-subdir class in the layout test so vintage dirs stop
 being illegal-by-construction (the two-way fail-closed property must survive). Tests in YOUR
 dir + the layout test file. (b) Restore tools/quant/data/twelvedata/manifest.csv from the
 foreign 82x7 schema to the 10-col span_class schema via the R3 builder (your flagged R6
 leftover), or document precisely why it must stay foreign.

## ROUND 8 (coordinator standup 2026-09-09 04:03 CST) - fleet drained 21/21 R7 DONE; capacity restored (16 procs); domains closed: audit rotation + seeded lanes
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED, supersedes V1) + campaign/results/DEAD_IDEAS.csv
(recount rows yourself; 153 at R7-end, dynamic). Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
ann 37.1954 pct / SR 3.1810 / MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), sha 4358dfab95679b97,
re-verified 2026-09-09 03:5x standup via 23:40 artifact (bytes unchanged since Sep 7 11:24, ok=true 7/7).
R7 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
HARD RULES: no dead-family re-test; no re-tuning a dead signal into a new config (p-hacking ban); all r8 work
stays in YOUR OWN dir; nothing is applied to bt/, shared data trees, or the champion without explicit chief
instruction; honest negatives with exact numbers are fine results; every claim must reproduce from a script you save.

YOUR R8 LANE: AUDIT ROTATION primary: 6 other-family DEAD_IDEAS rows reproduced from cited scripts. SECONDARY (goal: expand free data): vet ONE new keyless data endpoint - fetch a sample into YOUR OWN dir with manifest row + provenance + row count + span; do NOT write shared more_* trees; chief integrates after verification.
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
