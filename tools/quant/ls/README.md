# Long/Short Market-Neutral Backtesting Framework

A hyperparameter-driven framework for building, backtesting, and optimizing
long/short market-neutral equity portfolios with strict future-function
guards and built-in overfitting diagnostics.

## Quick start

```bash
# Baseline run (uses all cached Polygon CSVs in tools/quant/data/polygon/)
python -m tools.quant.ls.runner

# Override any hyperparameters
python -m tools.quant.ls.runner --set train_window=140 n_long=20 weighting=mean_var

# Use a named preset
python -m tools.quant.ls.runner --preset loose

# Sweep a hyperparameter grid
python -m tools.quant.ls.runner --sweep train_window=100,120,140 n_long=5,10,15
```

Python API:

```python
from tools.quant.ls import runner, experiment
from tools.quant.ls.config import Config

# Single experiment
cfg = Config(train_window=140, n_long=20, name="my_exp")
bundle = runner.run(cfg)

# A/B compare
df = experiment.compare_configs([
    ("baseline", {}),
    ("longer_train", {"train_window": 140}),
    ("more_names", {"n_long": 20, "n_short": 20}),
])

# Grid sweep
df = experiment.grid(Config(), {
    "train_window": [100, 120, 140],
    "n_long": [5, 10, 15],
    "weighting": ["equal", "risk_parity", "mean_var"],
})

# Random search (20 configs)
df = experiment.random_search(Config(), {
    "train_window": [80, 100, 120, 140, 160],
    "n_long": [5, 8, 10, 12, 15],
    "icir_threshold": [0.10, 0.20, 0.30, 0.40],
    "weighting": ["equal", "risk_parity", "mean_var", "shrunk"],
    "model_weight_smooth": [0.0, 0.3, 0.5],
}, n=20, seed=42)

# Pick the best
best = experiment.top_configs(df, metric="sharpe", k=3)
```

## Architecture

```
tools/quant/ls/
├── config.py         # Config dataclass — every tunable knob lives here (88 fields)
├── data.py           # Load + align equity panel + macro (VIX from FRED)
├── factors.py        # 14 alpha factors (momentum, reversal, vol, value-proxy, liquidity)
├── ic_screen.py      # Rolling RankIC + ICIR + Bonferroni gate
├── model.py          # Rolling OLS / ridge fit + OOS prediction (future-function safe)
├── optimizer.py      # Mean-variance / risk-parity / equal-weight with scipy SLSQP
├── portfolio.py      # Long/short sleeve selection + turnover control
├── backtest.py       # Event-driven, T+1 execution, VIX de-risking, beta guard
├── diagnostics.py    # Regime split + window sweep + weight-stability + ICIR decay
├── experiment.py     # Grid / random-search harness for fast A/B tuning
└── runner.py         # End-to-end orchestrator + CLI + artifact export
```

### Pipeline (runner.run)

1. **Load panel** — auto-discover CSVs, align on common trading days, ffill
   per-ticker (no future leak), load VIX from FRED.
2. **Compute factors** — 14 factors, all cross-sectionally winsorized (1/99
   pct), market-neutralized, z-scored.  Every factor uses `shift` / rolling
   with `min_periods`, so the value at time t depends only on data up to t.
3. **IC / ICIR screen** — rolling Spearman RankIC vs forward h-day returns.
   Factor is *kept* if `|ICIR| >= icir_threshold` AND `|mean IC| >=
   ic_mean_threshold` AND Bonferroni-adjusted t-test passes.  Sign-flip if
   IC is consistently negative.
4. **Rolling model** — every `refit_freq` days, fit OLS (or ridge) on the
   `[t-train_window-h, t-h]` window (the `-h` shift is the future-function
   guard: the forward return at the last training row is fully realized by
   time t).  Predict cross-sectional expected returns at t.
5. **Backtest** — every `rebalance_freq` days, construct target weights
   (long top n_long, short bottom n_short, beta-neutral, dollar-neutral,
   gross = `gross_leverage`).  T+1 execution.  VIX >= 90th pctile triggers
   50% gross cut.  Daily loss > 3% triggers next-period derisk.
6. **Diagnostics** — regime split (bull/sideways/bear Sharpe), window sweep
   (100/120/140), factor-weight stability (std/|mean|), ICIR decay.
7. **Export** — equity curve, daily/monthly returns, IC series, ICIR
   series, factor weights, factor stats, metrics.json, diagnostics CSVs,
   PNG plots.

