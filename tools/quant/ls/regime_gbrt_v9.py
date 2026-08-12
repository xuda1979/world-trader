#!/usr/bin/env python3
"""Regime-conditional GBRT v9: VIX interaction features + regime-aware training.

Previous approaches (v1-v8) tried blending separate models or overlaying
reversal signals. The reversal alpha was real in IC but failed scramble test
in backtest because naive linear blending can't capture non-linear
factor×regime interactions.

V9 takes a fundamentally different approach:
  1. Add VIX level as a feature to the GBRT model
  2. Add factor×VIX interaction features (reversal×VIX, momentum×VIX, etc.)
  3. The GBRT tree learns non-linear regime-conditional patterns directly
  4. No manual regime switching — the model handles it

This is the approach Gu-Kelly-Xiu (2020) advocate: let the ML model learn
the conditional factor structure rather than manually segmenting regimes.

Usage:
    python -m tools.quant.ls.regime_gbrt_v9
"""

import sys, os, time, json, copy
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from tools.quant.ls.config import Config
from tools.quant.ls import data as data_mod
from tools.quant.ls import factors as factors_mod
from tools.quant.ls import ic_screen
from tools.quant.ls import model as model_mod
from tools.quant.ls import backtest as bt_mod
from tools.quant.ls import runner

OUT_DIR = Path("tools/quant/ls/results/regime_gbrt_v9")
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


