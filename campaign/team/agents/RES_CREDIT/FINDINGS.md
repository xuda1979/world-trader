# RES_CREDIT FINDINGS — credit spread / rates-curve engines (decorrelated to equity momentum)
> Final verdict: honest **REJECT**. Best engine found passes every honesty gate but misses the
> charter's SR≥1.5 bar (charter explicitly allows REJECT-with-numbers). Two independent vectors
> agree credit/rates-spread is NOT a champion-eligible standalone sleeve.

## Overview (merge of the agent hunt + an independent BAA-AAA verification)
Both angles converge on the same conclusion at two different horizons:
- (a) **Yield-curve-slope (2s10s, t10y2y)** momentum-reversion: strongest credit-adjacent engine
  found — book SR 0.922 / per-unit battery SR 1.062, all gates PASS except SR≥1.5.
- (b) **BAA-AAA credit-spread** mean-reversion / momentum (independent test below): strongly
  negative in the costed/causal/vol-targeted harness — no configuration clears SR>=1.0.

## Agent hunt results (from LOG.log, preserved)
1. **Data verified (fail-closed lint):** HY OAS FRED only 3y span (n=785, 2023+); BAA 40y (n=10151),
   AAA 1983+, t10y2y 2005+ (n=5408), DGS2 to 1976, ETFs HYG/LQD/JNK/EMB/TLT 2002-2007+. 0 gaps,
   0 NA, all ranges plausible.
2. **Decorrelation-FIRST:** whole credit family passes — HYG_mom63 −0.018, LQD-HYG_rel +0.019,
   OAS_chg −0.034. Final sleeve corr_gate **−0.0166 PASS**. (Found + worked around an inf-poisoning
   bug: raw momentum proxies contain ±inf → NaN corr unless cleaned at load.)
3. **TDD RED→GREEN:** 5 tests written first (RED confirmed), then GREEN; combined suites 424 passed.
4. **23 grids / ~120 configs:** OAS→ETF lead-lag dead (all-negative one side); ETF carry eaten by
   2008/2020/2022; quality-spread, breakeven, real-yield, pair-RV all ≤0.36 SR. Winner family:
   **2s10s 5-day-change mean-reversion** — book SR 0.922, per-unit battery SR 1.062, halves
   0.838/1.396, neg yrs 2 (worst −4.47%), ac1 −0.018, uniqR 0.525, scramble p=0.000, leak True,
   corr −0.0198 — **all gates PASS except SR≥1.5**. Plateau: win/band OK, lag FAIL at lb=4 (robust
   lb=6 0.781). Start-cuts improving (2019+ 1.351, 2024+ 1.861), scrub5 min 0.897, fresh repro
   9.996e-17.
5. Disclosures in sleeves/ RC_t102_d5mr_w21_band50_vt5.csv.meta: the deep-history twin collapses at
   SR 0.118 = REGIME-SPECIFIC edge; a real 2s10s fly pays more than the 6.4bps ETF proxy (C2 warning).

## Independent verification (this session, 2026-09-09) — BAA-AAA credit spread
Using MORE_FRED DBAA (1986+, n=10203) / DAAA (1983+, n=10962) and BAA10Y (1986+, n=10167):
- BAA-AAA spread: mean 0.95, range 0.40..3.50 (long-history risk premium).
- Mean-reversion (z of spread, lb {63,126,252}; long LQD 2002+/HYG 2007+ when z>enter): best SR
  −0.00..+0.03 (LQD), all-negative on HYG (−0.24..−0.41), MDD −54%..−71%, 8-13 neg yrs.
- Momentum (z of lb-day spread change): long-side SR ~0, short-side SR −0.6..−1.6 (ann −9%..−19%,
  MDD −92%..−99%). The "buy credit when spread wide" mean-reversion is strongly negative (wide
  states persist — spread-widening is momentum at the tradeable horizon; vol-scaled 1.6x run over
  in 2008/2020).

## NEW DATA FINDING (corrects DATA_COVERAGE)
FRED BAML OAS (BAMLH0A0HYM2/BAMLC0A0CM/BAMLEMHBHYCRPIOAS) currently serves ONLY 793 daily
observations 2023-09-11..2026-09-07 (tested BOTH the api key and fredgraph.csv endpoints on
2026-09-09). The coverage doc's "~7400 rows from 1996+" is STALE for the current FRED vintage.
Long-history credit level data lives in the Moody's BAA/AAA / BAA10Y series (used above).

## Verdict
**REJECT.** No credit/rates-spread construction clears the SR≥1.5 champion bar in the honest,
costed, causal harness. Closest (2s10s slope MR, SR 1.062, all honesty gates PASS) is below the
charter threshold and is railway-regime-specific (deep-history twin SR 0.118). The BAA-AAA credit
spread remains useful as a REGIME/GATE input, not a standalone sleeve.

## Deliverables
sleeves/RC_t102_d5mr_w21_band50_vt5.csv + .meta; credit_lib.py; test_credit_lib.py;
emit_sleeve.py; credit_engine.py (independent BAA-AAA grid). FINDINGS above.

RES_CREDIT DONE
