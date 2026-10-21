#!/usr/bin/env python3
"""Regime-conditional L/S strategy v6: comprehensive sweep + noise gate.

Focus: find the BEST regime-conditional strategy that passes the scramble test.

From v4-v5:
  - Champion alone (r=10) gets Sharpe 0.854 (best so far)
  - Reversal in high-vol gets HV Sharpe 6.9 but dilutes overall
  - The key question: can we get HIGH overall Sharpe AND HIGH HV Sharpe?

V6 tests:
  1. Full grid: rebalance_freq x blend_ratio x VIX_threshold
  2. Two-pass approach: champion normally, leverage up reversal in HV
  3. Scramble test on the best config
  4. Compare to champion baseline

Usage:
    python -m tools.quant.ls.regime_conditional_v6
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

OUT_DIR = Path("tools/quant/ls/results/regime_conditional_v6")
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


def build_blended(pred_base, pred_rev, vix, vix_thresh, rev_w, stress_thresh=32.0):
    """Blend predictions: champion when VIX <= thresh, 
    (1-rev_w)*champion + rev_w*reversal when VIX > thresh."""
    pred = pred_base.copy()
    for date in pred.index:
        vix_val = vix.reindex([date]).iloc[0] if date in vix.index else 20.0
        if vix_val > vix_thresh and vix_val <= stress_thresh:
            base = pred_base.loc[date].reindex(pred.columns).fillna(0)
            rev = pred_rev.loc[date].reindex(pred.columns).fillna(0)
            if base.std() > 0:
                base = (base - base.mean()) / base.std()
            if rev.std() > 0:
                rev = (rev - rev.mean()) / rev.std()
            pred.loc[date] = (1 - rev_w) * base + rev_w * rev
    return pred


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
    return metrics, rs


def main():
    print("=" * 70)
    print("REGIME-CONDITIONAL STRATEGY V6 (Comprehensive Sweep)")
    print("=" * 70)

    cfg_base, panel, macro = load_panel()
    vix = get_vix(panel, macro)

    # Run champion models at different rebalance frequencies
    champ_preds = {}
    for r_freq in [5, 10, 20]:
        print(f"\n--- Champion GBRT (r={r_freq}) ---")
        cfg = Config(
            name=f"champ_r{r_freq}",
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
        res = runner.run(cfg, export=False)
        champ_preds[r_freq] = res["predictions"]
        print(f"  Sharpe={res['metrics'].get('sharpe',0):.3f}")

    # Compute reversal predictions
    print("\n--- Computing reversal predictions ---")
    pred_rev = compute_reversal_predictions(panel, vix)

    # Full grid sweep
    print("\n" + "=" * 70)
    print("GRID SWEEP: rebalance_freq x blend_ratio x vix_threshold")
    print("=" * 70)

    all_results = []

    for r_freq in [5, 10, 20]:
        pred_base = champ_preds[r_freq]
        cfg_bt = Config(
            name=f"bt_r{r_freq}",
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
            bypass_ic_screen=True, diag_regime_split=True,
        )

        for vix_thresh in [22, 25, 28]:
            for rev_w in [0.0, 0.3, 0.5, 0.7, 1.0]:
                pred = build_blended(pred_base, pred_rev, vix, float(vix_thresh), rev_w)
                m, rs = run_bt(panel, pred, cfg_bt, vix)
                sharpe = m.get('sharpe', 0)
                all_results.append({
                    'r_freq': r_freq,
                    'vix_thresh': vix_thresh,
                    'rev_w': rev_w,
                    'sharpe': sharpe,
                    'ret': m.get('annual_return', 0),
                    'dd': m.get('max_drawdown', 0),
                    'to': m.get('annual_turnover', 0),
                    'hv_sharpe': rs.get('high_vol', 0),
                    'stress_sharpe': rs.get('stress', 0),
                    'normal_sharpe': rs.get('normal', 0),
                })
                print(f"  r={r_freq:2d}  vix={vix_thresh:2d}  rev_w={rev_w:.1f}  "
                      f"Sharpe={sharpe:.3f}  dd={m.get('max_drawdown',0):.3f}  "
                      f"to={m.get('annual_turnover',0):.1f}  "
                      f"HV={rs.get('high_vol',0):.2f}")

    # Sort by Sharpe
    df = pd.DataFrame(all_results)
    df = df.sort_values('sharpe', ascending=False)
    df.to_csv(OUT_DIR / "grid_sweep.csv", index=False)

    print("\n" + "=" * 70)
    print("TOP 10 STRATEGIES BY SHARPE")
    print("=" * 70)
    print(f"{'r_freq':>5s}  {'vix':>4s}  {'rev_w':>5s}  {'Sharpe':>7s}  {'Return':>7s}  "
          f"{'MaxDD':>7s}  {'TO':>6s}  {'HV_SH':>6s}  {'Strs_SH':>7s}")
    print("-" * 68)
    for _, row in df.head(10).iterrows():
        print(f"{int(row.r_freq):5d}  {int(row.vix_thresh):4d}  {row.rev_w:5.1f}  "
              f"{row.sharpe:7.3f}  {row.ret:7.3f}  {row.dd:7.3f}  "
              f"{row.to:6.1f}  {row.hv_sharpe:6.2f}  {row.stress_sharpe:7.2f}")

    # Scramble test on top strategy
    best = df.iloc[0]
    print(f"\n--- Scramble test on best strategy ---")
    print(f"  Config: r={best.r_freq} vix_thresh={best.vix_thresh} rev_w={best.rev_w}")

    pred_base = champ_preds[int(best.r_freq)]
    cfg_bt = Config(
        name=f"bt_r{int(best.r_freq)}",
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160, refit_freq=20, rebalance_freq=int(best.r_freq),
        predict_horizon=10, return_horizon_fwd=10,
        n_long=13, n_short=13,
        vol_target_active=False,
        gross_leverage=1.0, cost_bps_one_side=6.0, slippage_bps=0.0,
        vix_derisk_factor=1.0, vix_level_threshold=32.0, vix_level_factor=0.3,
        use_call_rate_financing=True, long_financing_apply=True,
        bypass_ic_screen=True, diag_regime_split=True,
    )

    pred_real = build_blended(pred_base, pred_rev, vix, float(best.vix_thresh), best.rev_w)
    m_real, _ = run_bt(panel, pred_real, cfg_bt, vix)
    real_sharpe = m_real.get('sharpe', 0)

    scramble_sharpes = []
    np.random.seed(42)
    for i in range(20):
        shift = np.random.randint(20, 100)
        pred_scram = pred_rev.shift(shift)
        pred_blend = build_blended(pred_base, pred_scram, vix,
                                    float(best.vix_thresh), best.rev_w)
        m, _ = run_bt(panel, pred_blend, cfg_bt, vix)
        scramble_sharpes.append(m.get('sharpe', 0))

    scramble_sharpes = np.array(scramble_sharpes)
    p_value = (scramble_sharpes >= real_sharpe).mean()

    print(f"  Real Sharpe:     {real_sharpe:.3f}")
    print(f"  Scramble mean:   {scramble_sharpes.mean():.3f} ± {scramble_sharpes.std():.3f}")
    print(f"  P-value:         {p_value:.3f}")
    print(f"  Verdict:         {'PASS' if p_value < 0.05 else 'FAIL'}")

    # Save final results
    results = {
        "best_config": {
            "rebalance_freq": int(best.r_freq),
            "vix_threshold": int(best.vix_thresh),
            "reversal_weight": float(best.rev_w),
            "sharpe": float(best.sharpe),
        },
        "scramble_test": {
            "real_sharpe": float(real_sharpe),
            "scramble_mean": float(scramble_sharpes.mean()),
            "p_value": float(p_value),
            "verdict": "PASS" if p_value < 0.05 else "FAIL",
        },
        "top_10": df.head(10).to_dict('records'),
    }
    with open(OUT_DIR / "final_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  Results saved to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
