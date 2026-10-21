# CHARTER: HUNT_TIMESFM — Google TimesFM 3.0 forecasting sleeves (CIO add 2026-09-07)

## Mission
Test whether TimesFM (google/timesfm) zero-shot point forecasts carry post-cost alpha as a
campaign sleeve. HONEST gates only: a sleeve passes ONLY if it survives every gate below.
Expected outcome is NEGATIVE — most sleeves die; that is a fine result.

## ROUND 4 — probe first, then hunt (coordinator standup 2026-09-07 18:0x)

### Step 0 — feasibility probe (FAIL-CLOSED, do this first)  [CIO-verified 2026-09-07 ~18:0x]
The CIO already de-risked the environment — USE this recipe, do NOT rediscover it:
 1. A WORKING venv is ALREADY BUILT: /tmp/tfvenv (python3.14 + timesfm==3.0.1 + jax
    0.11.1 + jaxlib 0.11.1 + flax + optax + einshape). Use it directly:
        /tmp/tfvenv/bin/python -c "import timesfm, jax; print('OK')"
    (jax is PINNED at 0.11.1 on purpose: the default `timesfm[flax]` resolve pulls a
    broken jax 0.2.22 that ImportErrors on jaxlib.pocketfft. Keep 0.11.1.)
 2. ACCESSIBLE CHECKPOINT (verified 200 OK on HF): google/timesfm-2.5-200m-pytorch
    (0.23GB, fits 17GB RAM). The "3.0/2.0" repos (google/timesfm-3.0-* etc.) return 401
    (HF-gated/Pro) — do NOT spend time on them; the package code is 3.0.1 but the usable
    free weights are the 2.5-200m. Use the flax default repo
    google/timesfm-2.5-200m-flax (via timesfm_2p5) or the pytorch 0.23GB one.
 3. Test forecast on ONE toy series and save the output shape to work_r1/install_proof.txt.
 4. If /tmp/tfvenv was deleted or jax regressed, rebuild from the charter's ENV section below.
 5. If the model downloads are blocked/offline (401 persists even on 2.5-200m), STOP: write
    the exact failing probe to FINDINGS.md and end ROUND 4 DONE. Do NOT fake a backtest with
    a homemade ARIMA and call it TimesFM.

### If feasible — engine spec
- Data: use ONLY existing linted series in tools/quant/data/ (world_stock_index ETFs,
  more_etf/, more_fred/). NO new scraping. Champion window 2008-03-31..2026-08-27.
- Honest execution: forecast on day T using data up to T (strict T+1); forecast horizon h=1
  step; walk-forward, expanding window, min history 512 (TimesFM context), refit each bar
  or every K bars (report K).
