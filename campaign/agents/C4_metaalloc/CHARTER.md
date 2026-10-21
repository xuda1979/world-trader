# C4_metaalloc — Meta-allocation & construction research (NEW DOMAIN: construction itself)

Mission: the blend's ann @ MaxDD<=8% is limited by DD/return ratio ~0.17-0.33. Research
construction-level innovations that RAISE ann per unit MaxDD honestly (no lookahead, no leverage):

IDEAS (in order):
1. Per-sleeve drawdown throttling cross-validated: instead of global trailing-126d DD throttle,
   per-sleeve throttles with per-sleeve tuned thresholds on IS (2008-2016), TEST on 2017-2026.
   Honest OOS protocol mandatory.
2. Correlation-conditioned weights: trailing 126d correlation matrix of sleeves -> inverse-variance
   or min-var weights recomputed weekly (trailing only). Compare vs EW-of-vol-normalized.
3. Sleeve quality switch: monthly sleeve momentum (126d SR trailing) -> top-8-of-14 selection,
   tested honestly (does selection beat EW OOS? probably not — document).
4. Kalman/EGARCH vol forecasting for the vol target (vs expanding-window RV) — use only statsmodels
   or simple EWMA with multiple halflives blended; verify MaxDD improves OOS.
5. Risk-parity-of-correlation: weights ~ (vol^-1 x avg pairwise corr adjustment) weekly trailing.
6. Ensemble of throttles: 63d + 126d + 252d DD throttles averaged — smoother gating, less regime
   whipsaw; test vs single throttle on IS/OOS split.
7. Binary-search the global vol-target on IS only, apply unchanged to OOS (honest version of the
   vt=8 wall search that failed before — fix the look-ahead that invalidated B5's extreme config).

DELIVERABLE: a construction config (weights method, throttle, vt) that beats COORD_FINAL
(43.2% ann, -7.5% DD) on the OOS window 2017-2026 with MaxDD<=8% in BOTH subwindows.
Save config + daily csv as campaign/agents/C4_metaalloc/sleeves/C4_construct_v1.csv + meta.
Use ALL sleeves in campaign/results/sleeve_library + campaign/agents/*/sleeves (dedupe, >=250d
history, positive full SR). Log everything in FINDINGS.md with exact numbers.

HONESTY: IS/OOS split discipline: choose on 2008-2016, report 2017-2026 untouched. If OOS fails,
report honestly and try next idea. NEVER touch 2017+ data for parameter choices.
