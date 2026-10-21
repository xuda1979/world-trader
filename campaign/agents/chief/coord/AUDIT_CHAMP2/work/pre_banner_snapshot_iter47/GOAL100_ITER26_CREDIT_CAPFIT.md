> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
# GOAL100 ITER26 — CREDIT AT THE INVARIANT CAP (2026-09-19, session #9)

**Operator objective (unchanged, 5th verbatim issue):** keep improving; leverage <= 1.6;
maximize Sharpe; annual return >= 20%.

**Champion of record: UNCHANGED.** ITER21 gear-1.0 book sha16 `8559fa55ee9a3417`, weights
`d2d11c92a98683df` — ann 23.6054% (CAGR) / SR 3.751429 / MDD −3.6130% / 0 neg yrs /
gross 1.0 exact. Canonical verification 7/7 this session before sealing (byte-repro
1.032e-16). Champion sha16 asserted pre == post by the driver.

**Champion file re-pin (additive banner, 2026-09-19 session #11 — audit round4b
flagged the sha-only phrasing as unverifiable against future swaps):**
`campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv` — sha16
`8559fa55ee9a3417` / weights `d2d11c92a98683df` / CAGR 23.6054% / SR 3.751429 /
MDD −3.6130% / gross 1.0 exact (<= 1.6) / 0 neg yrs.

## Why this iteration exists (defect repair, not a rule change)

ITER25 rejected credit solely on Wmax 2.4745x > 2.0x — and #118 documented the MECHANISM
as an order-of-operations defect: `fit_relw` already re-solves bounded at 2/k per name,
then `apply_brwt_cap`'s pro-rata redistribution runs AFTER with no post-clamp and silently
breaks the invariant the fit just enforced. So "credit at the largest allocation the
EXISTING invariant permits" was never computed. ITER26 computed it: house order verbatim
plus ONE declared repair step — a parameter-free water-filling projection into
{share <= 2/13} (receivers = non-block, non-CFX4 names; identity on feasible vectors,
asserted exactly 0.0 on the incumbent). Pre-commit sealed before any candidate computation
(`coord/ITER26_CREDIT_CAPFIT/FINDINGS_PRECOMMIT.md`, sha16 `4d3373c65598a1cb`).

## Anchors (all exact)

projection-identity on incumbent 0.000e+00; weights 8.327e-17; bytes 9.996e-17; incumbent
IS-SR 4.198632 (ITER22/23/24/25 continuity); REPRO of ITER25's unprojected 13-pool vector
9.714e-17 (IS-SR 4.2575 / Wmax 2.4745x exact). Disclosed driver fix: G8 row counts are
coverage-restricted (CFX4 has ZERO coverage >= 2008-03-31 — the dead feed — so a naive
all-12-column dropna counts 0 rows; first run failed closed on the division, second run
computes the fit-window shrink over the fit's own `have` sets; bar unchanged).

## Result: admitted in-sample, killed by the OOS police — the cell's first reveal

| quantity | value | verdict |
|---|---|---|
| repair step | credit 0.19034 -> 0.15385 = 2/13 EXACTLY (sole violator); mass to 8 non-block incumbents; Wmax 2.0000x raw == effective | invariant holds BY CONSTRUCTION |
| 13-pool IS-SR | **4.2579** vs incumbent 4.198632 | **PASS** (+0.0593) |
| IS-MDD / neg yrs | −2.52% / 0 of 9 | PASS |
| G8 fit-window shrink | 0.0000% (1809 -> 1809 rows) | PASS |
| **FS SR (the reveal)** | **3.707892 vs incumbent 3.751429 (−0.0435)** | **FAIL G7** |
| OOS bins 2017-18 / 19-20 / 21-22 / 23-24 / 25-26 | −0.0086 / −0.1185 / +0.0258 / +0.1644 / −0.0939 = **2/5 positive** | FAIL G7 (need >= 4) |
| FS ann / MDD / neg yrs | 23.09% CAGR (20.94% arith) / −3.35% / 0 | PASS |

**VERDICT: REJECT — failed gates: 7 OOS police. No second reveal (sealed stop rule).**
The IS gain +0.059 INVERTED to FS −0.0435. ITER17 law's fourth consecutive kill
(bund_02y, cad 2/3/5y, seliccary, now credit).

## What this means

1. **The open operator item "relax Wmax 2.0x?" is answered WITH DATA for credit: relaxing
   buys nothing.** The invariant-legal 15.38% allocation already fails OOS; the
   unconstrained fit's "want" for 19.03% was worth +0.0004 IS-SR over the legal cap
   (margin noise) and would add MORE of the same OOS-failing exposure. Any future
   Wmax-relaxation pitch must first clear the ITER17 law. The only Wmax-bound measurement
   ever on the winning side remains ITER23's grid-edge (+0.024 FS-SR, informational,
   never revealed).
2. **The 13-pool fit's credit appetite was an artifact of constraint shadow-pricing, not
   of marginal alpha** — at the legal cap the fit is already saturated (4.2579 vs
   4.2575 unprojected). This is the same plateau pathology ITER22 documented on the
   12-pool grid.
3. **Frontier statement (now measured, not merely catalogued):** every in-rules cell is
   closed — gear (ITER21), weights (ITER22), grid edges (ITER23), census data axis
   (ITER24/#117b), 8c-era rejections (ITER25), and now the invariant-legal credit cell
   (ITER26, rejected at reveal). Remaining moves are purchased data or operator rule
   changes; both now carry measured evidence against them on their most promising axis.

## Deliverables

- `campaign/agents/chief/coord/ITER26_CREDIT_CAPFIT/`: FINDINGS_PRECOMMIT.md (sealed
  before any computation, sha16 `4d3373c65598a1cb`), FINDINGS.md, driver_2026-09-19.py
  + .log (audit trail incl. the disclosed G8 driver fix), candidate_credit_at_cap_weights.csv
  + _daily.csv (for the record only).
- `campaign/bt/tests/test_iter26_credit_capfit.py`: 6 reality-pins, mutation-checked
  RED -> restored byte-exact -> GREEN (asserts on artifacts, not exit codes).
- Suite after landing: **509 passed / 0 failed** (503 + 6, coordinator's own run).
