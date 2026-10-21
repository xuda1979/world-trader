#!/usr/bin/env python3
"""Regime-conditional GBRT v13: OUT-OF-SAMPLE validation on deep 8y panel.

The n10_r14 config (Sharpe 1.434) was found on the 2-year polygon panel.
This script validates whether it GENERALIZES to the deeper 8-year (2018-2026)
twelve_big / twelve_liq panels — the repo's gold-standard OOS test.

If n10_r14 holds on 8y, it's a genuine, robust champion config.

Usage:
    python -m tools.quant.ls.regime_gbrt_v13_oos
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

OUT_DIR = Path("tools/quant/ls/results/regime_gbrt_v13")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_panel(data_dir, start_date=None):
    cfg = Config(data_dir=data_dir, use_macro=True, start_date=start_date)
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
        print(f"  Proxy VIX: mean={proxy.mean():.1f}, >25: {(proxy>25).sum()}d (>25: {100*(proxy>25).mean():.1f}%)")
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
    print(f"  {label:45s}  Sharpe={sharpe:.3f}  ret={m.get('annual_return',0):.3f}  "
          f"dd={m.get('max_drawdown',0):.3f}  to={m.get('annual_turnover',0):.1f}  "
          f"NM={rs.get('normal',0):.2f}  HV={rs.get('high_vol',0):.2f}  "
          f"({dt:.0f}s)")
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
        shift = np.random.randint(20, 400)
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
    print("V13: OUT-OF-SAMPLE VALIDATION of n10_r14 on deep panels")
    print("=" * 70)

    n10_r14_cfg = dict(
        data_dir="tools/quant/data/polygon",  # replaced per panel
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

    # Test on: 2y polygon (baseline), 8y twelve_liq, and 8y twelve_big
    panels = [
        ("polygon_2y", "tools/quant/data/polygon", None),
        ("twelve_liq_8y", "tools/quant/data/twelve_liq", "2018-01-01"),
        ("twelve_big_8y", "tools/quant/data/twelve_big", "2018-01-01"),
    ]

    results = {}
    for pname, data_dir, start in panels:
        print(f"\n{'='*70}")
        print(f"=== PANEL: {pname} (dir={data_dir}) ===")
        print(f"{'='*70}")
        try:
            cfg, panel, macro = load_panel(data_dir, start)
            vix = get_vix(panel, macro)
            print(f"  Panel: {len(panel['prices'])} bars, {panel['prices'].shape[1]} names, "
                  f"{panel['prices'].index[0].date()}..{panel['prices'].index[-1].date()}")
            print(f"  VIX>25: {(vix>25).sum()}d")

            cfg_run = Config(**n10_r14_cfg).set(data_dir=data_dir, name=f"n10_r14_{pname}")
            m, rs, res = run_with_regime_split(panel, vix, cfg_run, f"n10_r14 on {pname}")
            results[pname] = {"metrics": m, "regime": rs}

            # Scramble test
            if pname != "polygon_2y":  # polygon already validated
                real_s, p_val = scramble_test(panel, cfg_run, res, vix, f"{pname}_n10_r14")
                results[pname]["scramble"] = {"real": float(real_s), "p": float(p_val),
                                               "verdict": "PASS" if p_val < 0.05 else "FAIL"}
        except Exception as e:
            print(f"  ERROR on {pname}: {e}")
            results[pname] = {"error": str(e)}

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: n10_r14 across panels")
    print("=" * 70)
    for pname, res in results.items():
        if "error" in res:
            print(f"\n  {pname}: ERROR {res['error']}")
            continue
        m = res["metrics"]
        rs = res["regime"]
        sc = res.get("scramble", {})
        print(f"\n  {pname}:")
        print(f"    Sharpe={m.get('sharpe',0):.3f}  ret={m.get('annual_return',0):.3f}  "
              f"dd={m.get('max_drawdown',0):.3f}  to={m.get('annual_turnover',0):.1f}")
        print(f"    Normal={rs.get('normal',0):.3f}  HighVol={rs.get('high_vol',0):.3f}")
        if sc:
            print(f"    Scramble: p={sc.get('p', float('nan')):.3f} → {sc.get('verdict','?')}")

    with open(OUT_DIR / "oos_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    return 0


if __name__ == "__main__":
    sys.exit(main())
