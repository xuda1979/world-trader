#!/usr/bin/env python3
"""Regime-conditional L/S strategy v8: final production config.

Findings from v1-v7:
  1. Reversal signals have strong IC in high-vol but FAIL scramble test
     in backtest (realistic costs + portfolio construction erode alpha)
  2. Champion GBRT with rebalance_freq=10 gets Sharpe 0.854 (best overall)
  3. Reversal overlay HURTS overall Sharpe (dilutes champion alpha)
  4. The VIX>=32 stress gate (cut to 30% gross) is beneficial

V8: Final production config — champion with optimized rebalance frequency.

The regime-conditional aspect is:
  - Normal (VIX <= 25): champion GBRT predictions, r=10
  - High-vol (25 < VIX <= 32): same champion, full exposure
  - Stress (VIX > 32): cut gross to 30% (existing VIX stress gate)

Usage:
    python -m tools.quant.ls.regime_conditional_v8
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

OUT_DIR = Path("tools/quant/ls/results/regime_conditional_v8")
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


def main():
    print("=" * 70)
    print("REGIME-CONDITIONAL STRATEGY V8 (Final Production Config)")
    print("=" * 70)

    cfg_base, panel, macro = load_panel()
    vix = get_vix(panel, macro)

    # Test multiple rebalance frequencies to find the best
    results = {}

    for r_freq in [5, 7, 10, 15, 20]:
        print(f"\n--- Champion GBRT (r={r_freq}) ---")
        cfg = Config(
            name=f"champion_r{r_freq}",
            data_dir="tools/quant/data/polygon",
            use_macro=True,
            model_method="gbrt",
            train_window=160, refit_freq=20, rebalance_freq=r_freq,
            predict_horizon=10, return_horizon_fwd=10,
            n_long=13, n_short=13,
            vol_target_active=False,
            gross_leverage=1.0, cost_bps_one_side=6.0, slippage_bps=0.0,
            vix_derisk_factor=1.0, vix_level_threshold=32.0, vix_level_factor=0.3,
            use_call_rate_financing=True, long_financing_apply=True,
            bypass_ic_screen=False, diag_regime_split=True,
        )
        t0 = time.time()
        res = runner.run(cfg, export=False)
        m = res["metrics"]
        pred = res["predictions"]

        # Regime split
        equity = res["result"]["equity_curve"]
        daily_ret = equity.pct_change().fillna(0)
        vix_bt = vix.reindex(daily_ret.index).fillna(20.0)

        regime_sharpes = {}
        for name, mask in [("normal", vix_bt <= 25), ("high_vol", vix_bt > 25), ("stress", vix_bt > 32)]:
            sub = daily_ret[mask.values]
            if len(sub) < 5:
                continue
            ann_ret = sub.mean() * 252
            ann_vol = sub.std() * np.sqrt(252)
            regime_sharpes[name] = ann_ret / ann_vol if ann_vol > 0 else 0

        sharpe = m.get('sharpe', 0)
        results[r_freq] = {
            'metrics': m,
            'regime_sharpes': regime_sharpes,
            'time': time.time() - t0,
        }
        print(f"  Sharpe={sharpe:.3f}  ret={m.get('annual_return',0):.3f}  "
              f"dd={m.get('max_drawdown',0):.3f}  to={m.get('annual_turnover',0):.1f}  "
              f"({time.time()-t0:.1f}s)")
        for rn, rs in regime_sharpes.items():
            print(f"    {rn:8s}: sharpe={rs:.3f}")

    # Summary
    print("\n" + "=" * 70)
    print("REBALANCE FREQUENCY SWEEP SUMMARY")
    print("=" * 70)
    print(f"{'r_freq':>6s}  {'Sharpe':>7s}  {'Return':>7s}  {'MaxDD':>7s}  {'TO':>6s}  "
          f"{'Normal':>7s}  {'HighVol':>7s}  {'Stress':>7s}")
    print("-" * 66)
    for r_freq, data in sorted(results.items(), key=lambda x: x[1]['metrics'].get('sharpe', 0), reverse=True):
        m = data['metrics']
        rs = data['regime_sharpes']
        print(f"{r_freq:6d}  {m.get('sharpe',0):7.3f}  {m.get('annual_return',0):7.3f}  "
              f"{m.get('max_drawdown',0):7.3f}  {m.get('annual_turnover',0):6.1f}  "
              f"{rs.get('normal',0):7.3f}  {rs.get('high_vol',0):7.3f}  {rs.get('stress',0):7.3f}")

    # Best config
    best_r = max(results, key=lambda k: results[k]['metrics'].get('sharpe', 0))
    best = results[best_r]
    print(f"\n  Best rebalance frequency: {best_r}")
    print(f"  Best Sharpe: {best['metrics'].get('sharpe', 0):.3f}")

    # Run scramble test on best
    print(f"\n--- Scramble test on best (r={best_r}) ---")
    cfg_best = Config(
        name=f"best_r{best_r}",
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160, refit_freq=20, rebalance_freq=best_r,
        predict_horizon=10, return_horizon_fwd=10,
        n_long=13, n_short=13,
        vol_target_active=False,
        gross_leverage=1.0, cost_bps_one_side=6.0, slippage_bps=0.0,
        vix_derisk_factor=1.0, vix_level_threshold=32.0, vix_level_factor=0.3,
        use_call_rate_financing=True, long_financing_apply=True,
        bypass_ic_screen=False, diag_regime_split=True,
    )
    # Re-run to get predictions for scramble
    res_best = runner.run(cfg_best, export=False)
    pred_best = res_best["predictions"]

    real_sharpe = res_best["metrics"].get('sharpe', 0)
    scramble_sharpes = []
    np.random.seed(42)
    for i in range(20):
        shift = np.random.randint(20, 200)
        pred_scram = pred_best.shift(shift)
        cfg_scram = cfg_best.copy()
        cfg_scram = cfg_scram.set(bypass_ic_screen=True)
        res_s = bt_mod.run_backtest(panel, pred_scram, cfg_scram)
        m_s = bt_mod.compute_metrics(res_s, cfg_scram, panel["prices"])
        scramble_sharpes.append(m_s.get('sharpe', 0))

    scramble_sharpes = np.array(scramble_sharpes)
    p_value = (scramble_sharpes >= real_sharpe).mean()

    print(f"  Real Sharpe:     {real_sharpe:.3f}")
    print(f"  Scramble mean:   {scramble_sharpes.mean():.3f} ± {scramble_sharpes.std():.3f}")
    print(f"  P-value:         {p_value:.3f}")
    print(f"  Verdict:         {'PASS' if p_value < 0.05 else 'FAIL'}")

    # Save
    final = {
        "best_rebalance_freq": best_r,
        "best_sharpe": real_sharpe,
        "scramble_test": {
            "real_sharpe": float(real_sharpe),
            "scramble_mean": float(scramble_sharpes.mean()),
            "scramble_std": float(scramble_sharpes.std()),
            "p_value": float(p_value),
            "verdict": "PASS" if p_value < 0.05 else "FAIL",
        },
        "all_configs": {str(k): {"sharpe": str(v['metrics'].get('sharpe', 0)),
                                  "turnover": str(v['metrics'].get('annual_turnover', 0))}
                         for k, v in results.items()},
    }
    with open(OUT_DIR / "final_results.json", "w") as f:
        json.dump(final, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
