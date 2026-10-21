"""Full pipeline prediction-blender."""
import os, sys, json, time
import numpy as np
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import data, factors, ic_screen, model, backtest

BASE = dict(
    predict_horizon=10, return_horizon_fwd=10,
    rebalance_freq=10, refit_freq=10, train_window=120,
    n_long=10, n_short=10,
    weighting="mean_var", opt_lambda_risk=0.5,
    position_cap_pct=0.20, gross_leverage=1.6, max_gross_leverage=1.6,
    vol_target_active=False,
    cost_bps_one_side=3.8, cost_round_trip_bps=7.6, slippage_bps=1.0,
    use_call_rate_financing=True, long_financing_apply=True,
    short_rebate_paid_bps=150.0, short_borrow_fee_etb_bps=25.0,
    long_financing_spread_bps=50.0,
    use_extra_factors=True, use_ohlc_factors=True,
    use_interaction_features=False,
    gbrt_label_transform="zscore", gbrt_label_residual="demean",
    gbrt_label_winsorize=0.01, gbrt_pred_clip=4.0, gbrt_pred_smooth=0.5,
    diag_window_sweep=(100, 120, 140), diag_regime_split=True,
    out_dir="tools/quant/ls/results",
    plot=False, verbose=False, save_intermediate=False,
)

GBRT_CFG = dict(
    model_method="gbrt", gbrt_max_depth=2, gbrt_n_estimators=200,
    gbrt_learning_rate=0.05, gbrt_min_samples_leaf=20, gbrt_max_features="sqrt",
    bypass_ic_screen=False, icir_threshold=0.08, ic_bonferroni=True,
    ic_mean_threshold=0.02, use_extra_factors=False, use_ohlc_factors=False,
    refit_freq=5,
)

RF_CFG = dict(
    model_method="rf", rf_max_depth=8, rf_n_estimators=500,
    rf_min_samples_leaf=15, rf_max_features="sqrt",
    bypass_ic_screen=True, refit_freq=10,
)

def run_model(panel, cfg):
    prices = panel["prices"]
    processed, stacked, factor_names = factors.all_factors(panel, cfg)
    if getattr(cfg, "use_extra_factors", True):
        extra_raw = factors.compute_extra_raw_factors(panel, cfg)
        extra_processed = factors.process_cross_section(extra_raw, panel, cfg)
        processed.update(extra_processed)
    if getattr(cfg, "use_ohlc_factors", False):
        ohlc_raw = factors.compute_ohlc_factors(panel, cfg)
        ohlc_processed = factors.process_cross_section(ohlc_raw, panel, cfg)
        processed.update(ohlc_processed)
    factor_names = list(processed.keys())
    fwd = ic_screen.forward_returns(prices, cfg.return_horizon_fwd)
    ic_df = ic_screen.compute_all_ic(processed, fwd, cfg)
    if getattr(cfg, "bypass_ic_screen", False):
        kept = list(factor_names)
        _, stats, _ = ic_screen.screen_factors(ic_df, cfg, factor_names)
        sign_flips = {}
    else:
        kept, stats, _ = ic_screen.screen_factors(ic_df, cfg, factor_names)
        sign_flips = {f: s.get("sign_flip", False) for f, s in stats.items()}
    if not kept: kept = factor_names[:5]
    out = model.roll_forward_dispatch(processed, panel, cfg, kept_factors=kept, sign_flips=sign_flips)
    return out["predictions"], kept

def run_blended(alpha=0.5):
    gbrt_full = dict(BASE, name="blend_gbrt", **GBRT_CFG)
    rf_full = dict(BASE, name="blend_rf", **RF_CFG)
    gbrt_cfg = Config.from_dict(gbrt_full)
    rf_cfg = Config.from_dict(rf_full)
    panel = data.load_panel(gbrt_cfg)
    t0 = time.time()
    print("Training GBRT...", flush=True)
    gbrt_pred, kept_g = run_model(panel, gbrt_cfg)
    print(f"  GBRT: {len(kept_g)} factors, {gbrt_pred.notna().any(axis=1).sum()} pred dates", flush=True)
    print("Training RF...", flush=True)
    rf_pred, kept_r = run_model(panel, rf_cfg)
    print(f"  RF: {len(kept_r)} factors, {rf_pred.notna().any(axis=1).sum()} pred dates", flush=True)
    blended = alpha * gbrt_pred + (1 - alpha) * rf_pred
    bt_full = dict(BASE, name=f"blend_full_a{alpha:.1f}",
        out_dir=f"tools/quant/ls/results/blend_full_a{alpha:.1f}",
        plot=False, verbose=False, save_intermediate=True)
    bt_cfg = Config.from_dict(bt_full)
    print("Backtesting...", flush=True)
    result = backtest.run_backtest(panel, blended, bt_cfg)
    metrics = backtest.compute_metrics(result, bt_cfg, panel["prices"])
    dt = time.time() - t0
    print(f"Done in {dt:.0f}s", flush=True)
    for k in ["sharpe","annual_return","annual_volatility","max_drawdown","annual_turnover","sortino"]:
        v = metrics.get(k, 0)
        print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
    return metrics

if __name__ == "__main__":
    for alpha in [0.4, 0.5, 0.6]:
        print(f"\nBLEND alpha={alpha}", flush=True)
        run_blended(alpha)
        print()
