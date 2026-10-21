#!/usr/bin/env python3
"""R5 charter authorship - coordinator standup 2026-09-08 04:0x CST.

Appends a ROUND 5 section to every roster agent charter, grounded in each agent's
actual R4 outcome. Idempotent (skips charters already containing the R5 marker).
Charters are append-only by convention.
"""
import os

ROOT = '/Users/daxu/software/world-trader/campaign/agents/chief/coord'

SHARED = """
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
"""

SECTIONS = dict()
SECTIONS['HUNT_COT2'] = """ (a) NEW CORNER (pre-registered): positioning signals from DATA_COTMORE's R4
 trader_count_panel.csv (29,017 rows x 51 cols, 35 families, PIT-checked) - ONLY from
 columns/families absent from DEAD_IDEAS (grep before you build). RESPECT the 2 PASS_WITH_EXN
 breaks: nat_gas_nymex 2022-02-08 (CFTC split, -86 pct) and lumber 2023-04-25 (+105 pct rename)
 - no z/level read across those dates; verify the panel's fail-closed BREAK gate fires on both.
 (b) Any sleeve clears the full V2 battery + beats-passive trio. Honest negative expected."""

SECTIONS['HUNT_CRYPTO2'] = """ (a) NEW CORNER (pre-registered): crypto carry from keyless OKX/Coinbase/
 Kraken endpoints (live per altdata5 2026-09-08) - funding-rate / perp-basis family at WEEKLY
 or slower rebalance; daily crypto turnover is lethal at 6.4bps full-|dW| (TimesFM EW6 died at
 112-154x annTO - do not repeat it). Cite exact endpoints + fetched row counts. (b) Full V2
 battery; decorrelation vs champion mandatory; honest negative expected."""

SECTIONS['HUNT_INTERNATIONAL2'] = """ (a) NEW CORNER (pre-registered): the NKY 77-year daily
 calendar (data-acquired row: newdata/NIKKEI225.csv, 20,166 rows 1949-05-16..2026-08-31, span
 blocker CLEARED). Build a Japan span-class sleeve per V2 section-9 with MANDATORY sub-span
 stability analysis (pre-1990 vs post - the 77y span is the whole point; a sleeve that only
 works post-2013 is a FAIL with that number stated). Full V2 battery + beats-passive."""

SECTIONS['HUNT_CMDT2'] = """ (a) NEW CORNER (pre-registered): propane DPROPANEMBTX daily 1992+
 n=8559 (data-acquired row; more_fred/; the old DPROPANEMTXCF id was INVALID - do not use it).
 Seasonality/spread corner vs the champion energy slots (brwt/diescrack/C5ng occupy them - your
 sleeve must DECORRELATE from those, corr gate 0.15/0.35). Full V2 battery; honest negative fine."""

SECTIONS['HUNT_MACRO2'] = """ (a) NEW CORNER (pre-registered): macro-regime covariates from keyless
 Eurostat / BLS / WorldBank cubes (altdata5 roster, live 2026-09-08) as a champion OVERLAY
 (V2 section-8j: report exact dSR + era-split; trailing-only transforms; PIT lag per series
 documented). (b) If the overlay shows a real effect, a standalone variant must then clear the
 full V2 battery - do not stop at the overlay. Honest negative fine."""

SECTIONS['HUNT_VOL2'] = """ (a) NEW CORNER (pre-registered): CBOE put/call archive 1995-2019
 (tools/quant/data/cboe_pcr/_raw/ 10/10 byte-identical; stitched pcr_covariates_SPY_daily.csv
 PIT strictly-prior, 1-session-carry cap, NaN after 2019-10-07). Vol-timing OVERLAY evaluated
 ONLY over 2006-2019 (frozen archive - disclose that hard limit; NOT a current-day signal).
 Era-robustness WITHIN the window is the gate (TimesFM single-era kill applied)."""

