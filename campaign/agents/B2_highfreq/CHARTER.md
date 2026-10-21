# B2_highfreq — MISSION: Short-duration, high-turnover engines with TIGHT MaxDD per unit return

## OVERRIDING GOAL
20y, SR>=2, ann>=50%, MaxDD<=8%, 6bps/side, free data, no leverage, OOS. Binding constraint:
MaxDD<=8% at 50% return. Short-duration mean-reversion/stat-arb books naturally have TIGHTER
drawdowns per unit return (they rotate fast, don't sit in multi-month regime losses).
HARVEST that.

## Data (free, on disk)
- Panel: tools/quant/data/twelve_big (298 names OHLCV 2006-09..2026-08) + twelve_extend (440).
  Loaders: campaign/harness/data.py (closes(), volumes(), ff_factors(), fred(name)).
- FRED 1990+: tools/quant/hedge_fund_strats/data_fred_new. FX: tools/quant/data/fx.

## Ideas (aim SR>=1.0 at <=12% vol, small MaxDD, corr<0.2)
1. **Short-horizon cross-sectional reversal**: 1-5d return reversal on equity panel, T+1,
   6bps/side. Check turnover cost grind carefully; if dies at 6, shorten to 3-5d.
2. **Volume-shock reversal**: extreme-volume days reverse; signal on volume z-score, T+1.
3. **Pair/stat-arb 5-20d reversion** on cointegrated pairs.
4. **Weekday/turn-of-month/seasonal effects** that survive scramble 200x.
5. **Cross-asset short momentum/reversal** on FRED 1990+ (rates, credit, FX) at 5-21d —
   fast-rotating, low regime-DD.

## HONESTY CONTRACT
T+1. 6bps/side (apply_cost). Gates: FULL SR>=0.6, halves>=0.3, <=2 negYr each>-5%, scramble
200x, trailing vt10, plateau, economic rationale. High-turnover: ALWAYS re-price costs —
if only clears at 6bps but dies at 8-10bps, report cost sensitivity honestly. No same-day
signals summarize in FINDINGS. Last line: ROUND 1 DONE
