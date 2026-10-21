# ITER26 PRE-COMMIT - sealed BEFORE any candidate computation (2026-09-19, session #9)

Operator objective (5th verbatim re-issue): "keep improving. the leverage must be <=1.6.
Maximize Sharpe ratio. The annual return can't be smaller than 20%."

Champion of record at seal time: ITER21 gear-1.0 book, sha16 8559fa55ee9a3417, weights
d2d11c92a98683df, ann 23.6054% (CAGR) / SR 3.751429 / MDD -3.6130% / 0 neg yrs / gross 1.0.
Fresh canonical verification THIS session, BEFORE sealing: ok=true 7/7 (weights_repro
8.327e-17, byte_repro 1.032e-16, cost full_dw 4.031 bp/yr, causality nav.shift(1),
truncation 0.0, gross 1.0000000 n_over 0, yearly 0 neg / worst +7.35%, MDD -3.6130%),
written to coord/verify_champion_r3_last_session8.json. No concurrent writer (coord mtimes
quiet since 02:55; no ITER25 processes live at 03:06).

## 1. Defect under repair (the reason this iteration exists)

ITER25 (sha16-sealed precommit d176f7cb8f2f11f5) found the 13-pool fit EARNS credit
relw 19.03%, IS-SR 4.2575 > 4.198632, IS-MDD -2.52%, 0/9 IS neg yrs - and rejected it
solely on Wmax 2.4745x > 2.0x, reveal never fired (sealed stop rule). #118 then documented
the MECHANISM: the house order is fit_relw -> apply_brwt_cap, where fit_relw ALREADY
enforces the invariant (second solve bounded at cap = W_MAX/k = 2/k per name - driver
lines 54-56) and apply_brwt_cap's pro-rata redistribution runs AFTER with NO post-clamp,
silently breaking the invariant the fit just enforced. The 2.4745x breach is credit at its
legal 15.38% bound PLUS redistributed brwt-block excess - an ORDER-OF-OPERATIONS defect
(#118: "apply_brwt_cap has NO post-redistribution clamp"), not credit's maximal legal
allocation. The cell "credit at the largest allocation the EXISTING invariant actually
permits" was never computed. ITER26 computes it. This is a DEFECT REPAIR, not an operator
rule change: the resulting vector satisfies Wmax <= 2.0x exactly as ratified (ITER23/24/25
convention), and gross/gear/CFX4/MDD/OOS police are untouched.

## 2. Frozen candidate (inherited verbatim from ITER25 section 2 - no new candidates)

- **A5_r7_credit_composite** (campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv,
  1990-01-03..2026-08-27, n=9163, col ret, 0 NaN; full .meta FRED DAAA/DBAA/DGS10;
  standalone battery PASSED: SR 1.51, scramble p=0.000, max |corr| to library 0.13).
- Exclusions inherited verbatim (H21_fixed no-.meta fail-closed; VOL2-R3/CRYPTO2
  standalone-bar; CFX4 dead; RB_hobr re-adjudicated #114). NO other sleeve is added.
  No bund/cad/seliccary revival (OOS-dead per #117/#117b); no new data (census closed).

## 3. Method (ITER25 machinery verbatim + ONE declared repair step)

Driver modeled on ITER25_CREDIT_READJ/driver_2026-09-19.py (anchor-validated):
- 13-name pool = champion 12 (B.NAMES) + credit. Frame >= 2008-03-31, IS < 2017-01-01.
- relw_pre = apply_brwt_cap(fit_relw(IS, shrink 0.70), cap 0.30) - VERBATIM house order.
- REPAIR STEP (the single change): project_wmax_invariant(relw_pre) - deterministic
  parameter-free water-filling: while max share > 2.0/13 + 1e-12: clamp every violating
  name to 2.0/13, distribute the collected excess pro-rata CURRENT values among receiving
  names = non-violating names NOT in BRWT_BLOCK and NOT CFX4; repeat. Guarantees asserted
  post-projection: max share <= 2.0/13 + 1e-12 (raw convention: Wmax = max*13 <= 2.0);
  BRWT_BLOCK combined share == 0.30 (untouched); CFX4 == 0; vector sum preserved
  (= pre-projection sum); receivers never decrease. Rejected alternative (disclosed):
  re-solving the fit with joint brwt+invariant constraints - rejected because it changes
  the house estimator instead of repairing its output.
- IDENTITY-ON-FEASIBLE anchor: the SAME projection applied to the incumbent 12-pool
  construction (k=12, cap 2.0/12) must be the identity - incumbent weights maxdev < 1e-12
  vs committed d2d11c92 vector (it is feasible at 1.9762x, so water-filling never fires).
- ANCHORS before any candidate: weights maxdev < 1e-12; bytes maxdev < 1e-12 vs champion
  CSV; grossmax <= 1.0 + 1e-9; incumbent IS-SR = 4.198632 (ITER22/23/24/25 continuity).
- REPRODUCTION anchor: the UNPROJECTED 13-pool fit must reproduce ITER25's logged vector
  (maxdev < 1e-9 vs coord/ITER25_CREDIT_READJ/candidate_A5r7credit_weights.csv) - proves
  the machinery is byte-equivalent before the repair step is allowed to differ.
- Book build = nav-rebalance algebra at gear 1.0, 6.4 bps FULL |dW|, margin
  max(gear-1,0)*4.5%/252. IS filters (verbatim): Wmax <= 2.0x (max share * 13; now by
  construction, asserted not assumed), IS-MDD >= -6%, 0 IS neg years. Admission =
  filters AND IS-SR > 4.198632. Effective-share disclosure: raw convention is the gate
  (as in ITER24/25); effective Wmax = max(share/(sum-CFX4)) * 13 logged informationally.
- G8 (declared STRICTER addition, from the #117b seliccary protocol): fit-window row
  shrink = 1 - n_rows(13-name IS frame) / n_rows(12-name IS frame), both inner-joined
  >= 2008-03-31 & < 2017-01-01, must be <= 2%.
- ONE global candidate, revealed ONCE if admitted.

## 4. Reveal gates (G1-G7 ITER25 verbatim + G8)

- G1: FS ann >= 20% (CAGR or arithmetic). G2: grossmax <= 1.6. G3: FS MDD >= -7%.
- G4: 0 FS negative years. G5: CFX4 relw = 0 exactly. G6: Wmax <= 2.0x.
- G7: OOS police - dSR vs incumbent positive in >= 4/5 bins {2017-18, 2019-20, 2021-22,
  2023-24, 2025-26} AND min bin dSR >= -0.10 AND FS SR > 3.751429. G8: fit-window
  shrink <= 2%.

## 5. Pre-declared deterministic amendment (gear restoration - NOT a search; ITER25 s5 verbatim)

If G2..G8 all PASS but G1 fails with FS CAGR >= 18%: compute net book at the SMALLEST
gear g in {1.00, 1.05, ..., 1.30} with CAGR(g) >= 20%. Adopt at g only if SR(g) > 3.751429
and all other gates hold at g. If FS CAGR < 18%, reject outright.

## 6. Stop rule + adoption ordering (ITER25 s6 verbatim)

- ANY gate fail (including at restored gear) => iteration CLOSED honest-negative. No
  second reveal, no candidate variations, no parameter retries, no further projections.
- On full PASS: champion swap does NOT happen inside the reveal step. First the full
  battery (vol/corr-matched placebo, single-episode-exclusion on dMDD, halves-consistency
  of the delta, independent re-verification from a second process, mutation-checked pins),
  then the archive+re-pin wave. Any battery failure also closes the iteration as a reject.
- Champion bytes are never written by the driver; sha16 asserted pre/post.

## 7. Deviation ledger (disclosed pre-reveal)

1. The repair step of section 3 - applied to the CANDIDATE construction only; identity on
   the incumbent (asserted). This is the iteration's declared single change and is the
   #118 defect repair. If the candidate is ultimately adopted, the builder-side fix
   (post-redistribution clamp in rawew13v2_build.apply_brwt_cap) lands separately with
   TDD pins; the reveal driver carries the mirror only.
2. G8 added (stricter; can only reject, never admit).
3. Everything else - pool, candidate, filters, gates, amendment, stop rule - VERBATIM
   ITER25/ITER24 machinery.

Honest prior (not a gate, recorded for calibration): the ITER17 law has killed every IS
gain revealed OOS this week (bund +0.074 IS -> FS -0.023; seliccary passed FS-SR + dAnn,
died 3/5 bins). The projection may also simply lower IS-SR below the 4.198632 bar, in
which case the credit cell closes as "even at its maximal invariant-legal allocation,
credit does not clear the IS bar". Either outcome closes the last unmeasured in-rules cell.

Seal: this file written before the driver is invoked; the driver log is the audit trail;
sha16 of this file recorded in the driver log header.