SECTIONS['HUNT_FXCARRY2'] = """ (a) FIRST reproduce why CFX4 sits at exactly 0.000 weight in
 RAWEW13v2_IS_SR_weights.csv (relw zero => IS-SR <= 0) - honestly, from CFX4_DTF21_63_raw_daily.csv
 + its meta. (b) NEW CORNER (pre-registered): Frankfurter FX daily (keyless, live per altdata5) -
 carry/trend family NOT in DEAD_IDEAS. If your corner's IS-SR <= 0, that IS the result - write it
 down. Full V2 battery; beats-passive for standalone."""
SECTIONS['HUNT_SECTOR2'] = """ (a) NEW CORNER (pre-registered): sector-rotation covariates from
 Nasdaq historical + PIT-safe news/social aggregates (GoogleNews / Reddit, keyless, live per
 altdata5 2026-09-08). PIT discipline is the game: publication lag per source documented; any
 series whose history cannot be proven prior -> drop it and say so. Overlay or standalone; full
 V2 battery."""

SECTIONS['HUNT_CREDIT2'] = """ (a) NEW CORNER (pre-registered): credit-carry from FRED spread
 families not already dead (grep DEAD_IDEAS for credit/OAS rows first - the D1_creditcurve /
 D-family graves are off-limits; a NEW series id with a NEW construction is the bar). Cite series
 ids + fetched spans. Full V2 battery; beats-passive trio required for standalone."""

SECTIONS['HUNT_TREASFUT'] = """ (a) NEW CORNER (pre-registered): TreasuryDirect auction data
 (keyless, live per altdata5) - auction-cycle positioning family (pre/post-auction drift in
 futures or a6r7-adjacent tenors WITHOUT re-testing a6r7's dead configs). Document fetch spans +
 gap structure. Full V2 battery; honest negative expected."""

SECTIONS['HUNT_TIMESFM'] = """ Your R4 kill was real and generalizes (single-era lift is not a
 sleeve). R5 NEW CORNER (pre-registered): TimesFM zero-shot forecast-direction on the NEW
 2026-09-08 spans ONLY - the NKY 77y calendar and/or propane 1992+ (see HUNT_INTERNATIONAL2 /
 HUNT_CMDT2 sources) - cross-asset family at weekly TO. Do NOT re-test the dead 6-ETF daily h=1
 config or the |fcst| champion overlay (both dead, R4). FIRST register your 2 R4 DEAD_IDEAS rows
 if absent (check; append if missing - they are your finding)."""

SECTIONS['CAMP_SHORT'] = """ (a) MHX shortability re-audit (carried from the CHAMPION20Y_V2
 deprecation banner): does any CURRENT champion sleeve imply single-name short exposure
 post-costfix? The 4 regenerated sleeves moved weights (brwt15 -0.040126, diescrack -0.032070,
 QAxasts -0.007740, dualmom -0.005128). (b) Spot-check C5 shortability on the champion of record
 (harness C5) and confirm top gross shares with exact numbers. No new signals."""

SECTIONS['CAMP_BORROW'] = """ (a) Freshness audit of the financing stack vs published IBKR rates:
 call 4.5 pct on (gross-1) => margin drag 2.70 pct/yr (re-derive); borrow 0.5 pct/yr on shorts
 (verify which sleeves actually carry short legs + their gross share). (b) Flag any drift > 10
 pct relative vs the modeled numbers with exact citations. No new signals; no champion edits."""

SECTIONS['CAMP_COST'] = """ (a) Guard round: re-run cost_reconciliation on the champion of record
 (full_dw vs half-turn hypothesis must stay REJECTED; charged 5.2622 bp/yr) and verify all 13
 sleeve input files byte-stable across the round (champion sha 4358dfab95679b97, weights
 149164b3b01aa110 at round start - report end-of-round shas). (b) Any agent-proposed cost change
 is OUT OF SCOPE - document, don't touch. No new signals."""
SECTIONS['DATA_FREDMORE'] = """ (a) Materialize + PIT-lint 2-3 NEW FRED series serving the R5
 corners (credit spreads for HUNT_CREDIT2, propane-adjacent energy for HUNT_CMDT2). Lint = gap
 structure + PIT lag + source-transition BREAK gate (the DATA_COTMORE R4 pattern). Update
 DEAD_IDEAS data-acquired rows for what you land. No signal hunting."""

