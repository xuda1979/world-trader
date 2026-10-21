# E1_20yspan — push the champion start date back to 2006/2007 (the "20-year" requirement)

Current champion starts 2008-09 (H21_f5/H21_br ML sleeves + A5r2/r4 VIX3M floors limit it).
The 12-pool (drop H21_f5, H21_br, A5r2, A5r4) can start 2007-01 (a6r7 has DGS2 1976+ data;
B3momhml 2006-01; dualmom 2007-10; C5ng DHHNGSP 1997+ — the SAVED sleeve starts 2008-03 only
because of its 90d vol warmup, REBUILDABLE to 1998).

TASKS:
1. Rebuild C5_ng_weekday_prem + C5_ng_summer_weekday from raw DHHNGSP (FRED, 1997-01+) with
   NO start-date truncation — warmup only. Save as E1 sleeves (all gates, 1998-2026).
2. Same de-truncation audit for a6r7 (DGS2 1976+! the saved sleeve starts 2007-01 — why?
   check the repro script's start; if arbitrary, rebuild from 1990), brwt (wti_full 1986+,
   brent data_fred? check span; rebuild from max available), A1inf (twelve panel 2006-09 floor),
   A1credit (1990 ✓ already).
3. Assemble the max-history 12-pool blend (your rebuilt sleeves + B3momhml + dualmom + carryv2
   + QAxasts? (2008 floor, keep but enters late) + XGB1y (2008 floor) etc). Report blend from
   earliest feasible start (target 2006-09) with all gates + per-year DDs. IS/OOS discipline:
   any new param chosen on pre-2017 only.
4. The catch: dropping H21 (ML keystones) costs ann. Quantify the 20y-variant frontier honestly:
   X-yrs span @ what ann/DD. Deliver GOAL100_CHAMPION20Y upgrade if you beat the coordinator's
   (GOAL100_CHAMPION20Y_BALANCED_daily.csv: 39.5% ann @ -7.1%, 20.4y span, SR 4.91).

Log all numbers. Last line: ROUND 1 DONE
