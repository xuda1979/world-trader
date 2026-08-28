# A5 — Volatility-conditioned equity premium (VIX family)
Families:
1. Contango carry: long SPX when VIX term structure (vix vs vix3m from alphaportfolio_replication/data/vix_daily.csv + vix3m.csv) in contango (vix<vix3m), cash/short in backwardation, T+1, vol-target 10%.
2. VIX percentile gate on MR crash sleeve: reuse meanrev crash sleeve concept — but NOTE: campaign/agents/A6 owns MR; coordinate via FINDINGS, don't duplicate. Instead: vol-managed equity premium (Moreira-Muir on SPX, scaled by lagged 21d vol).
3. Long SPX gated by dxy trend + hy_oas trend (credit-friendly regimes).
4. VIX break-glass: long VIX* when vix>32 AND vix9d... (no vix9d; use vix/vix3m spike) — event hedge overlay.
vix_daily.csv spans? CHECK first. Costs trivial (few switches). Main risk: SR<0.6 solo. If solo fails, test as OVERLAY multiplier on LIB:L_S_130_30 and report the BLENDED sleeve as yours.
