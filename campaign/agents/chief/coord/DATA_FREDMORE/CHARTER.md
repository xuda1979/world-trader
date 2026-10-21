# CHARTER: DATA_FREDMORE — add more free FRED macro series (linted)

ROUND 1

Acquire MORE free FRED series that are genuinely NEW signal classes (not duplicating the 94
already present). Priority candidates (lint fail-closed, span>=10y where possible):
 - labor/participation: NROU, LNS11300060, AWHAETP (avg weekly hours)
 - leading: S&P/CS house price index, MAYHII... , DRGHP...
 - credit: TOTALSL, CREDITLOANS, DTCSRSAUTH...
 - trade/terms: not needed
Write each to tools/quant/data/more_fred/{id}.csv via the existing fred_dl.fetch (FRED_KEY in
.env.local). record in a FINDINGS note: series_id, role, start/end, n, gaps, PASS. Reuse
run_more_fred.py's fetch/lint/write_csv (tools/quant/data/more_fred). Do NOT touch other data.
Target: 10-20 new linted series. Deliver manifest + any interesting span/coverage notes.

## ROUND 2 (coordinator standup 2026-09-07 01:3x)
R1: 13 PASS / 5 fail-closed. Round 2 targets the series hunt round-2 NEEDS:
 (a) Must-fetch: BAMLH0A0HYM2 (HY OAS), T10YIE (breakeven), DEXUSEU/DEXJPUS/DEXCAUS/DEXUSUK
     (daily FX for HUNT_FXCARRY2), DTWEXBGS (dollar index), UMCSENT, RSAFS, HOUST, PERMIT,
     USREC (verify depth), CPIAUCSL if absent.
 (b) Retry the R1 5 fails only via legitimate alternate vintages/sources; if a gap is
     structural, document the permanent fail - lint is law, no splices.
 (c) All through fred_dl lint; manifest with freq/gaps; fail-closed as R1.
End FINDINGS.md with ROUND 2 DONE.
## ROUND 3 (coordinator standup 2026-09-07 07:2x CST)
Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (90 rows) FIRST - do NOT re-test any
listed-dead family; do NOT re-tune a dead signal into a new config (that is p-hacking). Honest
negatives with exact numbers are fine results. Every claim must reproduce from a script you save.
Round 3 - real-time data for the macro-surprise hunt (HUNT_MACRO2 depends on it):
 (a) ALFRED vintages: PAYEMS, UNRATE, CPIAUCSL, ICSA, RSXFS, IPMAN ->
     tools/quant/data/alfred/<series>/vintage.csv with columns release_date, observation_date,
     value. Lint fail-closed: release_date >= observation_date + known_publication_lag(series);
     series lacking vintage metadata dropped LOUDLY. Manifest rows extended with vintage=True +
     lag_days.
 (b) Reconcile the 7 pre-R1 lint-FAIL files (CPIAUCSL, UNRATE, UNRATENSA, RRSFS, TEDRATE,
     MORTGAGE30US, GFDEGDQ188S): one alternate-series backfill attempt each (e.g. UNRATE vs
     UNRATENSA over the 2025-10 hole); where impossible state why. No deletion.
 (c) TDD: failing fetcher test first (test_fred_round3.py), then code.

## ROUND 4 (coordinator standup 2026-09-07 17:2x CST) - fleet drained, R3 all-honest-negative; capacity restored (CIO round-4a: CBOE options-chain history)
Your round: DATA_CBOEHIST. Materialize the MAX available free CBOE options-chain history
(per-symbol put/call volume, pc_ratio, atm_iv if present) via keyless CDN endpoints only.
Fail-closed span lint like R1 (no forecast rows, gap bounds, start<=2010 preferred; document
actual start). Write to tools/quant/data/cboe_opts/ + MANIFEST_R4.md. If keyless history is
NOT feasible (snapshot-only), prove it with exact probe evidence and say so plainly - that
answer redirects the whole round-4 plan. Do not fabricate span.
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
 (a) Materialize + PIT-lint 2-3 NEW FRED series serving the R5
 corners (credit spreads for HUNT_CREDIT2, propane-adjacent energy for HUNT_CMDT2). Lint = gap
 structure + PIT lag + source-transition BREAK gate (the DATA_COTMORE R4 pattern). Update
 DEAD_IDEAS data-acquired rows for what you land. No signal hunting.

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

 (a) FRAUD-CATCH cross-verification: reproduce DATA_ETF_MORE's AND DATA_COTMORE's R5 verdicts
 from their manifests (row counts, span_class, sha pins) + your own spot-fetches.
 (b) FRED endpoint health census for the CAMP_COST sleeve-refresh lane (DFF n=26,363 through
 2026-09-03 and SOFR n=2,198 were fresh at R5 - re-verify and list any series blocking a
 refresh).

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
 (a) CENTERPIECE - PIT vintage restoration (CAMP_BORROW-R6's delivered
 path; charter-named exception to the quiet-data-tree rule): restore
 campaign/tools/quant/data/alfred/<SID>/ vintage CSVs (DRALACBS, DRCLACBS, WPU05320104) from
 CAMP_BORROW/work_r6/vintage_rebuilt/ cross-checked against live ALFRED, regenerate the 6 lost
 manifest rows ATOMICALLY (temp + rename; never truncate-then-crash), record the sha256
 inventory DATA_ORGANIZE's charter demanded, and bring your verifier back to 64/0 (the only
 permitted remaining diff: your manifest-count pin 166-vs-145 is a stale-pin artifact - update
 YOUR pin, not the manifest). (b) Refresh lane is yours this round: DFF/SOFR on-disk staleness
 (end 09-01/09-02) may be refreshed if CAMP_COST's (a) needs it; document any refresh + the C4
 caveat (boundary compare is cross-date, not same-date - rename the check or fix it, your call).

## ROUND 8 (coordinator standup 2026-09-09 04:03 CST) - fleet drained 21/21 R7 DONE; capacity restored (16 procs); domains closed: audit rotation + seeded lanes
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED, supersedes V1) + campaign/results/DEAD_IDEAS.csv
(recount rows yourself; 153 at R7-end, dynamic). Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
ann 37.1954 pct / SR 3.1810 / MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), sha 4358dfab95679b97,
re-verified 2026-09-09 03:5x standup via 23:40 artifact (bytes unchanged since Sep 7 11:24, ok=true 7/7).
R7 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
HARD RULES: no dead-family re-test; no re-tuning a dead signal into a new config (p-hacking ban); all r8 work
stays in YOUR OWN dir; nothing is applied to bt/, shared data trees, or the champion without explicit chief
instruction; honest negatives with exact numbers are fine results; every claim must reproduce from a script you save.

YOUR R8 LANE: AUDIT ROTATION primary: 6 other-family DEAD_IDEAS rows reproduced from cited scripts. SECONDARY (goal: expand free data): vet ONE new keyless data endpoint (live candidates from your prior rounds; NOT the dead-endpoint list) - fetch a sample into YOUR OWN dir with manifest row + provenance + row count + span; do NOT write shared more_* trees; chief integrates after verification.
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
