# VERIFY_BEST — FINDINGS (track B independent re-verification, 2026-09-03)

Agent: loop_team/VERIFY_BEST. Charter: independently re-verify the campaign's best results.
Method: superpowers rigor — (0) negative-control tests proving every gate has teeth BEFORE use;
(1) byte-repro of frozen builder; (2) INDEPENDENT rebuild from raw sleeve files with my own
code (no import of honest13_build); (3) campaign/bt modules (engine/metrics/gates/reconcile)
for all headline numbers; (4) systematic-debugging on every anomaly. Scripts in scratch/.
Framework self-test: bt/tests 26/26 PASS before any use.

## 0. NEGATIVE CONTROLS (TDD RED discipline — gates must FAIL on tampered input)
scratch/tdd_negative.py, all PASS:
- N1 repro_ok catches 1e-6 tamper; N1b accepts identity. -> byte-repro gate is not vacuous.
- N2 ledger WITH costs reproduces (max_diff 0.0); N2b cost-omitting ledger FAILS at max_diff
  2.000e-05 — the exact BLOTTER_TESTER CRITICAL bug class is caught by bt.reconcile.
- N3 turnover gate accepts honest qty; N3b 2x-inflated qty FAILS.
- N4 constant series uniq_ratio ~0 -> flatten gate flags; noisy series passes.
- N5 return-roll preserves SR EXACTLY (real 1.358219; rolls @1/21/252/999 all 1.358219)
  -> any SR-based return-scramble null is provably degenerate. Confirmed.
- N6 (after fixing MY test construction — first version had no timing edge, real SR −0.66):
  AR(1) phi=0.6 book, real SR 8.542 -> rolled-position SR 0.073. Position-lag test has power.

## 1. OBJECT 1 — V3 CHAMPION (GOAL100_HONEST14V3_BALANCED_daily.csv): PASS
(a) Frozen builder byte-repro: `python3 campaign/scripts/honest13_build.py --verify-v3`:
  BALANCED max|new-old|=9.988e-17 IDENTICAL; SAFE 9.996e-17 IDENTICAL; AGGRESSIVE 9.986e-17
  IDENTICAL (n=5086 rows each, 2006-10-02..2026-08-27).
(b) INDEPENDENT rebuild from raw sleeve files (scratch/v3_rebuild.py; my own sn/vt/make/build
  re-derivation: 11 pool holiday-folded + 3 new sleeves at slot 0.10 vs 1.0, per-sleeve vt
  0.08 rolling-60 shift(1) cap 8, exec-cost adj on slot book, global vt SAFE .07/THR .04 AGGR
  .091/.03, throttle on trailing-126d-peak shift(1) DD, 6.0bps/side on all streams, borrow
  0.5%/yr + dualmom HTB uplift): max|rebuilt-committed| = 9.996e-17 (SAFE) / 9.986e-17
  (AGGR) / 9.988e-17 (BAL), inner-join complete (no index mismatch). BYTE-IDENTICAL.
(c) Headline metrics (bt.metrics.report on committed file, 2008-03-31+, n=4713):
  BALANCED: ann_geo 0.4361 (43.61%) SR_d 3.924 SR_m 4.016 MaxDD −0.0492 (−4.92%) vol 9.34%
    neg_years 0/19 worst_year +0.1394. MATCHES charter claim exactly (43.6/3.92/−4.92/0/19).
  SAFE: 0.3751 / 3.927 / −0.0487 / 0/19 worst +0.1348. AGGRESSIVE: 0.4996 / 3.912 / −0.0542 /
    0/19 worst +0.1437. H1 SR 3.790, H2 SR 4.060 (no half-decay).
(d) No-same-day-leak probe: rebuilt with SAME-DAY throttle (eq/rm without shift(1)) differs
  from committed by max 1.860e-02 — committed throttle is strictly trailing (T+1). PASS.
(e) Capital-real gross (rebuilt positions Σ|capW_i·gb·sc|, 2008-03-31+): BAL mean 3.477x
  p50 3.203x max 10.798x; 90.9% of days gross >1.6x (SAFE 86.9%, AGGR 92.2%). Confirms the
  3.48x claim AND that the 43.6% ann requires >1.6x leverage on ~91% of days.