def compute_vix_interaction_factors(panel, vix, cfg):
    """Add VIX level and factor×VIX interaction features.

    These features let the GBRT tree learn non-linear regime-conditional
    factor patterns. The tree can learn:
    - "When VIX is high, reversal signal is 5x more predictive"
    - "When VIX > 30, momentum reverses direction"
    - "High-vol stocks overreact more when VIX is elevated"
    """
    returns = panel["returns"]
    prices = panel["prices"]
    volumes = panel["volumes"]
    bench_col = "SPY" if "SPY" in returns.columns else returns.columns[0]
    bench = returns[bench_col]

    # VIX features (broadcast to all tickers)
    vix_aligned = vix.reindex(returns.index).fillna(20.0)

    interaction = {}

    # 1. VIX level (same for all tickers at each date — tree can split on it)
    interaction["vix_level"] = pd.DataFrame(
        np.tile(vix_aligned.values[:, None], (1, len(returns.columns))),
        index=returns.index, columns=returns.columns
    )

    # 2. VIX z-score (how elevated is VIX relative to its recent history)
    vix_mean_60 = vix_aligned.rolling(60).mean()
    vix_std_60 = vix_aligned.rolling(60).std().replace(0, np.nan)
    vix_z = (vix_aligned - vix_mean_60) / vix_std_60
    vix_z = vix_z.fillna(0)
    interaction["vix_zscore"] = pd.DataFrame(
        np.tile(vix_z.values[:, None], (1, len(returns.columns))),
        index=returns.index, columns=returns.columns
    )

    # 3. VIX change (5d, 20d)
    for lb in [5, 20]:
        vix_change = vix_aligned.diff(lb)
        vix_change = vix_change.fillna(0)
        interaction[f"vix_change_{lb}d"] = pd.DataFrame(
            np.tile(vix_change.values[:, None], (1, len(returns.columns))),
            index=returns.index, columns=returns.columns
        )

    # 4. Reversal × VIX interaction
    for lb in [5, 10]:
        rev = -returns.rolling(lb).sum()
        # Cross-sectional z-score the reversal
        mu = rev.mean(axis=1)
        std = rev.std(axis=1).replace(0, np.nan)
        rev_z = rev.sub(mu, axis=0).div(std, axis=0)
        # Multiply by VIX z-score (stronger reversal when VIX elevated)
        interaction[f"rev{lb}d_x_vixz"] = rev_z * vix_z.values[:, None]

    # 5. Momentum × VIX interaction (momentum reverses in high-vol)
    mom_12_1m = prices.shift(21) / prices.shift(252) - 1
    mu = mom_12_1m.mean(axis=1)
    std = mom_12_1m.std(axis=1).replace(0, np.nan)
    mom_z = mom_12_1m.sub(mu, axis=0).div(std, axis=0)
    interaction["mom12_x_vixz"] = mom_z * vix_z.values[:, None]

    # 6. Volatility × VIX interaction (high-vol stocks react more to VIX)
    vol_60d = returns.rolling(60).std()
    mu = vol_60d.mean(axis=1)
    std = vol_60d.std(axis=1).replace(0, np.nan)
    vol_z = vol_60d.sub(mu, axis=0).div(std, axis=0)
    interaction["vol60_x_vixz"] = vol_z * vix_z.values[:, None]

    # 7. Volume surprise × VIX
    vol_surprise = volumes / volumes.rolling(60).mean().replace(0, np.nan)
    mu = vol_surprise.mean(axis=1)
    std = vol_surprise.std(axis=1).replace(0, np.nan)
    vs_z = vol_surprise.sub(mu, axis=0).div(std, axis=0)
    interaction["volsurp_x_vixz"] = vs_z * vix_z.values[:, None]

    # 8. Beta × VIX (high-beta stocks overreact in high-vol)
    cov = returns.rolling(60).cov(bench)
    var = bench.rolling(60).var()
    beta = cov.div(var.replace(0, np.nan), axis=0)
    interaction["beta_x_vixz"] = beta.clip(0, 3) * vix_z.values[:, None]

    # 9. Idiosyncratic vol × VIX
    res = returns.sub(bench, axis=0)
    ivol = res.rolling(20).std()
    mu = ivol.mean(axis=1)
    std = ivol.std(axis=1).replace(0, np.nan)
    ivol_z = ivol.sub(mu, axis=0).div(std, axis=0)
    interaction["ivol_x_vixz"] = ivol_z * vix_z.values[:, None]

    # 10. VIX regime indicator (binary: 1 if VIX > 25)
    vix_regime = (vix_aligned > 25).astype(float)
    interaction["vix_high_regime"] = pd.DataFrame(
        np.tile(vix_regime.values[:, None], (1, len(returns.columns))),
        index=returns.index, columns=returns.columns
    )

    # 11. Short-term reversal signals (the ones with strong HV IC)
    for lb in [3, 5, 10]:
        rev = -returns.rolling(lb).sum()
        mu = rev.mean(axis=1)
        std = rev.std(axis=1).replace(0, np.nan)
        interaction[f"reversal_{lb}d"] = rev.sub(mu, axis=0).div(std, axis=0)

    # 12. Dispersion-weighted momentum
    cs_std = returns.rolling(20).std()
    past_20d = returns.rolling(20).sum()
    cs_mean = past_20d.mean(axis=1)
    disp_mom = -(past_20d.sub(cs_mean, axis=0).div(cs_std.replace(0, np.nan), axis=0))
    interaction["disp_mom_20d"] = disp_mom

    # 13. VIX-scaled reversal (stronger weight when VIX is higher)
    for lb in [5, 10]:
        rev = -returns.rolling(lb).sum()
        mu = rev.mean(axis=1)
        std = rev.std(axis=1).replace(0, np.nan)
        rev_z = rev.sub(mu, axis=0).div(std, axis=0)
        interaction[f"rev{lb}d_x_vix"] = rev_z * (vix_aligned / 20).values[:, None]

    print(f"  Built {len(interaction)} VIX interaction features")
    return interaction


