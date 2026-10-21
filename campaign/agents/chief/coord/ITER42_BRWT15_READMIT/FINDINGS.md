# ITER42 FINDINGS - BRWT15 RE-ADMISSION (pool-composition axis) - REJECTED ON G7

2026-09-19 session 22. Precommit FINDINGS_PRECOMMIT.md sha16 2b204b1a5f3f4e0c (with
Amendment 1) sealed BEFORE any candidate computation; the driver hard-asserted it.
Driver log: driver_iter42.log (values below are from that log and the arm CSV).

## VERIFIED-FIRST (session open)

Gauntlet ok=true 7/7 fresh verify_champion_r3_last_session22.json (weights 8.327e-17 /
bytes 1.032e-16 / gross max 1.0000000000006, 0 over / 0 neg yrs worst +7.3488 / MDD
-3.6130 / SR 3.751428690 / cagr 23.6054); champion 8559fa55ee9a3417, weights
d2d11c92a98683df; coord quiet since 15:25; one gauntlet fail-CLOSED on a coordinator
brwt7 path typo before anything ran (listed behavior).

## RESULT: EIGHTEENTH AXIS MEASURED-CLOSED. REVEAL FIRED, DIED ON G7.

- Anchors ALL EXACT: frozen blocks text-identical vs driver_iter41 AND driver_iter36;
  A1 sibling recons 9.999e-17 / 9.986e-17 / 9.996e-17 (n 6567/4580/4580); ii-prime
  overlap calendar identical, regen tail 2026-08-28 = siblings; projection identity on
  incumbent 0.0; weights 8.327e-17; bytes 9.996e-17; rows 1809; k 11; IS-SR 4.198632;
  Wmax_sf(x11) 1.8115x. Champion sha pre==post.
- THE CELL WAS ADMITTED - AND DECISIVELY: the 13-pool fit puts brwt15 at 8.3992 pct
  (fifth-largest line), IS-SR 4.294412 = bar + 0.095780 - THE LARGEST IS-LEVEL GAIN EVER
  MEASURED ON THIS CAMPAIGN (credit-at-cap +0.059, cov-target-at-cap +0.046, grid-edge
  +0.024), IS-MDD -2.58 pct, 0 IS neg years, k=12, rows 1809 (coverage law held).
- THE ALLOCATION IS DOUBLE-BOUND: brwt block = 0.300000 EXACTLY at the family cap with
  FOUR members; C5ng clamped at 0.166667 = 2/12 EXACTLY by the water-filling projection
  (projection identity 4.094e-03 = the clamp; the raw fit wanted C5ng past the per-name
  wall). The candidate book sits at BOTH invariants simultaneously.
- REVEAL (the single cell is its own argmax): FS SR 3.721744 < 3.751429 (-0.029685) -
  the +0.0958 IS gain INVERTS OOS. cagr 23.9585 PASS, arith 21.6532, MDD -3.7569 PASS,
  0 neg yrs, gross 1.000000000 exact, turnover 4.0585 bp/yr, margin 0, Wmax_sf 2.0000x
  PASS (at the wall), CFX4 0, G8 0. G7 bins: 2017-18 -0.0742 / 2019-20 -0.1884 /
  2021-22 +0.1005 / 2023-24 +0.0715 / 2025-26 +0.0689 = 3/5 positive (4 required),
  min bin -0.1884 => FAIL => REJECT per sealed stop rule. No second reveal.

## READING

1. STRONGEST ITER17-LAW EXHIBIT ON RECORD BY MAGNITUDE: the largest honest IS gain the
   campaign has ever measured (+0.0958) is the one that decays hardest OOS (-0.0297
   net). The IS optimizer is buying 2008-2016 Brent-WTI block-correlation structure
   (the fit dilutes the brwt trio across a fourth correlated member and pushes C5ng to
   its wall) - exactly the regime the 2017-20 bins kill. The police now 12-for-12 on
   reveal-type rejections.
2. BIN PATTERN INVERTED vs the recent family: prior police-kills were front-loaded
   gains (2017-20 positive, 2021+ negative, crisis-protective freezes); THIS one is
   back-loaded (2017-20 negative, 2021+ positive) - the OOS decay is EARLY, not late.
   Both directions kill; consistency, not sign, is what the gate measures.
3. G7 price-tag curve UNCHANGED in kind, one more point of evidence for KEEP.
4. brwt15 provenance caveat carried into the verdict: the candidate stream is the R6-
   convention RECONSTRUCTION (config triangulated by name/family-scalar/emission-start
   signature; overlap-calendar identical to the doubly-stale prefix vintage; the value
   delta to the prefix is the measured stale-cost + stale-2020-wave class, Amendment 1).
   The rejection is 3/5-bins-wide, not marginal-provenance-wide: even taken at face
   value the cell fails.

## FRONTIER

EIGHTEEN axes measured-closed (adds pool-composition-under-current-objective). The
re-add was the ONLY history-pre-registered membership perturbation; any other
membership choice is result-selected mining (ITER17 proxy-screen fraud class) and stays
refused. Per-variant brwt lb stays refused. Remaining levers UNCHANGED: purchased data
or operator rule change (price tags: G7-relaxation exhibits +0.0433 floor-dead / +0.0366
/ +0.0161 / +0.0075 / +0.0073 / +0.0034-first-3/5 / +0.0026; Wmax wall OOS-dead on
credit; the 20 pct floor MEASURED as the de-lever protector).

Landed: coord/ITER42_BRWT15_READMIT complete (precommit+Amendment 1, driver_iter42.py
assembled verbatim-block from driver_iter41 with the 4-member block at CALL SITES,
driver log, arm_13pool_weights.csv, candidate_13pool_daily.csv + candidate_13pool_weights.csv
for-the-record), test_iter42_brwt15_readmit.py 6 pins mutation-checked RED -> GREEN,
campaign/GOAL100_ITER42_BRWT15READMIT.md (after the suite per round4b), STANDUP coord
entry, memory #133 + index. SUITE 599 passed / 0 failed (593 + 6, own run).
