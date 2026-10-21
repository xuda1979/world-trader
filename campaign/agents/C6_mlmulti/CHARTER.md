# C6_mlmulti — ML multi-domain engines (NEW DOMAIN: ML on new inputs)

Mission: train compact ML models on NEW input domains (NOT the old equity panel features that
B4 already covered) to produce daily books passing ALL gates. sklearn only (fast, CPU).

IDEAS (in order):
1. Curve-ML: features = [DGS2, DGS5, DGS10 changes 1d/5d/21d, 2s10s z, breakeven z, hy_oas z,
   vix z, level vs 252d] -> predict DGS10-yield-driven bond book (long/short 10y via -dur*dy).
   Purged split: train 2008-2016, test 2017-2026 (report OOS SR — must be >= 1.0 FULL is fine,
   but report OOS separately).
2. KF-industry-ML: features = 48-industry VW momentum ranks (21/63/126d), industry vol,
   cross-dispersion -> predict next-21d industry dispersion or top-industry returns; trade top3/bottom3.
3. Positioning-ML: features = COT money-manager z-scores across ~20 markets (weekly) ->
   predict next-4w sign of underlying futures (only markets with on-disk prices). Weekly book.
4. FX-cross-ML: 8 fx pairs + dxy + gold features -> predict dxy daily sign; trade dxy via
   EUR_USD inverse proxy (or basket of 4 majors, vol-normalized).
5. Regime-ML (meta): features = sleeve-pool trailing stats (corr, vol, dispersion) -> predict
   which sleeves underperform next month -> monthly reweighting of existing sleeves.
   (Must beat EW OOS to save.)

NOTES: use sklearn GradientBoostingClassifier/Regressor, HistGradientBoosting, RandomForest,
Ridge. Purged K-fold or simple time splits; T+1 execution; 6bps on turnover; vol-target trailing.
Keep features strictly trailing. Report feature importances in meta.

HONESTY: All gates in GOAL100_AGENT_BRIEF.md. OOS discipline: train <= 2016, test 2017+;
report both; full-window stats must pass gates with OOS >= 0.8x full SR.
