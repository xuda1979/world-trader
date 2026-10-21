#!/usr/bin/env python3
"""Regime-conditional GBRT v11: refine best configs + scramble validation.

V10 found:
  - n=10 (10+10 names): Sharpe 0.940, HV 1.79, DD -2.4%, TO 1.7  ← best
  - rebalance_freq=14:  Sharpe 0.803, HV 2.04
  - VIX gate level has minimal impact (~0.68 all levels)

V11 combines the best parameters:
  1. n=10 × rebalance_freq ∈ {7, 10, 14, 20}
  2. n=12 × rebalance_freq ∈ {7, 10, 14} (interpolate between 10 and 13)
  3. Train window refinement (160 vs 200)
  4. Scramble validation on the top config

Usage:
    python -m tools.quant.ls.regime_gbrt_v11
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

OUT_DIR = Path("tools/quant/ls/results/regime_gbrt_v11")
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
    """Scramble test: shift predictions and compare Sharpe."""
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
    return real_sharpe, scramble_sharpes, p_value


def main():
    print("=" * 70)
    print("REGIME-CONDITIONAL GBRT V11 (Refinement + Validation)")
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
        rebalance_freq=7,
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

    # Phase 1: n=10 × rebalance freq
    print("\n--- Phase 1: n=10 × rebalance freq ---")
    for r_freq in [7, 10, 14, 20]:
        cfg = Config(**base).set(name=f"n10_r{r_freq}", rebalance_freq=r_freq)
        m, rs, res = run_with_regime_split(panel, vix, cfg, f"n10 r={r_freq}")
        all_results[f"n10_r{r_freq}"] = (m, rs, res)

    # Phase 2: n=12 × rebalance freq
    print("\n--- Phase 2: n=12 × rebalance freq ---")
    for r_freq in [7, 10, 14]:
        cfg = Config(**base).set(name=f"n12_r{r_freq}", n_long=12, n_short=12, rebalance_freq=r_freq)
        m, rs, res = run_with_regime_split(panel, vix, cfg, f"n12 r={r_freq}")
        all_results[f"n12_r{r_freq}"] = (m, rs, res)

    # Phase 3: n=10, tw refinement
    print("\n--- Phase 3: n=10, train window refinement ---")
    for tw in [140, 180, 200]:
        cfg = Config(**base).set(name=f"n10_tw{tw}", train_window=tw)
        m, rs, res = run_with_regime_split(panel, vix, cfg, f"n10 tw={tw}")
        all_results[f"n10_tw{tw}"] = (m, rs, res)

    # Phase 4: Best so far + scramble
    print("\n--- Phase 4: Identify best + scramble ---")
    best_name = max(all_results, key=lambda k: all_results[k][0].get('sharpe', 0))
    best_m, best_rs, best_res = all_results[best_name]
    print(f"\n  Best: {best_name}  Sharpe={best_m.get('sharpe',0):.3f}  HV={best_rs.get('high_vol',0):.3f}")

    # Find config details from name
    best_cfg = Config(**base)
    if "n12" in best_name:
        best_cfg = best_cfg.set(n_long=12, n_short=12)
    r_match = re.search(r'r(\d+)', best_name)
    if r_match:
        best_cfg = best_cfg.set(rebalance_freq=int(r_match.group(1)))
    tw_match = re.search(r'tw(\d+)', best_name)
    if tw_match:
        best_cfg = best_cfg.set(train_window=int(tw_match.group(1)))

    best_cfg = best_cfg.set(name="best_" + best_name)
    real_s, scram_s, p_val = scramble_test(panel, best_cfg, best_res, vix, best_name)

    # Also scramble-test the runner's own result (with IC screen)
    print("\n--- Also: scramble test on champion baseline (n=10 r=7) ---")
    cfg_base_c = Config(**base).set(name="champ_n10_r7")
    res_base_c = run_with_regime_split(panel, vix, cfg_base_c, "champion n10 r7")[2]
    real_s2, scram_s2, p_val2 = scramble_test(panel, cfg_base_c, res_base_c, vix, "n10_r7_runner")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY (sorted by Sharpe)")
    print("=" * 70)
    print(f"\n{'Config':<20s}  {'Sharpe':>7s}  {'Ret':>7s}  {'MaxDD':>7s}  {'TO':>6s}  {'Normal':>7s}  {'HighVol':>7s}  {'Stress':>7s}")
    print("-" * 90)
    for name, (m, rs, _) in sorted(all_results.items(), key=lambda x: x[1][0].get('sharpe', 0), reverse=True):
        print(f"{name:<20s}  {m.get('sharpe',0):7.3f}  {m.get('annual_return',0):7.3f}  "
              f"{m.get('max_drawdown',0):7.3f}  {m.get('annual_turnover',0):6.1f}  "
              f"{rs.get('normal',0):7.3f}  {rs.get('high_vol',0):7.3f}  {rs.get('stress',0):7.3f}")

    print(f"\n  Scramble ({best_name}): p={p_val:.3f} → {'PASS' if p_val<0.05 else 'FAIL'}")
    print(f"  Scramble (runner n10 r7): p={p_val2:.3f} → {'PASS' if p_val2<0.05 else 'FAIL'}")

    final = {
        "best": best_name,
        "best_sharpe": float(best_m.get('sharpe', 0)),
        "scramble_best": {"p": float(p_val), "verdict": "PASS" if p_val<0.05 else "FAIL"},
        "scramble_runner": {"p": float(p_val2), "verdict": "PASS" if p_val2<0.05 else "FAIL"},
        "all": {k: {"sharpe": float(v[0].get('sharpe', 0)), "hv": float(v[1].get('high_vol', 0))}
                for k, v in all_results.items()},
    }
    with open(OUT_DIR / "results.json", "w") as f:
        json.dump(final, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
