# ITER24 PRE-COMMIT -- DATA-AXIS SLEEVE-ADD (2026-09-19, coordinator)
Written BEFORE any candidate sleeve is built, any extended pool is fitted, or any OOS
number is computed in this session.

PROVENANCE DISCLOSURE: a prior session (2026-09-19 ~01:17-01:27 CST) recorded in its log
that it sealed an ITER24 pre-commit ("coord/ITER24_DA/FINDINGS_PRECOMMIT.md with Amendment 1")
and that a driver write was pending. NO such file exists anywhere on disk (verified by find
over the repo) -- those writes never landed. This file is therefore the ONLY ITER24
pre-registration, sealed fresh before this session's first computation. Its stop-rule
semantics are defined HERE (see "single reveal"), not reconstructed from the lost session.

## Operator objective (verbatim, unchanged since 2026-09-18; re-sent 2026-09-19 00:30)
> "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return
> can't be smaller than 20%."

## Why this axis is open
ITER23 closed the gear/weight/grid-edge axes and named the remaining admissible direction:
"a new admissible DATA axis (real OOS edge)". The census
(../ITER23_GRIDEDGE_REFIT/DATA_AXIS_CENSUS_2026-09-19.txt) screened 405 unwired series on
the CFX4 criterion (IS-fittable = >500 rows in IS window AND start <= 2008-03-31) and
charted a shortlist. This iteration is the BOUNDED test of that census: the frozen
candidate set below, ONE global selection, ONE reveal. Champion of record throughout:
ITER21 gear-1.0 book, sha16 8559fa55ee9a3417, weights d2d11c92a98683df (shrink 0.70 +
brwt-cap 0.30), ann 23.6054% / SR 3.751429 / MDD -3.6130% / 0 neg yrs / gross 1.0 exact.

## Anchors established BEFORE this file was sealed (this session)
- `python3 campaign/scripts/rawew13v2_build.py --verify`: max|new-old| = 9.996e-17
  IDENTICAL; weights max dev 8.327e-17 IDENTICAL; gross mean/max 1.000000, 0 days > 1.6;
  turnover 4.0308 bp/yr. The incumbent anchor is intact.
- Incumbent definitional stats (ITER23 log): IS-SR 4.1986, IS-ann 19.7493%, IS-MDD -2.5583%,
  0/9 IS neg years. NOTE: the incumbent's own IS-ann is < 20%, so the ITER20-era
  "IS ann >= 20%" filter is NOT in the frozen filter set (it would reject the incumbent);
  the operator 20% floor applies to the FULL-SAMPLE book at the adoption gates, as in
  ITER22/23. The driver must REPRODUCE IS-SR 4.1986 on the incumbent before any candidate
  is fitted (definitional continuity, same as ITER23).

## Frozen candidate set (census IS-fittable ∩ capital-real expressible) -- 28 sleeves
Family order (census charted order; F5 disclosed as an extension OUTSIDE the charted
4-family shortlist, ordered last = lowest prior):
- F1 bund_daily (EU curve, no European-rates family in pool): bund_{02y,03y,05y,07y,10y,15y,20y,30y} -- 8
- F2 em_rates FX pairs (batch-8 verified data; distinct from the dead twelvedata CFX4 feed):
  brazil_usdbrl, czech_eurczk, czech_usdczk, peru_usdpen, poland_eurpln, poland_usdpln -- 6
- F3 dm_rates: cad_govt_{2y,3y,5y,10y} -- 4
- F4 cboe vol complex: ZERO candidates -- EXCLUDED PRE-REVEAL on expressibility: the census
  files are index LEVELS (VIX/VIX6M/VVIX/GVZ/OVX close); no VIX-futures/ETP data exists on
  disk, so a sleeve on vol-index changes is not a capital-real instrument under
  TRADE_RECORD_STANDARD. (In-pool A5r2 already covers the contango corner partially.)
- F5 eia_weekly energy spots: wti_spot_daily, brent_spot_daily, natgas_HH_spot_daily,
  propane_mb_spot_daily, gasoline_{gulf,la,nyh}_spot_daily, jet_gulf_spot_daily,
  ulsd_{gulf,nyh}_spot_daily -- 10

NOT built (frozen, with reasons): brazil_selic + nok_policy_rate (single-leg policy-rate
streams are not USD capital-real without an FX/financing composite -- that recipe is outside
the frozen scope); cad_govt_long (ambiguous duration mapping); every partial-IS /
recent-only census row (<500 IS rows -- the CFX4 lesson). NO candidate may be added, no
series re-cut, no recipe re-chosen after the first fit runs.

## Frozen sleeve recipe (house recipe = scripts/a6_r7_bond2y_trend.py mechanics, verbatim,
## with TWO disclosed deviations)
- Rates series (yields in PERCENT -> /100 decimal): TR = -DUR*dy + y/252 (par-bond approx
  incl carry). DUR = 0.95 x tenor-years (a6r7 anchor 2y -> 1.9): 3y->2.85, 5y->4.75, 7y->6.65,
  10y->9.5, 15y->14.25, 20y->19.0, 30y->28.5.
