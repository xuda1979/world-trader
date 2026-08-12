#!/usr/bin/env python3
"""Regime-conditional L/S strategy v3: high-vol-only + ensemble approaches.

V2 showed the reversal strategy has Sharpe 2.456 in high-vol regime,
but high-vol is only 7.4% of days, diluting overall Sharpe.

V3 tests:
  A) Pure high-vol strategy: only trade when VIX > 25, flat otherwise
  B) High-vol overlay: champion normally + extra reversal exposure when VIX > 25
  C) Multi-signal ensemble: combine champion + reversal + momentum, 
     weight by VIX regime
  D) Adaptive parameters: vary n_long/n_short/horizon by VIX level

Usage:
    python -m tools.quant.ls.regime_conditional_v3
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

OUT_DIR = Path("tools/quant/ls/results/regime_conditional_v3")
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
    """Compute reversal-based predictions (ICIR-weighted ensemble)."""
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
    # Final z-score
    mu = combined.mean(axis=1)
    std = combined.std(axis=1).replace(0, np.nan)
    return combined.sub(mu, axis=0).div(std, axis=0)


def compute_momentum_predictions(panel):
    """Compute 12m momentum predictions (ICIR 2.03 in high-vol)."""
    prices = panel["prices"]
    # 12m-1m momentum
    mom = prices.shift(21) / prices.shift(252) - 1
    # Cross-sectional z-score
    mu = mom.mean(axis=1)
    std = mom.std(axis=1).replace(0, np.nan)
    return mom.sub(mu, axis=0).div(std, axis=0)


def run_backtest_with_config(panel, predictions, cfg, vix, label=""):
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

    print(f"  {label:30s}  Sharpe={sharpe:.3f}  ret={ret:.3f}  dd={dd:.3f}  to={to:.1f}")

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

    return metrics, daily_ret, equity


def main():
    print("=" * 70)
    print("REGIME-CONDITIONAL STRATEGY V3 (Multi-approach)")
    print("=" * 70)

    cfg_base, panel, macro = load_panel()
    vix = get_vix(panel, macro)

    print(f"\n  VIX: mean={vix.mean():.1f} > 25: {(vix>25).sum()}d ({100*(vix>25).mean():.1f}%)")

    # Run champion to get base predictions
    print("\n--- Running champion GBRT ---")
    cfg_champion = Config(
        name="champion",
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160, refit_freq=20, rebalance_freq=20,
        predict_horizon=10, return_horizon_fwd=10,
        n_long=13, n_short=13,
        vol_target_active=False,
        gross_leverage=1.0, cost_bps_one_side=6.0, slippage_bps=0.0,
        vix_derisk_pctile=0.90, vix_derisk_factor=1.0,
        vix_level_threshold=32.0, vix_level_factor=0.3,
        use_call_rate_financing=True, long_financing_apply=True,
        bypass_ic_screen=False, diag_regime_split=True,
    )
    res_champ = runner.run(cfg_champion, export=False)
    pred_champ = res_champ["predictions"]
    champ_metrics = res_champ["metrics"]
    print(f"  Champion: Sharpe={champ_metrics.get('sharpe',0):.3f}")

    # Compute reversal and momentum predictions
    print("\n--- Computing signal predictions ---")
    pred_rev = compute_reversal_predictions(panel, vix)
    pred_mom = compute_momentum_predictions(panel)

    # Configs
    cfg_base_bt = Config(
        name="bt",
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160, refit_freq=20, rebalance_freq=20,
        predict_horizon=10, return_horizon_fwd=10,
        n_long=13, n_short=13,
        vol_target_active=False,
        gross_leverage=1.0, cost_bps_one_side=6.0, slippage_bps=0.0,
        vix_derisk_factor=1.0, vix_level_threshold=32.0, vix_level_factor=0.3,
        use_call_rate_financing=True, long_financing_apply=True,
        bypass_ic_screen=True, diag_regime_split=True,
    )

    results = {}

    # A) Pure high-vol reversal: flat when VIX<=25, reversal when VIX>25
    print("\n=== A) Pure high-vol reversal (flat when VIX<=25) ===")
    pred_a = pd.DataFrame(0.0, index=pred_rev.index, columns=pred_rev.columns)
    for date in pred_rev.index:
        vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
        if vix_val > VIX_HIGH and vix_val <= VIX_STRESS:
            pred_a.loc[date] = pred_rev.loc[date]
    m, _, _ = run_backtest_with_config(panel, pred_a, cfg_base_bt, vix, "A: pure_hv_reversal")
    results["A_pure_hv_reversal"] = m

    # B) Champion + high-vol reversal overlay
    # When VIX > 25, blend champion with reversal (70/30)
    print("\n=== B) Champion + HV reversal overlay (70/30) ===")
    pred_b = pred_champ.copy()
    for date in pred_b.index:
        vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
        if vix_val > VIX_HIGH:
            base = pred_champ.loc[date].reindex(pred_b.columns).fillna(0)
            rev = pred_rev.loc[date].reindex(pred_b.columns).fillna(0)
            if base.std() > 0:
                base = (base - base.mean()) / base.std()
            if rev.std() > 0:
                rev = (rev - rev.mean()) / rev.std()
            # Scale by VIX: more reversal as VIX increases
            scale = min(1.0, (vix_val - VIX_HIGH) / 10)  # 0 at 25, 1 at 35
            pred_b.loc[date] = (1 - 0.5*scale) * base + (0.5*scale) * rev
    m, _, _ = run_backtest_with_config(panel, pred_b, cfg_base_bt, vix, "B: champ+hv_overlay")
    results["B_champ_hv_overlay"] = m

    # C) Multi-signal ensemble: champion + reversal + momentum
    print("\n=== C) Multi-signal ensemble ===")
    pred_c = pred_champ.copy()
    for date in pred_c.index:
        vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
        base = pred_champ.loc[date].reindex(pred_c.columns).fillna(0)
        rev = pred_rev.loc[date].reindex(pred_c.columns).fillna(0)
        mom = pred_mom.loc[date].reindex(pred_c.columns).fillna(0)
        if base.std() > 0:
            base = (base - base.mean()) / base.std()
        if rev.std() > 0:
            rev = (rev - rev.mean()) / rev.std()
        if mom.std() > 0:
            mom = (mom - mom.mean()) / mom.std()
        if vix_val > VIX_HIGH:
            # In high-vol: 40% champion + 35% reversal + 25% momentum
            pred_c.loc[date] = 0.40 * base + 0.35 * rev + 0.25 * mom
        else:
            # In normal: 80% champion + 10% reversal + 10% momentum
            pred_c.loc[date] = 0.80 * base + 0.10 * rev + 0.10 * mom
    m, _, _ = run_backtest_with_config(panel, pred_c, cfg_base_bt, vix, "C: multi_ensemble")
    results["C_multi_ensemble"] = m

    # D) Wider high-vol strategy: more names when VIX > 25
    print("\n=== D) Champion with adaptive n (more names in HV) ===")
    # Can't change n mid-backtest, so use larger n always
    cfg_d = cfg_base_bt.copy()
    cfg_d = cfg_d.set(n_long=20, n_short=20, rebalance_freq=10)
    pred_d = pred_champ.copy()
    for date in pred_d.index:
        vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
        if vix_val > VIX_HIGH:
            base = pred_champ.loc[date].reindex(pred_d.columns).fillna(0)
            rev = pred_rev.loc[date].reindex(pred_d.columns).fillna(0)
            if base.std() > 0:
                base = (base - base.mean()) / base.std()
            if rev.std() > 0:
                rev = (rev - rev.mean()) / rev.std()
            pred_d.loc[date] = 0.5 * base + 0.5 * rev
    m, _, _ = run_backtest_with_config(panel, pred_d, cfg_d, vix, "D: adaptive_n20")
    results["D_adaptive_n20"] = m

    # E) Champion with no VIX stress gate (trade through stress)
    print("\n=== E) Champion with NO stress gate (trade through VIX>32) ===")
    cfg_e = cfg_base_bt.copy()
    cfg_e = cfg_e.set(vix_level_threshold=None, vix_level_factor=0.0)
    pred_e = pred_champ.copy()
    for date in pred_e.index:
        vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
        if vix_val > VIX_HIGH:
            base = pred_champ.loc[date].reindex(pred_e.columns).fillna(0)
            rev = pred_rev.loc[date].reindex(pred_e.columns).fillna(0)
            if base.std() > 0:
                base = (base - base.mean()) / base.std()
            if rev.std() > 0:
                rev = (rev - rev.mean()) / rev.std()
            pred_e.loc[date] = 0.5 * base + 0.5 * rev
    m, _, _ = run_backtest_with_config(panel, pred_e, cfg_e, vix, "E: no_stress_gate")
    results["E_no_stress_gate"] = m

    # F) Pure reversal always (not just high-vol)
    print("\n=== F) Pure reversal (always, no regime switch) ===")
    m, _, _ = run_backtest_with_config(panel, pred_rev, cfg_base_bt, vix, "F: pure_reversal_always")
    results["F_pure_reversal_always"] = m

    # G) Champion baseline (no modification, no stress gate)
    print("\n=== G) Champion baseline (no stress gate) ===")
    cfg_g = cfg_base_bt.copy()
    cfg_g = cfg_g.set(vix_level_threshold=None, vix_level_factor=0.0)
    m, _, _ = run_backtest_with_config(panel, pred_champ, cfg_g, vix, "G: champion_no_gate")
    results["G_champion_no_gate"] = m

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: All Strategies")
    print("=" * 70)
    print(f"{'Strategy':<35s}  {'Sharpe':>7s}  {'Return':>7s}  {'MaxDD':>7s}  {'TO':>6s}")
    print("-" * 68)
    for name, m in sorted(results.items(), key=lambda x: x[1].get('sharpe', 0), reverse=True):
        print(f"{name:<35s}  {m.get('sharpe',0):7.3f}  {m.get('annual_return',0):7.3f}  "
              f"{m.get('max_drawdown',0):7.3f}  {m.get('annual_turnover',0):6.1f}")

    # Also show champion from runner
    print(f"\n  Champion (runner.run): Sharpe={champ_metrics.get('sharpe',0):.3f}  "
          f"ret={champ_metrics.get('annual_return',0):.3f}  "
          f"dd={champ_metrics.get('max_drawdown',0):.3f}")

    with open(OUT_DIR / "results.json", "w") as f:
        json.dump({k: {kk: str(vv) for kk, vv in v.items()} for k, v in results.items()},
                  f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