(f) Flatten scan on every sleeve net file (gate ac1<0.5, uniqR>=0.08): worst is diescrack
  uniqR 0.159 (>=0.08 ok); all 14 sleeves ok (brwt15 −0.081/0.329, brwt10 −0.101/0.610,
  brwt7 −0.065/0.614, brwt5 −0.056/0.623, C5ng +0.003/0.776, C5ngsum +0.034/0.466,
  A5r2 −0.025/0.768, a6r7 −0.002/0.870, QAxasts −0.040/0.988, carryv2 −0.080/0.987,
  dualmom −0.135/0.743, diescrack −0.039/0.159, CFX4 −0.132/0.967, FF2 −0.178/0.760).
  Champions: ac1 −0.066/−0.071/−0.061, uniqR 1.000/1.000/1.000, zero interior 0-runs>=20:
  none. NO FLATTENING. (XGB1y trap absent.)
(g) Independent degeneration cross-check (my own exact day-level kappa cap + 4.5% margin on
  (gross−1), all streams scaled linearly): V3 BAL @1.6x -> ann_geo 17.04%, SR_d 3.618, MDD
  −3.66%, gross mean 1.532x, days at cap 90.9%, 0/19 neg. vs AUDIT_LEVFRONTIER's 16.99%/3.628/
  −3.59% — agreement to 0.05pp ann; residual is cap-implementation convention (their budget-
  fill vs my exact kappa scaling), NOT an accounting gap. The "~17-20% honest ceiling at
  <=1.6x" claim is CONFIRMED.

## 2. OBJECT 2 — RAW-EW13@1.6x CANDIDATE: PASS
Independent rebuild (scratch/rawew13_rebuild.py; 13 net files = 11 POOL + diescrack + CFX4,
slot 1/13, NAV-drift weights, daily reset, costs 6.4bps/side x GEAR on reset turnover, margin
4.5%/yr on 0.6x, borrow inside sleeves):
- vs committed results/GOAL100_HONEST_RAWEW13_GEAR16_daily.csv: n=4805/4805 inner 4805,
  max|new-old|=9.991e-17 IDENTICAL.
- bt.engine.capital_gross of geared path: mean 1.600000, max 1.600000000000 (overshoot
  1.110e-15 = float64), min 1.600000; days >1.6+1e-9: 0/4805 (0.0000%). LEVERAGE CAP EXACT.
- bt.metrics.report (2008-03-31+, n=4805): ann_geo 0.2889 (28.89%) ann_arith 0.2560 SR_d
  3.884 SR_m 3.202 MaxDD −0.0425 (−4.25%) vol 6.59% neg_years 0/19 worst_year +0.1018
  (+10.18%). ALL match claimed 28.89/3.88/−4.25/0/19/+10.18. H1 SR 3.702, H2 SR 4.062;
  ac1 +0.007; uniqR 1.000; no zero-runs.
- Cost decomposition: EW-reset turnover 0.001087/day one-side = 0.03bps/yr cost; margin
  2.70%/yr charged on all 4805 days. (Borrow: inside sleeve net files, by construction.)

## 3. OBJECT 3 — TRADE BLOTTERS RECONCILE: PASS
(a) Per-book ledgers results/BLOTTER_HONEST14V3_{SAFE,AGGRESSIVE,BALANCED}.csv
    (rows 239440/239502/239505; streams trade/overlay_vt/throttle/borrow/mark all present)
    via bt.reconcile.ledgers_reproduce(pnl_contrib − cost_total vs committed book):
  SAFE ok=True max|diff|=6.783e-16 (5086 days); AGGRESSIVE 7.399e-16; BALANCED 7.303e-16.
  Ledger-only pre-window days (1990-2006 marks): 4207 days, net sum +0.000e+00 (pure zeros).
  ALL THREE reproduce the champion to ~7e-16 (< 1e-8 gate). PASS.
(b) RAW-EW14 geared blotter (agents/loop_team/AUDIT_LEVFRONTIER/BLOTTER_RAWEW14_GEAR16.csv,
    67,242 records; trade-records-only schema date,sleeve,instrument,side,price,price_source,
    qty_notional,weight_from,weight_to,cost_bps — no pnl column; PnL identity is by
    construction, see (c)):
  - bt.reconcile.turnover_reconciles: ok=True, max_rel 5.575e-09 (<1e-8), 14 sleeves.
  - Independent weight-path rebuild (14 names, NAV-drift x1.6, direct lookup — NOTE my first
    join attempt misaligned via MultiIndex stack and showed spurious 3.96e-01 diffs; root
    cause = pandas stack/join alignment bug in MY probe, fixed with direct indexing):
    weight_to vs rebuilt path: max|diff| 5.000e-11, 0/67242 rows >1e-9 (file is 10-dp rounded).
    qty_notional vs |path diff|: max 5.000e-11, 0 rows >1e-9.
    weight_from == previous weight_to per sleeve: max gap 0.000e+00 (position continuity exact).
    sum(weight_to) per date: 1.5999999996..1.6000000004 (=1.6 within rounding).
    REAL-priced 69.2% (46525/46525 REAL rows carry non-NaN price); cost_bps uniform {6.4};
    side in {BUY,SELL}; qty >= 0 all rows. PASS.