- FX / spot-price series: TR = series.pct_change() (daily return; the trend rule decides
  direction -- no manual sign choice anywhere).
- Signal: LONG when trailing K=378-obs mean TR > 0, else FLAT.
- Cadence freeze: decisions every CAD=42 obs (iloc::CAD, reindex, ffill).
- T+1: gross = W.shift(1)*TR; turnover = |W.shift(1)-W.shift(2)|.
- Cost: 6.4 bps one-side on FULL |dW| -- DEVIATION 1 (a6r7 used 6.0);
  TRADE_RECORD_STANDARD 6.4 governs new sleeves; deliberately conservative vs real
  futures/FX costs.
- Vol target: 12% ann, expanding(min 60d) std .shift(1), cap 5x -- sleeve-internal leverage
  lives INSIDE the sleeve net series per house convention (same as in-pool a6r7); the
  BOOK's gross stays gear = 1.0 exact.
- Sleeve eval start 2007-01-01 (a6r7 verbatim); pool alignment at 2008-03-31.
- DEVIATION 2 (disclosure, not a knob): cost is charged FLAT 6.4bp across families (no
  per-instrument pricing: EM-FX spreads and energy basis are not re-priced from meta prose
  per campaign rule; 6.4 is the standard and conservative for listed futures/FX).

## Frozen test protocol per candidate S (28 total; pool fit is the selector -- CFX4 lesson)
Pool13 = champion 12 NAMES + S (CFX4 stays in the pool, pinned 0 by the brwt-cap transform).
relw = apply_brwt_cap(fit_relw(IS window 2008-03-31..<2017-01-01, shrink 0.70), cap 0.30)
on the 13-name frame, with the builder's exact fit (3 multi-starts, two-stage W_MAX/k cap).
IS filters (ITER23's verbatim set, all must hold):
  i.   Wmax = max(relw)/(1/13) <= 2.0x
  ii.  IS MDD >= -6% at gear 1.0
  iii. 0 IS negative years
Family admission: S is ADMITTED iff the filters hold on the 13-pool book AND
IS-SR(13-pool) > 4.1986 (the incumbent's IS-SR; requires relw[S] > 0 -- a zero-weight S
returns the incumbent book exactly, since full-coverage S changes no inner join).
Report for EVERY candidate regardless of outcome: relw[S], IS-SR, IS-ann, IS-MDD,
IS neg yrs, Wmax, admitted Y/N. No candidate is ever dropped from the report table.

## Selection and the SINGLE REVEAL (stop rule, frozen)
Selection is IS-ONLY over ALL admitted candidates: global argmax = highest IS-SR
(tie-break: higher relw[S], then lexical sleeve name). Exactly ONE candidate ever reaches
OOS. If NO candidate is admitted: honest negative, iteration closes, no reveal, no FS
number printed for any candidate beyond the IS table. If the revealed argmax fails ANY
adoption gate below: the iteration closes as an honest negative -- the second-best
candidate is NOT revealed, no gate is revisited, no later family is promoted. Total OOS
policing events for the whole iteration: exactly 1.

## Adoption gates on the revealed 13-pool book at gear 1.0 (ITER22/23 verbatim, ALL must pass)
1. FS ann >= 20% (operator floor); 2. gross <= 1.6 every day; 3. FS MDD >= -7% wall;
4. 0 FS negative years; 5. CFX4 weight = 0 exactly; 6. Wmax <= 2.0x; 7. OOS police vs the
incumbent champion: dSR on the five 2017+ 2-yr bins >= 4/5 positive AND no bin < -0.10
AND FS SR > 3.751429.

## Revert path
Champion bytes are NEVER written during selection (candidates emitted to the ITER24_DA dir
or stdout only). Any adoption: archive the incumbent byte-exact first (precedent), land the
full re-pin wave + suite green (including new pins) BEFORE the swap is declared, then update
CHAMPION docs + memory. No adoption: incumbent bytes untouched, FINDINGS.md records the
honest negative with the full 28-row IS table.

## Disclosed priors (no-peeking defense, stated before the reveal)
- ITER17 law: IS-only gains die at OOS (RB_hobr OOS -1.39pp). Prior expectation: MOST or ALL
  of the 28 are IS-rejected or OOS-rejected; the deliverable either way is the frontier
  statement for the census families.
- Within-family correlation is high (bund tenors ~+0.8; the 3 gasoline/ULSD spots are
  near-duplicates); the fit concentrates within family and the Wmax cap may bind -- recorded,
  not tuned around.
- Poland series end 2025-12-31 and bund ends 2026-08-03: those candidates carry dead-weight
  allocation to sample end under the pool's fillna(0) arithmetic -- an honest OOS handicap,
  no special-casing.