SECTIONS['DATA_ETF_MORE'] = """ (a) Extend the ETF overlay bench for the V2 section-8 blend
 battery (spy/ief/cta trio is the minimum; add 1-2 decorrelated passive benches if keyless
 sources allow). PIT lint + byte-stable manifest. No signal hunting."""

SECTIONS['DATA_COTMORE'] = """ (a) Extend trader_count_panel.csv with any families the 2026-09-08
 fetch adds (re-run your BREAK gate; keep the 2 known PASS_WITH_EXN rows stable - nat_gas
 2022-02-08, lumber 2023-04-25). (b) One honest attempt to refresh the CBOE PCR archive past
 2019-10-04 from current CBOE CDN paths; if still frozen, document the exact HTTP evidence and
 stop. No signal hunting."""

SECTIONS['AUDIT_CHAMP2'] = """ (a) CHAMPION20Y_V2 rebuild-or-drop EXECUTION (chartered by the
 coordinator's 03:1x deprecation banner): rebuild the 20y table from POST-costfix sleeves with
 fresh builder --verify IDENTICAL + MHX shortability re-audit, OR complete the quarantine doc on
 why it stays deprecated. Either is an honest outcome; a rebuild that cannot reach IDENTICAL is
 a DROP with numbers. (b) Fix the champion_card.py PYTHONPATH footgun (one-line sys.path insert
 or wrapper script, TDD). (c) GOAL80_FINAL_REPORT.md: coordinator leaned CONFIRM (self-scoped
 prior-campaign history) - independently verify its 43.2 pct best-honest claim is self-consistent
 with its own artifacts; confirm or flag with numbers."""

SECTIONS['AUDIT_FWBUGS'] = """ EXECUTE GATES_CONTRACT_V2 section-12 Step-2 flip, runbook steps
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
 flip-only-in-flight and say so explicitly in FINDINGS."""

SECTIONS['AUDIT_RECON'] = """ Post-flip acceptance round (runs AFTER AUDIT_FWBUGS lands the
 section-12 flip - poll their FINDINGS.md; if not landed by your start, audit the CURRENT tree
 state instead and state which you did): (a) verify_champion_r3_cmd.sh 7/7 and champion
 UNCHANGED by the flip (champion sha 4358dfab95679b97 before == after - prove the gates flip is
 champion-neutral). (b) Re-run the 26 production call-site census yourself; any verdict change
 under default-on leak = escalation. (c) Confirm commit-wave B5 state (dirty path count + list)
 for the coordinator."""

SECTIONS['AUDIT_GATES2'] = """ Post-flip validation round (coordinate-by-file with AUDIT_FWBUGS -
 they flip, you validate; do NOT edit bt/gates.py or their test files): (a) verify the
 section-12 step-5 pair tests landed in campaign/bt/tests/ and pass. (b) Re-run YOUR R4 fixtures
 under the flipped default: the 3 GREEN stay GREEN and the 1 RED migration pin goes GREEN (or
 document exactly why not). (c) Sweep gated docs for 'opt-in pending' phrasing - banner to
 RATIFIED + DEFAULT-ON (insert-only, the AUDIT_CHAMP2 R4 banner pattern). (d) DEAD_IDEAS recount
 + well-formedness (your R4 audit pattern, new count)."""

missing, appended, skipped = [], [], []
for agent, txt in SECTIONS.items():
    p = os.path.join(ROOT, agent, 'CHARTER.md')
    if not os.path.exists(p):
        missing.append(agent)
        continue
    body = open(p).read()
    if '## ROUND 5' in body:
        skipped.append(agent)
        continue
    with open(p, 'a') as f:
        f.write(SHARED + txt + '\n')
    appended.append(agent)

roster = [s.strip() for s in open(os.path.join(ROOT, 'AGENTS.txt'))
          if s.strip() and not s.strip().startswith('#')]
no_r5 = [a for a in roster if '## ROUND 5' not in open(
    os.path.join(ROOT, a, 'CHARTER.md')).read()]

print('appended:', len(appended), appended)
print('skipped (already R5):', skipped)
print('missing charters:', missing)
print('roster agents still lacking R5:', no_r5 if no_r5 else 'NONE - roster complete')