(c) The 14-name candidate's return path recomputed independently (port*1.6 − to*1.6*6.4e-4 −
    0.6*4.5%/252) reconciles with the committed 13-name file only up to the documented FF2
    difference (blotter book = RAW-EW14 incl FF2; committed file = RAW-EW13 excl FF2) — as
    documented in AUDIT FINDINGS; not a discrepancy.

## 4. OBJECT 4 — SCRAMBLE DEGENERACY / VALIDITY: CONFIRMED + NEW FRAMEWORK DEFECT FOUND
(a) RETURN-roll degenerate: np.roll of the BOOK preserves SR to 4+ decimals (3.4653 at lags
    1/63/252/2000) — SR is permutation-invariant; any return-scramble null is VOID. Confirmed.
(b) POSITION-lag valid: same book, positions rolled by 500: SR 3.4653 -> −0.1420. Timing
    destroyed. Confirmed.
(c) NEW DEFECT (root-caused, bt/gates.py scramble_positions, line `real_sr =
    sharpe_d(pd.Series(r))`): the baseline is the RAW-RETURN SR, not the REAL BOOK's SR
    (sig*r). Its own docstring says "fraction of scrambled-book SR >= real SR". Impact:
    - Synthetic timing book: real SR 3.4653, scrambled books centered ~0 -> bt baseline
      (≈0) gives p=0.980 — the test would ACCEPT a destroyed book (WRONG).
    - V3 champion (300 draws, lags 21..T−21, positions = committed construction matrix,
      scrambled with 6.4bps turnover cost charged): bt baseline p = 0.0767 (would spuriously
      FAIL a 0.05 gate); CORRECT baseline (real book recomposed identically = positions x raw
      sleeve returns − 6.4bps turnover, net SR 4.516) gives scrambled SRs mean 3.027, p95
      4.080, max 5.006, p = 0.0067 -> CHAMPION PASSES the honest position-lag scramble.
    Campaign-canonical semantics (scripts/e3_lib.py scramble_pval_pos: baseline =
    sr(net_of(real positions))) confirm the fix direction. RECOMMEND: patch
    bt.gates.scramble_positions baseline to the real book's SR (one line) + add a
    negative-control test (destroyed book must give p < 0.5).
(d) Champion with corrected baseline: p = 0.0067 (PASS; see (c)). The RAW-EW13 book has NO
    signal by construction (static EW slots), so the scramble gate does not apply (its honesty
    gate is the leverage/cost accounting, verified in §2).

## 5. VERDICT
- V3 champion (43.61%/3.924/−4.92%/0/19 at gross mean 3.477x): REAL — byte-reproducible,
  independently rebuilt from raw sleeves to ~1e-16, no same-day leak, no flattening,
  pos-lag scramble p=0.0067, ledgers reconcile to ~7e-16.
- RAW-EW13@1.6x (28.89%/3.884/−4.25%/0/19, worst +10.18%): REAL — byte-identical
  independent rebuild, gross exactly 1.6x (0 days >1.6+1e-9), margin + costs charged.
- Leverage honesty: at <=1.6x + 4.5% margin V3 BAL degenerates to 17.04% (my independent
  exact cap; AUDIT's 16.99% within convention variance) — the "43.6% needs 3.5x gross"
  caveat is confirmed. Both results are honest about their leverage.
- One framework defect found and documented (§4c scramble baseline); champion unaffected
  under corrected semantics. Negative controls prove all other gates have teeth.

DISCREPANCIES FLAGGED: none in committed campaign numbers. 1 defect in campaign/bt tooling
(scramble baseline), 1 probe-construction error of my own (root-caused, fixed), 1 pandas
alignment pitfall in verification code (root-caused, replaced with direct indexing).

VERIFY_BEST DONE
