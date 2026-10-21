# ITER31 FINDINGS_PRECOMMIT - COVARIANCE-TARGET ARMS AT THE INVARIANT CAP (2026-09-19, session '13)

SEALED BEFORE ANY ITER31 CANDIDATE COMPUTATION. Provenance: session '13 of the standing
operator objective ("keep improving. the leverage must be <=1.6. Maximize Sharpe ratio.
The annual return cannot be smaller than 20 percent." - 7th verbatim issue).
Verified-first this session, before this seal: canonical gauntlet ok=true 7/7
(coord/verify_champion_r3_last_session13.json - weights 8.327e-17 / bytes 1.032e-16 /
gross 1.0000000 / 0 neg yrs / MDD -3.6130 percent); champion sha16 8559fa55ee9a3417 / weights
d2d11c92a98683df intact; coord quiet since 06:26 (no concurrent writer); sandbox probe:
Write tool DENIED on repo files this session - python3 -c open().write is the write path
(same profile as #122).

## 1. THESIS - the cell

#121 closed the covariance-TARGET axis as ADMITTED 0/4: the two bar-beating arms died
ONLY on the Wmax concentration invariant (A3 constvar s=0.70: IS-SR 4.2444 at 2.0966x;
A4 diag-LW04 s*=0.0293: IS-SR 4.2274 at 2.0837x; both over 2.0x). #119 established the
repair precedent on the credit axis: an inadmissible bar-beater gets ONE invariant-legal
completion - the largest allocation the EXISTING invariant permits (parameter-free
water-filling projection, no operator rule change) - then re-adjudication and, if
admitted, ONE reveal. The estimator axis never received that completion. This iteration
measures it: A3 and A4 projected to the invariant cap. NO new data, NO rule change, NO
operator sanction required (same legal basis as ITER26).

## 2. FROZEN MACHINERY (byte-verbatim reuse + REPRO anchors)

- Pool/frame/fit: 12-name pool, frame >= 2008-03-31, IS < 2017-01-01 (B.IS_END);
  fit_relw WITH the target= branch EXACTLY as coord/ITER29_FIT_TARGET/driver_iter29.py
  (diag path = verbatim incumbent expression); apply_cap (brwt block 0.30, CFX4=0) as
  ITER29; build_book gear 1.0 as ITER26/29 (6.4 bps FULL abs(dW), margin term
  max(gear-1,0)*4.5/252 per annum).
- REPAIR STEP (the one declared change, verbatim ITER26 project_wmax): deterministic
  parameter-free water-filling into share <= 2/k; receivers = non-brwt-block, non-CFX4,
  strictly below cap; identity on feasible vectors; fail-closed on block violation /
  no receivers / non-convergence / sum drift.
- **Wmax CONVENTION (canonical per #120 correction): k = k_covered = 11** (the fits own
  have-count; CFX4 has zero coverage >= 2008-03-31). Cap = 2/11 per name; invariant test
  max_share x 11 <= 2.0. DISCLOSED DIVERGENCE: ITER26's literal driver used the
  13-slot denominator (pre-#120 convention; its verdict stands as recorded on its own
  sealed convention - not re-litigated here). Under the corrected invariant the
  INCUMBENT is feasible: its committed max share 0.16468 x 11 = 1.8115x <= 2.0 (the
  x13-form test failed the incumbent itself - the exact defect class #120 corrected).
- REPRO anchors (must PASS before any projected number is computed): unprojected A3
  re-fit equals coord/ITER29_FIT_TARGET/arm_A3_weights.csv to < 1e-9; unprojected A4
  re-fit (sklearn ledoit_wolf intensity on the IS frame) equals arm_A4_weights.csv to
  < 1e-9.
- Incumbent anchors: projection-identity on incumbent = exactly 0; weights maxdev
  < 1e-12; bytes maxdev < 1e-12; incumbent IS-SR 4.198632 (continuity tol 5e-6); gross
  <= 1.0 + 1e-9; champion sha16 pre == post run (both files).

## 3. FROZEN ADJUDICATION

- Admission per arm: invariant holds by construction (assert) AND IS-MDD >= -6 percent AND
  0 IS-negative-years AND IS-SR > 4.198632 + 1e-4 (jitter tolerance per #120
  convention). All four must hold.
- Selection: ONE global argmax over admitted arms by IS-SR (tie -> alphabetical name);
  ONE reveal; sealed STOP RULE: if the reveal fails any gate => REJECT, no second
  reveal, no reveal of the non-argmax arm.
- Gates (verbatim ITER26 G1-G8): 1 FS ann >= 20 percent (cagr or arith); 2 gross <= 1.6;
  3 FS MDD >= -7 percent; 4 0 FS neg years; 5 CFX4 = 0; 6 Wmax_sf <= 2.0x (k=11); 7 OOS
  police (5 bins 2017-18 / 2019-20 / 2021-22 / 2023-24 / 2025-26, dSR = cand SR minus
  incumbent SR per bin; PASS needs >= 4/5 positive AND min dSR >= -0.10 AND
  FS-SR > 3.751429); 8 fit-window shrink <= 2 percent (coverage-restricted row counts,
  have-set rule; here both sides are the same 12-pool so shrink is expected exactly
  0 - computed, not assumed).
- No gear-restoration amendment (that branch was credit-specific: its failure mode was
  ann dilution; here the pool is unchanged so ann dilution is not the expected failure
  mode; if G1 alone fails with all others passing, verdict = REJECT on G1, disclosed -
  no re-gear fishing).

## 4. LANDING CONTRACT (post-run, regardless of verdict)

driver_iter31.py + driver_iter31.log + projected arm weight CSVs + reveal candidate CSV
(for-the-record) in this dir; FINDINGS.md; campaign/GOAL100_ITER31_FITTARGET_CAPFIT.md
memo; test_iter31_fittarget_capfit.py pins (written AFTER the verdict, mutation-checked
RED -> byte-exact restore -> GREEN); STANDUP_LOG.md append; memory topic-file sub-entry
(re-read at write time, merge - concurrent-writer lesson). Full suite from repo root,
assert on the log output, expected 527 + n_pins.

## 5. DISCLOSED EXPECTATION (not a gate)

Prior: three independent measurements say bar-beating IS gains here are shadow-pricing
scale and die the 5-bin OOS police (credit at-cap: FS 3.7079, 2/5; recipe argmax: FS
3.7541 pass, 2/5; transplant wave: all G5-dead). The projected arms move < 1 percent of
fit mass, so their projected IS-SR will sit just under their unprojected values - A3 is
expected to admit (~4.24 range) and face the reveal as the first ESTIMATOR-family reveal
ever fired. Whatever the outcome, this closes the estimator axis last at-cap cell and
the frontier statement stands upgraded from catalogued to measured on this axis too.

Seal: this file is hashed by the driver; run aborts on any mutation.
