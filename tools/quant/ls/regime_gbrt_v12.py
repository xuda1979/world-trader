#!/usr/bin/env python3
"""Regime-conditional GBRT v12: refine around the n10_r14 winner.

v11 found n10_r14: Sharpe 1.431 (PASS scramble). V12 refines:
  1. Rebalance frequency near 14: {10, 12, 14, 16, 18, 21}
  2. Names near 10: {9, 10, 11} × r=14
  3. refit_freq refinement (freshness of retrain): {10, 20}
  4. Confirm the full production config (not just bypass) 

Usage:
    python -m tools.quant.ls.regime_gbrt_v12
"""

import sys, os, time, json, re
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from tools.quant.ls.config import Config
from tools.quant.ls import data as data_mod
from tools.quant.ls import backtest as bt_mod
from tools.quant.ls import runner

OUT_DIR = Path("tools/quant/ls/results/regime_gbrt_v12")
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
        if len(vix) > 100 and vix.std() > 0.1:
            return vix.reindex(panel["prices"].index).ffill()
    prices = panel["prices"]
    if "SPY" in prices.columns:
        spy_ret = np.log(prices["SPY"] / prices["SPY"].shift(1))
        proxy = (spy_ret.rolling(20).std() * np.sqrt(252) * 100).reindex(prices.index).ffill()
        print(f"  Using proxy VIX: mean={proxy.mean():.1f}, >25: {(proxy>25).sum()}d")
        return proxy
    return pd.Series(20.0, index=prices.index)


def run_with_regime_split(panel, vix, cfg, label):
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


def scramble_test(panel, cfg, res, vix, label, n_scrambles=30):
    pred = res["predictions"]
    cfg_bt = cfg.copy()
    cfg_bt = cfg_bt.set(bypass_ic_screen=True)
    res_real = bt_mod.run_backtest(panel, pred, cfg_bt)
    real_sharpe = bt_mod.compute_metrics(res_real, cfg_bt, panel["prices"]).get('sharpe', 0)

    scramble_sharpes = []
    np.random.seed(42)
    for i in range(n_scrambles):
        shift = np.random.randint(20, 200)
        pred_s = pred.shift(shift)
        res_s = bt_mod.run_backtest(panel, pred_s, cfg_bt)
        m_s = bt_mod.compute_metrics(res_s, cfg_bt, panel["prices"])
        scramble_sharpes.append(m_s.get('sharpe', 0))

    scramble_sharpes = np.array(scramble_sharpes)
    p_value = (scramble_sharpes >= real_sharpe).mean()
    print(f"\n  Scramble test ({label}):")
    print(f"    Real:      {real_sharpe:.3f}")
    print(f"    Scramble:  {scramble_sharpes.mean():.3f} ± {scramble_sharpes.std():.3f}")
    print(f"    P-value:   {p_value:.3f}")
    print(f"    Verdict:   {'PASS' if p_value < 0.05 else 'FAIL'}")
    return real_sharpe, p_value


def main():
    print("=" * 70)
    print("REGIME-CONDITIONAL GBRT V12 (Refine n10_r14 Winner)")
    print("=" * 70)

    cfg_base, panel, macro = load_panel()
    vix = get_vix(panel, macro)
    print(f"  VIX: >25: {(vix>25).sum()}d  mean={vix.mean():.1f}")

    base = dict(
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160,
        refit_freq=20,
        rebalance_freq=14,
        predict_horizon=10,
        return_horizon_fwd=10,
        n_long=10,
        n_short=10,
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

    # Phase 1: rebalance freq refinement around 14
    print("\n--- Phase 1: rebalance freq refinement (n=10) ---")
    for r_freq in [10, 12, 14, 16, 18, 21]:
        cfg = Config(**base).set(name=f"n10_r{r_freq}", rebalance_freq=r_freq)
        m, rs, res = run_with_regime_split(panel, vix, cfg, f"n10 r={r_freq}")
        all_results[f"n10_r{r_freq}"] = (m, rs, res)

    # Phase 2: names refinement at r=14
    print("\n--- Phase 2: names refinement (r=14) ---")
    for n in [9, 10, 11]:
        cfg = Config(**base).set(name=f"n{n}_r14", n_long=n, n_short=n)
        m, rs, res = run_with_regime_split(panel, vix, cfg, f"n={n} r=14")
        all_results[f"n{n}_r14"] = (m, rs, res)

    # Phase 3: refit_freq refinement
    print("\n--- Phase 3: refit_freq refinement (n10 r14) ---")
    for rf in [10, 20, 40]:
        cfg = Config(**base).set(name=f"n10_r14_refit{rf}", refit_freq=rf)
        m, rs, res = run_with_regime_split(panel, vix, cfg, f"n10 r14 refit={rf}")
        all_results[f"n10_r14_refit{rf}"] = (m, rs, res)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY (sorted by Sharpe)")
    print("=" * 70)
    print(f"\n{'Config':<22s}  {'Sharpe':>7s}  {'Ret':>7s}  {'MaxDD':>7s}  {'TO':>6s}  {'Normal':>7s}  {'HighVol':>7s}  {'Stress':>7s}")
    print("-" * 90)
    for name, (m, rs, _) in sorted(all_results.items(), key=lambda x: x[1][0].get('sharpe', 0), reverse=True):
        print(f"{name:<22s}  {m.get('sharpe',0):7.3f}  {m.get('annual_return',0):7.3f}  "
              f"{m.get('max_drawdown',0):7.3f}  {m.get('annual_turnover',0):6.1f}  "
              f"{rs.get('normal',0):7.3f}  {rs.get('high_vol',0):7.3f}  {rs.get('stress',0):7.3f}")

    # Scramble test the top 2
    best_names = [k for k, _ in sorted(all_results.items(), key=lambda x: x[1][0].get('sharpe', 0), reverse=True)[:2]]
    for bname in best_names:
        bm, brs, bres = all_results[bname]
        # reconstruct config
        cfg = Config(**base)
        r_m = re.search(r'r(\d+)', bname)
        if r_m:
            cfg = cfg.set(rebalance_freq=int(r_m.group(1)))
        n_m = re.search(r'n(\d+)_', bname)
        if n_m:
            cfg = cfg.set(n_long=int(n_m.group(1)), n_short=int(n_m.group(1)))
        rf_m = re.search(r'refit(\d+)', bname)
        if rf_m:
            cfg = cfg.set(refit_freq=int(rf_m.group(1)))
        cfg = cfg.set(name="best_" + bname)
        scramble_test(panel, cfg, bres, vix, bname)

    # Save
    final = {
        "all": {k: {"sharpe": float(v[0].get('sharpe', 0)), "hv": float(v[1].get('high_vol', 0))}
                for k, v in all_results.items()},
    }
    with open(OUT_DIR / "results.json", "w") as f:
        json.dump(final, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
