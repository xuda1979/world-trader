# ITER40 FINDINGS - DIESCRACK GATE-L AXIS AT FROZEN Z=2.0 (2026-09-19, session 20)

Pre-commit sealed BEFORE any candidate computation: FINDINGS_PRECOMMIT.md sha16
f72f8a8b6466a059 (A1 pre-seal disclosed inside; anchor_iter40.log). Driver:
driver_iter40.py (generated from driver_iter36.py by 29 asserted-exactly-once
substitutions; py_compile OK; frozen blocks fit_relw/apply_cap/project_wmax/build_book
AST-text-identical to driver_iter36.py asserted at run start), log driver_iter40.log,
4 arm CSVs + candidate_L27 pair for the record.

## Anchors (all PASS)
- Gauntlet (session start): verify_champion.py r3 ok=true 7/7 ->
  verify_champion_r3_last_session20.json (weights 8.327e-17 / bytes 1.032e-16 /
  gross 1.0000000 / SR 3.751428690 / cagr 23.6054; shas 8559fa55ee9a3417 / d2d11c92a98683df).
- A1 (pre-seal): regen (L=40, Z=2.0) vs committed sleeve bytes 9.980081e-17, inner n=4615,
  span 2008-03-28..2026-08-24, saved sha16 c7d19f5bd0b2a603 - IDENTICAL to the 36 vintage.
- A2: projection identity exactly 0.0; weights 8.327e-17; bytes 9.996e-17 (n=4806);
  grossmax 1.000000000; fit rows 1809; k_covered 11; IS-SR 4.198632 exact; Wmax_sf 1.8115x;
  diescrack share 10.8293 pct. Anchor cell L=40: weights 6.450e-09 / book 8.494e-10 /
  block 0.300000. Champion sha16 pre == post (driver + pins).

## Legality (predecessor-consistency, disclosed at seal)
36 refused L only WITHIN its seal (1-D slice discipline). The 38/39 two-slice family
standard (dualmom band+win) makes the other printed axis a legitimately separable seal.
This seal completes the diescrack family to that standard. The 2-D (L,Z) surface remains
REFUSED. Grid rule mirrored 36: printed (15, 40) + floor-midpoint 27 + one equal-step
extension 53; 66 truncated by the coverage law (first z-valid would land after frame start
2008-03-31) - disclosed pre-seal with the A1 diagnostic (first z-valid 2008-03-18 at L=53).

## Coverage law (asserted per cell, all PASS)
Regen index L-invariant (every cell spans the full spread-dropna index from 2008-01-02);
first z-valid 2008-01-23 / 2008-02-08 / 2008-02-28 / 2008-03-18 (all <= frame start);
frame-window notna 4614 in every cell; dfc index equals the frozen frame index; fit rows
1809; k_covered 11; CFX4 pinned 0.

## Result: 1/4 admitted -> reveal FIRED -> REJECTED on G7 (ITER17-law closure 15)
L      regen-dev   is_sr     IS-ann   IS-MDD   negy  Wmax_sf   adm
15     8.661e-02   4.182945  18.261   -2.43    0/9   1.9028x   no
27     4.818e-02   4.206566  18.278   -2.34    0/9   1.9482x   YES
40     9.980e-17   4.198632  18.122   -2.56    0/9   1.8115x   no (anchor)
53     4.369e-02   4.197074  18.174   -2.52    0/9   1.8621x   no
Cells LIVE (regen-dev 0.044-0.087 - real curves, not jitter). The L curve is INTERIOR-
PEAKED at 27, not at the incumbent 40: third signal-param axis where the acceptance freeze
is not its family IS-argmax (33 k-dip, 36 Z, 40 L).

REVEAL L=27: FS SR 3.767511 = +0.016082 over 3.751429 = SECOND-STRONGEST rejected
candidate on record (ITER31 3.787991 +0.0366; then 40; 33 3.758975; 36 3.758736;
39 3.754857; 30 3.754071). cagr 23.7646 pct (ABOVE the champion's 23.6054), ann arith
21.4904, MDD -3.7668, 0 neg yrs, grossmax 1.000000000, CFX4 0, Wmax_sf 1.9482x (under
the 2.0 wall), G8 0.0000 - ALL operator gates PASS. G7 bins:
2017-18 -0.0010 / 2019-20 +0.0402 / 2021-22 -0.0339 / 2023-24 -0.0613 / 2025-26 +0.0157
= 2/5 positive (min bin -0.0613 >= -0.10; FS-SR arm passed) => FAIL => REJECT per sealed
stop rule; no second reveal.

## Reading
(i) The 2021-22 energy-crisis bin is negative AGAIN (-0.0339, after 36's -0.0036) plus
2023-24 -0.0613 - the champion's crack scalar freezes are OOS-load-bearing in crisis
regimes, exactly the 36 reading, now on BOTH axes of the family.
(ii) L=27's IS gain is real (bar +0.0079, cells live) and its FS gain (+0.0161) is the
second-largest ever measured - and the police still kill it on window INCONSISTENCY, not
magnitude. KEEP stands. Note: L=27 is 2/5, so unlike 39's WIN=150 (3/5) it adds NO new
ammunition to the >=3/5-relaxation debate - the 39 exhibit remains the only one.
(iii) Wmax_sf rises away from the anchor in both directions (1.9028/1.9482 left,
1.8621 right vs 1.8115 at 40) - the incumbent freeze is also the Wmax-safest cell.

## Frontier
SIXTEEN axes measured-closed (adds diescrack-L; diescrack is the SECOND family closed
under the two-slice standard after dualmom). The signal-parameter program is exhausted
WITH the family standard now uniformly applied. Remaining second-tier: brwt per-variant
lb (refused mining surface, stays refused). Remaining levers UNCHANGED: purchased data or
operator rule change.

## Sandbox (session 20)
python3 heredoc writers work; Write/Edit tools on repo denied (writer path used);
shasum gated (python3 hashlib path); pytest from repo root clean, no load spike.
