# V8-GOV ADOPTION PACKAGE (2026-09-30) — the admissible V8 lane, measured. NOT adopted.

**Status: CANDIDATE EVALUATION ONLY.** System of record remains V7 (reproduce 9/9 PASS,
ledger recon 7.2e-16). This package exists so the operator's act/hold decision on the
2 HARD stops is served by measured, governed options instead of the inadmissible 9/19
OPT_V8 (pre-costfix inputs, full-period fit — adjudicated 2026-09-19).

## What was built (this session)

1. **`gov_v8_solve.py`** — the spec §4 recipe, solver-validated: re-solving V7's 20
   sleeves reproduces the committed weights to **2.43e-4 max|diff|** (inside the pinned
   3e-4 S1 tolerance; drift = the attributed a6 F-F 202608 restatement, spec §4.1).
   Solver fidelity proven before any new candidate was emitted.
2. **`V8GOV_candidate_weights.csv`** — the 18-sleeve governed re-solve (V7's 20 minus
   the 2 monitor HARD stops), IS-only, provenance-clean inputs, all bounds honored.
3. **`gov_v8_eval.py` / `V8GOV_EVAL_2026-09-30.csv`** — full daily-ledger comparison
   (same engine as the counterfactual; V7 arm recon vs committed ledger 7.2e-16).

## The comparison (daily ledger, LEV 1.6, 6.4bp/side, margin 5.3%)

| arm | full SR | OOS SR | full ann | OOS ann | trail2y SR | trail2y ann | DD | H1/H2 SR |
|---|---|---|---|---|---|---|---|---|
| **V7_RECORD** (20 slv) | 4.042 | 3.593 | 27.47% | 29.57% | 3.641 | 23.70% | -3.16% | 5.67/3.49 |
| **A4_ZERO_RENORM** (20 slv, zero 2 from 2024-10) | 4.070 | 3.660 | 27.95% | 30.44% | 3.850 | 27.91% | -3.16% | 5.67/3.57 |
| **V8GOV_18SLV** (18-sleeve recipe re-solve) | 3.955 | 3.613 | 27.05% | 29.85% | 4.065 | 25.93% | -3.23% | 5.44/3.51 |

## What the numbers say (honest reading)

**The pure recipe re-solve (V8GOV) is NOT better than the simple zero+renorm arm.**
It wins only on trail2y SR (4.065 vs 3.850) — the window in-sample to the stop
decision — and loses on every selection-free metric: full SR (-0.116 vs A4), OOS SR
(-0.047), OOS ann (-0.59pp), deeper DD. Mechanism (measured): dropping XREV removes
-1.43pp of IS mean, and the SR>=6.5 constraint binds at slack 0.0000 in both solves,
so the solver must take weight from C4 (-0.71pp IS) — the book's best engine — to
re-satisfy the constraint, paying 0.82pp IS mean vs V7's solve (17.77% -> 16.96%).
The recipe was tuned for the 20-sleeve pool; its 6.5 constraint is a corner that
does not transfer cleanly to 18.

**A4 (zero + renormalize) weakly dominates V7 everywhere** (full SR 4.070 vs 4.042,
OOS SR 3.660 vs 3.593, OOS ann +0.86pp, DD identical, H2 SR +0.07) and dominates
V8GOV on all selection-free windows. It is also the minimal-intervention arm: no
re-solve, no new fit, weights remain V7's solved vector with two zeros and a 1.135x
renormalization of the survivors — the same transformation the pre-committed
prune rule would have applied had w been >= 10%.

## Recommendation (for operator sign-off, not executed)

**If acting on the HARD stops: choose A4 (zero + renormalize), NOT a recipe re-solve.**
Vehicle: a governed V7.1-style spec bump — new spec file (per §8, "any edit to
weights invalidates this document; new versions = new V# spec file"), carrying:
- the same 20-sleeve table with 2 zeroed weights + renormalized survivors,
- the §4.1 S1 language updated: a zero+renorm is NOT a re-solve; the 3e-4 pin retires
  to 1e-6 (the recipe still regenerates the V7.1 vector from the same solve),
- the decay-monitor history line (stops fired 2026-09-19, acted on <date>).

**If not acting: HOLD (A0).** The stops cost ~4pp/yr in the trail2y regime but the
forward-looking delta is small (OOS ann +0.86pp for A4); the FROZEN-weights
governance and zero hindsight risk are worth more than that if regime persistence
is uncertain.

## Why no spec file was written yet

The operator decision (act vs hold) selects the arms; the vehicle (spec bump) is
ready to draft the moment the decision lands. Writing a V7.1 spec before the decision
would presume it.

---
*Reproduce: `python3 campaign/work_backtest_oos/gov_v8_solve.py` (solver validation +
18-slv solve), `python3 campaign/work_backtest_oos/gov_v8_eval.py` (comparison table).*

## ADDENDUM 2026-09-28 16:5x (landing session): E1-refresh vintage note

This package's quoted numbers (written 11:0x-11:40, before the 12:0x E1/DHHNGSP
refresh landing, commit 17e5be6) are on the PRE-E1-refresh ledger. The committed
CSVs alongside (V8GOV_EVAL_2026-09-30.csv, HARDSTOP_COUNTERFACTUAL_2026-09-30.csv,
V8GOV_candidate_weights.csv, V8GOV_candidate_meta.json) are REGENERATED on the
post-refresh ledger (105,636 rows, recon 1.04e-17) by the same scripts — both
deterministic. The vintage shift is exactly the 19 new E1 marks (all drift in the
same direction, e.g. A0 full SR 4.042 -> 4.0458; A4 4.070 -> 4.074; every
qualitative conclusion — A4 weak dominance, ranking, DD, negYr=0 — is unchanged).
The operator act/hold decision is unaffected: the deltas it weighs are
arm-to-arm differences, measured on ONE ledger in the committed CSVs.
