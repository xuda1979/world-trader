# V7.1 SESSION REPORT — 2026-09-29: HARD-STOP GOVERNED ACT (A4 ZERO+RENORM ADOPTED)

## Trigger

The operator decided the standing act/hold question on the 2 decay-monitor HARD stops
(exit 2 since 2026-09-19, b9f8dee): **ACT — A4 (zero + renormalize)**, the arm measured
weakly dominant on every selection-free metric (full SR 4.074 vs 4.0458; OOS SR 3.665
vs 3.597; OOS ann +0.87pp; DD identical -3.161%; 0 neg years) and minimal-intervention
(no re-fit; the same transformation the pre-committed prune rule would have applied had
w >= 10%). The 18-sleeve recipe re-solve (V8GOV) was evaluated and REJECTED in the same
decision (loses to A4 on full SR -0.116, OOS SR -0.047, OOS ann -0.59pp, deeper DD;
mechanism: the SR>=6.5 corner does not transfer from 20 to 18 sleeves — the solver raids
C4, the book's best engine).

## What was executed (the governed act path, per the adoption package vehicle)

1. **Weights**: `OPT_20V71_weights.csv` — the committed V7.0 vector with
   `FXD1_KRWTRI_raw_daily.csv` and `crossasset_rev_L8.csv` zeroed and the 18 survivors
   renormalized by 1/0.880835 = 1.135286. Exact arithmetic on the committed vector
   (transform pin: 9.0e-17 vs 1e-6 retired S1 baseline).
2. **Spec**: `V71_REPLICATION_SPEC.md` — new V# spec file per V7.0 §8 (any edit to
   weights invalidates; new versions = new V# spec file). Carries: the 20-sleeve table
   with the new weights; §4.1 S1 retirement language (3e-4 pin retired to 1e-6
   baseline; zero+renorm is NOT a re-solve; the decomposed S1 gate); §4.2 the exact
   transform; §7 decay-monitor history (fired 2026-09-19; evidence package 2026-09-30;
   acted 2026-09-29; re-solve lane rejected); §2 weight-switch date 2024-10-01.
3. **Ledger**: `OPT_20V71_FULL_LEDGER.csv` (105,590 rows) — engine identical to
   `rebuild_v7_ledger.py` with the weight switch; pre-switch marks BYTE-IDENTICAL to
   the V7.0 ledger (max|d| = 0.0); post-switch marks reconcile to LEV x gross at 5.2e-16.
4. **Gates** (all green, all this session, nothing carried):
   - `reproduce_v71.py` — 14/14 PASS ("ALL REPRODUCED — safe for live use").
   - `replicate_from_doc_v71.py` — 4/4 stages PASS (stage-1 recipe→V7.0 2.43e-4 within
     the attributed a6 pin; stage-2 exact transform 9.0e-17 vs 1e-6; stage-3 full doc
     path 1.72e-4 within 1.135286×3e-4; §1 table 4.3e-9).
   - `backtest_pseudocode_v71.py` — 6/6 PASS. Deployment convention (drifted weights):
     **OOS 31.13%/yr arith (canonical for live), monthly SR 3.65, daily DD -3.18%,
     0 neg years**; drift capture +0.68pp over ledger 30.455% (V7.0 pattern: +0.67pp).
   - `v71_oos_decay_monitor.py` — **exit 0** (first green live gate since 2026-09-19):
     20 sleeves = 18 held (0 HARD, 2 decay: D_xlu_ief 0.06 ratio, a6_r2 0.745) + 2
     RETIRED (reported for recovery watch, excluded from fail-close per spec §7).
   - V7.0 preserved: `reproduce_v7.py` re-run this session 9/9 PASS; V7.0 spec, weights,
     ledger untouched.
5. **Tests**: `test_v71_hardstop_act.py` (6 pins: exact-transform invariant; pre-switch
   byte-identity; post-switch recon; §6 canonicals on the committed ledger; V7.0
   artifacts unchanged; spec-table parse) + `test_v71_oos_decay_monitor.py` (5 pins:
   report structure incl. retired semantics; exit-0 with 0 held HARD; retired health
   visibility; independent rule re-derivation on held sleeves; read-only artifacts).
   Full bt suite: **29 failed / 710 passed** — the 29 failures are the documented
   pre-existing baseline (identical set at HEAD 5471552); zero regressions from this act.

## Decision evidence (all landed prior, unchanged this session)

- `HARDSTOP_GOVERNANCE_MEMO_2026-09-30.md` — 5-arm counterfactual, in-sample warning
  (the +4.2pp trail2y delta is in-sample to the stop decision; honest forward delta
  OOS ann +0.87pp), decision options. Now marked RESOLVED: ACTED.
- `V8GOV_ADOPTION_PACKAGE_2026-09-30.md` — solver validation (2.43e-4), 18-slv re-solve
  measured and rejected, A4 recommendation. Now marked RESOLVED.
- Committed CSVs (post-E1-refresh, deterministic, byte-identical on re-run this session):
  `V8GOV_EVAL_2026-09-30.csv`, `HARDSTOP_COUNTERFACTUAL_2026-09-30.csv`,
  `V8GOV_candidate_weights.csv`, `V8GOV_candidate_meta.json`.

## Honesty notes

- The trail2y headline gain (+4.2pp) remains IN-SAMPLE to the stop decision; the
  forward-looking expectation is the small OOS/full deltas (+0.87pp OOS ann). The act
  was chosen for weak dominance + minimal intervention + clearing a standing governance
  flag, NOT for the in-sample number.
- The 2 retired sleeves keep their decay data visible in the V7.1 monitor; if their
  trail2y SR recovers above 0 the recovery is observable (test pin re-validates openly).
- The V8GOV 18-slv re-solve remains available as evidence; its lane is closed (rejected).
- The V7.0 spec is superseded history, preserved byte-exact; any future act follows the
  same vehicle (new V# spec file, full gate battery, dated session memo).

## Landed (this session)

- `campaign/work_backtest_oos/OPT_20V71_weights.csv` (committed V7.1 weights)
- `campaign/work_backtest_oos/OPT_20V71_FULL_LEDGER.csv` (committed V7.1 ledger)
- `campaign/work_backtest_oos/V71_REPLICATION_SPEC.md` (system of record)
- `campaign/work_backtest_oos/rebuild_v71_ledger.py` (deterministic builder)
- `campaign/work_backtest_oos/v71_oos_decay_monitor.py` (+ V71_OOS_DECAY_REPORT.csv/.json)
- `reproduce_v71.py`, `replicate_from_doc_v71.py`, `backtest_pseudocode_v71.py` (gates)
- `campaign/bt/tests/test_v71_hardstop_act.py`, `campaign/bt/tests/test_v71_oos_decay_monitor.py`
- RESOLUTION markers on the memo + adoption package
- Live-engine repoint: campaign/ibkr_v7_engine.py -> OPT_20V71_weights.csv (dry-run verified)
- This memo.

## Not landed (out of scope, unchanged)

- Live IBKR pilot sessions (the engine is REPOINTED — campaign/ibkr_v7_engine.py now
  reads OPT_20V71_weights.csv; --dry-run verified: retired sleeves $0, survivors at
  renormalized targets, e.g. C4/brwt7 $272,469, RB $201,377, 3%ers $54,494 at NAV $1M —
  but Gateway login/pilot sessions are operator tasks, not research tasks).
- Any re-solve of the 20-sleeve recipe on the current vintages (S1 stage-1 remains at
  the attributed a6 drift; a clean re-solve is a future governed decision).
- The 29 pre-existing suite failures (documented baseline; dedicated bt/infra round).

## ADDENDUM 2026-09-30 (RB FRED refresh, double-audit session): vintage note

The canonical numbers in §"What was executed" above are the 2026-09-29 act-time vintage.
The 2026-09-30 double audit found RB_hobr_crack stale (last row 2026-08-25, +36d >
35d limit — date rollover, both monitors flagged it); the fix was the routine refresh:
DHOILNYH + DCOILBRENTEU re-fetched from FRED (append-only +19 rows each, through
2026-09-22, overlap exact 0.0), sleeve re-emitted (append-only +18 rows, full_pass=True),
both ledgers rebuilt (V7.0 recon 1.04e-17; V7.1 pre-switch marks still byte-identical),
evidence CSVs regenerated, pins re-pinned with dated audit trails (best.json
pins_prerefresh_rb_20260930; round6 fill0/resolve appended-marks re-pin).

Current (post-RB-refresh) V7.1 canonicals: full SR 4.0792, OOS SR 3.6718, full ann
27.969%, OOS ann 30.481%, trail2y SR 3.9223 / ann 28.125%, DD -3.161%, H1/H2
5.671/3.5790, 0 neg years; deployment 31.16%/yr (+0.68pp drift capture). V7.0: OOS SR
4.0702, OOS DD -0.8000%, full SR 4.5703. All qualitative conclusions unchanged (A4
weak dominance, negYr=0, monitor exits 2/0). All 8 gates green; suite identical to the
29-failure documented baseline.
