#!/usr/bin/env python3
"""Regime-conditional L/S strategy v2: prediction blending approach.

Instead of running two separate models, we:
  1. Run the champion GBRT model to get base predictions
  2. When VIX > 25, compute reversal-based predictions and blend them
  3. The blend ratio depends on how high VIX is

This is more practical and avoids the data-alignment issues of running
two separate model fits.

Usage:
    python -m tools.quant.ls.regime_conditional_v2
"""

import sys, os, time, json, copy
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from tools.quant.ls.config import Config
from tools.quant.ls import data as data_mod
from tools.quant.ls import factors as factors_mod
from tools.quant.ls import ic_screen
from tools.quant.ls import model as model_mod
from tools.quant.ls import portfolio as pf
from tools.quant.ls import backtest as bt_mod
from tools.quant.ls import runner

OUT_DIR = Path("tools/quant/ls/results/regime_conditional_v2")
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


def compute_reversal_signals(panel, vix):
    """Compute reversal-based predictions for high-vol regime.

    Research shows:
    - 5d reversal ICIR=0.80 in high-vol (vs 0.04 normal)
    - 10d reversal ICIR=0.66 in high-vol (vs 0.01 normal)
    - Dispersion-weighted momentum ICIR=1.05 in high-vol
    - Beta-adjusted reversal ICIR=0.62 in high-vol
    """
    returns = panel["returns"]
    prices = panel["prices"]
    volumes = panel["volumes"]

    bench_col = "SPY" if "SPY" in returns.columns else returns.columns[0]
    bench = returns[bench_col]

    signals = {}

    # 1. 5-day reversal (strongest: ICIR 0.80)
    rev_5d = -returns.rolling(5).sum()
    signals["rev_5d"] = rev_5d

    # 2. 10-day reversal (ICIR 0.66)
    rev_10d = -returns.rolling(10).sum()
    signals["rev_10d"] = rev_10d

    # 3. Dispersion-weighted momentum (ICIR 1.05)
    cs_std = returns.rolling(20).std()
    past_20d = returns.rolling(20).sum()
    cs_mean = past_20d.mean(axis=1)
    disp_mom = -(past_20d.sub(cs_mean, axis=0).div(cs_std.replace(0, np.nan), axis=0))
    signals["disp_mom_20d"] = disp_mom

    # 4. Beta-adjusted reversal (ICIR 0.62)
    cov = returns.rolling(60).cov(bench)
    var = bench.rolling(60).var()
    beta = cov.div(var.replace(0, np.nan), axis=0)
    past_10d = returns.rolling(10).sum()
    beta_rev = -past_10d * beta.clip(0, 3)
    signals["beta_rev_10d"] = beta_rev

    # 5. Volume-weighted 5d reversal
    past_vol = volumes.rolling(5).mean()
    avg_vol = volumes.rolling(60).mean()
    vol_ratio = past_vol / avg_vol.replace(0, np.nan)
    vol_w_rev = -returns.rolling(5).sum() * vol_ratio
    signals["vol_w_rev_5d"] = vol_w_rev

    # 6. VIX-scaled 10d reversal
    vix_z = (vix - vix.rolling(60).mean()) / vix.rolling(60).std().replace(0, np.nan)
    vix_z = vix_z.reindex(returns.index).fillna(0)
    vix_scaled_rev = -returns.rolling(10).sum() * vix_z.values[:, None]
    signals["vix_scaled_rev"] = vix_scaled_rev

    # 7. Idiosyncratic vol reversal
    res = returns.sub(bench, axis=0)
    ivol = res.rolling(20).std()
    past_res_10d = res.rolling(10).sum()
    ivol_rev = -past_res_10d * ivol
    signals["ivol_rev_10d"] = ivol_rev

    # 8. Liquidity shock reversal
    vol_change = volumes.pct_change(5)
    vol_spike = vol_change.rolling(20).rank(pct=True)
    liq_shock = -returns.rolling(5).sum() * vol_spike
    signals["liq_shock_rev"] = liq_shock

    # Weight each signal by its research ICIR (high-vol regime)
    weights = {
        "rev_5d": 0.80,
        "rev_10d": 0.66,
        "disp_mom_20d": 1.05,
        "beta_rev_10d": 0.62,
        "vol_w_rev_5d": 0.36,
        "vix_scaled_rev": 0.60,
        "ivol_rev_10d": 0.40,
        "liq_shock_rev": 0.44,
    }

    # Normalize each signal cross-sectionally (z-score)
    normalized = {}
    for name, sig in signals.items():
        # Cross-sectional z-score at each date
        mu = sig.mean(axis=1)
        std = sig.std(axis=1).replace(0, np.nan)
        z = sig.sub(mu, axis=0).div(std, axis=0)
        normalized[name] = z * weights.get(name, 0.5)

    # Combine: weighted average
    combined = sum(normalized.values()) / len(normalized)
    # Final cross-sectional z-score
    mu = combined.mean(axis=1)
    std = combined.std(axis=1).replace(0, np.nan)
    combined_z = combined.sub(mu, axis=0).div(std, axis=0)

    return combined_z