def run_config(panel, macro, vix, cfg, label, use_vix_features=False):
    """Run a full pipeline with optional VIX interaction features."""
    t0 = time.time()

    if use_vix_features:
        # Add VIX interaction features to the factor set
        vix_factors = compute_vix_interaction_factors(panel, vix, cfg)

        # Compute standard factors
        raw = factors_mod.compute_raw_factors(panel, cfg)
        extra = factors_mod.compute_extra_raw_factors(panel, cfg)
        ohlc = factors_mod.compute_ohlc_factors(panel, cfg) if hasattr(factors_mod, 'compute_ohlc_factors') else {}
        interactions = factors_mod.compute_interaction_features(panel, cfg) if hasattr(factors_mod, 'compute_interaction_features') else {}

        all_raw = {}
        all_raw.update(raw)
        all_raw.update(extra)
        all_raw.update(ohlc)
        all_raw.update(interactions)
        all_raw.update(vix_factors)

        processed = factors_mod.process_cross_section(all_raw, panel, cfg)

        # IC screen
        from tools.quant.ls.ic_screen import forward_returns, compute_all_ic, screen_factors
        fwd_ret = forward_returns(panel["prices"], cfg.return_horizon_fwd)
        ic_df = compute_all_ic(processed, fwd_ret, cfg)
        kept, stats, icir = screen_factors(ic_df, cfg, list(processed.keys()))
        sign_flips = {f: s.get("sign_flip", False) for f, s in stats.items()}
        print(f"  Kept {len(kept)} factors: {kept[:10]}...")

        # Run GBRT
        res_model = model_mod.roll_forward_gbrt(processed, panel, cfg,
                                                 kept_factors=kept, sign_flips=sign_flips)
        predictions = res_model["predictions"]

        # Backtest
        res_bt = bt_mod.run_backtest(panel, predictions, cfg)
        metrics = bt_mod.compute_metrics(res_bt, cfg, panel["prices"])

        # Regime split
        equity = res_bt["equity_curve"]
        daily_ret = equity.pct_change().fillna(0)
        vix_bt = vix.reindex(daily_ret.index).fillna(20.0)
        regime_sharpes = {}
        for rname, mask in [("normal", vix_bt <= 25), ("high_vol", vix_bt > 25), ("stress", vix_bt > 32)]:
            sub = daily_ret[mask.values]
            if len(sub) < 5:
                continue
            ann_ret = sub.mean() * 252
            ann_vol = sub.std() * np.sqrt(252)
            regime_sharpes[rname] = ann_ret / ann_vol if ann_vol > 0 else 0

        result = {
            "metrics": metrics,
            "regime_sharpes": regime_sharpes,
            "predictions": predictions,
            "equity_curve": equity,
        }
    else:
        # Standard runner
        result = runner.run(cfg, export=False)
        # Extract regime split
        equity = result["result"]["equity_curve"]
        daily_ret = equity.pct_change().fillna(0)
        vix_bt = vix.reindex(daily_ret.index).fillna(20.0)
        regime_sharpes = {}
        for rname, mask in [("normal", vix_bt <= 25), ("high_vol", vix_bt > 25), ("stress", vix_bt > 32)]:
            sub = daily_ret[mask.values]
            if len(sub) < 5:
                continue
            ann_ret = sub.mean() * 252
            ann_vol = sub.std() * np.sqrt(252)
            regime_sharpes[rname] = ann_ret / ann_vol if ann_vol > 0 else 0
        result["regime_sharpes"] = regime_sharpes

    dt = time.time() - t0
    m = result["metrics"]
    rs = result.get("regime_sharpes", {})
    sharpe = m.get('sharpe', 0)
    print(f"  {label:45s}  Sharpe={sharpe:.3f}  ret={m.get('annual_return',0):.3f}  "
          f"dd={m.get('max_drawdown',0):.3f}  to={m.get('annual_turnover',0):.1f}  "
          f"NM={rs.get('normal',0):.2f}  HV={rs.get('high_vol',0):.2f}  "
          f"Strs={rs.get('stress',0):.2f}  ({dt:.1f}s)")

    return result


