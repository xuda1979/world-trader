> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
# ITER40 - DIESCRACK L-AXIS CLOSURE (2026-09-19, session 20)

## Objective (operator, verbatim - re-sent 2026-09-19 14:00, unchanged)
> "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return
> can't be smaller than 20%."

**CHAMPION OF RECORD UNCHANGED** (no adoption - reveal police-killed on G7):
`campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv` sha16 `8559fa55ee9a3417` -
weights `d2d11c92a98683df` (shrink 0.70 + brwt-cap 0.30, gear 1.0) - **ann 23.6054% /
SR 3.751429 / MDD -3.6130% / 0 neg years / gross 1.0 exact** - all operator constraints
met with headroom.

## What this iteration resolved
Memory #130 declared the signal-parameter program exhausted with diescrack closed on its
Z-slice alone (ITER36). The 38/39 two-slice family standard (dualmom band+win = two seals)
implies a family is closed only when every printed axis carries a book-level measurement.
ITER40 sealed the other printed axis: the lookback L at frozen gate Z=2.0 (precommit
f72f8a8b6466a059 BEFORE any candidate; A1 pre-seal 9.980081e-17 = the 36 vintage; grid
(15, 27, 40, 53) = printed points + floor-midpoint + one equal-step extension, 66
coverage-law-truncated and disclosed pre-seal).

## Result
- 1/4 admitted: the L curve is INTERIOR-PEAKED at 27 (IS-SR 4.206566 = bar +0.007934);
  the incumbent L=40 is NOT its family IS-argmax (third such axis: 33, 36, 40). L=15
  4.182945 / L=53 4.197074 below the bar; all cells LIVE.
- Single reveal at argmax L=27: FS SR 3.767511 = **+0.016082, the second-strongest
  rejected candidate on record** (after ITER31 +0.0366). EVERY operator gate PASS - cagr
  23.7646% (above the champion), gross 1.0, MDD -3.7668%, 0 neg yrs, CFX4 0, Wmax 1.9482x
  under the 2.0 wall, G8 0 - but G7 bins = 2/5 positive (-0.0010 / +0.0402 / -0.0339 /
  -0.0613 / +0.0157) => FAIL => REJECT per the sealed stop rule.
- The 2021-22 crisis bin negative again: the champion's crack freezes are
  OOS-load-bearing in crisis regimes (36's reading, now on both axes). L=27 is 2/5, so it
  adds nothing to the >=3/5-relaxation debate - ITER39's WIN=150 remains the only such
  exhibit, recommendation KEEP unchanged.
- The incumbent freeze is also the Wmax-safest cell (1.8115x vs 1.86-1.95 away from it).

## Frontier statement (objective: SR-max s.t. gross<=1.6, ann>=20%)
SIXTEEN axes measured-closed (adds diescrack-L). diescrack is the second family closed
under the two-slice standard (after dualmom). The signal-parameter program is exhausted
WITH the family standard uniformly applied; remaining second-tier: brwt per-variant lb
(refused mining surface, stays refused). Levers UNCHANGED: purchased data or operator
rule change - both evidence-contradicted on their best axes (Wmax-relax data-dead #119;
the +0.0161 and +0.0366 exhibits both police-killed 2/5 and 1/5 respectively).

## Verification artifacts
- Pre-commit (sealed pre-reveal): coord/ITER40_DIESCRACK_L/FINDINGS_PRECOMMIT.md
- A1 pre-seal: coord/ITER40_DIESCRACK_L/anchor_iter40.log (+ anchor_iter40_a1.py)
- Driver + log: coord/ITER40_DIESCRACK_L/driver_iter40.py + driver_iter40.log
- Findings: coord/ITER40_DIESCRACK_L/FINDINGS.md (deviations: NONE)
- Pins: campaign/bt/tests/test_iter40_diescrack_l.py - 6 tests, mutation-checked RED
  (fake cell value caught by 2 pins) -> byte-exact restore (40ac27f816f662f2) -> GREEN.
  Full suite: 587 passed / 0 failed (581+6, own run, 74.02s).
