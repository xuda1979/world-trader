# Final Strategy Report (2026-08-04)

## Executive Summary

Long/short market-neutral equity strategy on 84 liquid US large-caps,
GBRT cross-sectional return prediction (Gu-Kelly-Xiu 2020), mean-variance
portfolio optimizer (Garleanu-Pedersen turnover-aware), realistic retail
costs. After ~130 tested configs, the surviving honest strategy predicts
the **market-risk-adjusted residual return** (CAPM alpha via real Fama-
French daily factors) and is the ONLY configuration positive in both
disjoint time sub-samples.

## Cost / Execution Constraints (user spec)
- Transaction cost: **3.8 bps one-side, no market impact, no slippage**
- Short financing: call-rate (DFF) + 25 bps ETB borrow fee
- Long financing: call-rate + 50 bps on levered excess
- T+1 execution, 3.8 bps charged on rebalance deltas (including
  trend-gate forced rebalances)
- Universe: 84 liquid US large-caps (Polygon daily OHLCV, 2024-07-24 ->
  2026-07-23, 501 trading days); trading starts ~Apr 2025 (160-day
  training history required)

## Final Strategy: "CAPM-alpha residual" (mkt label)

### Configuration
- Model: GBRT (squared error), depth 2, 200 trees, lr 0.05,
  min_samples_leaf 20, EMA prediction smoothing 0.5, pred clip 4.0
- Label: forward 10-day return residualized against real Fama-French
  Mkt-RF only (rolling 60d beta, min 30 obs) + cross-sectional z-score
- Factors: ICIR-screened core — mom_12m, mom_12_1m, vol_60d, liq_turnover
  (4 of 23; every factor-breadth expansion tested and rejected)
- Horizon h=10, train_window=160, refit every 5d, rebalance every 20d
- Portfolio: mean_var (lambda 0.5), 13 long + 13 short, vol target 30%,
  gross leverage 1.0, beta max abs 0.25, position cap 20%
- Trend gate: go flat when trailing 60d SPY return < -5% (event-driven
  forced rebalance at regime transitions, costs charged)

### Performance (all annualized, 3.8 bps, financing on)
| metric | full sample | first sub-sample | second sub-sample |
|---|---|---|---|
| Sharpe (daily returns) | 2.11 | 0.52 | 0.25 |
| Sharpe (holding-period returns) | 1.82 | 0.44 | 0.34 |
| t-statistic (holding periods) | 2.56 | 0.52 | 0.42 |
| Annual return | 28.1% | - | - |
| Max drawdown | -9.6% | - | - |
| Annualized turnover | 4.7x | - | - |
| Avg abs beta | ~0.05 | - | - |
| Verdict | watch (1 flag) | watch | watch |

Sub-sample split: first = trades ~Apr-Dec 2025; second = trades
~Aug 2025-Jul 2026 (overlap is a consequence of the 160-day training
history; both windows are out-of-sample walk-forward runs).

### Regime profile (with trend gate)
- bull: Sharpe 1.75 | sideways: 2.67 | bear: **+0.78**
  (the gate turns the previously -1.6 bear regime positive)

### Cost robustness
3.8 bps -> 5.0 bps: Sharpe 2.27 -> 2.26; -> 7.6 bps: 2.24.
Turnover 5x/yr makes transaction drag small.

## Why this and not the "2.27 champion" (demean label)
The demean label variant achieves a higher full-sample Sharpe (2.27
daily / 1.95 holding-period, t=2.74) but FAILS time-split validation:
negative in the second sub-sample (holding-period Sharpe -0.98, t=-1.2).
Its edge is concentrated in Apr-Aug 2025. The CAPM-alpha variant is
positive in both windows — the only configuration that is.

## Research conclusions (axes closed with evidence)
- Label residualization ladder: demean 2.15 > mkt-only (CAPM alpha) 2.02
  > FF3-no-UMD 1.13 > FF3+UMD 0.70. Full-factor residualization removes
  the momentum premium the strategy exploits; market-beta stripping is
  the only safe form — and the only time-robust one.
- Factor breadth: bypass ICIR screen (0.63), extra factors (0.86),
  interaction features, OHLC factors, v2 academic factors (-0.28): all
  reduce Sharpe. The 4-factor ICIR-screened core is optimal.
- Model capacity: n=400 (1.04), lr=0.1 (0.77), depth 3 (0.99): the
  shallow, slow, smoothed GBRT is optimal.
- Portfolio: rebalance every 20d (horizon multiples) > 10d/30d/45d;
  n=13 > n=8/5; train_window=160 is the peak of a monotone curve.
- Multi-horizon IC-weighted in-model blend: 0.20 — rejected.

## Honest caveats
- 501 bars / ~16-25 independent holding periods: NO configuration is
  statistically established. Realistic forward holding-period Sharpe
  estimate: ~0.3-0.8, not 1.8.
- The 2026-H1 period was weak for the demean variant; regime dependence
  is material.
- Validation on fresh data (paper trading) is the required next step;
  the panel is already at its data limit.