def scramble_test(panel, predictions, cfg, vix, label, n_scrambles=20):
    """Scramble test: shift predictions randomly and compare Sharpe."""
    res = bt_mod.run_backtest(panel, predictions, cfg)
    m = bt_mod.compute_metrics(res, cfg, panel["prices"])
    real_sharpe = m.get('sharpe', 0)

    scramble_sharpes = []
    np.random.seed(42)
    for i in range(n_scrambles):
        shift = np.random.randint(20, 200)
        pred_scram = predictions.shift(shift)
        res_s = bt_mod.run_backtest(panel, pred_scram, cfg)
        m_s = bt_mod.compute_metrics(res_s, cfg, panel["prices"])
        scramble_sharpes.append(m_s.get('sharpe', 0))

    scramble_sharpes = np.array(scramble_sharpes)
    p_value = (scramble_sharpes >= real_sharpe).mean()

    print(f"\n  Scramble test: {label}")
    print(f"    Real:      {real_sharpe:.3f}")
    print(f"    Scramble:  {scramble_sharpes.mean():.3f} ± {scramble_sharpes.std():.3f}")
    print(f"    P-value:   {p_value:.3f}")
    print(f"    Verdict:   {'PASS' if p_value < 0.05 else 'FAIL'}")

    return real_sharpe, scramble_sharpes, p_value


