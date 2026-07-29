# L/S Market-Neutral Strategy — Research Log

## Current Date
2026-07-29

## Research Directive
Build a retail-realistic long/short market-neutral strategy aligned with:
1. **Gu-Kelly-Xiu (2020, RFS)** — GBRT as the benchmark ML model for cross-sectional return prediction
2. **Gârleanu-Pedersen (2013, JF)** — L1 turnover penalty in the portfolio optimizer
3. **Novy-Marx & Velikov (2016)** — 20-day prediction horizon is optimal at 7.6bps round-trip costs
4. **Freyberger (2020)** — residualize returns against common factors before fitting trees
5. **Constraint**: 3.8bps one-side commission, call-rate short financing, 84-ticker universe, 501 trading days

## Data
- **Source**: Polygon daily OHLCV
- **Universe**: 84 liquid US large-caps (AAPL, MSFT, NVDA, ... SPY, QQQ, XLF as benchmarks)
- **Date range**: 2024-07-22 → 2026-07-23 (501 trading days, ~2 years)
- **Short history**: Only 2 years — a fundamental statistical constraint

## Current State (as of 2026-07-29)

### Baseline metrics (realistic costs)
| Config | Sharpe | Ann Return | Max DD | Turnover | Verdict |
|---|---|---|---|---|---|
| BEST_rev3_n13_vt20_38bps (no borrow) | 1.61 | 28.7% | -10.6% | 41.8 | likely_overfit |
| AUDIT_rev3_n13_vt20_with_borrow | 0.53 | 7.1% | -12.6% | 34.2 | likely_overfit |
| AUDIT_lev16_rev3_n13_with_borrow | 0.29 | 6.9% | -6.4% | 15.8 | likely_overfit |
| probe_baseline (icir, lev1.6, call-rate) | 0.40 | 3.2% | -8.3% | 12.1 | watch |

### Key finding
The "1.61 Sharpe" in BEST was an artifact of **ignoring short-borrow costs**. With realistic call-rate financing (150bps rebate forgone + 25bps ETB borrow fee), Sharpe drops to 0.29-0.53. This confirms the user's concern: the strategy must survive realistic costs.

### Overfitting diagnosis
1. **Window sensitivity**: Sharpe varies from +0.40 to -0.49 across train_window ∈ {100,120,140}. The strategy is NOT robust to train window choice.
2. **Factor decay**: 5 of 23 factors show ICIR decay (vol_60d, skew_60d, downside_skew, range_vol_60d, resid_mom_6m).
3. **Regime concentration**: Returns come almost entirely from the "sideways" regime (Sharpe 1.72). Bull regime Sharpe is -0.82.
4. **Only 5 factors pass ICIR screen**: resid_mom_6m, mom_12_1m, range_vol_60d, mom_12m, rank_mom_12m.

### Bug fixed today
- `diagnostics.py` window_sweep was using OLS `roll_forward` even when the main run used ICIR/GBRT. Fixed to use `roll_forward_dispatch` so the sweep is apples-to-apples.

## Literature-Based Hypotheses to Test

### H1: Novy-Marx 20-day horizon is optimal at 7.6bps RT
- Current default: predict_horizon=3, rebalance_freq=3
- Test: predict_horizon ∈ {3, 5, 10, 20, 21}, rebalance_freq ∈ {3, 5, 10, 20}
- Expectation: 20-day horizon should give best net Sharpe after costs

### H2: GP turnover penalty calibrated to actual costs
- Cost = 3.8bps one-side + 1bps slippage = 4.8bps per side
- GP penalty = 4.8e-4 per unit turnover
- Test: gp_turnover_penalty ∈ {0, 0.00038, 0.00048, 0.001, 0.0038}
- Test: gp_no_trade_band ∈ {0, 0.005, 0.01, 0.02}

### H3: GBRT with Freyberger residualization
- Test: gbrt_label_residual ∈ {none, demean, pca}
- Test: gbrt_label_transform ∈ {raw, zscore, rank}
- Test: gbrt_pred_smooth ∈ {0, 0.3, 0.5, 0.7} (EMA smoothing)

### H4: Equal-weight beats mean-variance in small samples
- DeMiguel-Garlappi-Uppal (2009): 1/N is robust when estimation error is large
- Test: weighting ∈ {equal, risk_parity, mean_var, shrunk}

### H5: Train window robustness
- With 501 days, train_window=120 uses 24% of data for training
- Test: train_window ∈ {60, 80, 100, 120, 140, 160, 200}
- Select configs that are robust across ±20% window variations

## Next Steps
1. Run the GBRT comparison sweep (in progress)
2. Run horizon sweep (H1)
3. Run GP penalty sweep (H2)
4. Run GBRT label/smoothing sweep (H3)
5. Run weighting sweep (H4)
6. Run train window robustness sweep (H5)
7. Select configs that pass ALL robustness gates
8. Document final strategy

## Files Modified
- `tools/quant/ls/diagnostics.py` — fixed window_sweep to use dispatched model method
- (prior uncommitted) `config.py` — added long_financing fields
- (prior uncommitted) `backtest.py` — added financing cost tracking
- (prior uncommitted) `model.py` — added label winsorization (look-ahead-safe)
