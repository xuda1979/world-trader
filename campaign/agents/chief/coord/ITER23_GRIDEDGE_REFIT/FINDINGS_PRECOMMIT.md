# ITER23 PRE-COMMIT (2026-09-19, coordinator) - written BEFORE any extended-grid reveal

## Operator objective (verbatim, unchanged since 2026-09-18; re-sent 2026-09-19 00:30)
> "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return
> can't be smaller than 20%."

## Why extend a grid ITER22 explicitly declined to extend
ITER22 re-solved the ITER20 family under the corrected gear-1.0 objective and chose NOT to
extend it ("Not extending the grid is the anti-overfit discipline"). Two structural facts,
both visible in ITER22's OWN disclosed table, make one bounded extension an honest
completeness check rather than a fishing trip:

1. SHRINK EDGE: the IS-SR argmax sits at the shrink axis's lowest evaluated value
   (0.70 of {0.98, 0.85, 0.70}). An argmax on a grid EDGE is a truncation signal: the
   family's true argmax may lie beyond the evaluated set. Until that direction is resolved,
   the "weight axis exhausted" claim is technically unsupported.
2. CAP BOUNDARY: the brwt-cap axis's admissible edge is unresolved. (0.70, 0.30) carries
   Wmax 1.9762x -- strictly INSIDE the 2.0x invariant -- while (0.70, 0.25) is
   Wmax-inadmissible at 2.1173x. The Wmax == 2.0x crossing lies somewhere in cap
   (0.25, 0.30) and was never evaluated; admissible points may exist between the two.

DISCLOSED knowledge leak (transparency over purity): ITER22's table shows FS-SR RISING
toward the tight-cap / inadmissible corner ((0.85, 0.25) 3.7740 and (0.70, 0.25) 3.7769,
both > incumbent 3.751429). We therefore EXPECT the extended points to look attractive on
full-sample SR. The defenses are structural, not hopeful:
- Selection is IS-SR ONLY (the pure gear-1.0 objective ITER22 corrected) -- never FS;
- Adoption gates are ITER22's verbatim, including the STRICT OOS police (dSR >= 4/5 bins
  positive, no bin < -0.10, FS SR > incumbent);
- ITER22 already documented that "FS rank INVERTS IS rank at the tight-cap end -- selecting
  on FS there is IS-noise mining". If the extended argmax wins on IS and then fails the OOS
  police, that is the documented IS-noise signature and the deliverable is the honest
  negative that CLOSES the edge question.

## Extended grid (7 builder-native points, frozen)
- Axis A (cap boundary resolution), shrink 0.70 fixed: brwt_cap in {0.29, 0.28, 0.27, 0.26}.
- Axis B (shrink edge completeness), cap 0.30 fixed: shrink_d in {0.60, 0.50, 0.40}.
No other points. No cap=None (retired ann-max config, out of family). No s-arm (dropped in
ITER22: Wmax-inadmissible at any gear). Builder-native knobs only: relw =
apply_brwt_cap(fit_relw(IS, shrink_d), cap), gear 1.0, canonical mechanics untouched.

## Anchor requirement (established THIS session, before any candidate)
default build() --verify vs champion of record: maxdev 9.996e-17 IDENTICAL, gross 1.0 exact,
sha16 8559fa55ee9a3417; weights d2d11c92a98683df. Cross-check: the incumbent grid point
(0.70, 0.30) must reproduce ITER22's IS-SR 4.1986 (definitional continuity with ITER22).

## IS-selection filters (identical to ITER22, IS-computable)
1. Wmax (max relw share vs 1/12 equal) <= 2.0x
2. IS MDD >= -6% at gear 1.0
3. 0 IS negative years

## Selection rule (frozen)
argmax IS-SR at gear 1.0 over {7 extended points} UNION {incumbent (0.70, 0.30)};
tie-break higher IS ann. If the argmax is the incumbent, NO adoption -- the deliverable is
the closed-frontier statement with the shrink edge and cap boundary resolved.

## Adoption gates on the delivered book (ITER22's verbatim, ALL must pass)
1. FS ann >= 20% (operator floor); 2. gross <= 1.6 every day; 3. FS MDD >= -7% wall;
4. 0 FS negative years; 5. CFX4 weight = 0 exactly; 6. Wmax <= 2.0x; 7. OOS police vs the
incumbent champion: dSR on the five 2017+ 2-yr bins >= 4/5 positive AND no bin < -0.10 AND
FS SR > 3.751429. Delivered gear: g = 1.0 (SR strictly falls above 1.0; the floor is met
there and is never chased with gear).

## Revert path
Champion bytes untouched during selection (--emit-candidate only). Any adoption archives the
incumbent byte-exact per precedent, runs the full re-pin wave + suite green (including new
pins) BEFORE the swap is declared.
