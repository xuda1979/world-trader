#!/usr/bin/env python3
"""Regime-conditional L/S strategy v5: production-ready + validation.

V4 found: rebalance_freq=10 + 50% reversal blend when VIX > 25 → Sharpe 0.726
  - High-vol Sharpe: 6.944
  - Stress Sharpe: 16.017
  - MaxDD: -0.029 (36% better than champion)
  - Turnover: 5.3

V5 does:
  1. Sweep blend ratios (30/70, 40/60, 50/50, 60/40) to find optimum
  2. Sweep VIX thresholds (22, 25, 28, 30) for regime switch
  3. Run scramble/noise test validation (the repo's definitive gate)
  4. Export the best config for live deployment

Usage:
    python -m tools.quant.ls.regime_conditional_v5
"""

import sys, os, time, json
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from tools.quant.ls.config import Config
from tools.quant.ls import data as data_mod
from tools.quant.ls import backtest as bt_mod
from tools.quant.ls import runner

OUT_DIR = Path("tools/quant/ls/results/regime_conditional_v5")
OUT_DIR.mkdir(parents=True, exist_ok=True)


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
    returns = panel["returns"]
    prices = panel["prices"]
    volumes = panel["volumes"]
    bench_col = "SPY" if "SPY" in returns.columns else returns.columns[0]
    bench = returns[bench_col]

    signals = {}
    weights = {}

    signals["rev_5d"] = -returns.rolling(5).sum()
    weights["rev_5d"] = 0.80
    signals["rev_10d"] = -returns.rolling(10).sum()
    weights["rev_10d"] = 0.66

    cs_std = returns.rolling(20).std()
    past_20d = returns.rolling(20).sum()
    cs_mean = past_20d.mean(axis=1)
    signals["disp_mom_20d"] = -(past_20d.sub(cs_mean, axis=0).div(cs_std.replace(0, np.nan), axis=0))
    weights["disp_mom_20d"] = 1.05

    cov = returns.rolling(60).cov(bench)
    var = bench.rolling(60).var()
    beta = cov.div(var.replace(0, np.nan), axis=0)
    signals["beta_rev_10d"] = -returns.rolling(10).sum() * beta.clip(0, 3)
    weights["beta_rev_10d"] = 0.62

    vix_z = (vix - vix.rolling(60).mean()) / vix.rolling(60).std().replace(0, np.nan)
    vix_z = vix_z.reindex(returns.index).fillna(0)
    signals["vix_scaled_rev"] = -returns.rolling(10).sum() * vix_z.values[:, None]
    weights["vix_scaled_rev"] = 0.60

    vol_change = volumes.pct_change(5)
    vol_spike = vol_change.rolling(20).rank(pct=True)
    signals["liq_shock_rev"] = -returns.rolling(5).sum() * vol_spike
    weights["liq_shock_rev"] = 0.44

    past_vol = volumes.rolling(5).mean()
    avg_vol = volumes.rolling(60).mean()
    vol_ratio = past_vol / avg_vol.replace(0, np.nan)
    signals["vol_w_rev_5d"] = -returns.rolling(5).sum() * vol_ratio
    weights["vol_w_rev_5d"] = 0.36

    res = returns.sub(bench, axis=0)
    ivol = res.rolling(20).std()
    signals["ivol_rev_10d"] = -res.rolling(10).sum() * ivol
    weights["ivol_rev_10d"] = 0.40

    abs_ret_5d = returns.abs().rolling(5).mean()
    signals["range_rev_5d"] = -returns.rolling(5).sum() * abs_ret_5d
    weights["range_rev_5d"] = 0.42

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


def build_blended_predictions(pred_base, pred_rev, vix, vix_threshold, rev_weight):
    """Build blended predictions: champion when VIX <= threshold,
    (1-rev_weight)*champion + rev_weight*reversal when VIX > threshold."""
    pred = pred_base.copy()
    for date in pred.index:
        vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
        if vix_val > vix_threshold and vix_val <= 32.0:
            base = pred_base.loc[date].reindex(pred.columns).fillna(0)
            rev = pred_rev.loc[date].reindex(pred.columns).fillna(0)
            if base.std() > 0:
                base = (base - base.mean()) / base.std()
            if rev.std() > 0:
                rev = (rev - rev.mean()) / rev.std()
            pred.loc[date] = (1 - rev_weight) * base + rev_weight * rev
    return pred


