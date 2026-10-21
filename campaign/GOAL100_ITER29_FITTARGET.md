# GOAL100 ITER29 — WEIGHT-FIT COVARIANCE-TARGET AXIS CLOSED (2026-09-19, session #11)

**Operator objective (verbatim, 6th issue):** keep improving; leverage <= 1.6; maximize
Sharpe; annual return >= 20%.

**Champion of record: UNCHANGED.**
`campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv` — sha16
`8559fa55ee9a3417` / weights `d2d11c92a98683df` / CAGR 23.6054% / SR 3.751429 /
MDD −3.6130% / gross 1.0 exact (<= 1.6) / 0 neg yrs.

## What this iteration measured

The champion weight fit shrinks the IS covariance toward the DIAGONAL at fixed
intensity s = 0.70. The INTENSITY is measured-closed (ITER22 15-pt grid + ITER23 grid
edges). The TARGET FORM was never measured — this iteration sealed (pre-commit sha16
`040d6db10788b7f8`, incl. pre-run Amendment 1 swapping hand-rolled constcorr-LW04 for
sklearn's battle-tested diag-target optimal intensity) and ran 4 estimator arms on the
byte-verbatim ITER28 mirror (same frame, optimizer, caps, gates):

| arm | target | s | IS-SR | Wmax_sf | verdict |
|-----|--------|---|-------|---------|---------|
| A1 | constcorr | 0.70 | 4.1658 | 2.5479x | double-dead (< bar AND > wall) |
| A2 | singleindex | 0.70 | 4.1986 | 1.8115x | = bar equality (jitter filter denies); **weights == committed to 1.5e-6** |
| A3 | constvar | 0.70 | **4.2444** (+0.046) | **2.0966x** | NOT ADMITTED — over the wall |
| A4 | diag-LW04 | s* = 0.0293 | **4.2274** (+0.029) | **2.0837x** | NOT ADMITTED — over the wall |

**ADMITTED 0/4 => honest negative, no reveal, stop rule honored.** Driver defect fixed
pre-reveal and disclosed (A2 branch used the 12-col raw frame instead of the fit's
11-col dropna X — fail-closed ValueError; fixed to the pre-commit's own definition;
no arm had run).

## Why this closure matters — the wall is estimator-invariant

Every arm that beats the IS bar does so by concentrating PAST the Wmax 2.0x
concentration invariant; every arm inside the wall delivers exactly the incumbent
solution (A2's weights equal the committed vector to solver jitter — an independent
estimator cross-validating the champion weights, now pinned). Lower shrink = trust the
noisy sample covariance = concentrate — the same shadow-price structure ITER22 measured
on the weight grid, now measured from the estimator direction. A4's data-driven
intensity (2.93% vs the hand-set 70%) quantifies the incumbent's conservatism: buying
it back is worth +0.029 IS-SR — and sits at 2.08x behind the operator's wall. With
intensity (ITER22/23) and target (this) both closed, the fit-rule cell space measured
to date is: rule form (ITER15 adoption), intensity, target.

## Frontier after ITER29

gear (ITER21), weights (ITER22), grid edges (ITER23), census data
(ITER24/#117b/27/28), 8c-era ledger (ITER25), invariant-legal credit (ITER26),
estimator target (ITER29) — all measured closed. The only bars that ever measured
ABOVE the incumbent on IS in the entire campaign now all sit behind the same two
doors: the operator's Wmax 2.0x wall (estimator arms A3/A4, grid corner ITER23) or
the OOS police (every admitted sleeve addition). Remaining levers unchanged: purchased
data or operator rule change — with the operator-side price tags now measured on three
independent axes (Wmax: +0.046 IS-SR / +0.024 FS-SR at the edge; estimator: +0.046;
credit: 19% allocation already OOS-dead at the legal 15.38%).

## Landing

coord/ITER29_FIT_TARGET/ (precommit+findings+driver+log+4 arm weight CSVs);
campaign/bt/tests/test_iter29_fit_target.py — 6 pins, mutation-checked RED (log
mutated ADMITTED 0->4) -> byte-exact restore (sha16 cadfde8a83f927aa) -> GREEN;
this memo; STANDUP_LOG; memory #121. Suite: CONFIRMED 521 passed / 0 failed (515 + 6), own run this
session, 123.10s. Champion sha16 asserted pre == post by the driver AND by pin.
