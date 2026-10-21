# ITER28 FINDINGS - CENSUS REMAINDER, FILTER-REPAIR REVEAL (2026-09-19, session #10)

Pre-commit sealed BEFORE the run: FINDINGS_PRECOMMIT.md sha16 9c1f22cba582364a. Driver
driver_iter28.py sha16 f4d79d28f0f0934b (generated from driver_iter27.py by targeted
replacements ONLY: OUT dir, filter normalization x13 -> x k_covered, k plumbing, log
names - everything else byte-verbatim), log driver_iter28.log.

## Anchors (all PASS)
weights maxdev 8.327e-17; bytes maxdev 9.996e-17 (n=4806); grossmax 1.000000000, 0 days
>1.6; incumbent IS-SR 4.198632 exact (asserted); 12-pool fit rows 1809, k_covered=11
(CFX4 zero IS coverage - matches #119's "really an 11-name fit"). Champion sha16
pre == post: 8559fa55ee9a3417 / d2d11c92a98683df. NOK unit gate PASS (tail60 4.3412%/yr
vs the 4.25 policy rate; head60 8.8701%/yr); nokcarry joint tr n=6961 (1999-01-04..2026-09-07).

## Corrected-filter table: ADMITTED 2/30
- xly_etf: REAL admission - earned relw 0.02806 (2.806%), IS-SR 4.200683 > 4.198632
  (+0.0021), IS-MDD -2.56%, 0 neg-yrs, g8 0.00%, Wmax_sf 1.9321x.
- xlf_etf: JITTER ADMISSION (disclosed, immaterial) - earned relw EXACTLY 0.000000;
  standalone recompute shows its 13-pool fit-objective SR equals the incumbent's to
  -4.2e-14. Its i_sr lands a hair above the bar purely from 13th-column solver/book
  arithmetic (zero-weight rows all print 4.1986; xlf's trajectory landed above,
  eem/efa/etc below). Lost the argmax to xly by 0.002 - orders of magnitude beyond
  jitter - so the reveal choice was unaffected. LESSON for future pre-commits: the
  admission test needs a jitter tolerance (e.g. require |relw[S]| > 1e-4 OR
  IS-SR - bar > 1e-4) so zero-weight rows cannot slip through on solver noise.
- All 28 others: 13 exact duplicates (relw 0.000, fit == incumbent), 14 IS-SR-lowering
  with small weights, slv optimizer-anomaly (relw 0.18974 yet book IS-SR 0.4982 /
  ann 29.56% - SLSQP returned a return-heavy non-Sharpe point under SLV's extreme
  VT-levered variance; inadmissible under BOTH normalizations, Wmax_sf 2.2769x),
  nokcarry double-dead (IS-SR 4.1869 < bar AND g8 2.21% > 2% from USD_NOK calendar gaps).

## GLOBAL ARGMAX -> SINGLE REVEAL: xly_etf (consumer-discretionary sector trend, price-only)
Book: 13-pool + xly_etf at gear 1.0, n=4813 (2008-03-31..2026-09-09; the ETF feed ends
09-09 vs the champion's 08-28). FS SR **3.750133 < 3.751429** (-0.001296); ann arith
21.2905% / cagr 23.5197%; MDD -3.5674%; 0 neg yrs; grossmax 1.000000000; Wmax 1.9321x;
CFX4 relw 0.0.
Gates: G1 ann>=20% PASS, G2 gross<=1.6 PASS, G3 MDD>=-7% PASS, G4 0 neg yrs PASS,
G5 CFX4=0 PASS, G6 Wmax<=2.0x PASS, **G7 OOS police FAIL** - bins
+0.0187 / -0.0095 / -0.0075 / +0.0183 / -0.0323 = 2/5 positive (<4 required), min bin
-0.0323 (>= -0.10 ok), FS SR below incumbent (fails third arm). Two of three G7 arms fail.
**VERDICT: REJECT per sealed stop rule - ITER17 law kill #5** (after bund #117, seliccary
#117b, credit #119; the +0.0021 IS gain inverts to -0.0013 OOS). Champion byte-stable.

## STRATEGIC CONSEQUENCE - the census remainder is MEASURED-CLOSED; zero silent cells remain
Every IS-FITTABLE line of DATA_AXIS_CENSUS_2026-09-19.txt now has a recorded verdict:
- bund_daily 8: admitted on IS, OOS-rejected at the single reveal (#117);
- em_rates 6: IS-dead (0/6); cad 4: superseded by the argmax stop rule (#117);
- eia energy 10: IS-dead (0/10); cboe vol complex: excluded, not capital-real, no VIX
  futures on disk (ITER24 recorded);
- seliccary: OOS-dead 3/5 (#117b);
- cboe non-vol ETF complex 29: 13 pure duplicates (relw exactly 0), 14 lower IS-SR with
  small weights, slv inadmissible anomaly, xlf jitter (relw 0), **xly IS-alive ->
  OOS-DEAD (this reveal)**;
- nokcarry: double-dead (IS-SR + g8).
The data axis closure is now COMPLETE WITH MEASUREMENTS over the whole screened universe.
Frontier statement unchanged in substance, now airtight: gear (ITER21), weights (ITER22),
grid edges (ITER23), census data (ITER24/#117b/ITER27/ITER28), 8c-era ledger (ITER25),
invariant-legal credit (ITER26) - ALL closed. Remaining levers = purchased data (e.g.
total-return ETF series, VIX futures, regional basis) or operator rule change - both
evidence-contradicted on their best axes (Wmax-relax data-dead for credit #119; the
grid-edge +0.024 FS-SR measurement remains informational only, #116).

## Convention corrections landed by this pair of iterations
1. Wmax filters in any future driver MUST use max_share x k_covered (the fit's own
   have-count), never x 13 - the ITER24_DA x13 form is miscalibrated (the incumbent's
   own committed fit violates it).
2. Admission tests need a jitter tolerance so zero-weight candidates cannot be admitted
   on solver noise (xlf).