- Signals to try (a-priori, before seeing results — declare them in FINDINGS first):
  (a) forecast-direction L/S: long if fcst[T+1] > last[T], short if <, on 3-6 liquid ETFs
      (SPY or the champion's own index sleeves); vol-target 10%; costs FULL |dW|*6.4bps
      one-side, borrow 0.5%/yr, margin 4.5%/yr on (gross-1), same as every engine.
  (b) forecast-magnitude vol overlay: scale champion exposure by |fcst| percentile — must
      include the content-free vol-mask control that killed HUNT_CREDIT2 (d) and the
      whitening critique; adoptable only if it beats the content-free control.
- Gates per GATES_CONTRACT.md: SR>=1.0, both halves >=0.5, <=2 neg years (none < -5%),
  scramble p<0.05, |corr|<0.15 vs champion, span >=8y for any adoptable claim.
- Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (108 rows) FIRST. Momentum /
  reversal / carry families are CLOSED — if your TimesFM signal reduces to "model says
  continue last move", note it as a re-test of a dead family and report it as such.
- Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv ann 37.195% / SR 3.181 /
  MDD -6.69% / 0 neg yrs (re-verified 17:0x). NEVER modify committed champion files.
- Save every script + sleeve CSV in HUNT_TIMESFM/; end FINDINGS.md last line with exactly:
  ROUND 4 DONE

### ENV rebuild (if /tmp/tfvenv is gone; verified working recipe)
    python3 -m venv /tmp/tfvenv
    /tmp/tfvenv/bin/python -m pip install -U pip
    /tmp/tfvenv/bin/python -m pip install "timesfm[flax]==3.0.1" \
        "jax==0.11.1" "jaxlib==0.11.1" "flax" "optax" "einshape"
    # jax MUST be 0.11.1 (matches jaxlib) or jaxlib.pocketfft ImportError at runtime.

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
 Your R4 kill was real and generalizes (single-era lift is not a
 sleeve). R5 NEW CORNER (pre-registered): TimesFM zero-shot forecast-direction on the NEW
 2026-09-08 spans ONLY - the NKY 77y calendar and/or propane 1992+ (see HUNT_INTERNATIONAL2 /
 HUNT_CMDT2 sources) - cross-asset family at weekly TO. Do NOT re-test the dead 6-ETF daily h=1
 config or the |fcst| champion overlay (both dead, R4). FIRST register your 2 R4 DEAD_IDEAS rows
 if absent (check; append if missing - they are your finding).

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

 (a) Family CLOSED 0/8 across R4+R5 (both spans, both horizons, full V2 battery). Preserve the
 environment honestly: document /tmp/tfvenv + checkpoint cache state in work_r6/env_note.md, or
 declare them ephemeral - either is a fine answer; 0/8 does not justify more GPU/env spend, so
 NO new model corners.
 (b) FRAUD-CATCH: reproduce HUNT_COT2's AND HUNT_INTERNATIONAL2's R5 verdicts from published
 artifacts with your own code.
 (c) Curation of your 4 DEAD_IDEAS rows (verify repro paths).

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
 (a) AUDIT (own code): DATA_COTMORE + trader-count panel integrity -
 recount 51 cols / 35 families from disk, verify the 2 EXN break gates (nat_gas_nymex 2022-02-08,
 lumber 2023-04-25) still fail closed, and check DEAD_IDEAS rows 135-137 (COT2-R6 curation)
 verbatim. (b) No TimesFM re-test (family CLOSED 0/8; env EPHEMERAL-WITH-PROVEN-RECIPE - document
 any /tmp/tfvenv rebuild if you touch it). No DEAD_IDEAS rows unless a real defect surfaces
 (your R6 consolidation precedent).

## ROUND 8 (coordinator standup 2026-09-09 04:03 CST) - fleet drained 21/21 R7 DONE; capacity restored (16 procs); domains closed: audit rotation + seeded lanes
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED, supersedes V1) + campaign/results/DEAD_IDEAS.csv
(recount rows yourself; 153 at R7-end, dynamic). Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
ann 37.1954 pct / SR 3.1810 / MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), sha 4358dfab95679b97,
re-verified 2026-09-09 03:5x standup via 23:40 artifact (bytes unchanged since Sep 7 11:24, ok=true 7/7).
R7 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
HARD RULES: no dead-family re-test; no re-tuning a dead signal into a new config (p-hacking ban); all r8 work
stays in YOUR OWN dir; nothing is applied to bt/, shared data trees, or the champion without explicit chief
instruction; honest negatives with exact numbers are fine results; every claim must reproduce from a script you save.

YOUR R8 LANE: AUDIT ROTATION (R4 pattern): (i) pick 6 DEAD_IDEAS.csv rows from families OTHER THAN TimesFM/forecasting that carry saved scripts; independently reproduce each from its CITED script (not FINDINGS prose); report reproduced / diverged (exact numbers) / unreproducible per row. (ii) pick 2 rows from your OWN family lacking a saved script and rebuild the script from FINDINGS description if derivable; tag the row upgraded-evidence.
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
