# ITER28 PRE-COMMIT - CENSUS REMAINDER, FILTER-REPAIR REVEAL (2026-09-19, session #10)

Sealed BEFORE the repair run computes any admission. This is the #118 -> #119-precedent
repair of the defect disclosed in coord/ITER27_CENSUS_REMAINDER/FINDINGS.md (sha16
11f4c732492f0c31): ITER27's sealed Wmax filter used max_share x 13 <= 2.0, but CFX4 has
ZERO IS coverage so k_covered = 12 and the campaign-recorded scale-free invariant
(#117 convention note, #117b normalization lesson) is max_share <= 2/k_covered = 1/6.
The ITER27 run itself is untouched and its stop rule was honored (0 admitted as sealed,
NO reveal fired). This iteration re-measures the SAME frozen candidate set under the
corrected filter and fires the (still FIRST) reveal for whatever is admitted.

## Frozen (identical to ITER27 pre-commit, one delta)
- Candidate set: the SAME 30 (29 cboe non-vol capital-real ETFs + nokcarry two-leg);
  same sleeve builder, same 13-pool fit mirror, same anchors, same G1-G7 reveal gates,
  same STOP RULE (0 admitted => negative, no reveal; admitted argmax fails any gate =>
  REJECT, no second reveal).
- THE DELTA (the repair): per-candidate Wmax filter becomes
  wmax_sf = max_share(13-pool fit) x k_covered <= 2.0 + 1e-9, where k_covered = number
  of have-columns in the fit (names with any IS data; CFX4 excluded by zero coverage).
  fit_relw returns k so the anchor and every row report the scale-free value. All other
  filters unchanged: IS-MDD >= -6%, 0 IS-neg yrs, g8 fit-row shrink < 2%, admission
  IS-SR > 4.198632 strict.
- Expected from the ITER27 as-run table (disclosed, not decisive): exactly xly_etf
  flips to admitted (max share 0.16101, IS-SR 4.2007). The driver recomputes ALL 30
  rows under the corrected filter; whatever the table says, governs.

## Anchors required BEFORE the reveal (fail-closed)
1. Session gauntlet already PASS this session (ok=true 7/7,
   ITER27.../verify_champion_r3_iter27_start.json); champion sha16 8559fa55ee9a3417 /
   weights d2d11c92a98683df byte-verified start of session.
2. Driver anchors re-asserted in-run: weights maxdev < 1e-12; bytes maxdev < 1e-12
   (n=4806); grossmax <= 1.0+1e-9; incumbent IS-SR 4.198632 (asserted).
3. Champion sha16 pre == post (asserted in-driver).

## Multiplicity
No candidate in this set has ever had a reveal (not in ITER24's 28, not in ITER25/26
credit cells). xly's reveal, if it fires, is its FIRST. This is a defect repair, not a
second reveal: ITER27 fired nothing.

## Output contract
driver_iter28.py + driver_iter28.log + candidate CSVs (if reveal fires) under
coord/ITER28_CENSUSREMAINDER_FIX/. Pins extended in
campaign/bt/tests/test_iter27_census_remainder.py (both iterations). Suite green from
repo root. Memory sub-entry #120 AFTER verdict (topic file re-read at write time).
