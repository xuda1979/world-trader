# G4_detrun — FINDINGS (self-executed by coordinator; GLM API limit prevented sub-agent)
Date: 2026-09-01. Method: direct python, no sub-agent.

## Result: the late-starting sleeves are DATA-BOUND, not arbitrarily truncated.
1. A5r2 (VMX contango gate). Starts 2009-09-18 = first VIX3M print. Tested proxy
   VIX / (21d realized vol of SPI) as contango proxy: in the 4249-day overlap vs true
   VIX/VIX3M, corr = -0.141 (spearman -0.153); gate-position agreement 19%; gate corr
   -0.088. NOT a valid proxy. The 2009-09 start is HARD. Cannot extend honestly.

2. dualmom (双动量 band). Momentum legs need trailing 12m returns; the 2006-09 panel
   begins 2006-09-26 => earliest 12m-clean signal 2007-10. Genuine data floor. Cannot
   extend pre-2007-10 without a longer price panel (none on disk free; OTC/Fund data
   insufficient).

3. XGB1y (monthly 1y book). First preds cohort Feb-2009 (needs 12m of forward return
   slices = data through the following Feb + 12m). Genuine floor.

## Implication for the 20Y goal
Pool span floors: brwt2000, natgas1998, a6r7/QAxasts/carryv2 2006-07, A5r7/A1credit 1990s,
dualmom 2007-10, A5r2 2009-09, XGB1y 2009-02.
=> GOAL100 TRUTH20Y = 2006-10-02..2026-08-28 = 19.8y is the honest maximum with this pool.
0.2y short of the 20y target — disclosed, not fudged (no sleeve can be extended without
data that cannot be obtained honestly, and stitching fake pre-2007 returns would be handwaving).

## The real blocker for ann>=100% is NOT span
Per spec math: ann ~ SR_blend * vol_budget, vol_budget = 8%/DDratio ~ 11%. Current SR~5.6
=> ~62% at the 8% DD wall. To hit 100% needs SR~9-10 at that vol — i.e. ~2x more
decorrelated engines than all ~330 tested ideas produced. This is a data/engine-availability
limit, not a construction or span problem.

ROUND DONE