def run_bt(panel, predictions, cfg, vix, label=""):
    res = bt_mod.run_backtest(panel, predictions, cfg)
    metrics = bt_mod.compute_metrics(res, cfg, panel["prices"])
    equity = res["equity_curve"]
    daily_ret = equity.pct_change().fillna(0)
    vix_bt = vix.reindex(daily_ret.index).fillna(20.0)

    sharpe = metrics.get('sharpe', 0)
    ret = metrics.get('annual_return', 0)
    dd = metrics.get('max_drawdown', 0)
    to = metrics.get('annual_turnover', 0)

    # Regime split
    regime_sharpes = {}
    for name, mask in [("normal", vix_bt <= 25), ("high_vol", vix_bt > 25), ("stress", vix_bt > 32)]:
        sub = daily_ret[mask.values]
        if len(sub) < 5:
            continue
        ann_ret = sub.mean() * 252
        ann_vol = sub.std() * np.sqrt(252)
        regime_sharpes[name] = ann_ret / ann_vol if ann_vol > 0 else 0

    return metrics, regime_sharpes


def scramble_test(panel, pred_base, pred_rev, vix, cfg_bt, vix_threshold, rev_weight, n_scrambles=20):
    """Run scramble/noise test: shuffle reversal signal dates and compare.

    If the strategy's Sharpe drops to ~0 when the reversal signal is
    randomly shuffled, the alpha is real. If it stays high, it's noise.
    """
    print(f"\n  Scramble test ({n_scrambles} runs)...")
    real_metrics, _ = run_bt(panel,
        build_blended_predictions(pred_base, pred_rev, vix, vix_threshold, rev_weight),
        cfg_bt, vix, "real")

    real_sharpe = real_metrics.get('sharpe', 0)
    scramble_sharpes = []

    np.random.seed(42)
    for i in range(n_scrambles):
        # Shuffle the reversal predictions (shift by random amount)
        shift = np.random.randint(20, 100)
        pred_scrambled = pred_rev.shift(shift)
        pred_blend = build_blended_predictions(pred_base, pred_scrambled, vix,
                                                vix_threshold, rev_weight)
        m, _ = run_bt(panel, pred_blend, cfg_bt, vix, f"scramble_{i}")
        scramble_sharpes.append(m.get('sharpe', 0))

    scramble_sharpes = np.array(scramble_sharpes)
    p_value = (scramble_sharpes >= real_sharpe).mean()

    print(f"    Real Sharpe:     {real_sharpe:.3f}")
    print(f"    Scramble Sharpe: mean={scramble_sharpes.mean():.3f}  std={scramble_sharpes.std():.3f}")
    print(f"    P-value:         {p_value:.3f}")
    print(f"    Verdict:         {'PASS' if p_value < 0.05 else 'FAIL'} (p<0.05 required)")

    return real_sharpe, scramble_sharpes, p_value


