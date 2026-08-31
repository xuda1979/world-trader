# C2 Round-2: extend the proven fly/spread reversion family (HIGH PRIORITY — this family WORKS)

Round-1 lesson: UST fly z-reversion SR 1.85 works (audited, calendar-scramble p=0.049).
Extend WITHIN family with different markets/terms, not re-tuning the same two flies:

1. Individual flies as SEPARATE sleeves (A and B separately, not just the pair): save each if
   gates pass solo (likely A yes; B weaker). More decorrelated components = better blend.
2. 2s10s + 5s30s STEEPENERS as separate z-reversion sleeves (2-leg, not 3-leg).
3. Fly with TIPS leg: 10y TIPS-vs-nominal (DFII10 vs DGS10) real-yield fly? 10y breakeven
   (T10YIE) z-reversion as its own sleeve; 5y (T5YIE) second.
4. International curve flies using DGS-equivalent? (intl 10y series are MONTHLY — verify;
   if monthly-only, document and skip).
5. bill-area flies: 1MO-3MO-6MO spread reversion (2001+ window honest caveat).
6. Extreme z: asymmetric entries (|z|>2 entry, |z|<0.5 exit) with hold-until-exit — lower
   turnover variant; does it raise net SR after costs?

Deliver 2-4 more sleeves (C2_flyA_*, C2_flyB_*, C2_steep_*, C2_be_*, ...). All gates + decorrelation
vs blend AND vs C2_fly2AB_75 (want corr<0.5 between sibling flies, else merge). Log in FINDINGS_2.
Last line: ROUND 2 DONE