def main():
    print("=" * 70)
    print("REGIME-CONDITIONAL GBRT V9 (VIX Interaction Features)")
    print("=" * 70)

    cfg_base, panel, macro = load_panel()
    vix = get_vix(panel, macro)

    print(f"\n  VIX: mean={vix.mean():.1f} > 25: {(vix>25).sum()}d ({100*(vix>25).mean():.1f}%)")

    # Config base
    cfg_common = dict(
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160,
        refit_freq=20,
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

    results = {}

    # 1. Champion baseline at different rebalance frequencies
    print("\n--- Phase 1: Champion baselines ---")
    for r_freq in [7, 10, 20]:
        cfg = Config(name=f"champion_r{r_freq}", rebalance_freq=r_freq,
                     bypass_ic_screen=False, **cfg_common)
        res = run_config(panel, macro, vix, cfg, f"Champion r={r_freq}")
        results[f"champion_r{r_freq}"] = res

    # 2. GBRT with VIX interaction features
    print("\n--- Phase 2: GBRT + VIX interaction features ---")

    # Build VIX interaction features
    print("  Computing VIX interaction features...")
    vix_features = compute_vix_interaction_factors(panel, vix, Config(**cfg_common))

    # Compute standard factors
    print("  Computing standard factors...")
    raw = factors_mod.compute_raw_factors(panel, Config(**cfg_common))
    extra = factors_mod.compute_extra_raw_factors(panel, Config(**cfg_common))
    ohlc = factors_mod.compute_ohlc_factors(panel, Config(**cfg_common)) if hasattr(factors_mod, 'compute_ohlc_factors') else {}
    std_interactions = factors_mod.compute_interaction_features(panel, Config(**cfg_common)) if hasattr(factors_mod, 'compute_interaction_features') else {}

    all_raw = {}
    all_raw.update(raw)
    all_raw.update(extra)
    all_raw.update(ohlc)
    all_raw.update(std_interactions)
    all_raw.update(vix_features)
    print(f"  Total factors: {len(all_raw)}")

    processed = factors_mod.process_cross_section(all_raw, panel, Config(**cfg_common))

    # IC screen
    from tools.quant.ls.ic_screen import forward_returns, compute_all_ic, screen_factors
    fwd_ret = forward_returns(panel["prices"], 10)
    ic_df = compute_all_ic(processed, fwd_ret, Config(**cfg_common))
    kept, stats, icir = screen_factors(ic_df, Config(**cfg_common), list(processed.keys()))
    sign_flips = {f: s.get("sign_flip", False) for f, s in stats.items()}
    print(f"  Kept {len(kept)} factors: {kept}")

    # Run GBRT with VIX features at different rebalance frequencies
    for r_freq in [7, 10, 20]:
        cfg = Config(name=f"vix_gbrt_r{r_freq}", rebalance_freq=r_freq,
                     bypass_ic_screen=True, **cfg_common)
        t0 = time.time()
        res_model = model_mod.roll_forward_gbrt(processed, panel, cfg,
                                                 kept_factors=kept, sign_flips=sign_flips)
        predictions = res_model["predictions"]
        res_bt = bt_mod.run_backtest(panel, predictions, cfg)
        metrics = bt_mod.compute_metrics(res_bt, cfg, panel["prices"])

        equity = res_bt["equity_curve"]
        daily_ret = equity.pct_change().fillna(0)
        vix_bt = vix.reindex(daily_ret.index).fillna(20.0)
        regime_sharpes = {}
        for rname, mask in [("normal", vix_bt <= 25), ("high_vol", vix_bt > 25), ("stress", vix_bt > 32)]:
            sub = daily_ret[mask.values]
            if len(sub) < 5:
                continue
            ann_ret = sub.mean() * 252
            ann_vol = sub.std() * np.sqrt(252)
            regime_sharpes[rname] = ann_ret / ann_vol if ann_vol > 0 else 0

        dt = time.time() - t0
        sharpe = metrics.get('sharpe', 0)
        print(f"  {'VIX-GBRT r=' + str(r_freq):45s}  Sharpe={sharpe:.3f}  "
              f"ret={metrics.get('annual_return',0):.3f}  dd={metrics.get('max_drawdown',0):.3f}  "
              f"to={metrics.get('annual_turnover',0):.1f}  "
              f"NM={regime_sharpes.get('normal',0):.2f}  HV={regime_sharpes.get('high_vol',0):.2f}  "
              f"Strs={regime_sharpes.get('stress',0):.2f}  ({dt:.1f}s)")

        results[f"vix_gbrt_r{r_freq}"] = {
            "metrics": metrics,
            "regime_sharpes": regime_sharpes,
            "predictions": predictions,
        }

    # 3. Scramble test on best VIX-GBRT
    print("\n--- Phase 3: Scramble validation ---")
    best_vix_key = max([k for k in results if k.startswith("vix_gbrt")],
                       key=lambda k: results[k]["metrics"].get('sharpe', 0))
    best_champ_key = max([k for k in results if k.startswith("champion")],
                         key=lambda k: results[k]["metrics"].get('sharpe', 0))

    print(f"\n  Best champion: {best_champ_key} Sharpe={results[best_champ_key]['metrics'].get('sharpe',0):.3f}")
    print(f"  Best VIX-GBRT: {best_vix_key} Sharpe={results[best_vix_key]['metrics'].get('sharpe',0):.3f}")

    # Scramble test the best VIX-GBRT
    cfg_scram = Config(name=f"scramble_{best_vix_key}",
                       rebalance_freq=int(best_vix_key.split('r')[-1]),
                       bypass_ic_screen=True, **cfg_common)
    real_s, scram_s, p_val = scramble_test(
        panel, results[best_vix_key]["predictions"], cfg_scram, vix, best_vix_key
    )

    # Summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"\n{'Strategy':<30s}  {'Sharpe':>7s}  {'Return':>7s}  {'MaxDD':>7s}  "
          f"{'TO':>6s}  {'Normal':>7s}  {'HighVol':>7s}  {'Stress':>7s}")
    print("-" * 85)
    for name, res in sorted(results.items(), key=lambda x: x[1]["metrics"].get('sharpe', 0), reverse=True):
        m = res["metrics"]
        rs = res.get("regime_sharpes", {})
        print(f"{name:<30s}  {m.get('sharpe',0):7.3f}  {m.get('annual_return',0):7.3f}  "
              f"{m.get('max_drawdown',0):7.3f}  {m.get('annual_turnover',0):6.1f}  "
              f"{rs.get('normal',0):7.3f}  {rs.get('high_vol',0):7.3f}  {rs.get('stress',0):7.3f}")

    print(f"\n  Scramble test ({best_vix_key}): p={p_val:.3f} → {'PASS' if p_val < 0.05 else 'FAIL'}")

    # Save
    final = {
        "best_strategy": best_vix_key if p_val < 0.05 else best_champ_key,
        "scramble": {"real": float(real_s), "p_value": float(p_val), "verdict": "PASS" if p_val < 0.05 else "FAIL"},
        "all_sharpes": {k: float(v["metrics"].get('sharpe', 0)) for k, v in results.items()},
    }
    with open(OUT_DIR / "results.json", "w") as f:
        json.dump(final, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
