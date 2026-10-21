# ITER27 FINDINGS - CENSUS REMAINDER (2026-09-19, session #10)

Pre-commit sealed BEFORE any candidate computation: FINDINGS_PRECOMMIT.md sha16
ccd882e6391f3742. Driver: driver_iter27.py (sha16 27a88caa9732a0d5), log driver_iter27.log,
30 sleeve CSVs under sleeves/.

## Anchors (all PASS pre-candidate)
- Independent gauntlet: verify_champion.py r3 args => ok=true 7/7 (weights_repro 8.327e-17,
  byte_repro 1.032e-16, cost full_dw implied ratio 1.000000000, causality causal, gross
  1.0000000 / n_over 0, 0 neg yrs, MDD -3.6130%). JSON: verify_champion_r3_iter27_start.json.
- Driver: weights maxdev 8.327e-17; bytes maxdev 9.996e-17 (n=4806); grossmax 1.000000000,
  0 days >1.6; incumbent IS-SR 4.198632 exact (asserted <5e-6); 12-pool fit rows 1809.
- Champion sha16 pre == post (8559fa55ee9a3417 / weights d2d11c92a98683df).

## As-sealed result: ADMITTED 0/30 => HONEST NEGATIVE, no reveal (STOP RULE honored)
- 13/29 ETFs earned EXACTLY 0.000 relative weight (eem efa emb ewt fxi hyg iwm jnk lqd shy
  xlb xle xlf) - pure duplicates of existing pool exposure; 13-pool fit == incumbent fit
  (IS-SR 4.1986, Wmax 2.1409x-in-13-units identical). The equity/bond/credit-ETF complex is
  IS-dead as duplicates, exactly the energy-family pattern (WTI 0.000).
- 16/29 earned small weights (0.0007-0.037) and every one LOWERED IS-SR below the 4.198632
  bar (best runner-up tlt 4.1985 / xlk 4.1985, both still below).
- slv_etf ANOMALY (disclosed): earned relw 0.18974 yet 13-pool IS-SR collapsed to 0.4982
  with IS-ann 29.56% - an optimizer-pathology signature (SLSQP returned a return-heavy
  non-Sharpe point under SLV's extreme VT-levered variance), not a real allocation.
  Inadmissible under EITHER normalization (scale-free max share 0.18974 x 12 = 2.2769x >
  2.0); sleeve CSV kept for the record; NOT chased further (stop-rule discipline).
- nokcarry: fit earned it 0.00331; IS-SR 4.1869 < bar AND g8 fit-row shrink 2.21% > 2%
  (USD_NOK calendar gaps) - double-dead, the seliccary analogue confirms #117b's verdict
  family. NOK unit gate PASSED (tail60 4.3412%%/yr vs the 4.25 policy rate; head60 8.8701%%/yr).

## DEFECT DISCLOSED (caught at reveal time, NOT repaired inside this sealed run)
The sealed filter coded Wmax as max_share x 13 <= 2.0. CFX4 has ZERO IS coverage, so the
covered pool is 12 and the campaign-recorded scale-free invariant (#117 convention note;
#117b normalization lesson: max share <= 2/k_covered; a 13-slot denominator overstates by
13/12) is max_share <= 2/12 = 0.166667. Proof of miscalibration: the INCUMBENT's committed
fit (C5ng share 0.16468) violates the x13 filter (2.1409 > 2.0) - a filter the live
champion fails is definitionally wrong. Under the correct invariant EXACTLY ONE candidate
flips: xly_etf (max share 2.0931/13 = 0.16101 <= 1/6; IS-SR 4.2007 > 4.198632; IS-MDD
-2.56%%; 0 neg-yrs; g8 0.00%%). No other row flips (zero-weight rows fail IS-SR by
equality; all other weighted rows fail IS-SR strictly; slv fails Wmax under both).
This is a PRE-COMMIT AUTHORING error (the x13 wording was copied from ITER24_DA), caught
before any reveal fired. Per the #118 -> #119 precedent, the repair is a NEW sealed
iteration (coord/ITER28_CENSUSREMAINDER_FIX) with the corrected filter frozen; the xly
reveal remains a FIRST reveal (no candidate in this set has ever had one). ITER27's own
stop rule is honored to the letter: no reveal fired here, no second run inside ITER27.