def main():
    print("=" * 70)
    print("REGIME-CONDITIONAL STRATEGY V5 (Optimization + Validation)")
    print("=" * 70)

    cfg_base, panel, macro = load_panel()
    vix = get_vix(panel, macro)

    # Run champion with rebalance_freq=10
    print("\n--- Running champion GBRT (r=10) ---")
    cfg_champ = Config(
        name="champion_r10",
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160, refit_freq=20, rebalance_freq=10,
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
    print(f"  Champion (r=10): Sharpe={res_champ['metrics'].get('sharpe',0):.3f}")

    # Compute reversal predictions
    print("\n--- Computing reversal predictions ---")
    pred_rev = compute_reversal_predictions(panel, vix)

    # Config for backtests
    cfg_bt = Config(
        name="bt",
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160, refit_freq=20, rebalance_freq=10,
        predict_horizon=10, return_horizon_fwd=10,
        n_long=13, n_short=13,
        vol_target_active=False,
        gross_leverage=1.0, cost_bps_one_side=6.0, slippage_bps=0.0,
        vix_derisk_factor=1.0, vix_level_threshold=32.0, vix_level_factor=0.3,
        use_call_rate_financing=True, long_financing_apply=True,
        bypass_ic_screen=True, diag_regime_split=True,
    )

    # Phase 1: Sweep blend ratios
    print("\n" + "=" * 70)
    print("PHASE 1: Blend Ratio Sweep (VIX threshold=25, r=10)")
    print("=" * 70)
    blend_results = {}
    for rev_w in [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0]:
        pred = build_blended_predictions(pred_champ, pred_rev, vix, 25.0, rev_w)
        m, rs = run_bt(panel, pred, cfg_bt, vix, f"rev_w={rev_w}")
        blend_results[rev_w] = (m, rs)
        print(f"  rev_w={rev_w:.1f}  Sharpe={m.get('sharpe',0):.3f}  "
              f"ret={m.get('annual_return',0):.3f}  dd={m.get('max_drawdown',0):.3f}  "
              f"to={m.get('annual_turnover',0):.1f}  "
              f"HV_sharpe={rs.get('high_vol',0):.2f}")

    # Find best
    best_rev_w = max(blend_results, key=lambda k: blend_results[k][0].get('sharpe', 0))
    print(f"\n  Best blend ratio: rev_w={best_rev_w}  Sharpe={blend_results[best_rev_w][0].get('sharpe',0):.3f}")

    # Phase 2: Sweep VIX thresholds
    print("\n" + "=" * 70)
    print(f"PHASE 2: VIX Threshold Sweep (rev_w={best_rev_w}, r=10)")
    print("=" * 70)
    thresh_results = {}
    for vix_thresh in [20, 22, 25, 28, 30]:
        pred = build_blended_predictions(pred_champ, pred_rev, vix, float(vix_thresh), best_rev_w)
        m, rs = run_bt(panel, pred, cfg_bt, vix, f"vix_thresh={vix_thresh}")
        thresh_results[vix_thresh] = (m, rs)
        print(f"  vix_thresh={vix_thresh:2d}  Sharpe={m.get('sharpe',0):.3f}  "
              f"ret={m.get('annual_return',0):.3f}  dd={m.get('max_drawdown',0):.3f}  "
              f"to={m.get('annual_turnover',0):.1f}  "
              f"HV_sharpe={rs.get('high_vol',0):.2f}")

    best_thresh = max(thresh_results, key=lambda k: thresh_results[k][0].get('sharpe', 0))
    print(f"\n  Best VIX threshold: {best_thresh}  Sharpe={thresh_results[best_thresh][0].get('sharpe',0):.3f}")

    # Phase 3: Scramble validation
    print("\n" + "=" * 70)
    print(f"PHASE 3: Scramble Validation (rev_w={best_rev_w}, vix_thresh={best_thresh})")
    print("=" * 70)
    real_sharpe, scramble_sharpes, p_value = scramble_test(
        panel, pred_champ, pred_rev, vix, cfg_bt, float(best_thresh), best_rev_w,
        n_scrambles=20
    )

    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"\n  Best configuration:")
    print(f"    VIX threshold:  {best_thresh}")
    print(f"    Reversal weight: {best_rev_w}")
    print(f"    Rebalance freq:  10 days")
    print(f"    VIX stress gate: 32 → 30% gross")
    print(f"\n  Performance:")
    best_m, best_rs = thresh_results[best_thresh]
    print(f"    Overall Sharpe:  {best_m.get('sharpe',0):.3f}")
    print(f"    Annual return:   {best_m.get('annual_return',0):.3f}")
    print(f"    Max drawdown:    {best_m.get('max_drawdown',0):.3f}")
    print(f"    Turnover:        {best_m.get('annual_turnover',0):.1f}")
    print(f"    Normal Sharpe:   {best_rs.get('normal',0):.3f}")
    print(f"    HighVol Sharpe:  {best_rs.get('high_vol',0):.3f}")
    print(f"    Stress Sharpe:   {best_rs.get('stress',0):.3f}")
    print(f"\n  Validation:")
    print(f"    Scramble p-value: {p_value:.3f}")
    print(f"    Verdict:          {'PASS' if p_value < 0.05 else 'FAIL'}")

    # Save
    results = {
        "best_config": {
            "vix_threshold": best_thresh,
            "reversal_weight": best_rev_w,
            "rebalance_freq": 10,
        },
        "best_metrics": {k: str(v) for k, v in best_m.items()},
        "regime_sharpes": {k: str(v) for k, v in best_rs.items()},
        "scramble_test": {
            "real_sharpe": str(real_sharpe),
            "scramble_mean": str(np.mean(scramble_sharpes)),
            "scramble_std": str(np.std(scramble_sharpes)),
            "p_value": str(p_value),
            "verdict": "PASS" if p_value < 0.05 else "FAIL",
        },
        "blend_sweep": {str(k): str(v[0].get('sharpe', 0)) for k, v in blend_results.items()},
        "threshold_sweep": {str(k): str(v[0].get('sharpe', 0)) for k, v in thresh_results.items()},
    }
    with open(OUT_DIR / "final_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n  Results saved to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
