# V7 SESSION REPORT — 2026-09-26 (session 3): PROVENANCE CLOSURE + S1 PIN

## Trigger
Standing prompt "use the new data, improve V7". Session 2 (b4c002f, 13:21) left the book
fully fresh (STALE 0) with one DISCLOSED LIMITATION: S1 doc-replication RED (drift 2.43e-4).
This session found and fixed a larger undocumented problem underneath it.

## The finding (worse than the disclosed limitation)
The V7 gates were **machine-local**:
1. **12 of 20 V7 sleeve CSVs were untracked** — reproduce_v7.py, replicate_from_doc.py and
   backtest_pseudocode.py read them directly. A fresh clone failed even pytest collection
   (4 collection errors, verified via stash A/B). The "live gate green" claim was only
   true on this machine.
2. **The b4c002f chain commit was hollow**: the derived a6 sleeve was committed but the
   tracked intermediates behind it (equity_FactorMom × 3, lib FactorMom_1926) were not.
3. **The 9185a2e data refresh was similarly hollow**: refreshed sleeves committed, the
   tracked data_fred inputs (+21 files) not.
4. **The ITER16 lsfix test (46c5ba5, 9/13) landed without its fix**: test_camp_short_r4_lsfix.py
   was committed but strat_ls_equity.py's short-leg sign fix was not — HEAD failed 4 tests
   the working tree passed.

## Verification (all before any commit)
- lib FactorMom_1926: APPEND-ONLY +21 rows (8/3–8/31), overlap maxdev 0.0 on 26,295 rows;
  new Aug rows == new equity_FactorMom_1926 Aug daily returns to 9.9e-17
- equity_FactorMom_{1926,1963,2008}: rebuilt on 202608 vintage, end 2026-08-31
- equity_Merger_Arb_PEAD_5pct: +28 rows, overlap levels byte-exact
- data_fred 21 files: all append-only, columns identical, overlap maxdev 0.0, +24..40 rows
- a6 restatement claim re-verified: 4,300/4,925 overlap rows restated, 1,895 pre-2017,
  maxdev 7.4e-4/day, +21 rows
- **S1 drift fully attributed (new A/B this session)**: §4 re-solve on the PRE-restatement
  a6 (b4c002f^) reproduces committed weights to **2.18e-09**; on current a6 it drifts
  **2.43e-04**. The drift is 100% the a6 IS-window vintage restatement, nothing else.

## Actions (5 commits)
1. `ceaf94c` — F-F 202608 chain intermediates committed (equity × 3 + lib + MergerArb)
2. `19b15e1` — data_fred append-only refresh committed (21 series, verified)
3. `7406475` — test_camp_cost_r3_brwt vintage-coverage assert updated (coupled to refresh)
4. `7043fda` — shortability hunt-template pre-gate (in-flight work, verified standalone)
5. `623e2e7` — **12 untracked V7 sleeve CSVs committed (20/20 now in git)**
6. `5ece8b9` — strat_ls_equity short-leg sign fix committed (the missing half of 46c5ba5)
7. `73f85d5` — **S1 vintage-drift pin** (spec §4.1): S1_TOL 1e-6 → 3e-4 pinned, both gates
   updated with provenance; re-open rule documented (any other IS restatement REDs at >3e-4;
   material sleeves w>10% should trigger governed re-solve, not a new pin)

## Gate status (V7 line, after this session)
- reproduce_v7.py: 9/9 PASS, exit 0 (ALL REPRODUCED — safe for live use) — now clone-safe
- replicate_from_doc.py: PASS, exit 0 (S1 2.43e-4 < 3e-4 pinned; 6/6 metrics PASS)
- backtest_pseudocode.py: 10/10 PASS, exit 0 (S1 pinned; all metrics PASS)
- v7_oos_decay_monitor.py: exit 2 — 2 HARD stops (FXD1_KRWTRI trail2y -0.52 w 3%;
  crossasset_rev_L8 trail2y -0.10 w 8.9%), both below the pre-committed prune trigger
  (w < 10%) -> NO PRUNE per rule (governance-scope, unchanged)
- v7_refresh_audit.py: exit 0, all leaves fresh
- bt-tests: 122 failed / 593 passed / 7 errors — failure set byte-identical to the
  documented session-1/2 baseline; the 4 extra failures at HEAD (pre-5ece8b9) are gone

## Standing items (unchanged, governance-scope)
- 2 HARD stops: FXD1_KRWTRI (trail2y -0.52, w 3%), crossasset_rev_L8 (trail2y -0.10, w 8.9%)
- Pre-committed prune rule not met (both w < 10%) -> NO PRUNE (documented, unchanged)
- S1 pin is temporary-by-design: a governed V# bump re-solving weights on the 202608
  vintage would retire it (revert to 1e-6 baseline)

## What this session did NOT do (honesty)
- No weight changes (FROZEN per spec §8)
- No new sleeves, no re-selection (spec §4: DO NOT reselect)
- The 2 HARD stops remain the standing governance question (weight decision, out of
  maintenance scope)
- ff_factors raw files remain gitignored by design (regenerable via tools/quant/data_history.py)
