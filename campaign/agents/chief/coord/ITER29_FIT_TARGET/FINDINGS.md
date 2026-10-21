# ITER29 FINDINGS — WEIGHT-FIT COVARIANCE-ESTIMATOR-TARGET FAMILY (2026-09-19, session #11)

Pre-commit sealed BEFORE any variant computation: FINDINGS_PRECOMMIT.md sha16
040d6db10788b7f8 (includes Amendment 1, pre-run: A4 swapped from hand-rolled
constcorr-LW04 to sklearn diag-target optimal intensity — implementation-risk
disclosure). Driver: driver_iter29.py (generated from driver_iter28.py by targeted
replacements ONLY: header, OUT dir, fit_relw target branch, ARMS section, reveal
labels, log name — anchors/book/gates byte-verbatim), log driver_iter29.log.

## Anchors (all PASS pre-variant)
weights maxdev 8.327e-17; bytes maxdev 9.996e-17 (n=4806); grossmax 1.000000000 /
0 days > 1.6; incumbent IS-SR 4.198632 exact (continuity asserted 5e-6); fit rows
1809, k_covered 11. Champion sha16 pre == post: 8559fa55ee9a3417 / d2d11c92a98683df.

## DRIVER DEFECT FIXED PRE-REVEAL (disclosed)
Run 1 failed fail-closed in the A2 branch: the single-index market/beta math used the
raw 12-column frame (df_isr, includes the all-NaN-in-IS CFX4 column) instead of the
fit's own dropna'd 11-column X — shape (12,) vs (11,) ValueError at A2. Fix: Xv =
X.values (exactly the pre-commit's own definition "market m = row-mean of the IS frame
X"). No arm had completed at failure time except A1's table row (in-memory); full
re-run from anchors. No pre-commit change needed — the code now matches what was
already sealed.

## RESULT: ADMITTED 0 / 4 — HONEST NEGATIVE, no reveal (STOP RULE honored)
- A1 constcorr s=0.70: IS-SR 4.1658 (< bar) AND Wmax_sf 2.5479x (> 2.0) — double-dead.
  Keeping the average pairwise correlation in the target inflates off-diagonal
  covariance; the optimizer concentrates harder and lands past the invariant.
- A2 singleindex s=0.70: IS-SR 4.1986 = BAR (equality — the jitter-tolerance filter
  correctly denies admission) at Wmax_sf 1.8115x. **The resulting weight vector equals
  the COMMITTED champion weights to maxdev 1.47e-6 (solver jitter; C5ng 1.473e-6,
  carryv2 1.363e-6) — the incumbent fit is the FIXED POINT of a different covariance
  target. Independent-estimator cross-validation of the incumbent: the champion
  weights are not an artifact of the diagonal-target choice.**
- A3 constvar s=0.70: IS-SR 4.2444 = bar + 0.0458 (BEST arm) BUT Wmax_sf 2.0966x >
  2.0 => NOT ADMITTED by the operator concentration invariant.
- A4 diag-LW04 s* = 0.0293 (sklearn 1.9.0 optimal intensity on the IS frame):
  IS-SR 4.2274 = bar + 0.0288 BUT Wmax_sf 2.0837x > 2.0 => NOT ADMITTED.

## STRATEGIC CONSEQUENCE — the estimator-target axis closes WITH STRUCTURE, not just a zero
1. THE WALL IS ESTIMATOR-INVARIANT. Every arm that beats the IS bar (A3 +0.046, A4
   +0.029) does so by concentrating past Wmax 2.0x (2.0966x / 2.0837x); every arm
   inside the wall (A2) delivers EXACTLY the incumbent. The concentration invariant
   binds estimator choice exactly as it binds weights (ITER22/23) and sleeve additions
   (ITER24-28): within the operator's wall, the incumbent solution is a fixed point
   of the whole estimator neighborhood measured here; above the wall's shadow price
   lie only IS-optimism gains (lower shrink = trust noisy sample cov = concentrate),
   which is the SAME plateau pathology ITER22 documented, now measured from the
   estimator direction. A4's data-driven intensity (2.93% vs the hand-set 70%)
   quantifies HOW conservative the incumbent estimator is — and what buying that
   conservatism costs in IS-SR (+0.029) behind the wall.
2. Cross-validation asset: A2 == committed weights (1.5e-6) is a NEW independent
   verification of the champion weight vector, recorded for the integrity file.
3. With this, the weight-fit estimator family is closed: intensity (ITER22/23),
   target form (this iteration). The fit-rule cell space measured to date: rule form
   (ITER15 adoption), intensity, target. Remaining fit-rule cells (e.g. robust/
   non-Gaussian objectives, mean-vector shrinkage) are charted but lower-prior than
   the measured walls suggest.

## Landed (this dir)
FINDINGS_PRECOMMIT.md (sha16 040d6db10788b7f8, Amendment 1 inside), driver_iter29.py,
driver_iter29.log, arm_A1/A2/A3/A4_weights.csv, this FINDINGS.md. Pins: 
campaign/bt/tests/test_iter29_fit_target.py (mutation-checked). Memo:
campaign/GOAL100_ITER29_FITTARGET.md. Suite CONFIRMED: 521 passed / 0 failed (515 + 6), own run, 123.10s (post-landing background run, output read).

Champion of record UNCHANGED: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16
8559fa55ee9a3417 / weights d2d11c92a98683df / CAGR 23.6054% / SR 3.751429 / MDD
-3.6130% / gross 1.0 (<= 1.6) / 0 neg yrs.
