# ITER22 FINDINGS (2026-09-19, coordinator) - HONEST NEGATIVE: the weight lever is exhausted

## What was run (per FINDINGS_PRECOMMIT.md, sealed before the reveal)
The full ITER20 grid re-solved under the corrected gear-1.0 objective (pure IS-SR; the
gear-1.6 selection carried a -k/sigma high-vol handicap bonus, k = 6.696e-5/day):
15 builder-native points, shrink_d {0.98,0.85,0.70} x brwt_cap {0.45..0.25}, filters
{Wmax<=2.0x, IS-MDD>=-6%, 0 IS neg yrs}, selection = argmax IS-SR @ gear 1.0.

## Result
- **Argmax = (shrink 0.70, cap 0.30), IS-SR 4.1986 = the INCUMBENT vector.** No adoption.
  The gear-1.6 selection is objective-robust: the -k/sigma bias did not change the pick.
- Full admissible ordering (IS-SR desc): (0.70,0.30) 4.1986 > (0.98,0.25) 4.1920 >
  (0.85,0.30) 4.1828 > (0.98,0.30) 4.1652 > (0.70,0.35) 4.1325 > ... > (0.98,0.45) 3.9206.
- The two Wmax-inadmissible neighbours (0.85,0.25) 2.0587x and (0.70,0.25) 2.1173x show
  the highest FS-SR (3.7740/3.7769): the FS frontier keeps rising exactly where the
  concentration invariant cuts it off. The invariant binds; that is its job.
- Plateau shape (ITER20 caveat #2 reproduced at gear 1.0): admissible FS-SR spans
  3.55-3.77 and FS rank INVERTS IS rank at the tight-cap end - selecting on FS there is
  IS-noise mining, which the pre-commit forbade.

## Frontier statement (objective: SR-max s.t. gross<=1.6, ann>=20%)
Champion of record stands: ITER21 gear-1.0 book, weights (0.70, 0.30) d2d11c92a98683df,
sha16 8559fa55ee9a3417, ann 23.6054% / SR 3.751429 / MDD -3.6130% / 0 neg yrs.
1. GEAR axis: exhausted (margin-drag identity: SR flat on (0,1], strictly falling above;
   g=1.0 is the argmax-ann point of the flat set; pinned by test).
2. WEIGHT axis (pre-committed family): exhausted (this iteration - argmax = incumbent
   under the corrected objective).
3. POOL: RB_hobr and the ITER16/17 candidates remain OOS-rejected (pinned, now including
   the OOS-SR arm under the SR-max objective); EW12v2 dominated (3.6665 < 3.7514); the
   brwt-filter screen dominated AND fails the floor at 1.0 (SR 3.730, ann 19.44%).
4. NOT ADMISSIBLE: the concurrent OPT_V* track (campaign/work_backtest_oos/OPT_V5..V7,
   "SR 6-6.7") - full-period weight fit by its own champion card (its "OOS" is decorative),
   pre-costfix sleeve bytes in the book (diescrack__prefix/QAxasts__prefix = the archived
   UNDERCHARGED-cost vintage), no canonical mechanics (T+1 NAV drift / FULL |dW| 6.4bp /
   margin), and V7's own full_ann 18.75% is below the 20% floor. Classic proxy-screen
   artifact family per the ITER17 law; must never be championed.

## What would genuinely move SR from here (operator-decision territory)
- A new admissible DATA axis (new sleeve with real OOS edge) - the R8 hunts all rejected;
- Operator sanction to relax a structural invariant (Wmax 2.0x / the 12-sleeve pool pin /
  gross<1.0 floor farming is impossible - ann binds first), each of which is a rule change,
  not an improvement;
- NOTHING inside the current family. The book sits at the corner of its own constraints.
