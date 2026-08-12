#!/usr/bin/env python3
"""Regime-conditional L/S strategy v4: high-frequency rebalance for VIX responsiveness.

Key insight from v3: with rebalance_freq=20, only 1/12 rebalance dates
coincide with VIX > 25. The strategy can't react to high-vol regimes.

V4 fixes this by:
  1. Using rebalance_freq=5 (weekly) so the strategy reacts to VIX changes
  2. Computing daily reversal signals (not just at rebalance dates)
  3. Blending champion GBRT predictions with reversal signals when VIX > 25
  4. Testing multiple blend ratios and rebalance frequencies

Usage:
    python -m tools.quant.ls.regime_conditional_v4
"""

import sys, os, time, json
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from tools.quant.ls.config import Config
from tools.quant.ls import data as data_mod
from tools.quant.ls import factors as factors_mod
from tools.quant.ls import backtest as bt_mod
from tools.quant.ls import runner

OUT_DIR = Path("tools/quant/ls/results/regime_conditional_v4")
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIX_HIGH = 25.0
VIX_STRESS = 32.0


def load_panel():
    cfg = Config(data_dir="tools/quant/data/polygon", use_macro=True)
    panel = data_mod.load_panel(cfg)
    macro = data_mod._load_macro(cfg, panel["prices"].index)
    panel["macro"] = macro
    return cfg, panel, macro


def get_vix(panel, macro):
    if macro is not None and "VIX" in macro.columns:
        vix = macro["VIX"].dropna()
        if len(vix) > 100:
            return vix.reindex(panel["prices"].index).ffill()
    prices = panel["prices"]
    if "SPY" in prices.columns:
        spy_ret = np.log(prices["SPY"] / prices["SPY"].shift(1))
        return (spy_ret.rolling(20).std() * np.sqrt(252) * 100).reindex(prices.index).ffill()
    return pd.Series(20.0, index=prices.index)


def compute_reversal_predictions(panel, vix):
    """Compute daily reversal-based predictions."""
    returns = panel["returns"]
    prices = panel["prices"]
    volumes = panel["volumes"]
    bench_col = "SPY" if "SPY" in returns.columns else returns.columns[0]
    bench = returns[bench_col]

    signals = {}
    weights = {}

    # 5d reversal (ICIR 0.80 in high-vol)
    signals["rev_5d"] = -returns.rolling(5).sum()
    weights["rev_5d"] = 0.80

    # 10d reversal (ICIR 0.66)
    signals["rev_10d"] = -returns.rolling(10).sum()
    weights["rev_10d"] = 0.66

    # Dispersion-weighted momentum (ICIR 1.05)
    cs_std = returns.rolling(20).std()
    past_20d = returns.rolling(20).sum()
    cs_mean = past_20d.mean(axis=1)
    signals["disp_mom_20d"] = -(past_20d.sub(cs_mean, axis=0).div(cs_std.replace(0, np.nan), axis=0))
    weights["disp_mom_20d"] = 1.05

    # Beta-adjusted reversal (ICIR 0.62)
    cov = returns.rolling(60).cov(bench)
    var = bench.rolling(60).var()
    beta = cov.div(var.replace(0, np.nan), axis=0)
    signals["beta_rev_10d"] = -returns.rolling(10).sum() * beta.clip(0, 3)
    weights["beta_rev_10d"] = 0.62

    # VIX-scaled reversal (ICIR 0.60)
    vix_z = (vix - vix.rolling(60).mean()) / vix.rolling(60).std().replace(0, np.nan)
    vix_z = vix_z.reindex(returns.index).fillna(0)
    signals["vix_scaled_rev"] = -returns.rolling(10).sum() * vix_z.values[:, None]
    weights["vix_scaled_rev"] = 0.60

    # Liquidity shock reversal (ICIR 0.44)
    vol_change = volumes.pct_change(5)
    vol_spike = vol_change.rolling(20).rank(pct=True)
    signals["liq_shock_rev"] = -returns.rolling(5).sum() * vol_spike
    weights["liq_shock_rev"] = 0.44

    # Vol-weighted 5d reversal (ICIR 0.36)
    past_vol = volumes.rolling(5).mean()
    avg_vol = volumes.rolling(60).mean()
    vol_ratio = past_vol / avg_vol.replace(0, np.nan)
    signals["vol_w_rev_5d"] = -returns.rolling(5).sum() * vol_ratio
    weights["vol_w_rev_5d"] = 0.36

    # Idiosyncratic vol reversal (ICIR 0.40)
    res = returns.sub(bench, axis=0)
    ivol = res.rolling(20).std()
    signals["ivol_rev_10d"] = -res.rolling(10).sum() * ivol
    weights["ivol_rev_10d"] = 0.40

    # Range reversal (ICIR 0.42)
    abs_ret_5d = returns.abs().rolling(5).mean()
    signals["range_rev_5d"] = -returns.rolling(5).sum() * abs_ret_5d
    weights["range_rev_5d"] = 0.42

    # Normalize and weight
    normalized = {}
    for name, sig in signals.items():
        mu = sig.mean(axis=1)
        std = sig.std(axis=1).replace(0, np.nan)
        z = sig.sub(mu, axis=0).div(std, axis=0)
        normalized[name] = z * weights[name]

    combined = sum(normalized.values()) / sum(weights.values())
    mu = combined.mean(axis=1)
    std = combined.std(axis=1).replace(0, np.nan)
    return combined.sub(mu, axis=0).div(std, axis=0)


