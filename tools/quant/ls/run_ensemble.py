"""Strategy ensemble portfolio optimizer.

Takes the successful GBRT strategies from the 8-way comparison and optimizes
allocation ACROSS them at the strategy level.  Each strategy produces a daily
return stream; we treat those streams as the "assets" and solve for ensemble
weights subject to:

  - walk-forward OOS weight selection (no in-sample overfitting of ensemble)
  - dollar-neutral at the strategy level (sum of strategy weights = 1, long-only
    across strategies since each strategy is already a market-neutral L/S book)
  - per-strategy cap (no single strategy > 40% of risk budget)
  - Gârleanu-Pedersen turnover penalty on strategy-weight changes

Three ensemble methods are compared:
  1. equal_weight      -- naive 1/N across successful strategies
  2. sharpe_weighted   -- weight ~ OOS Sharpe (walk-forward 60-day window)
  3. mean_var_oos      -- walk-forward mean-variance on strategy return streams

Run:
    python -m tools.quant.ls.run_ensemble
"""""
from __future__ import annotations
import os, sys, time, json, math
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import numpy as np
import pandas as pd
from tools.quant.ls import Config, runner, optimizer as opt

# ---- successful strategies from the 8-way comparison (Sharpe > 0.5, reasonable DD) ----
# We keep the same BASE config as run_gbrt_compare.py so the ensemble is
# apples-to-apples with the comparison table.
BASE = dict(
    data_dir="tools/quant/data/polygon",
    universe=(),
    benchmark="SPY",
    return_horizon_fwd=5, return_type="log",
    factor_winsorize_p=0.01, factor_neutralize=["market"], factor_zscore=True,
    use_extra_factors=True,
    icir_threshold=0.08, ic_mean_threshold=0.005, ic_sign_check=True,
    train_window=120, refit_freq=5, predict_horizon=5,
    n_long=10, n_short=10, use_fixed_n=True,
    weighting="mean_var", long_short_balance=True,
    beta_check=True, beta_target=0.0, beta_max_abs=0.15,
    position_cap_pct=0.25, vol_target_active=True, vol_target_annual=0.15,
    opt_method="scipy_slsqp", opt_lambda_risk=2.0,
    cost_bps_one_side=3.8, cost_round_trip_bps=7.6, slippage_bps=1.0,
    rebalance_freq=5, turnover_threshold_diff=0.001,
    hold_to_reduce_turnover=True, t_plus_1=True, gross_leverage=1.6,
    initial_capital=1_000_000,
    short_borrow_apply=True, short_borrow_annual_bps=50.0,
    short_borrow_htb_premium_bps=200.0,
    sharpe_gate_enabled=False, diag_regime_split=False,
    save_intermediate=False, plot=False, verbose=False,
)

GBRT_BASE = dict(
    model_method="gbrt",
    gbrt_n_estimators=200, gbrt_max_depth=3, gbrt_learning_rate=0.05,
    gbrt_subsample=1.0, gbrt_min_samples_leaf=20, gbrt_max_features="sqrt",
    gbrt_pred_clip=4.0, gbrt_pred_smooth=0.5,
    gp_turnover_penalty=0.0038, gp_no_trade_band=0.01,
)

STRATEGIES = [
    ("gbrt_raw", dict(model_method="gbrt", gbrt_n_estimators=200,
        gbrt_max_depth=3, gbrt_learning_rate=0.05, gbrt_subsample=1.0,
        gbrt_min_samples_leaf=20, gbrt_max_features="sqrt",
        gbrt_pred_clip=4.0, gbrt_pred_smooth=0.0,
        gp_turnover_penalty=0.0, gp_no_trade_band=0.0)),
    ("gbrt_gp_demean", dict(GBRT_BASE, gbrt_label_residual="demean",
        gbrt_label_winsorize=0.01)),
    ("gbrt_gp_demean_zscore", dict(GBRT_BASE, gbrt_label_residual="demean",
        gbrt_label_transform="zscore", gbrt_label_winsorize=0.01)),
    ("gbrt_gp_demean_huber", dict(GBRT_BASE, gbrt_loss="huber",
        gbrt_alpha=0.9, gbrt_label_residual="demean",
        gbrt_label_winsorize=0.01)),
    ("gbrt_gp_demean_rank", dict(GBRT_BASE, gbrt_label_residual="demean",
        gbrt_label_transform="rank", gbrt_label_winsorize=0.01)),
    ("gbrt_gp", dict(GBRT_BASE)),
]


