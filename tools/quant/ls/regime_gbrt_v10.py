#!/usr/bin/env python3
"""Regime-conditional strategy v10: parameter tuning for high-vol resilience.

V9 showed adding VIX features to GBRT hurts (extra noise). But the champion
GBRT with r=7 already gets Sharpe 0.582 with good HV performance.

V10 focuses on TUNING the champion config for better high-vol performance:
  1. Sweep n_long/n_short (more names = more diversification in high-vol)
  2. Sweep train_window (shorter window adapts faster to regime changes)
  3. Sweep gbrt parameters (depth, learning_rate, n_estimators)
  4. Test different VIX stress gate levels (30, 35, 40)
  5. Test vol-targeting (scale exposure by realized vol)

Usage:
    python -m tools.quant.ls.regime_gbrt_v10
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

OUT_DIR = Path("tools/quant/ls/results/regime_gbrt_v10")
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
        if len(vix) > 100 and vix.std() > 0.1:  # check non-constant
            return vix.reindex(panel["prices"].index).ffill()
    # Proxy VIX from SPY realized vol
    prices = panel["prices"]
    if "SPY" in prices.columns:
        spy_ret = np.log(prices["SPY"] / prices["SPY"].shift(1))
        proxy = (spy_ret.rolling(20).std() * np.sqrt(252) * 100).reindex(prices.index).ffill()
        print(f"  Using proxy VIX (FRED unavailable): mean={proxy.mean():.1f}, >25: {(proxy>25).sum()}d")
        return proxy
    return pd.Series(20.0, index=prices.index)


def run_with_regime_split(panel, vix, cfg, label):
    """Run full pipeline and report metrics with regime split."""
    t0 = time.time()
    res = runner.run(cfg, export=False)
    m = res["metrics"]

    equity = res["result"]["equity_curve"]
    daily_ret = equity.pct_change().fillna(0)
    vix_bt = vix.reindex(daily_ret.index).fillna(20.0)

    rs = {}
    for name, mask in [("normal", vix_bt <= 25), ("high_vol", vix_bt > 25), ("stress", vix_bt > 32)]:
        sub = daily_ret[mask.values]
        if len(sub) < 5:
            continue
        ann_ret = sub.mean() * 252
        ann_vol = sub.std() * np.sqrt(252)
        rs[name] = ann_ret / ann_vol if ann_vol > 0 else 0

    dt = time.time() - t0
    sharpe = m.get('sharpe', 0)
    print(f"  {label:50s}  Sharpe={sharpe:.3f}  ret={m.get('annual_return',0):.3f}  "
          f"dd={m.get('max_drawdown',0):.3f}  to={m.get('annual_turnover',0):.1f}  "
          f"NM={rs.get('normal',0):.2f}  HV={rs.get('high_vol',0):.2f}  "
          f"Strs={rs.get('stress',0):.2f}  ({dt:.0f}s)")

    return m, rs, res


def main():
    print("=" * 70)
    print("REGIME-CONDITIONAL GBRT V10 (Parameter Tuning for High-Vol)")
    print("=" * 70)

    cfg_base, panel, macro = load_panel()
    vix = get_vix(panel, macro)

    print(f"\n  VIX: mean={vix.mean():.1f} > 25: {(vix>25).sum()}d ({100*(vix>25).mean():.1f}%)")

    base = dict(
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160,
        refit_freq=20,
        rebalance_freq=7,
        predict_horizon=10,
        return_horizon_fwd=10,
        n_long=13,
        n_short=13,
        vol_target_active=False,
        gross_leverage=1.0,
        cost_bps_one_side=6.0,
        slippage_bps=0.0,
        vix_derisk_factor=1.0,
        vix_level_threshold=32.0,
        vix_level_factor=0.3,
        use_call_rate_financing=True,
        long_financing_apply=True,
        diag_regime_split=True,
    )

    all_results = {}

    # Phase 1: Baseline
    print("\n--- Phase 1: Baseline ---")
    cfg = Config(**base).set(name="baseline_r7")
    m, rs, res = run_with_regime_split(panel, vix, cfg, "Baseline (r=7, n=13)")
    all_results["baseline"] = (m, rs)

    # Phase 2: Sweep n_long/n_short
    print("\n--- Phase 2: Sweep n_long/n_short ---")
    for n in [8, 10, 15, 20]:
        cfg = Config(**base).set(name=f"n{n}_r7", n_long=n, n_short=n)
        m, rs, _ = run_with_regime_split(panel, vix, cfg, f"n={n} (r=7)")
        all_results[f"n{n}"] = (m, rs)

    # Phase 3: Sweep train_window
    print("\n--- Phase 3: Sweep train_window ---")
    for tw in [100, 120, 200]:
        cfg = Config(**base).set(name=f"tw{tw}_r7", train_window=tw)
        m, rs, _ = run_with_regime_split(panel, vix, cfg, f"train_window={tw} (r=7)")
        all_results[f"tw{tw}"] = (m, rs)

    # Phase 4: Sweep VIX stress gate
    print("\n--- Phase 4: Sweep VIX stress gate ---")
    for thresh, factor in [(30, 0.3), (32, 0.3), (32, 0.5), (35, 0.3), (None, 0.0)]:
        if thresh is None:
            label = "no_gate"
            cfg = Config(**base).set(name="no_gate_r7", vix_level_threshold=None, vix_level_factor=0.0)
        else:
            label = f"vix{thresh}_f{factor}"
            cfg = Config(**base).set(name=f"{label}_r7", vix_level_threshold=float(thresh),
                         vix_level_factor=factor)
        m, rs, _ = run_with_regime_split(panel, vix, cfg, f"VIX gate: thresh={thresh} factor={factor}")
        all_results[label] = (m, rs)

    # Phase 5: Sweep rebalance frequency (fine-grained)
    print("\n--- Phase 5: Sweep rebalance frequency ---")
    for r_freq in [5, 10, 14]:
        cfg = Config(**base).set(name=f"r{r_freq}", rebalance_freq=r_freq)
        m, rs, _ = run_with_regime_split(panel, vix, cfg, f"rebalance_freq={r_freq}")
        all_results[f"r{r_freq}"] = (m, rs)

    # Phase 6: Sweep GBRT parameters
    print("\n--- Phase 6: Sweep GBRT depth/learning_rate ---")
    for depth, lr, n_est in [(3, 0.05, 200), (2, 0.1, 100), (2, 0.02, 300)]:
        cfg = Config(**base).set(name=f"d{depth}_lr{lr}_n{n_est}",
                     gbrt_max_depth=depth, gbrt_learning_rate=lr, gbrt_n_estimators=n_est)
        m, rs, _ = run_with_regime_split(panel, vix, cfg,
                                          f"depth={depth} lr={lr} n_est={n_est}")
        all_results[f"d{depth}_lr{lr}_n{n_est}"] = (m, rs)

    # Summary
    print("\n" + "=" * 70)
    print("FULL RESULTS (sorted by Sharpe)")
    print("=" * 70)
    print(f"\n{'Config':<30s}  {'Sharpe':>7s}  {'Return':>7s}  {'MaxDD':>7s}  "
          f"{'TO':>6s}  {'Normal':>7s}  {'HighVol':>7s}  {'Stress':>7s}")
    print("-" * 85)
    for name, (m, rs) in sorted(all_results.items(), key=lambda x: x[0][0].get('sharpe', 0), reverse=True):
        print(f"{name:<30s}  {m.get('sharpe',0):7.3f}  {m.get('annual_return',0):7.3f}  "
              f"{m.get('max_drawdown',0):7.3f}  {m.get('annual_turnover',0):6.1f}  "
              f"{rs.get('normal',0):7.3f}  {rs.get('high_vol',0):7.3f}  {rs.get('stress',0):7.3f}")

    # Best config
    best_name = max(all_results, key=lambda k: all_results[k][0].get('sharpe', 0))
    best_m, best_rs = all_results[best_name]
    print(f"\n  Best: {best_name}  Sharpe={best_m.get('sharpe',0):.3f}  "
          f"HV Sharpe={best_rs.get('high_vol',0):.3f}")

    # Save
    final = {
        "best": best_name,
        "best_sharpe": float(best_m.get('sharpe', 0)),
        "all": {k: {"sharpe": float(v[0].get('sharpe', 0)),
                     "hv_sharpe": float(v[1].get('high_vol', 0)),
                     "turnover": float(v[0].get('annual_turnover', 0))}
                for k, v in all_results.items()},
    }
    with open(OUT_DIR / "results.json", "w") as f:
        json.dump(final, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