def run_bt(panel, predictions, cfg, vix, label=""):
    """Run backtest and report metrics with regime split."""
    res = bt_mod.run_backtest(panel, predictions, cfg)
    metrics = bt_mod.compute_metrics(res, cfg, panel["prices"])

    equity = res["equity_curve"]
    daily_ret = equity.pct_change().fillna(0)
    vix_bt = vix.reindex(daily_ret.index).fillna(20.0)

    sharpe = metrics.get('sharpe', 0)
    ret = metrics.get('annual_return', 0)
    dd = metrics.get('max_drawdown', 0)
    to = metrics.get('annual_turnover', 0)

    print(f"  {label:40s}  Sharpe={sharpe:.3f}  ret={ret:.3f}  dd={dd:.3f}  to={to:.1f}")

    # Regime split
    for name, mask in [("normal", vix_bt <= VIX_HIGH), ("high_vol", vix_bt > VIX_HIGH),
                       ("stress", vix_bt > VIX_STRESS)]:
        sub = daily_ret[mask.values]
        if len(sub) < 5:
            continue
        ann_ret = sub.mean() * 252
        ann_vol = sub.std() * np.sqrt(252)
        sharpe_r = ann_ret / ann_vol if ann_vol > 0 else 0
        print(f"    {name:8s}: n={len(sub):4d}  sharpe={sharpe_r:.3f}")

    return metrics


