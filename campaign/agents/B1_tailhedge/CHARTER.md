# B1_tailhedge — MISSION: Compress MaxDD per unit return (the binding constraint)

## OVERRIDING GOAL (escalated)
20y, SR>=2, ann>=50%, MaxDD<=8%, 6bps/side, free data, NO leverage, OOS. Current best:
vol-targeted EW blend of 15 sleeves -> ann 50% at 22% vol but MaxDD -18%. Need MaxDD<=8% at
50% return = tail efficiency 2x better (DD/return ~0.34 -> 0.16). YOUR mission: tail-risk
overlays that compress the LEFT TAIL of a high-return blend honestly.

## Reference blend (reproduce it, then overlay)
Take these 15 sleeves (in campaign/results/sleeve_library + campaign/agents/*/sleeves +
tools/quant/reports/xgb_horizons): XGB1y_deploy, h21_f5, h21_br, Merger_Arb_PEAD,
A1_mix_breadthCTA_SharpeW_LS13030, A5_r2_contango_rateshock, a6_r2_pair_residmom_fm1926,
A1_carry_seasonal_v2, A5_r7_credit_composite, a6_r7_bond2y_trend, A1_infl_breadth_mom,
A2_fx_carry_W11_accrual, AP_gold, QA_xasts_tsmom189, A1_credit_regime_mom. EW + vol-target
to 22% (expanding ewm63, shift-1, clip 5). That is baseline: ann~50%, MaxDD~-18%.

## Ideas (honest, T+1, trailing-only)
1. **VIX level/term crash gate**: de-risk the blend when trailing (5-30d) VIX high/rising,
   with hysteresis. Never same-day VIX (A5: 2.30->1.13 honest). shift(1).
2. **Realized-vol accelerator + drawdown throttle**: step down gross when trailing realized
   vol OR trailing drawdown > threshold (hysteresis avoids whipsaw).
3. **Flight-to-safety sleeve**: long gold/treasuries when credit spreads blow (DAAA-DBAA,
   HY OAS), neutrally sized, to offset equity-LS losses. Verify publish-lag.
4. **Put-replication / convexity**: synthesize convexity by buying VIX-futures-like exposure
   via VIX after trailing down-moves (skew/vol-of-vol). FRED vix 1990+.
5. **Naive protective put on blend**: hold a % in a SPY-short sleeve that is long-only when
   VIX>threshold — explicitly a hedge leg, size to minimize blend MaxDD.

## HONESTY CONTRACT
T+1. 6bps/side on overlay turnover. Gates on the OVERLAY-ONLY sleeve: FULL SR>=0.6 (an
insurance sleeve can be SR>0 if it nets positive across full cycle; if it's net-negative
it may STILL be worth it — report its full cost and the combined blend metrics so the
coordinator can judge). Report combined (overlay, blend+overlay: ann, MaxDD, SR, DD/ann).
Target: cut DD/ann from 0.34 toward 0.16 while keeping ann>=25%. Save any standalone-passing
sleeve. Log all lookahead traps. Last line: ROUND 1 DONE