## Future-function guard

Every stage is built to avoid look-ahead:

- **Data**: per-ticker `ffill(limit_area="inside")` — never fills leading
  NaNs (no data yet) and only uses each ticker's own past.
- **Factors**: momentum uses `shift(skip)`, vol uses `shift(skip).rolling()`,
  so the value at t depends only on `[t-window-skip, t-skip-1]`.
- **Model**: training window ends at `t-h` so forward returns are realized
  before the prediction date t.  `data.assert_no_future_function` is
  available as a belt-and-suspenders check.
- **Backtest**: predictions are forward-filled to daily, but rebalance
  decisions at t use `panel.iloc[:t+1]` (sliced).  T+1 execution means
  new weights earn returns starting at t+1.

If a leak is detected, `FutureFunctionError` is raised immediately.

## Hyperparameter reference (`Config`)

### Data / universe
| field | default | description |
|---|---|---|
| `data_dir` | `tools/quant/data/polygon` | CSV directory |
| `universe` | `()` | () = auto-discover |
| `universe_min_len` | 200 | drop tickers with fewer bars |
| `universe_min_avg_vol` | 5e5 | drop illiquid names |
| `benchmark` | `SPY` | for beta / regime detection |
| `use_macro` | True | load VIX from FRED |
| `min_common_history` | 200 | require this many aligned bars |

### Factors
| field | default | description |
|---|---|---|
| `factor_winsorize_p` | 0.01 | clip at 1/99 pct |
| `factor_neutralize` | `("market",)` | cross-sectional demean |
| `mom_1m`, `mom_3m`, `mom_6m`, `mom_12m` | 21/63/126/252 | momentum windows |
| `mom_skip_recent` | 5 | skip last N days (reversal contamination) |
| `reversal_1w`, `reversal_3w` | 5/15 | short-term reversal |
| `vol_window` | 60 | realized vol window |
| `vol_skip_recent` | 5 | exclude last N days from vol calc |
| `ma_dev_50`, `ma_dev_200` | 50/200 | price/MA deviation |
| `high_lookback` | 252 | 52-week-high distance |

### IC / ICIR screen
| field | default | description |
|---|---|---|
| `ic_window` | 120 | rolling ICIR window |
| `ic_min_obs` | 60 | min IC obs to judge |
| `icir_threshold` | 0.30 | keep if \|ICIR\| >= this |
| `ic_mean_threshold` | 0.02 | AND \|mean IC\| >= this |
| `ic_bonferroni` | True | apply Bonferroni on per-factor t-tests |
| `ic_alpha_familywise` | 0.05 | family-wise alpha |
| `ic_sign_check` | True | flip sign if IC consistently negative |

### Model
| field | default | description |
|---|---|---|
| `train_window` | 120 | rolling train window (days) |
| `refit_freq` | 5 | refit every N days |
| `predict_horizon` | 5 | forward return horizon |
| `model_ols_ridge_lambda` | 0.0 | 0=OLS, >0=ridge |
| `model_intercept` | True | fit intercept |
| `model_min_train_obs` | 80 | skip refit if fewer obs |
| `model_min_factors` | 2 | skip if fewer factors survive |
| `model_max_factor_weight` | 5.0 | cap \|standardized coef\| |
| `model_weight_smooth` | 0.3 | EMA smoothing of factor weights |

### Portfolio construction
| field | default | description |
|---|---|---|
| `n_long`, `n_short` | 10/10 | number of positions per side |
| `quantile_top_pct`, `quantile_bot_pct` | 0.03 | alternative to n_long/n_short |
| `use_fixed_n` | True | True=n_long/n_short, False=pct |
| `weighting` | `risk_parity` | `equal`/`risk_parity`/`mean_var`/`shrunk` |
| `long_short_balance` | True | dollar-neutral |
| `beta_target` | 0.0 | portfolio beta target |
| `beta_max_abs` | 0.05 | \|beta\| <= this (rule VIII.1) |
| `position_cap_pct` | 0.20 | max weight per name |
| `gross_leverage` | 1.0 | \|long\|+\|short\| gross |

### Optimizer
| field | default | description |
|---|---|---|
| `opt_method` | `scipy_slsqp` | `scipy_slsqp`/`closed_form_mv`/`risk_parity` |
| `opt_lambda_risk` | 1.0 | risk aversion for mean-var |
| `opt_max_iter` | 200 | SLSQP max iter |
| `opt_tol` | 1e-7 | SLSQP tolerance |