def main():
    print("=" * 70)
    print("REGIME-CONDITIONAL STRATEGY V4 (High-Freq Rebalance)")
    print("=" * 70)

    cfg_base, panel, macro = load_panel()
    vix = get_vix(panel, macro)
    prices = panel["prices"]

    print(f"\n  VIX: mean={vix.mean():.1f} > 25: {(vix>25).sum()}d ({100*(vix>25).mean():.1f}%)")

    # Run champion with rebalance_freq=5 for more responsive rebalancing
    print("\n--- Running champion GBRT (rebalance_freq=5) ---")
    cfg_champ = Config(
        name="champion_r5",
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160, refit_freq=20, rebalance_freq=5,
        predict_horizon=10, return_horizon_fwd=10,
        n_long=13, n_short=13,
        vol_target_active=False,
        gross_leverage=1.0, cost_bps_one_side=6.0, slippage_bps=0.0,
        vix_derisk_factor=1.0, vix_level_threshold=32.0, vix_level_factor=0.3,
        use_call_rate_financing=True, long_financing_apply=True,
        bypass_ic_screen=False, diag_regime_split=True,
    )
    res_champ = runner.run(cfg_champ, export=False)
    pred_champ = res_champ["predictions"]
    champ_metrics = res_champ["metrics"]
    print(f"  Champion (r=5): Sharpe={champ_metrics.get('sharpe',0):.3f}")

    # Check VIX at rebalance dates
    pred_dates = pred_champ.dropna(how='all').index
    vix_at_pred = vix.reindex(pred_dates).fillna(20.0)
    n_hv_rebal = (vix_at_pred > VIX_HIGH).sum()
    print(f"  Rebalance dates: {len(pred_dates)}, VIX>25 at rebalance: {n_hv_rebal}")

    # Compute daily reversal predictions
    print("\n--- Computing daily reversal predictions ---")
    pred_rev = compute_reversal_predictions(panel, vix)
    print(f"  Reversal predictions: {pred_rev.shape}")

    # Config for backtests
    cfg_bt = Config(
        name="bt",
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160, refit_freq=20, rebalance_freq=5,
        predict_horizon=10, return_horizon_fwd=10,
        n_long=13, n_short=13,
        vol_target_active=False,
        gross_leverage=1.0, cost_bps_one_side=6.0, slippage_bps=0.0,
        vix_derisk_factor=1.0, vix_level_threshold=32.0, vix_level_factor=0.3,
        use_call_rate_financing=True, long_financing_apply=True,
        bypass_ic_screen=True, diag_regime_split=True,
    )

    results = {}

    # Strategy 1: Champion baseline (r=5, with stress gate)
    print("\n=== 1) Champion baseline (r=5, stress gate) ===")
    m = run_bt(panel, pred_champ, cfg_bt, vix, "1: champion_r5")
    results["1_champion_r5"] = m

    # Strategy 2: Champion + reversal blend when VIX > 25
    print("\n=== 2) Champion + 50% reversal when VIX > 25 ===")
    pred_2 = pred_champ.copy()
    for date in pred_2.index:
        vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
        if vix_val > VIX_HIGH and vix_val <= VIX_STRESS:
            base = pred_champ.loc[date].reindex(pred_2.columns).fillna(0)
            rev = pred_rev.loc[date].reindex(pred_2.columns).fillna(0)
            if base.std() > 0:
                base = (base - base.mean()) / base.std()
            if rev.std() > 0:
                rev = (rev - rev.mean()) / rev.std()
            pred_2.loc[date] = 0.5 * base + 0.5 * rev
    m = run_bt(panel, pred_2, cfg_bt, vix, "2: champ+50%_rev_hv")
    results["2_champ_50_rev_hv"] = m

    # Strategy 3: Pure reversal when VIX > 25, champion otherwise
    print("\n=== 3) Pure reversal when VIX > 25, champion otherwise ===")
    pred_3 = pred_champ.copy()
    for date in pred_3.index:
        vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
        if vix_val > VIX_HIGH and vix_val <= VIX_STRESS:
            rev = pred_rev.loc[date].reindex(pred_3.columns).fillna(0)
            if rev.std() > 0:
                rev = (rev - rev.mean()) / rev.std()
            pred_3.loc[date] = rev
    m = run_bt(panel, pred_3, cfg_bt, vix, "3: pure_rev_hv_champ_nm")
    results["3_pure_rev_hv"] = m

    # Strategy 4: Ramp blend (0% at VIX=20, 100% at VIX=35)
    print("\n=== 4) Ramp blend (0% rev at VIX=20, 100% at VIX=35) ===")
    pred_4 = pred_champ.copy()
    for date in pred_4.index:
        vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
        if vix_val > 20:
            scale = min(1.0, (vix_val - 20) / 15)  # 0 at 20, 1 at 35
            base = pred_champ.loc[date].reindex(pred_4.columns).fillna(0)
            rev = pred_rev.loc[date].reindex(pred_4.columns).fillna(0)
            if base.std() > 0:
                base = (base - base.mean()) / base.std()
            if rev.std() > 0:
                rev = (rev - rev.mean()) / rev.std()
            pred_4.loc[date] = (1 - scale) * base + scale * rev
    m = run_bt(panel, pred_4, cfg_bt, vix, "4: ramp_blend_20_35")
    results["4_ramp_blend"] = m

    # Strategy 5: No stress gate + reversal in high-vol
    print("\n=== 5) No stress gate + 50% reversal when VIX > 25 ===")
    cfg_5 = cfg_bt.copy()
    cfg_5 = cfg_5.set(vix_level_threshold=None, vix_level_factor=0.0)
    pred_5 = pred_champ.copy()
    for date in pred_5.index:
        vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
        if vix_val > VIX_HIGH:
            base = pred_champ.loc[date].reindex(pred_5.columns).fillna(0)
            rev = pred_rev.loc[date].reindex(pred_5.columns).fillna(0)
            if base.std() > 0:
                base = (base - base.mean()) / base.std()
            if rev.std() > 0:
                rev = (rev - rev.mean()) / rev.std()
            pred_5.loc[date] = 0.5 * base + 0.5 * rev
    m = run_bt(panel, pred_5, cfg_5, vix, "5: no_gate+50%_rev_hv")
    results["5_no_gate_rev"] = m

    # Strategy 6: Daily rebalance (r=1) with reversal in high-vol
    print("\n=== 6) Daily rebalance + reversal when VIX > 25 ===")
    cfg_6 = cfg_bt.copy()
    cfg_6 = cfg_6.set(rebalance_freq=1)
    # Need daily predictions — forward fill champion predictions
    pred_6 = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    # Forward fill champion predictions
    for date in pred_champ.index:
        if date in pred_6.index:
            pred_6.loc[date] = pred_champ.loc[date].reindex(pred_6.columns)
    pred_6 = pred_6.ffill()
    # Override with reversal when VIX > 25
    for date in pred_6.index:
        vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
        if vix_val > VIX_HIGH and vix_val <= VIX_STRESS:
            base = pred_6.loc[date].reindex(pred_6.columns).fillna(0)
            rev = pred_rev.loc[date].reindex(pred_6.columns).fillna(0)
            if base.std() > 0:
                base = (base - base.mean()) / base.std()
            if rev.std() > 0:
                rev = (rev - rev.mean()) / rev.std()
            pred_6.loc[date] = 0.5 * base + 0.5 * rev
    m = run_bt(panel, pred_6, cfg_6, vix, "6: daily_r+50%_rev_hv")
    results["6_daily_rev"] = m

    # Strategy 7: r=10 with reversal in high-vol (moderate frequency)
    print("\n=== 7) Rebalance every 10d + 50% reversal when VIX > 25 ===")
    cfg_7 = cfg_bt.copy()
    cfg_7 = cfg_7.set(rebalance_freq=10)
    pred_7 = pred_champ.copy()
    for date in pred_7.index:
        vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
        if vix_val > VIX_HIGH and vix_val <= VIX_STRESS:
            base = pred_champ.loc[date].reindex(pred_7.columns).fillna(0)
            rev = pred_rev.loc[date].reindex(pred_7.columns).fillna(0)
            if base.std() > 0:
                base = (base - base.mean()) / base.std()
            if rev.std() > 0:
                rev = (rev - rev.mean()) / rev.std()
            pred_7.loc[date] = 0.5 * base + 0.5 * rev
    m = run_bt(panel, pred_7, cfg_7, vix, "7: r10+50%_rev_hv")
    results["7_r10_rev"] = m

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: V4 Strategies (sorted by Sharpe)")
    print("=" * 70)
    print(f"{'Strategy':<45s}  {'Sharpe':>7s}  {'Return':>7s}  {'MaxDD':>7s}  {'TO':>6s}")
    print("-" * 76)
    for name, m in sorted(results.items(), key=lambda x: x[1].get('sharpe', 0), reverse=True):
        print(f"{name:<45s}  {m.get('sharpe',0):7.3f}  {m.get('annual_return',0):7.3f}  "
              f"{m.get('max_drawdown',0):7.3f}  {m.get('annual_turnover',0):6.1f}")

    print(f"\n  Champion (runner.run, r=5): Sharpe={champ_metrics.get('sharpe',0):.3f}")

    with open(OUT_DIR / "results.json", "w") as f:
        json.dump({k: {kk: str(vv) for kk, vv in v.items()} for k, v in results.items()},
                  f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
