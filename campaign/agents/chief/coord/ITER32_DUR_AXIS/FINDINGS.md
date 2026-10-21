# ITER32 FINDINGS - DUR-AXIS (signal-parameter) SWEEP - HONEST NEGATIVE (2026-09-19, session 14)

Precommit sealed 8ebb2c3da5faf91f BEFORE the driver ran; driver asserts the sha.
Anchors ALL EXACT: A2 legacy generator vs saved sleeve 9.975e-17 (bit-exact, same
number as the ITER30 anchor); A3 pool mirror identity 0.0 exact / weights 8.327e-17 /
bytes 9.996e-17 / fit rows 1809 / k_covered 11 / incumbent IS-SR 4.198632 continuity.

GRID (DUR only; K=378 CAD=42 legacy-6.0bp T+1 VT12 CAP5 frozen; pool 12 slots frozen):
  1.40 -> IS-SR 4.192924  (IS-ann 17.859, Wmax_sf 1.6129x)  BELOW BAR
  1.65 -> IS-SR 4.196927  (IS-ann 18.004, Wmax_sf 1.7204x)  BELOW BAR
  1.90 -> IS-SR 4.198632  (IS-ann 18.122, Wmax_sf 1.8115x)  ANCHOR = GRID ARGMAX
  2.15 -> IS-SR 4.197999  (IS-ann 18.178, Wmax_sf 1.8551x)  BELOW BAR
  2.40 -> IS-SR 4.197272  (IS-ann 18.226, Wmax_sf 1.8941x)  BELOW BAR
ADMITTED 0/5 at the 1e-4 jitter bar -> NO REVEAL per sealed stop rule (no candidate
CSV exists; no operator gate consumed). Champion shas pre==post True.

READINGS:
1. The incumbent coefficient DUR=1.9 is the IS-OPTIMAL point of its own one-parameter
   family: IS-SR is concave in DUR with the interior max exactly at the incumbent.
   FOURTH independent plateau confirmation (weights ITER22, estimator target ITER29,
   recipe ITER30, signal-parameter DUR ITER32): the champion is the fixed point of
   every measured neighborhood, now including its own signal construction.
2. IS-ann RISES monotonically with DUR (17.86 -> 18.23) while IS-SR falls: raising
   DUR buys return with more than proportional vol. Under the operator objective
   (max SR s.t. ann >= 20, gross <= 1.6) the SR-max point is the incumbent; the
   return-hungry direction is the WRONG direction on the literal objective.
3. Wmax_sf grows with DUR (1.61x -> 1.89x, all feasible < 2.0x): no concentration
   pressure anywhere on this axis; the incumbent 1.8115x sits mid-range.
4. Anchor-cell repair echo: weights dev 5.483e-09 vs committed is the SAME SLSQP
   boundary-jitter number ITER30 disclosed (identical digits, same active set at the
   brwt-cap boundary); book dev 2.477e-10. Regenerated stream reproduces the
   incumbent through fit + build to ~2.5e-10.

FRONTIER: TEN axes measured-closed: gear (ITER21), weights (ITER22), grid edges
(ITER23), census data (ITER24/#117b/27/28), 8c-era ledger (ITER25), credit-at-cap
(ITER26), covariance-target (ITER29), covariance-target-AT-CAP (ITER31), recipe
(ITER30), signal-parameter DUR (ITER32). Remaining levers UNCHANGED: purchased data
or operator rule change (G7 price tag +0.0366 from #123 stands).

AUDIT-FLAG RESOLUTION carried by this session: RAWEW15_REFRESH_CANDIDATE 07:30:16
re-emit is byte-identical (dc3d7c9e / 8c19ef22) to the #123 record - deterministic
refresh, zero drift, benign; writer not quantum-gpt, not the cron skip path.
Landed: coord/ITER32_DUR_AXIS/ (precommit + driver + log + 5 arm weights CSVs),
test_iter32_dur_axis.py 6 pins (mutation-checked RED -> byte-exact restore -> GREEN),
campaign/GOAL100_ITER32_DURAXIS.md, STANDUP_LOG, memory #124.
