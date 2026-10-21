# G2_creditetf — FINDINGS (self-executed by coordinator; GLM 429 prevented sub-agent)

## Result: A5r7 AND A1credit are PAPER sleeves — their edge is NOT tradeable.
- Rebuilt A1credit (BAA credit-regime momentum) on REAL credit ETFs from twelvedata:
  LQD (IG) SR -0.16, HYG (HY) SR -0.19 (vs 0.92 on synthetic FRED BAA total-return).
- Rebuilt A5r7 (credit composite) on real LQD/HYG 63d-momentum: SR -0.28 to -0.61 (vs 1.37 synth).
- Root cause: corr(real LQD returns, synthetic BAA-synth TR) = **0.029**. The synthetic
  -7*d(y)/100 + y/252 bond approximation does NOT track the real IG-bond ETF price path
  (yield-index vs ETF total-return differ in roll, carry convention, index selection).
- Instrument reality check of synthetic-bond legs elsewhere:
  - Synth us10y TR vs real IEF (7-10y) = **corr 0.955**  -> FAITHFUL (rates OK)
  - Synth 2y TR vs real IEF = corr 0.721          -> rates OK
  - Synth BAA TR vs real LQD/HYG = **corr 0.03**   -> UNFAITHFUL (credit = paper)

## DECISION
- EXCLUDE A5r7 and A1credit from the strict champion (paper credit edge).
- KEEP a6r7, QAxasts (rates/macro with faithful synthetic bond legs, corr 0.72-0.96)
  and all other instrument-real sleeves.
- Strict tradeable champion (12 sleeves): 49-53% ann, SR 5.24, DD ~-6%, 0/19 neg years,
  OOS 56-60% (GOAL100_STRICTTRADE_BALANCED_daily.csv).

ROUND DONE
