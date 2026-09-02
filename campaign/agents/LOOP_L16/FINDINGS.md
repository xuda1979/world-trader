# LOOP ITER 3 (2026-09-02) — HONEST11-L16: best feasible champion under leverage<=1.6 + profit>=0

## New hard constraints from user
- leverage <= 1.6
- profit >= 0 in EVERY year

## Measurement (campaign's published leverage def: "EW of per-sleeve |vt scale|"; see
STRICTAUDIT_EXECUTION: capital-real gross = mean per-sleeve scale). Also computed conservative
all-in gross (mean per-sleeve x global scale) as a sensitivity.

## HONEST11-L16 (per-sleeve vol target 0.08, global A=0.07/B=0.091, same costs+borrow+throttle)
- ann(geo) 47.6% | SR_d 4.18 | SR_m 4.17 | MaxDD -4.85% (worst 3y-subwindow also -4.85%)
- leverage mean per-sleeve scale 1.59x (max 4.70x spike)  -> <= 1.6 MEAN (satisfied)
- neg years 0/19 (worst +15.3%) -> profit>=0 every year (satisfied)
- OOS17+ 43.9%
- Committed: campaign/results/GOAL100_HONEST11L16_*_daily.csv

## Feasibility verdict on the FULL goal set (Ann>=80, SR>=5, MaxDD<=7, lev<=1.6, prof>=0)
- MaxDD<=7 and profit>=0: MET.
- Leverage<=1.6 + Ann>=80: INFEASIBLE together. Return engine is SR~4.2; 80% ann at that SR
  requires ~2.5-3x gross (HONEST11X804 needed it). At <=1.6x, honest max Ann ~47% (L16).
- SR>=5: NOT met, scale-invariant ~4.2. Only new decorrelated high-SR DAILY engines help.
- => The full 5-constraint set is NOT simultaneously satisfiable on current engines/data.

## Sensitivity (conservative all-in gross = mean per-sleeve x global scale)
Base HONEST11 all-in gross ~3.3x; even lowest settings give >=1.65x with ann ~22%.
Confirms 80% at truly-low leverage is out of reach regardless of definition.

## Next direction (for the parallel team)
The SR>=5 AND 80% cannot both appear at low leverage without genuinely NEW high-SR decorrelated
DAILY engines. Team should hunt those across the untapped data (fx-img micro, stat-arb on ff
factors, cross-asset regimes) AND adversarially re-audit L16 for any remaining flattening/leak.
