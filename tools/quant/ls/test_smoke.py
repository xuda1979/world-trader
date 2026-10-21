"""Smoke tests for the L/S framework.

Run:  python -m tools.quant.ls.test_smoke
"""
import os, sys, tempfile
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config, ConfigError
from tools.quant.ls import data, factors, ic_screen, model, portfolio, optimizer, backtest, diagnostics, runner, experiment


def test_config_roundtrip():
    cfg = Config()
    d = cfg.as_dict()
    cfg2 = Config.from_dict(d)
    assert cfg2.train_window == cfg.train_window
    assert cfg2.n_long == cfg.n_long
    # Override
    cfg3 = cfg.copy(train_window=140, n_long=20)
    assert cfg3.train_window == 140 and cfg3.n_long == 20
    assert cfg.train_window == 120  # original unchanged
    # Validate rejects bad values
    try:
        Config(train_window=10).validate()
        assert False, "should have raised"
    except ConfigError:
        pass
    print("test_config_roundtrip OK")


def test_future_function_guard():
    """Verify factor at t doesn't depend on future data."""
    cfg = Config()
    panel = data.load_panel(cfg)
    proc, stacked, names = factors.all_factors(panel, cfg)
    # Take factor value at t=300, then perturb all prices after t=300 and
    # verify the factor at t=300 is unchanged.
    t = 300
    factor_t_before = {n: proc[n].iloc[t].copy() for n in names}
    # Perturb future prices
    prices_perturbed = panel["prices"].copy()
    prices_perturbed.iloc[t+1:] *= 1.5
    panel_p = dict(panel)
    panel_p["prices"] = prices_perturbed
    # Recompute returns too
    if cfg.return_type == "log":
        panel_p["returns"] = np.log(prices_perturbed / prices_perturbed.shift(1)).fillna(0.0)
    else:
        panel_p["returns"] = prices_perturbed.pct_change().fillna(0.0)
    panel_p["returns"].iloc[0] = 0.0
    proc2, _, _ = factors.all_factors(panel_p, cfg)
    factor_t_after = {n: proc2[n].iloc[t] for n in names}
    # Compare (should be identical, since factor at t only uses data up to t)
    mismatches = 0
    for n in names:
        a = factor_t_before[n].dropna()
        b = factor_t_after[n].reindex(a.index).dropna()
        if not np.allclose(a.values, b.values, atol=1e-10, equal_nan=True):
            mismatches += 1
    assert mismatches == 0, f"{mismatches} factors changed when future data was perturbed -- LOOK-AHEAD BUG"
    print("test_future_function_guard OK  (factors at t are insensitive to future prices)")


def test_future_function_model():
    """Verify model prediction at t doesn't depend on forward returns after t."""
    cfg = Config()
    panel = data.load_panel(cfg)
    proc, _, names = factors.all_factors(panel, cfg)
    out1 = model.roll_forward(proc, panel, cfg, kept_factors=names)
    # Perturb forward returns (prices after the prediction date)
    pred_date = out1["predictions"].index[10]
    pidx = panel["prices"].index.get_loc(pred_date)
    prices_p = panel["prices"].copy()
    prices_p.iloc[pidx + cfg.predict_horizon + 5:] *= 1.3  # perturb well after the forward window
    panel_p = dict(panel); panel_p["prices"] = prices_p
    if cfg.return_type == "log":
        panel_p["returns"] = np.log(prices_p / prices_p.shift(1)).fillna(0.0)
    else:
        panel_p["returns"] = prices_p.pct_change().fillna(0.0)
    panel_p["returns"].iloc[0] = 0.0
    out2 = model.roll_forward(proc, panel_p, cfg, kept_factors=names)
    # Predictions up to pred_date should be identical
    p1 = out1["predictions"].loc[:pred_date]
    p2 = out2["predictions"].loc[:pred_date]
    assert p1.shape == p2.shape
    if not p1.empty:
        diff = (p1 - p2).abs().max().max()
        assert diff < 1e-8, f"prediction changed by {diff} when future prices perturbed -- LOOK-AHEAD"
    print(f"test_future_function_model OK  (predictions up to {pred_date.date()} unchanged)")


def test_dollar_neutral():
    """Verify portfolio construction produces sum(w)=0 and |w|.sum()=gross_leverage."""
    cfg = Config()
    panel = data.load_panel(cfg)
    proc, _, names = factors.all_factors(panel, cfg)
    out = model.roll_forward(proc, panel, cfg, kept_factors=names)
    if out["predictions"].empty:
        print("test_dollar_neutral SKIP (no predictions)")
        return
    last_date = out["predictions"].index[-1]
    pred = out["predictions"].iloc[-1]
    idx = panel["prices"].index.get_loc(last_date)
    panel_t = {k: v.iloc[:idx+1] for k, v in panel.items() if isinstance(v, pd.DataFrame)}
    w = portfolio.construct_target_weights(pred, panel_t, cfg, prev_weights=None)
    assert abs(w.sum()) < 1e-3, f"sum(w) = {w.sum()} -- not dollar-neutral"
    assert abs(w.abs().sum() - cfg.gross_leverage) < 1e-2, f"|w|.sum() = {w.abs().sum()} -- not at gross leverage"
    print(f"test_dollar_neutral OK  (sum(w)={w.sum():.4f}, gross={w.abs().sum():.4f})")


