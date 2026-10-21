# GOAL100 ITER46 — CENSUS REMAINDER CLOSED (cad_govt_long, 2026-09-19)

Champion of record (UNCHANGED, byte-verified pre==post this session): `GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv`
sha16 `e67446186e269b88` / weights `bde8612d0b295068` / CAGR 23.68% / SR 3.7648 /
MDD -3.66% / 0 neg yrs / gross 1.0 (leverage 1.0 of the 1.6 cap; 23.68% of the 20% floor held).

## The 22nd measured axis (session 26 of the operator's standing "keep improving" directive)

Operator objective (verbatim): keep improving; leverage <= 1.6; maximize Sharpe; annual
return >= 20%. Roster scalar program EXHAUSTED at 21 axes (#136). This session enumerated
the census long-tail EXACTLY: of the IS-FITTABLE lines in DATA_AXIS_CENSUS_2026-09-19.txt,
the classes already measured (ITER24 bund 8 + em_fx 6 + cad 4 + eia 10 + selic; ITER27 the
29 cboe non-vol ETFs + nokcarry) and the excluded classes (vol/index LEVELS on the F4
expressibility rule - SPX/OEX/DJX included; partial-IS; recent-only) leave EXACTLY ONE
LEGAL CELL: `dm_rates/cad_govt_long.csv`, the 5th CAD tenor ITER24's frozen set never
enumerated. Selection: census metadata + campaign history, result-blind (ITER17 law).

## Discipline

Precommit v1 `5597f574c70f88c1` sealed BEFORE any candidate computation (A1 sibling
re-type anchors pre-seal: regen vs the ITER24-saved cad_govt_10y/2y sleeves = 9.995e-17 /
9.975e-17 FULL coverage; recipe = the frozen ITER24 trend recipe at the pre-registered
dur 9.5 = printed 0.95*10, no novel scalar, dur-sweep refused). RUN-1 fail-closed at the
inherited `nrows == 1809` assert (new-member cell keeps its Canadian-holiday calendar:
1780 = 1809 - 29 CAD holidays = 1.603 pct, inside the pre-registered G8 2 pct bound);
Amendment 1 `7027fd6f05e3c1cb` re-sealed BEFORE the corrected run (no tolerance weakened;
run-1 record preserved verbatim in the amendment). RUN-2 green: frozen blocks
text-identical vs driver_iter43/36/45 (AST run-start proof); A2 committed-frame continuity
exact (weights 8.327e-17, bytes 9.991e-17, IS-SR = bar 4.203733 exactly).

## Result

- CELL ADMITTED on IS: share 4.5852 pct, IS-SR 4.225176 = bar +0.021443 (largest
  membership gain since ITER42's +0.0958), IS-MDD -2.39 BETTER, 0 IS neg-yrs,
  Wmax_sf 1.8949x under the 2.0x wall, projection identity 0.0.
- REVEAL (the single cell): FS SR 3.754843 < 3.764764 (-0.0099) - the IS gain INVERTS
  OOS; ALL 7 operator gates PASS (CAGR 23.5410 pct, arith 21.3077, gross 1.000000000,
  MDD -3.5266 BETTER, 0 neg yrs, CFX4 0, Wmax_sf 1.8949x, G8 1.603 pct) but G7 bins
  [-0.0058, -0.0360, +0.0028, +0.0512, -0.0180] = 2/5 positive => REJECT per the sealed
  stop rule, no second reveal. NINTH consecutive police kill; the police again binds on
  CONSISTENCY, not magnitude (2019-20 bin -0.0360 while 2023-24 prints +0.0512).

## Frontier after ITER46

**The census screen is MEASURED-CLOSED end-to-end under the current objective** - every
IS-FITTABLE line of the census of record now carries a verdict (ITER24 + ITER27 + ITER46).
The free-data program has NO remaining legal cell. The long end of the CAD curve is the
same 2008-2016 rates-trend artifact that killed the bund family: rates-trend complex is
now measured dead under BOTH champions. Remaining operator levers UNCHANGED: purchased
data (total-return ETF series, VIX futures, regional basis) or operator rule change -
both evidence-contradicted on their best axes (nine consecutive G7 kills; the strongest
3/5 relaxation exhibit remains ITER39 WIN=150 at +0.0034).

## Artifacts

coord/ITER46_CADGOVTLONG/ complete: FINDINGS_PRECOMMIT.md (v1 + Amendment 1) 7027fd6f05e3c1cb,
anchor_iter46_a1.py/.log, driver_iter46.py e2ff2b7b2ed69f52, driver_iter46.log 92fd6a2cb7b30065,
arm_cadlong_stream/weights CSVs, candidate_cadlong_daily.csv (for-the-record, REJECTED),
FINDINGS.md 9697ede0b8ed1443. Pins: test_iter46_cadgovtlong.py 6 pins, mutation-checked RED
(fake FS-SR + fake bin caught by 2 pins) -> byte-exact restore (log 92fd6a2cb7b30065) -> GREEN.