def run_strategy():
    print("=" * 70)
    print("REGIME-CONDITIONAL STRATEGY V2 (Prediction Blending)")
    print("=" * 70)

    # Load data
    cfg_base, panel, macro = load_panel()
    vix = get_vix(panel, macro)

    print(f"\n  VIX: mean={vix.mean():.1f} median={vix.median():.1f}")
    print(f"  VIX > 25: {(vix > 25).sum()} days ({100*(vix>25).mean():.1f}%)")
    print(f"  VIX > 32: {(vix > 32).sum()} days ({100*(vix>32).mean():.1f}%)")

    # Champion config
    cfg_champion = Config(
        name="champion",
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160,
        refit_freq=20,
        rebalance_freq=20,
        predict_horizon=10,
        return_horizon_fwd=10,
        n_long=13,
        n_short=13,
        vol_target_active=False,
        gross_leverage=1.0,
        cost_bps_one_side=6.0,
        slippage_bps=0.0,
        vix_derisk_pctile=0.90,
        vix_derisk_factor=1.0,
        vix_level_threshold=32.0,
        vix_level_factor=0.3,
        use_call_rate_financing=True,
        long_financing_apply=True,
        bypass_ic_screen=False,
        diag_regime_split=True,
    )

    # Step 1: Run champion to get base predictions
    print("\n--- Step 1: Running champion GBRT model ---")
    t0 = time.time()
    res_champ = runner.run(cfg_champion, export=False)
    champ_metrics = res_champ["metrics"]
    pred_base = res_champ["predictions"]
    print(f"  Champion: Sharpe={champ_metrics.get('sharpe',0):.3f}  "
          f"ret={champ_metrics.get('annual_return',0):.3f}  "
          f"dd={champ_metrics.get('max_drawdown',0):.3f}  "
          f"to={champ_metrics.get('annual_turnover',0):.1f}  "
          f"({time.time()-t0:.1f}s)")

    # Step 2: Compute reversal-based predictions
    print("\n--- Step 2: Computing reversal signals for high-vol regime ---")
    rev_predictions = compute_reversal_signals(panel, vix)
    print(f"  Reversal predictions: {rev_predictions.shape}")
    print(f"  Valid dates: {rev_predictions.dropna(how='all').shape[0]}")

    # Step 3: Blend predictions regime-conditionally
    print("\n--- Step 3: Blending predictions by VIX regime ---")

    # Strategy variants to test
    variants = {
        "blend_50_50": {"normal_weight": 0.5, "highvol_weight": 0.5},
        "blend_70_30": {"normal_weight": 0.7, "highvol_weight": 0.3},
        "blend_30_70": {"normal_weight": 0.3, "highvol_weight": 0.7},
        "blend_90_10": {"normal_weight": 0.9, "highvol_weight": 0.1},
        "blend_10_90": {"normal_weight": 0.1, "highvol_weight": 0.9},
        "pure_reversal_hv": {"normal_weight": 0.0, "highvol_weight": 1.0},
        "pure_champion": {"normal_weight": 1.0, "highvol_weight": 0.0},
        # Linear ramp: blend more as VIX increases
        "ramp_25_35": {"ramp": True, "vix_low": 20, "vix_high": 35},
    }

    results = {}

    for name, params in variants.items():
        print(f"\n  Testing variant: {name}")

        # Build blended predictions
        pred_blended = pred_base.copy()

        if params.get("ramp"):
            # Linear ramp: 0% reversal at vix_low, 100% at vix_high
            vix_low = params["vix_low"]
            vix_high = params["vix_high"]
            for date in pred_base.index:
                vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
                if vix_val <= vix_low:
                    hw = 0.0
                elif vix_val >= vix_high:
                    hw = 1.0
                else:
                    hw = (vix_val - vix_low) / (vix_high - vix_low)
                nw = 1.0 - hw
                if date in rev_predictions.index:
                    base = pred_base.loc[date].reindex(pred_blended.columns).fillna(0)
                    rev = rev_predictions.loc[date].reindex(pred_blended.columns).fillna(0)
                    # Normalize both to same scale
                    if base.std() > 0:
                        base = (base - base.mean()) / base.std()
                    if rev.std() > 0:
                        rev = (rev - rev.mean()) / rev.std()
                    pred_blended.loc[date] = nw * base + hw * rev
        else:
            nw = params["normal_weight"]
            hw = params["highvol_weight"]
            for date in pred_base.index:
                vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
                if vix_val > VIX_HIGH:
                    base = pred_base.loc[date].reindex(pred_blended.columns).fillna(0)
                    rev = rev_predictions.loc[date].reindex(pred_blended.columns).fillna(0)
                    if base.std() > 0:
                        base = (base - base.mean()) / base.std()
                    if rev.std() > 0:
                        rev = (rev - rev.mean()) / rev.std()
                    pred_blended.loc[date] = nw * base + hw * rev

        # Run backtest
        cfg_bt = cfg_champion.copy()
        cfg_bt = cfg_bt.set(vix_derisk_factor=1.0, vix_level_threshold=VIX_STRESS, vix_level_factor=0.3)
        res = bt_mod.run_backtest(panel, pred_blended, cfg_bt)
        metrics = bt_mod.compute_metrics(res, cfg_bt, panel["prices"])

        sharpe = metrics.get('sharpe', 0)
        ret = metrics.get('annual_return', 0)
        dd = metrics.get('max_drawdown', 0)
        to = metrics.get('annual_turnover', 0)

        results[name] = metrics
        print(f"    Sharpe={sharpe:.3f}  ret={ret:.3f}  dd={dd:.3f}  to={to:.1f}")

        # Regime split
        equity = res["equity_curve"]
        daily_ret = equity.pct_change().fillna(0)
        vix_bt = vix.reindex(daily_ret.index).fillna(20.0)
        for regime_name, mask in [("normal", vix_bt <= VIX_HIGH), ("high_vol", vix_bt > VIX_HIGH)]:
            sub = daily_ret[mask.values]
            if len(sub) < 5:
                continue
            ann_ret = sub.mean() * 252
            ann_vol = sub.std() * np.sqrt(252)
            sharpe_r = ann_ret / ann_vol if ann_vol > 0 else 0
            print(f"      {regime_name:8s}: n={len(sub):4d}  sharpe={sharpe_r:.3f}")

    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY: All Variants")
    print("=" * 70)
    print(f"{'Variant':<25s}  {'Sharpe':>7s}  {'Return':>7s}  {'MaxDD':>7s}  {'Turnover':>8s}")
    print("-" * 60)
    for name, m in sorted(results.items(), key=lambda x: x[1].get('sharpe', 0), reverse=True):
        print(f"{name:<25s}  {m.get('sharpe',0):7.3f}  {m.get('annual_return',0):7.3f}  "
              f"{m.get('max_drawdown',0):7.3f}  {m.get('annual_turnover',0):8.1f}")

    # Save
    with open(OUT_DIR / "comparison.json", "w") as f:
        json.dump({k: {kk: str(vv) for kk, vv in v.items()} for k, v in results.items()},
                  f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(run_strategy())
