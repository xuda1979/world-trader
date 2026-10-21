# ITER29 FINDINGS_PRECOMMIT — WEIGHT-FIT COVARIANCE-ESTIMATOR FAMILY (2026-09-19, session #11)
# Sealed BEFORE any variant return was computed. Provenance: coordinator main session #11;
# mirrors are byte-verbatim from coord/ITER28_CENSUSREMAINDER_FIX/driver_iter28.py except
# the disclosed changes below (house targeted-replacement discipline, ITER27->28 precedent).

## Operator objective (verbatim, 6th issue): keep improving; leverage <= 1.6; maximize
## Sharpe; annual return >= 20%.

## THESIS
The champion weight fit (fit_relw) shrinks the IS sample covariance toward the DIAGONAL
at fixed intensity s=0.70: Sig* = 0.30*S + 0.70*diag(diag(S)). The shrink INTENSITY is
measured-closed (ITER22 15-pt grid: argmax = incumbent (0.70, 0.30); ITER23 grid edges:
all inadmissible Wmax). The shrink TARGET FORM is an orthogonal, NEVER-measured cell of
the same estimator. Fit-rule changes have adoption precedent (ITER15: IS max-Sharpe
replaced SR^P) — this is an iteration-class lever, not an operator rule change.

## FROZEN FAMILY (5 arms; everything else byte-verbatim from the ITER28 mirror:
## same 12-pool frame, same IS window 2008-03-31..B.IS_END, same fit_relw optimizer/
## starts/bounds/W_MAX, same apply_cap, same build_book gear 1.0, same gates G1-G7,
## same 5 OOS bins vs incumbent champion 3.751429)
- A0 ANCHOR (NOT a candidate): diagonal target s=0.70 — must reproduce committed
  weights (maxdev < 1e-12), bytes (maxdev < 1e-12, n=4806), grossmax <= 1+1e-9,
  incumbent IS-SR 4.198632 (tol 5e-6). Fit rows must equal 1809, k_covered 11.
- A1 constcorr s=0.70: target T = sd*sd' * C_cc elementwise, where sd_i = sqrt(diag(S)),
  R = inv(D) S inv(D), rho = mean(offdiag(R)), C_cc = (1-rho) I + rho * ones.
  Sig* = 0.30*S + 0.70*T.
- A2 singleindex s=0.70: market m = row-mean of the IS frame X; beta_i = cov(x_i,m)/var(m);
  psi_i = max(var(x_i) - beta_i^2 var(m), 0); T = var(m) * beta beta' + diag(psi).
  Sig* = 0.30*S + 0.70*T.
- A3 constvar s=0.70: T = mean(diag(S)) * I. Sig* = 0.30*S + 0.70*T.
- A4 LW04 constcorr optimal intensity: s* = clip((pi_hat - rho_hat)/gamma_hat, 0, 1) per
  Ledoit-Wolf 2004 constant-correlation formulas computed on X (mu-agnostic); Sig* =
  (1-s*)*S + s* * T_cc. s* recorded in the log.

## ADMISSION FILTERS (per #120 conventions, frozen)
For each variant arm: max_share x k_covered <= 2.0 + 1e-9; IS-MDD >= -6%; 0 IS-neg yrs;
fit rows == 1809 (identical frame, asserted); JITTER TOLERANCE: IS-SR must exceed the
incumbent bar 4.198632 by MORE than 1e-4 (the xlf lesson — equality-level deltas are
solver noise, never admission). Objective: pure IS-SR of the fitted book at gear 1.0.

## SELECTION + STOP RULE (frozen)
ONE global IS-argmax among ADMITTED arms; ONE reveal vs the incumbent champion book;
gates G1-G7 verbatim (G7 = 5-bin OOS police, >= 4/5 positive, min bin >= -0.10, FS SR
> 3.751429). Fail => REJECT, no second reveal, no repair iteration unless a PRE-REVEAL
defect is disclosed (ITER27->28 precedent; any repair re-seals fresh). Champion bytes
must be identical pre/post run (asserted). If NO arm is admitted => honest negative,
estimator-target axis closed.

## EXCLUSIONS (recorded pre-reveal)
None beyond the arms — this family adds NO sleeve and NO data; it perturbs only the
covariance target inside the existing fit. The incumbent fit itself is A0, the anchor.

## ANCHORS ALREADY RUN THIS SESSION (before sealing)
verify_champion.py r3 args => ok=true 7/7 (campaign/agents/chief/coord/
verify_champion_r3_iter29_start.json): weights_repro 8.327e-17, byte_repro 1.032e-16,
cost full_dw ratio 1.000000000, causality causal, gross 1.0000000 / n_over 0, 0 neg yrs.
Champion sha16 8559fa55ee9a3417 / weights d2d11c92a98683df verified on disk this session.

## DEVIATIONS FROM THIS PRE-COMMIT: none at seal time. Any post-seal change must be
## disclosed in FINDINGS.md with the same discipline as ITER27's DEFECT DISCLOSED.


## AMENDMENT 1 (pre-run, BEFORE any variant computation — same session, no arm has run)
A4 is REPLACED: the Ledoit-Wolf 2004 CONSTANT-CORRELATION closed-form (pi/rho/gamma
formulas) is swapped for the DIAGNOAL-target Ledoit-Wolf optimal intensity via the
battle-tested sklearn implementation (sklearn.covariance.ledoit_wolf, 1.9.0), applied as
Sig* = (1 - s*_lw) * S + s*_lw * diag(diag(S)) on our annualized unbiased sample S.
Rationale: the constcorr LW04 index conventions are error-prone to hand-implement; the
diagonal-target LW estimator is the canonical well-tested form. Only the INTENSITY is
borrowed from sklearn (computed on the raw IS frame X); it is applied consistently in
our units. Dependency: sklearn (verified importable in this env, 1.9.0). Arms are now:
A1 constcorr s=0.70, A2 singleindex s=0.70, A3 constvar s=0.70, A4 diag-LW04 s=s*_lw.
Everything else in this pre-commit unchanged. Amended-sha discipline: this file's new
sha16 is cited by the driver and FINDINGS.
