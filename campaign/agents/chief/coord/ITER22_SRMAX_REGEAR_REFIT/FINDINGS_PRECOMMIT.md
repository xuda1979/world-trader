# ITER22 PRE-COMMIT (2026-09-19, coordinator) - written BEFORE any gear-1.0 grid reveal

## Operator objective (verbatim, unchanged)
> "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return
> can't be smaller than 20%."

## The open lever: the ITER20 grid selection was solved under the WRONG (geared) objective
ITER20 selected (shrink 0.70, cap 0.30) as argmax IS-SR **at gear 1.6**. For any weight
vector w, the geared book is net_1.6 = 1.6*u(w) - c with u = raw - turnover-cost and the
CONSTANT c = 0.6*RATE/252, so

    SR_1.6(w) = SR_u(w) - k / sigma_u(w),   k = c/1.6 = 6.696e-5/day  (annualized ~ -0.30 SR)

The -k/sigma term is a HANDICAP BONUS FOR HIGH-VOL books (a fixed drag diluted by vol).
The canonical gear is now 1.0, where net_1.0 = u(w) exactly (gross-1 = 0 -> no margin) and
SR is scale-invariant below 1.0. The correct selection objective at the operating point is
PURE SR_u(w). ITER20's pick may therefore sit off the true SR-argmax of its own family by
up to ~0.1 annual-SR across the grid's sigma spread. ITER22 re-solves the IDENTICAL grid
under the corrected objective. This is a re-derivation, not a new family.

## Grid (IDENTICAL to ITER20's pre-committed family, GOAL100_ITER20_SRMAX_FRONTIER.md)
- relw = apply_brwt_cap(fit_relw(IS, shrink_d), cap): shrink_d in {0.98, 0.85, 0.70} x
  brwt_cap in {0.45, 0.40, 0.35, 0.30, 0.25}. 15 points. Builder-native knobs only.
- The s in {0, 0.25} arm is DROPPED, disclosed: at ITER20 every s=0.25 point violated the
  Wmax <= 2.0x-equal invariant by construction (2.6x), and Wmax is gear-invariant (it is a
  property of relw, not of gear), so those points are inadmissible at ANY gear. No
  admissible point is lost by the drop.
- cap=None (no cap) is NOT added: not in the pre-committed SR-max family (it is the retired
  ann-max vintage's config). Not extending the grid is the anti-overfit discipline.

## IS-selection filters (IS-computable, per point)
1. Wmax (max relw share vs 1/12 equal) <= 2.0x
2. IS MDD >= -6% (the historical family bound, evaluated at gear 1.0)
3. 0 IS negative years

NOTE the IS-ann>=20% filter from ITER20 is DROPPED, disclosed: at gear 1.0 even the
INCUMBENT champion has IS ann 19.7493% (ITER21 adoption caveat #4); the operator's floor
is a FULL-SAMPLE statement about the delivered book and moves to the adoption gates.

## Selection rule (pre-committed)
argmax IS-SR over grid points passing the filters, evaluated on the gear-1.0 net series
(the pure objective). Tie-break: higher IS ann. If the argmax is the incumbent vector
(0.70, 0.30), the weight lever is EXHAUSTED at this objective and NO adoption happens -
the honest frontier statement is the deliverable.

## Delivered operating gear (pre-committed)
g = 1.0 if FS ann @1.0 >= 20%, else the smallest 2dp g > 1.0 whose FS ann >= 20%
(floor-driven only; SR above 1.0 strictly falls, so the floor is paid for, never chased).

## Adoption gates on the delivered book (ALL must pass)
1. FS ann >= 20% (operator floor); 2. gross <= 1.6 every day; 3. FS MDD >= -7% wall;
4. 0 FS negative years; 5. CFX4 weight = 0 exactly; 6. Wmax <= 2.0x; 7. OOS reveal: dSR vs
the incumbent champion on the five 2017+ 2-yr bins >= 4/5 positive AND no bin < -0.10 AND
FS SR > incumbent 3.751429. (Stricter than ITER20's 3/5: this candidate differs from the
incumbent only by a small objective correction, so a marginal win must not clear adoption.)

## Anchor requirement
ANCHOR-1.0 already established today (driver_anchored_2026-09-19.log): default build() vs
champion bytes maxdev 1.023e-16 IDENTICAL, gross 1.0 exact; ANCHOR-1.6 vs archived ITER20
vintage 1.110e-16. Numbers are trusted only on top of these.

## Revert path
Champion bytes untouched during selection. Any adoption archives the incumbent byte-exact
per precedent and requires the full re-pin wave + suite green before the swap is declared.
