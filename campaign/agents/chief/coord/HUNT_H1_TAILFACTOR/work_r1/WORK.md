# HUNT_H1_TAILFACTOR R1 — work_r1 record (engine + coverage audit + countersign)

Written AFTER the charter was sealed (58df590f, 2026-10-17 18:52 CST) and BEFORE
any forward return of any panel symbol was computed against any panel factor
value (the real panel never reaches the grid — span guard §Scope-3 fail-closed;
the only grid executions are on deterministic SYNTHETIC fixtures, see below).
This file countersigns the charter (../CHARTER.md IS the pre-registration per
§Scope-1) and records the engine that will mechanically implement it at
evaluation time (≥60 panel dates / ≥3 calendar months, ~early Dec 2026).

## What exists in work_r1 (as of 2026-10-17)

| artifact | role |
|---|---|
| `r1_engine.py` | mechanical implementation of the charter: Stage 0 coverage audit, Stage 1 span guard (fail-closed), Stage 2 gated exhaustive-grid evaluation. Never judges — verdicts ADOPT/REJECT/UNJUDGEABLE are adjudicated by the chief in FINDINGS.md against GATES_CONTRACT_V2. |
| `test_r1_engine.py` | regression tests (19 checks, all PASS, pytest 3 + standalone 19) proving the fail-closed machinery BEFORE the real panel matures. |
| `r1_results.json` | REAL-panel run artifact (2026-10-17): pin PIN-OK, coverage audit, span guard verdict **PROTOCOL-HOLD** (13/60 dates, 2/3 months). NO grid — the engine exits before Stage 2 per §Scope-2 quarantine. |
| `r1_results_synthetic.json` | SYNTHETIC-fixture run artifact: exercises the FULL pipeline (stages 0–2, all 30 grid cells) on a deterministic synthetic panel so the evaluation machinery itself is validated pre-maturity. NOT the live panel; carries no evidential weight for adoption. |
| `WORK.md` | this file. |

## Engine protocol (what run_round does, in order)

1. **Pin guard** (`pin_prefix_guard`): the charter-sealed snapshot
   (sha256 `cae23d09649b1917a77d978e1fbfcac49b52b88961479bdece1a576384339fd1`,
   114 rows / 13 dates / 9 symbols) must remain a byte-identical PREFIX of the
   live `H1_tailfactor_panel.csv`. Append-only scheduled accrual passes;
   mutation / deletion / reordering / truncation of sealed rows →
   **PROTOCOL-VIOLATION**, no grid evaluation, fail-closed.
2. **Stage 0 coverage audit** (diagnostics ONLY, allowed on the fragment per
   §Scope-2): rows/dates/symbols/months, per-date holes, duplicate rows, value
   sanity (p20∈[0,1), var99≤var95<0 monotone, no NaN factors), file sha256.
3. **Stage 1 span guard** (§Scope-3): ≥60 distinct dates AND ≥3 calendar months
   required to reach EVALUATE; otherwise **PROTOCOL-HOLD**, engine exits,
   nothing downstream executes.
4. **Stage 2 grid evaluation** (only on EVALUATE): the §Scope-4 exhaustive
   30-cell grid (per-symbol factor × z-window {21,63} × threshold {1.0,1.5,2.0}
   × 3 families a/b/c), T+1 execution, harness costs 6.4bps one-side |dW| +
   4.5%/yr margin on (gross−1) + 0.5%/yr borrow on short notional, metrics
   per campaign/bt/metrics.py. The WHOLE grid is reported. Pre-committed
   primary: `a_tail_risk_off|p20_30d|L63|t1.5` (SPY long/flat).

## Regression tests — 19/19 PASS (pytest 3 passed; standalone 19 passed, 0 failed)

1. **Pin guard, fail-closed** (7 checks): live panel PIN-OK; appended accrual
   stays PIN-OK; sealed-row mutation blocked; sealed-row deletion blocked;
   truncated panel blocked; sealed-row reordering blocked; byte-identical copy
   PIN-OK.
2. **Span guard on the real 13-date panel** (4 checks): real run exit 0;
   verdict PROTOCOL-HOLD with hold_reason; NO grid key in the real artifact
   (quarantine mechanically enforced); pin_check PIN-OK.
3. **Synthetic determinism + artifact separation** (8 checks): consecutive
   synthetic runs byte-identical; synthetic run never touches the real
   artifact; synthetic span_guard reaches EVALUATE; 30 grid cells present;
   pre-registered primary cell present; real-mode rerun after synthetic still
   PROTOCOL-HOLD + PIN-OK; real artifact rewrite deterministic.

The synthetic grid run additionally demonstrates the machinery can separate
signal families on planted structure (best-sr cell `b_tail_harvest|p20_30d|L21|t2.0`
SR 1.56 vs primary 0.65 on planted fixtures) — a PIPELINE probe only; it says
nothing about the live panel and is treated as zero evidence per the charter's
anti-p-hack commitments.

## Coverage audit of the live panel (2026-10-17, diagnostics only)

- 114 rows, 13 dates (2026-09-08 → 2026-10-16), 9 symbols, 2 calendar months.
- Holes: 2026-10-08 (8 symbols missing), 2026-10-09 (7 missing) — the
  documented CBOE feed gap carried since accrual; noted, not actionable.
- dup_rows 0. Value sanity all TRUE (p20∈[0,1), var monotone negative, no NaN).
- File sha256 == charter pin (prefix check on the full 115-line file: exact
  match — the sealed snapshot IS the current file, accrual not yet past it at
  run time).
- Span guard: 13/60 dates, 2/3 months → **PROTOCOL-HOLD** (correct).

## Countersign

The charter's pre-registration is mechanically enforceable and now enforced:
every path the engine can take (PIN-OK/PIN-VIOLATION, HOLD/EVALUATE,
synthetic/real) has a regression test or a deterministic artifact on file.
No forward return of any panel symbol has been computed against any panel
factor value as of this writing. The round remains PROTOCOL-HOLD until the
panel accrues ≥60 dates and ≥3 months; the next session touching this hunt
should only need to re-run `python3 r1_engine.py` (no `--synthetic`) and
adjudicate in FINDINGS.md against GATES_CONTRACT_V2.

Round state: PROTOCOL-HOLD (by design). Champion of record untouched:
RAWEW13v2_WEIGHTED_GEAR16, sha16 a8ed233bd0f6fd5d.