def collect_strategy_returns():
    out_dir = 'tools/quant/ls/results/ensemble'
    os.makedirs(out_dir, exist_ok=True)
    cfg0 = Config(out_dir=out_dir, name='ensemble', **BASE)
    daily_rets = {}
    metrics = {}
    for name, overrides in STRATEGIES:
        cfg = cfg0.copy(name=name, **overrides)
        print(f'  running {name}...')
        t0 = time.time()
        try:
            bundle = runner.run(cfg, export=False)
            dr = bundle['result']['daily_returns'].dropna()
            daily_rets[name] = dr
            m = bundle['metrics']
            metrics[name] = m
            print(f'    {name}: Sharpe={m["sharpe"]:.3f}  ann_ret={m["annual_return"]:.4f}  bars={len(dr)}  ({time.time()-t0:.1f}s)')
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f'    {name}: ERROR {e}')
    df = pd.DataFrame(daily_rets)
    return df, metrics

# ---- ensemble weight schemes ----
def equal_weight(rets: pd.DataFrame) -> pd.Series:
    n = rets.shape[1]
    return pd.Series(1.0/n, index=rets.columns, name='equal_weight')

def sharpe_weighted(rets: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """Walk-forward Sharpe-weighted: at each date t, weight strategies by
    their trailing-window Sharpe (realised OOS, no lookahead)."""
    ann = 252.0
    sharpes = (rets.rolling(window).mean() / rets.rolling(window).std()) * math.sqrt(ann)
    sharpes = sharpes.clip(lower=0.0)  # never allocate to negative-Sharpe strategies
    # Normalise rows to sum to 1
    row_sum = sharpes.sum(axis=1).replace(0, np.nan)
    weights = sharpes.div(row_sum, axis=0).fillna(0.0)
    return weights

def mean_var_oos(rets: pd.DataFrame, window: int = 60, lam: float = 2.0,
                 cap: float = 0.40) -> pd.DataFrame:
    """Walk-forward mean-variance on strategy return streams.

    At each date t, use the trailing  days of strategy returns to
    estimate mu and Sigma, then solve the long-only weight vector subject to
    sum(w)=1 and w_i <= cap.  No lookahead -- only past data is used.
    """
    from scipy.optimize import minimize
    cols = rets.columns.tolist()
    n = len(cols)
    weights_mat = np.full((len(rets), n), np.nan)
    for i in range(len(rets)):
        if i < window:
            continue
        win = rets.iloc[i-window:i].dropna(axis=1, how='any')
        if win.shape[1] < 2:
            continue
        mu = win.mean().values
        Sigma = win.cov().values
        Sigma = (Sigma + Sigma.T) / 2.0
        # Regularise Sigma
        Sigma += np.eye(len(mu)) * 1e-6
        w0 = np.ones(len(mu)) / len(mu)
        bounds = [(0.0, cap)] * len(mu)
        cons = [{'type': 'eq', 'fun': lambda w: w.sum() - 1.0}]
        obj = lambda w: -float(w @ mu) + 0.5 * lam * float(w @ Sigma @ w)
        try:
            res = minimize(obj, w0, method='SLSQP', bounds=bounds, constraints=cons,
                           options={'maxiter': 200, 'ftol': 1e-7})
            w = res.x
        except Exception:
            w = w0
        # Map back to full column index
        for j, col in enumerate(win.columns):
            weights_mat[i, cols.index(col)] = w[j]
    return pd.DataFrame(weights_mat, index=rets.index, columns=cols)


def apply_ensemble_oos(rets: pd.DataFrame, weights: pd.DataFrame, t_cost: float = 0.0) -> dict:
    """Apply walk-forward strategy weights to produce the ensemble equity curve.

    CRITICAL OOS GUARD:
      The weight at date t is decided using ONLY data up to t-1 (the weights
      frame is shifted by 1 day before it touches returns).  So the ensemble
      return on day t = sum_i w_{i,t-1} * r_{i,t}.  This guarantees we never
      use same-day returns to set the weight that earns those returns.

    t_cost: turnover cost on strategy-weight changes (fraction per unit).
            Set to 0.0 for the base case; strategy-level rebalancing is cheap
            because we're trading liquid strategy books, not individual names.
    """
    # Align weights to returns index
    w = weights.reindex(rets.index).ffill().fillna(0.0)
    # SHIFT WEIGHTS BY 1 DAY -- this is the OOS guard
    w_shifted = w.shift(1).fillna(0.0)
    # Daily ensemble return
    daily_ens = (w_shifted * rets).sum(axis=1)
    # Turnover cost on weight changes
    if t_cost > 0:
        delta = w_shifted.diff().abs().sum(axis=1).fillna(0.0)
        daily_ens = daily_ens - delta * t_cost
    # Equity curve
    equity = (1.0 + daily_ens).cumprod() * 1_000_000
    # Metrics
    ann = 252.0
    mu = daily_ens.mean() * ann
    sd = daily_ens.std() * math.sqrt(ann)
    sharpe = mu / sd if sd > 0 else 0.0
    max_dd = ((equity / equity.cummax()) - 1.0).min()
    return {
        'daily_returns': daily_ens, 'equity_curve': equity,
        'sharpe': sharpe, 'annual_return': mu, 'annual_vol': sd,
        'max_drawdown': float(max_dd),
        'final_equity': float(equity.iloc[-1]),
        'n_days': len(daily_ens),
    }


def main():
    out_dir = 'tools/quant/ls/results/ensemble'
    os.makedirs(out_dir, exist_ok=True)
    print('=== Step 1: collect strategy daily returns (OOS) ===')
    rets, metrics = collect_strategy_returns()
    if rets.empty or rets.shape[1] < 2:
        print('ERROR: not enough strategies returned data')
        return 1
    # Align on common dates, drop early NaNs
    rets = rets.dropna(how='all').fillna(0.0)
    print(f'  combined return matrix: {rets.shape}  range {rets.index[0].date()}..{rets.index[-1].date()}')
    # Per-strategy summary
    print()
    print('=== Per-strategy OOS metrics ===')
    print(f"{'strategy':<28} {'sharpe':>7} {'ann_ret':>8} {'ann_vol':>8} {'max_dd':>8} {'final_eq':>10}")
    for col in rets.columns:
        m = metrics.get(col, {})
        print(f'{col:<28} {m.get("sharpe",0):>7.3f} {m.get("annual_return",0):>8.4f} '
              f'{m.get("annual_volatility",0):>8.4f} {m.get("max_drawdown",0):>8.4f} '
              f'{m.get("final_equity",0):>10.0f}')
    # Save raw returns
    rets.to_csv(os.path.join(out_dir, 'strategy_daily_returns.csv'))

    print()
    print('=== Step 2: build ensemble portfolios (walk-forward OOS) ===')
    # 1) Equal weight
    w_eq = equal_weight(rets)
    w_eq_mat = pd.DataFrame([w_eq]*len(rets), index=rets.index)
    r_eq = apply_ensemble_oos(rets, w_eq_mat)
    # 2) Sharpe-weighted (60-day walk-forward)
    w_sharpe = sharpe_weighted(rets, window=60)
    r_sharpe = apply_ensemble_oos(rets, w_sharpe)
    # 3) Mean-variance OOS (60-day walk-forward)
    w_mv = mean_var_oos(rets, window=60, lam=2.0, cap=0.40)
    r_mv = apply_ensemble_oos(rets, w_mv)
    # 4) Mean-variance OOS + GP turnover penalty at strategy level
    # (reuse mean_var weights; the GP cost is applied inside apply_ensemble_oos)
    r_mv_gp = apply_ensemble_oos(rets, w_mv, t_cost=0.00038)
    rows = []
    for name, r in [("equal_weight", r_eq), ("sharpe_weighted", r_sharpe),
                    ("mean_var_oos", r_mv), ("mean_var_oos_gp", r_mv_gp)]:
        rows.append({"method": name, "sharpe": round(r["sharpe"], 3),
                     "annual_return": round(r["annual_return"], 4),
                     "annual_vol": round(r["annual_vol"], 4),
                     "max_dd": round(r["max_drawdown"], 4),
                     "final_equity": round(r["final_equity"], 0),
                     "n_days": r["n_days"]})
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "ensemble_results.csv"), index=False)
    print()
    print('=== Ensemble OOS results ===')
    print(df.to_string(index=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
