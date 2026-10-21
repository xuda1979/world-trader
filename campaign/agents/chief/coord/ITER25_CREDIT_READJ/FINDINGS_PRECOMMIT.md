# ITER25 PRE-COMMIT - sealed BEFORE any candidate computation (2026-09-19, session #7)

Operator objective (4th verbatim re-issue): "keep improving. the leverage must be <=1.6.
Maximize Sharpe ratio. The annual return can't be smaller than 20%."

Champion of record at seal time: ITER21 gear-1.0 book, sha16 8559fa55ee9a3417, weights
d2d11c92a98683df, ann 23.6054% (CAGR) / SR 3.751429 / MDD -3.6130% / 0 neg yrs / gross 1.0.
Fresh canonical gauntlet THIS session, BEFORE sealing: ok=true 7/7 (byte_repro 1.032e-16,
gross 1.0000000, n_over 0, cost 4.031 bp/yr, causality nav.shift(1)). Weights sha16
d2d11c92a98683df verified.

## 1. Audit finding under test (the reason this iteration exists)

Adoption gate 8c ("Blend dAnn > 0, HARD", GATES_CONTRACT_V2) and the ITER16 new-engine
rejections built on it were certified against champions that have since been SUPERSEDED
TWICE (ee03f5c0 ann 39.50% era; then the 1.6-gross pin). The operator's stated constraint
is a FLOOR - ann >= 20% - not "no dilution vs incumbent". 8c as written can reject a
candidate that RAISES the objective (SR) while staying inside the operator's actual
constraint set. No post-ITER19/20/21 re-adjudication of the standing 8c-only rejects
exists on disk. RB_hobr is the ONE exception (re-anchored under the current objective,
#114: IS +0.32 SR but OOS -1.13pp ann / -0.015 SR - died on robustness, stays dead).

SCOPE = re-adjudicate the standing 8c-only-rejected candidates under the CURRENT champion
and the OPERATOR'S stated gates. Robustness gates are NOT weakened: the OOS police, Wmax
concentration invariant, capital-real/cost/causality requirements, and the standalone
sleeve qualification bar all remain exactly as ratified.

## 2. Frozen candidate set (chosen on artifact existence + provenance ONLY, pre-reveal)

- **A5_r7_credit_composite** (campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv,
  1990-01-03..2026-08-27, n=9163, col `ret`, 0 NaN). THE candidate. Provenance: full .meta
  (FRED DAAA/DBAA/DGS10; construction R = 0.1*TR_AA + 0.6*TR_SPR + 0.3*(TR_AA -
  hedge*TR_UST); T+1 shift(1) with the same-day-lookahead draft DISCARDED and disclosed;
  6 bps one-side; trailing-only vol-target 10% clip 2.0). Standalone battery PASSED:
  SR 1.51, plateau no-isolated-spike, halves 1.69/1.35, 2 neg years in 37 both > -5%,
  scramble p=0.000 (200 perms, T+1 costs reapplied), max |corr| to 42-sleeve library 0.13.
  Repro: campaign/scripts/a5_r7_final_credit_composite.py. Known tail mismatch: sleeve ends
  2026-08-27 vs champion 2026-08-28 (credit flat on the book's last day; disclosed, no
  filter depends on it).
- Excluded pre-reveal, with reasons (recorded so the exclusion is auditable):
  - **H21_fixed** (campaign/agents/COORD/sleeves/H21_fixed.csv): NO .meta on disk -
    provenance fail-closed (same class as ITER24's vol-complex exclusion).
  - **VOL2-R3 six + CRYPTO2-R3**: never passed the STANDALONE sleeve bar (VOL2 gate-a
    SR>=1.0: best 0.78; gate-d neg-years: 3 neg yrs worst -7.8%) - the exclusion is
    independent of 8c and predates this iteration's gate question.
  - **CFX4 family**: dead (vendor artifact; fx_hist extension rendered unreproducible).
  - **RB_hobr**: already re-adjudicated under the current objective (#114) - rejected on
    OOS honesty, not on 8c. Not re-opened.

## 3. Method (ITER24 machinery verbatim, so results are comparable across iterations)

Driver modeled on ITER24_DA/driver_2026-09-19.py (own implementation of the rawew13v2
algebra, anchor-validated every run):
- 13-name pool = champion 12 (B.NAMES) + credit. Frame >= 2008-03-31.
- relw = apply_brwt_cap(fit_relw(IS = 2008-03-31..<2017-01-01, shrink 0.70), cap 0.30);
  CFX4 pinned 0. Book build = nav-rebalance algebra at gear 1.0, 6.4 bps FULL |dW|,
  margin max(gear-1,0)*4.5%/252.
- ANCHORS before any candidate: weights maxdev < 1e-12 vs committed vector; bytes maxdev
  < 1e-12 vs champion CSV; grossmax <= 1.0+1e-9; incumbent IS-SR = 4.198632 (ITER22/23/24
  continuity). Champion + weights sha16 pre-run == post-run (bytes never written).
- IS filters (ITER23/24 verbatim): Wmax <= 2.0x equal (max share * 13 <= 2.0),
  IS-MDD >= -6%, 0 IS neg years. Admission = filters AND IS-SR > 4.198632.
- ONE global IS-argmax (here: the single candidate, if admitted), revealed ONCE.

## 4. Reveal gates (G1-G7, ITER24 verbatim)

- G1: FS ann >= 20% (CAGR or arithmetic, either passes - champion headline convention
  is CAGR 23.6054%).
- G2: grossmax <= 1.6 (leverage cap).
- G3: FS MDD >= -7%.
- G4: 0 FS negative years.
- G5: CFX4 relw = 0 exactly.
- G6: Wmax <= 2.0x.
- G7: OOS police - dSR vs incumbent positive in >= 4/5 bins {2017-18, 2019-20, 2021-22,
  2023-24, 2025-26} AND min bin dSR >= -0.10 AND FS SR > 3.751429.

## 5. Pre-declared deterministic amendment (gear restoration - NOT a search)

If G2..G7 all PASS but G1 fails with FS CAGR >= 18%: compute net book at the SMALLEST
gear g in {1.00, 1.05, ..., 1.30} with CAGR(g) >= 20% (ann scales ~linearly in gear; the
ITER21 identity makes net SR strictly decreasing on [1, 1.6], so smallest-restoring g is
the SR-argmax choice - one deterministic computation, no mining). Adopt at g only if
SR(g) > 3.751429 and all other gates hold at g. If FS CAGR < 18%, reject outright
(restoration is non-viable under the margin drag).

## 6. Stop rule + adoption ordering

- ANY gate fail (including at restored gear) => iteration CLOSED honest-negative. No
  second reveal, no candidate variations, no parameter retries.
- On 7/7 PASS: the champion swap does NOT happen inside the reveal step. First: full
  battery - 8h-style vol/corr-matched placebo, 8i single-episode-exclusion on dMDD,
  halves-consistency of the delta, independent re-verification from a second process,
  mutation-checked pins - then the archive+re-pin wave. Fail-closed ordering: any battery
  failure also closes the iteration as a reject.
- Champion bytes are never written by the driver; sha16 asserted pre/post.

## 7. Deviation ledger (disclosed pre-reveal)

1. Weights set by the house pool fit (minsharpe, shrink 0.70, brwt-cap 0.30) rather than
   hand-picked overlay rungs: this is the ITER20/22/23/24-ratified selector; the SS8
   fixed-rung blend grid is not re-run.
2. 8c (dAnn > 0) replaced by the operator's stated floor (G1 ann >= 20%): this
   substitution IS the audit finding under test - it is declared, not silent. All other
   SS8 robustness content is preserved via G3/G4/G7 and the post-PASS battery.
3. Credit sleeve's own internal vol-target (10%, clip 2.0) is part of the published
   sleeve stream - used as-is, consistent with how every other pool sleeve enters the fit.

Seal: this file written before the driver is invoked; driver log is the audit trail.
