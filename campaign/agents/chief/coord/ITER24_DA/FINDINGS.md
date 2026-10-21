# ITER24 FINDINGS (2026-09-19, coordinator) -- HONEST NEGATIVE: the census data axis
# fails at OOS. The ITER17 law ("IS-only gains die at OOS") reproduces on the data axis.
# Champion of record UNCHANGED: ITER21 gear-1.0, sha16 8559fa55ee9a3417,
# weights d2d11c92a98683df, ann 23.6054% (CAGR) / SR 3.751429 / MDD -3.6130% / 0 neg yrs.

## What was run (per FINDINGS_PRECOMMIT.md, sealed BEFORE this session's first computation)
28 frozen candidate sleeves (census IS-fittable n capital-real expressible) added one at a
time to the champion 12-sleeve pool; relw = apply_brwt_cap(fit_relw(IS 2008-03-31..<2017-01-01,
shrink 0.70), cap 0.30) on each 13-name frame; ITER23's verbatim IS filters {Wmax <= 2x equal
(= 2/13 share), IS-MDD >= -6%, 0 IS neg yrs}; admission additionally requires IS-SR > 4.1986.
House sleeve recipe = a6_r7 mechanics (378-obs trend, 42-obs cadence freeze, T+1, vol-target
12% cap 5x) with the two pre-committed deviations (6.4bps FULL |dW|; flat cost across
families). ONE global IS-argmax revealed; OOS police ran exactly once.

## Anchors (all BEFORE any candidate, this session)
build() --verify 9.996e-17 IDENTICAL / weights 8.327e-17 IDENTICAL / gross 1.0 exact /
incumbent IS-SR 4.198632 reproduces ITER22/23's 4.1986 (definitional continuity).
Champion sha16 pre-run = post-run = 8559fa55ee9a3417 (bytes never written).

## Result: 11/28 admitted (F1 bund 8/8, F3 cad 3/4); argmax bund_02y FAILS the OOS police
- F1 bund_daily: ALL EIGHT tenors admitted. IS-SR 4.2120..4.2729 (argmax bund_02y,
  relw 9.93%). The pool fit WANTS the EU-rates trend sleeve on the IS window.
- F3 dm_rates: cad 2y/3y/5y admitted (best IS-SR 4.2678); cad 10y not (Wmax 2.0354x).
- F2 em_rates FX: 0/6 -- every candidate has IS-SR <= incumbent AND drives Wmax past 2.0x.
  The fit never wants EM-FX trend on the IS window.
- F5 eia energy spots: 0/10 -- same double rejection; WTI and propane earn exactly 0.0
  weight (the pool already holds brwt* spread + diescrack crack sleeves from this data).
- F4 cboe vol complex: excluded pre-reveal (index levels, not capital-real; recorded in the
  pre-commit, unchanged).

REVEAL (bund_02y 13-pool book, gear 1.0, n=4806): FS SR 3.728158 < incumbent 3.751429;
ann CAGR 23.2440% (arith 21.0652%); MDD -3.3107%; 0 neg years; gross 1.0 exact;
Wmax 1.8001x; CFX4 = 0 exactly. OOS dSR vs incumbent: 2017-18 -0.0257, 2019-20 -0.0939,
2021-22 +0.0210, 2023-24 +0.1381, 2025-26 -0.0529 -> 2/5 positive, FS SR below incumbent.
GATE 7 FAIL -> REJECT. Per the sealed stop rule: no second reveal; iteration closed.

## Reading
1. The bund family's IS gain (+0.074 IS-SR) INVERTS to an OOS loss (-0.023 FS-SR): the ECB
   secular easing trend carried the IS window; the 2022 bund repricing and post-2022 chop
   erase it. This is the ITER17 law reproduced to the letter on a new data axis.
2. Cad 2y was nearly identical (IS-SR 4.2678) -- same rates-trend signal family, same fate
   would be expected; per the stop rule it was NOT revealed, and the IS tables are recorded
   for the audit trail instead.
3. The EM-FX and energy rejections are IS-level: no OOS question was ever reached. The
   double rejection (no IS edge AND Wmax-inadmissible) makes these families dead at the
   screen, not at the gate.
4. Frontier statement after ITER24: gear/weight/grid-edge closed (ITER21-23); the census
   data axis is now ALSO tested and closed at the first-family resolution its screen
   supported (bund admitted, failed OOS; em/dm partial; vol/energy not expressible or
   IS-dead). The champion remains the corner of its constraints. What would move SR from
   here remains: (a) an operator invariant relaxation (declined without sanction), or
   (b) genuinely NEW data (bought regional basis / VIX futures / EM local-curve composites)
   outside this census -- each a purchase/mandate decision, not an iteration.

## Deviations from the pre-commit: NONE.
Informational convention notes (no filter depends on either):
- The driver's IS-ann column is arithmetic annualization (incumbent 18.12%); ITER23's table
  printed 19.7493% under its own convention. IS-ann is not a filter in either iteration.
- Wmax is reported as max_share x k (k = pool size): the incumbent's 1.9762x at k=12 reads
  2.1409x at k=13 on the SAME share vector -- the invariant "max share <= 2x equal" is
  scale-free; the filter used 2/13 for 13-name pools, correctly.

## Deliverables
- driver_2026-09-19.py + driver_2026-09-19.log (this dir): full run; log = the audit trail.
- sleeves/*.csv: the 28 candidate sleeve series (reproducible inputs).
- candidate_bund_02y_daily.csv + candidate_bund_02y_weights.csv: the revealed book (NOT a
  champion; emitted for the record only).
- campaign/bt/tests/test_iter24_data_axis.py: reality-pins (champion sha, argmax OOS failure,
  EM/energy zero-admission on the IS table facts) with a recorded mutation check.
- campaign/GOAL100_ITER24_DATAAXIS.md: operator-facing decision memo.

## Mutation check (recorded, post-FINDINGS)
test_iter24_argmax_book_fails_oos_police mutated (FS-SR assertion inverted) -> RED
("assert 3.7281584939437584 > 3.751428690289051" fails as expected); restored byte-identical
-> 3/3 GREEN. Full suite after landing: 499 passed (496 + 3), 0 failed.