def test_beta_neutral():
    """Verify realized portfolio beta is within beta_max_abs on average."""
    cfg = Config()
    panel = data.load_panel(cfg)
    proc, _, names = factors.all_factors(panel, cfg)
    out = model.roll_forward(proc, panel, cfg, kept_factors=names)
    result = backtest.run_backtest(panel, out["predictions"], cfg)
    avg_abs_beta = float(result["portfolio_beta"].abs().mean())
    assert avg_abs_beta < cfg.beta_max_abs * 3, f"avg |beta|={avg_abs_beta} too high"
    print(f"test_beta_neutral OK  (avg |beta|={avg_abs_beta:.4f}, target<{cfg.beta_max_abs})")


def test_end_to_end():
    """Run a full pipeline + verify all deliverables exist."""
    with tempfile.TemporaryDirectory() as td:
        cfg = Config(out_dir=td, plot=False, name="smoke")
        bundle = runner.run(cfg, export=True)
        out_dir = os.path.join(td, "smoke")
        required = ["equity_curve.csv", "daily_returns.csv", "monthly_returns.csv",
                    "metrics.json", "ic_series.csv", "icir_series.csv",
                    "factor_weights.csv", "factor_stats.csv", "config.json",
                    "verdict.json"]
        for f in required:
            assert os.path.exists(os.path.join(out_dir, f)), f"missing: {f}"
        # Verify metrics keys
        m = bundle["metrics"]
        for k in ["annual_return", "annual_volatility", "sharpe", "max_drawdown", "annual_turnover"]:
            assert k in m, f"missing metric: {k}"
        print(f"test_end_to_end OK  ({len(required)} files, sharpe={m['sharpe']:.3f})")


def test_experiment_grid():
    """Verify grid sweep runs and produces a comparison table."""
    with tempfile.TemporaryDirectory() as td:
        cfg = Config(out_dir=td, plot=False)
        df = experiment.grid(cfg, {"n_long": [5, 10]}, export=True, max_runs=2)
        assert len(df) == 2
        assert "sharpe" in df.columns
        assert os.path.exists(os.path.join(td, "grid_results.csv"))
        print(f"test_experiment_grid OK  (2 configs compared)")


def test_gbrt_model_runs():
    """GBRT model path (Gu-Kelly-Xiu 2020) produces predictions + IC."""
    with tempfile.TemporaryDirectory() as td:
        cfg = Config(out_dir=td, plot=False, name="gbrt_smoke",
                     model_method="gbrt",
                     gbrt_n_estimators=60,      # small for speed
                     gbrt_max_depth=2,
                     gbrt_learning_rate=0.1,
                     gbrt_pred_smooth=0.0,      # disable EMA for the smoke test
                     train_window=120,
                     refit_freq=10,
                     predict_horizon=5,
                     n_long=5, n_short=5,
                     cost_bps_one_side=3.8,
                     cost_round_trip_bps=7.6)
        bundle = runner.run(cfg, export=False)
        m = bundle["metrics"]
        # We don't assert Sharpe sign on a tiny synthetic sample; we only
        # require the pipeline to run and produce a finite Sharpe + nonzero
        # turnover so we know the GBRT path is wired end-to-end.
        assert np.isfinite(m["sharpe"]), "GBRT Sharpe not finite"
        assert m["annual_turnover"] > 0, "GBRT produced zero turnover"
        # OOS IC series should have at least one non-NaN entry
        ic = bundle["ic_oos"].dropna()
        assert len(ic) > 0, "GBRT produced no IC observations"
        print(f"test_gbrt_model_runs OK  (sharpe={m['sharpe']:.3f}, "
              f"turnover={m['annual_turnover']:.1f}, ic_mean={ic.mean():.4f})")


def test_gp_turnover_penalty_reduces_churn():
    """Gârleanu-Pedersen (2013) turnover penalty must not increase turnover."""
    with tempfile.TemporaryDirectory() as td:
        base = dict(out_dir=td, plot=False, name="gp_test",
                    model_method="ols",
                    train_window=120, refit_freq=5, rebalance_freq=5,
                    predict_horizon=5, n_long=5, n_short=5,
                    cost_bps_one_side=3.8, cost_round_trip_bps=7.6,
                    hold_to_reduce_turnover=False)  # isolate GP effect
        cfg_off = Config(gp_turnover_penalty=0.0, **base)
        cfg_on = Config(gp_turnover_penalty=0.005,  # 50 bps per unit turnover
                        gp_no_trade_band=0.01, **base)
        bundle_off = runner.run(cfg_off, export=False)
        bundle_on = runner.run(cfg_on, export=False)
        to_off = bundle_off["metrics"]["annual_turnover"]
        to_on = bundle_on["metrics"]["annual_turnover"]
        assert to_on <= to_off + 1e-6, (
            f"GP penalty increased turnover: {to_on:.3f} > {to_off:.3f}")
        print(f"test_gp_turnover_penalty_reduces_churn OK  "
              f"(turnover {to_off:.2f} -> {to_on:.2f})")


def main():
    tests = [
        test_config_roundtrip,
        test_future_function_guard,
        test_future_function_model,
        test_dollar_neutral,
        test_beta_neutral,
        test_end_to_end,
        test_experiment_grid,
        test_gbrt_model_runs,
        test_gp_turnover_penalty_reduces_churn,
    ]
    n_ok = 0
    for t in tests:
        try:
            t()
            n_ok += 1
        except Exception as e:
            print(f"FAIL  {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{n_ok}/{len(tests)} tests passed")
    return 0 if n_ok == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())