### Backtest / execution
| field | default | description |
|---|---|---|
| `cost_bps_one_side` | 6.5 | 6.5 bps -> 13 bps round-trip |
| `cost_round_trip_bps` | 13.0 | used for rebalance threshold |
| `slippage_bps` | 0.0 | additional slippage |
| `rebalance_freq` | 5 | rebalance every N days |
| `turnover_threshold_diff` | 0.0013 | rebalance only if pred diff > cost |
| `hold_zone_top_pct`, `hold_zone_bot_pct` | 0.03 | keep if still in top/bottom 3% |
| `t_plus_1` | True | signal T, execute T+1 |
| `initial_capital` | 1,000,000 | starting equity |

### Risk controls (rule VIII)
| field | default | description |
|---|---|---|
| `vix_derisk_pctile` | 0.90 | VIX >= 90th pctile of 20d history |
| `vix_derisk_factor` | 0.5 | cut gross by this |
| `max_daily_loss_pct` | 0.03 | 3% daily loss -> derisk |
| `max_daily_loss_factor` | 0.5 | cut gross by this |

### Diagnostics (rule X)
| field | default | description |
|---|---|---|
| `diag_regime_split` | True | bull/sideways/bear Sharpe |
| `diag_window_sweep` | `(100,120,140)` | re-run with these train_windows |
| `diag_weight_vol_flag` | True | flag if factor weight std/|mean| > 2 |

## Presets

| name | description |
|---|---|
| `baseline` | Config defaults |
| `strict` | High ICIR threshold (0.40), 8+8 names, mean_var weighting |
| `loose` | Low threshold (0.10), 15+15 names, no Bonferroni |
| `fast` | Short windows (80d train, 10d refreq) for quick iteration |
| `robust` | Longer train (140), shrunk cov, higher risk aversion, tighter caps |

## Outputs (per experiment, under `out_dir/<name>/`)

| file | rule |
|---|---|
| `equity_curve.csv` | IX.1 |
| `daily_returns.csv` | IX.1 |
| `monthly_returns.csv` | IX.1 |
| `metrics.json` | IX.2 (Sharpe, vol, max DD, turnover) |
| `ic_series.csv` | IX.3 (RankIC time series) |
| `icir_series.csv` | IX.3 (rolling ICIR) |
| `factor_weights.csv` | IX.4 (per-refit factor coefficients) |
| `per_factor_icir.png` | IX.5 (ICIR tracking curves) |
| `predictions.csv` | model output (expected returns) |
| `factor_stats.csv` | XI.1 (ICIR + Bonferroni t-test per factor) |
| `diag_regime.csv` | X.1 (bull/sideways/bear) |
| `diag_window_sweep.csv` | X.2 (100/120/140) |
| `diag_weight_stability.csv` | X.3 (weight std/mean) |
| `diag_icir_decay.csv` | X.1 (first-half vs second-half ICIR) |
| `verdict.json` | X.3 (overfitting assessment) |
| `rolling_icir.png` | IX.3 plot |
| `factor_weights.png` | IX.4 plot |
| `equity_curve.png` | IX.1 plot |
| `config.json` | full config snapshot |

## Adding a new factor

```python
# In factors.py, add to compute_raw_factors:
def _my_factor(prices, window):
    return prices.rolling(window).something()

raw["my_factor"] = _my_factor(prices, cfg.my_window)
```

Then add `my_window: int = 30` to `Config`.  The rest (IC, screening,
model, diagnostics) picks it up automatically.

## Adding a new risk control

```python
# In backtest.py run_backtest, inside the daily loop:
if my_condition:
    risk_scale *= cfg.my_derisk_factor
    risk_events.append({"date": date, "type": "my_rule", ...})
```

Add `my_derisk_factor: float = 0.5` to `Config`.

## Notes on the default run

- Universe: ~80 liquid large-caps (auto-downloaded via Polygon, 2024-07 to
  2026-07, ~500 trading days).
- With strict default ICIR>=0.30, few factors survive; the runner falls
  back to the top-5 by |ICIR| so the pipeline still runs.  Use `--preset
  loose` or lower `icir_threshold` to see more factors pass.
- The default Sharpe is negative on this short sample — that's expected
  for a market-neutral L/S with no surviving factors.  The framework's
  value is in the *infrastructure* (future-function safety, diagnostics,
  hyperparameter sweeps) so you can iterate quickly on factor design.
