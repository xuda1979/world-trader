# ITER23 FINDINGS (2026-09-19, coordinator) - HONEST NEGATIVE: the grid edges are invariant
# boundaries, not truncation artifacts. The weight family is CLOSED with its edges explained.

## What was run (per FINDINGS_PRECOMMIT.md, sealed before the reveal)
7 builder-native points extending the ITER20/22 family past both of its unresolved edges,
at canonical gear 1.0 under the pure IS-SR objective:
- Axis A (cap boundary): (shrink 0.70, brwt_cap) in {0.29, 0.28, 0.27, 0.26}
- Axis B (shrink edge):  (shrink_d, cap 0.30) in {0.60, 0.50, 0.40}
Filters {Wmax <= 2.0x equal, IS MDD >= -6%, 0 IS neg yrs}; selection = argmax IS-SR over
admissible points UNION the incumbent. Anchor first: default build() vs champion bytes
9.996e-17 IDENTICAL; incumbent grid point reproduced ITER22's IS-SR 4.1986 exactly.

## Result: ALL 7 extended points are Wmax-INADMISSIBLE; argmax = the INCUMBENT
- Wmax(0.70, 0.29) = 2.0044x -- the cap axis crosses the 2.0x invariant between 0.29 and
  0.30: the incumbent (0.70, 0.30) is the LAST admissible point on that axis.
- Wmax(0.60, 0.30) = 2.0108x -- the shrink axis crosses the invariant immediately below the
  grid edge: shrink 0.70 was a TRUE concentration boundary, not a truncated grid.
- Every extended point passes IS-MDD and 0-IS-neg-yrs and would raise IS-SR (up to 4.2234)
  and FS-SR (up to 3.7751 > incumbent 3.7514) -- the ENTIRE tempting direction is the
  concentration direction, and the Wmax 2.0x invariant forbids all of it. The invariant
  binds; that is its job.

## Frontier statement (objective: SR-max s.t. gross<=1.6, ann>=20%) -- now COMPLETE at
## pre-committed-family resolution
Champion of record stands: ITER21 gear-1.0 book, weights (0.70, 0.30) d2d11c92a98683df,
sha16 8559fa55ee9a3417, ann 23.6054% / SR 3.751429 / MDD -3.6130% / 0 neg yrs.
1. GEAR axis: exhausted (ITER21 cost-structure identity; pinned by test).
2. WEIGHT axis: exhausted AND edge-resolved (ITER22 grid argmax + THIS iteration: both grid
   edges terminate at the Wmax 2.0x invariant, so no admissible extension exists in any
   direction of the builder-native family).
3. POOL: RB_hobr / ITER16-17 candidates OOS-rejected (pinned); EW12v2 dominated; brwt-filter
   screen dominated and fails the floor at gear 1.0.
4. NOT ADMISSIBLE: the OPT_V5..V7 track (fraud family, per ITER22 -- never champion it).
5. What would move SR from here is UNCHANGED and remains operator-decision territory:
   a new admissible DATA axis (real OOS edge), or relaxing a structural invariant
   (Wmax 2.0x -- worth ~+0.02 FS-SR at the very edge, declined here without sanction;
    the 12-sleeve pool pin; gross<1.0 floor farming impossible, ann binds first).
   NOTHING inside the current family. The book sits at the corner of its own constraints,
   and every wall of that corner has now been probed and found to be a rule, not a fence.

## Deviations from the pre-commit: NONE. (No point added, no filter altered, no FS peeking
## in selection -- FS numbers were computed for the record and the OOS police never fired
## because no non-incumbent point was admissible.)

## Deliverables
- driver_2026-09-19.log (this dir): full reveal table + anchors
- campaign/bt/tests/test_iter23_gridedge_closure.py: pins of the computed facts. These are
  reality-pins, not change-drivers, so they land GREEN by construction; their ability to
  FAIL is demonstrated by a mutation run (inverted-Wmax assertion -> RED, recorded below)
  before the file was finalized. No production code was changed in ITER23. Mutation check (recorded): with the Wmax
  threshold mutated 2.0 -> 2.05 the boundary test goes RED (cap-0.29 point sits at
  2.0044x, proving the pin resolves the crossing); reverted, 7/7 GREEN. New suite total:
  489 baseline + 7 ITER23 pins.
- campaign/GOAL100_ITER23_GRIDEDGE.md: operator-facing decision memo
