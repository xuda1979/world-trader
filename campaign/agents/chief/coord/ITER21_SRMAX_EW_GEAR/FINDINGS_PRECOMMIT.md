# ITER21 PRE-COMMIT (2026-09-18, coordinator) - written BEFORE any candidate build/reveal

## Operator objective (verbatim, restated 2026-09-18)
> "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return
> can't be smaller than 20%."

Sharpe-max subject to **ann >= 20%** and **gross <= 1.6**. NOTE: the 09-18 ITER20 grid
pinned "gross exactly 1.6" as a FAMILY assumption; the operator's constraint is a CAP.
This iteration releases that pin and adds the gear dimension.

## Two structural facts established from builder source before any reveal
1. rawew13v2_build.py:262-264: `net = port - to*BPS - max(gear-1,0)*RATE/252`. Turnover and
   borrow scale exactly ~ gear; the margin term does not (it is 0 for gear <= 1).
   => net SR(gear) is EXACTLY flat on (0, 1.0] and STRICTLY DECREASING on [1, 1.6].
   SR-max s.t. ann>=20% therefore selects the SMALLEST admissible gear, not 1.6.
   (Consistent with #109: gear 1.705 -> SR FELL 3.2358 -> 3.2084.)
2. rawew13v2_build.py:4 records the pre-ITER15 equal-weight book at SR 3.88 / ann 28.89% /
   MDD -4.25% (OLD 13-sleeve pool) -- already above the incumbent champion's SR 3.4551 at
   the same gear 1.6. The ann-max era moved off it; the SR-max objective points back.

## Pre-committed candidate family (exactly 2 points, no grid trawl)
- **A (primary): EW12v2** - uniform relw = 1/11 on the 11 tradeable v2-pool sleeves
  (10 POOL + diescrack), CFX4 pinned 0 (champion invariant), through the REAL build()
  mechanics (T+1-causal NAV drift, costfix sleeve bytes, FULL |dW| @ 6.4bps, margin
  formula above). Zero fitted parameters - no IS selection of any kind.
- **B (fallback): incumbent ITER20 weight vector** (shrink 0.70 + brwt-cap 0.30, committed
  RAWEW13v2_IS_SR_weights.csv), same mechanics, de-gear.
- Gear: **g = 1.05** for both, PRE-COMMITTED round number (not floor-chasing): meets the
  20% floor with margin, keeps gross 35% under the cap. The full gear curve is reported
  for transparency but g=1.05 is the pre-selected operating point; SR is analytically
  ~flat from g_floor to 1.0, so the choice inside that band does no SR work.

## Admissibility (checked on the delivered book; A has nothing IS-fitted so no IS peeking exists)
1. gross <= 1.6 every day (cap, operator) - expect ~1.05
2. ann (FS, geo, net) >= 20% (floor, operator)
3. 0 negative calendar years (campaign invariant)
4. FS MDD >= -7% wall
5. Wmax <= 2.0x equal (trivial for A: 1.0x)
6. CFX4 weight = 0 exactly
7. OOS (>=2017) dSR vs incumbent positive on the five 2-yr bins

## Selection rule (pre-committed)
Adopt the best-SR admissible point of {A, B} if it beats the incumbent (SR 3.455068,
sha16 766fc0ce9926d793). A 2-point comparison is disclosed as such; A is expected to
dominate on the diversification argument, B is the conservative fallback.

## Anchor requirement (before trusting anything)
A mechanics-exact anchor FIRST: build() with the committed ITER20 vector at gear 1.6 must
reproduce the champion bytes to <1e-12 (the frontier memo's 9.996e-17 pattern).

## Revert path
Incumbent bytes stay byte-exact; any swap archives them as
archive_*_SUPERSEDED_by_ITER21_ewgear105.csv per the ITER20 precedent.
