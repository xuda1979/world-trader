#!/usr/bin/env python3
"""Regime-conditional L/S strategy v7: pure reversal in high-vol + validation.

V6 showed that blending reversal with champion HURTS overall Sharpe.
But the high-vol regime Sharpe is 6.9+ for reversal.

V7 tests:
  1. Does the reversal signal ALONE pass the scramble test?
  2. Does the reversal signal in HIGH-VOL only pass the scramble test?
  3. What's the best overall approach: champion alone vs regime-conditional?

The key question: is the high-vol reversal alpha REAL or noise?

Usage:
    python -m tools.quant.ls.regime_conditional_v7
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

OUT_DIR = Path("tools/quant/ls/results/regime_conditional_v7")
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


def run_bt(panel, predictions, cfg, vix):
    res = bt_mod.run_backtest(panel, predictions, cfg)
    metrics = bt_mod.compute_metrics(res, cfg, panel["prices"])
    equity = res["equity_curve"]
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
    return metrics, rs, daily_ret


def scramble_test(panel, predictions_fn, cfg, vix, label, n_scrambles=30):
    """Run scramble test: shuffle the signal and compare."""
    # Real
    pred_real = predictions_fn(shuffle_shift=0)
    m_real, rs_real, _ = run_bt(panel, pred_real, cfg, vix)
    real_sharpe = m_real.get('sharpe', 0)

    # Scrambled
    scramble_sharpes = []
    np.random.seed(42)
    for i in range(n_scrambles):
        shift = np.random.randint(20, 200)
        pred_scram = predictions_fn(shuffle_shift=shift)
        m, _, _ = run_bt(panel, pred_scram, cfg, vix)
        scramble_sharpes.append(m.get('sharpe', 0))

    scramble_sharpes = np.array(scramble_sharpes)
    p_value = (scramble_sharpes >= real_sharpe).mean()

    print(f"\n  {label}:")
    print(f"    Real Sharpe:      {real_sharpe:.3f}")
    print(f"    Scramble Sharpe:  mean={scramble_sharpes.mean():.3f}  std={scramble_sharpes.std():.3f}")
    print(f"    P-value:          {p_value:.3f}")
    print(f"    Verdict:          {'PASS' if p_value < 0.05 else 'FAIL'}")
    if rs_real:
        for rn, rs in rs_real.items():
            print(f"    {rn:8s} Sharpe: {rs:.3f}")

    return real_sharpe, scramble_sharpes, p_value


def main():
    print("=" * 70)
    print("REGIME-CONDITIONAL STRATEGY V7 (Validation Focus)")
    print("=" * 70)

    cfg_base, panel, macro = load_panel()
    vix = get_vix(panel, macro)

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

    # Test 1: Pure reversal signal (always on)
    print("\n" + "=" * 70)
    print("TEST 1: Pure reversal signal (always on) — scramble test")
    print("=" * 70)
    s1, sc1, p1 = scramble_test(panel,
        lambda shuffle_shift: pred_rev if shuffle_shift == 0 else pred_rev.shift(shuffle_shift),
        cfg_bt, vix, "Pure reversal (always)")

    # Test 2: Reversal only in high-vol (VIX > 25), flat otherwise
    print("\n" + "=" * 70)
    print("TEST 2: Reversal only in high-vol (VIX>25), flat otherwise")
    print("=" * 70)
    def make_hv_only(shuffle_shift):
        pred = pd.DataFrame(0.0, index=pred_rev.index, columns=pred_rev.columns)
        src = pred_rev if shuffle_shift == 0 else pred_rev.shift(shuffle_shift)
        for date in pred.index:
            vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
            if vix_val > 25.0 and vix_val <= 32.0:
                pred.loc[date] = src.loc[date].reindex(pred.columns).fillna(0)
        return pred
    s2, sc2, p2 = scramble_test(panel, make_hv_only, cfg_bt, vix, "HV-only reversal")

    # Test 3: Reversal only in high-vol, no stress gate
    print("\n" + "=" * 70)
    print("TEST 3: Reversal in high-vol (VIX>25), NO stress gate")
    print("=" * 70)
    cfg_no_gate = cfg_bt.copy()
    cfg_no_gate = cfg_no_gate.set(vix_level_threshold=None, vix_level_factor=0.0)
    def make_hv_no_gate(shuffle_shift):
        pred = pd.DataFrame(0.0, index=pred_rev.index, columns=pred_rev.columns)
        src = pred_rev if shuffle_shift == 0 else pred_rev.shift(shuffle_shift)
        for date in pred.index:
            vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
            if vix_val > 25.0:
                pred.loc[date] = src.loc[date].reindex(pred.columns).fillna(0)
        return pred
    s3, sc3, p3 = scramble_test(panel, make_hv_no_gate, cfg_no_gate, vix, "HV reversal (no gate)")

    # Test 4: Champion baseline (no regime switching)
    print("\n" + "=" * 70)
    print("TEST 4: Champion baseline (r=10) — for reference")
    print("=" * 70)
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
    champ_metrics = res_champ["metrics"]
    print(f"  Champion Sharpe: {champ_metrics.get('sharpe',0):.3f}")

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"\n  {'Strategy':<35s}  {'Sharpe':>7s}  {'P-value':>8s}  {'Verdict':>8s}")
    print(f"  {'-'*35}  {'-'*7}  {'-'*8}  {'-'*8}")
    print(f"  {'Pure reversal (always)':<35s}  {s1:7.3f}  {p1:8.3f}  {'PASS' if p1<0.05 else 'FAIL':>8s}")
    print(f"  {'HV-only reversal (VIX>25)':<35s}  {s2:7.3f}  {p2:8.3f}  {'PASS' if p2<0.05 else 'FAIL':>8s}")
    print(f"  {'HV reversal (no gate)':<35s}  {s3:7.3f}  {p3:8.3f}  {'PASS' if p3<0.05 else 'FAIL':>8s}")
    print(f"  {'Champion (r=10)':<35s}  {champ_metrics.get('sharpe',0):7.3f}  {'n/a':>8s}  {'n/a':>8s}")

    results = {
        "pure_reversal": {"sharpe": s1, "p_value": p1, "verdict": "PASS" if p1<0.05 else "FAIL"},
        "hv_only_reversal": {"sharpe": s2, "p_value": p2, "verdict": "PASS" if p2<0.05 else "FAIL"},
        "hv_no_gate": {"sharpe": s3, "p_value": p3, "verdict": "PASS" if p3<0.05 else "FAIL"},
        "champion": {"sharpe": champ_metrics.get('sharpe', 0)},
    }
    with open(OUT_DIR / "validation_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
