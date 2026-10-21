#!/usr/bin/env python3
"""Regime-conditional L/S strategy: different models for VIX<=25 vs VIX>25.

Research findings (regime_alpha_research.py):
  - 12m momentum ICIR 2.03 in high-vol (t=8.14) vs 0.11 normal → 18x stronger
  - Short-term reversal ICIR 0.80 in high-vol vs 0.04 normal → 20x stronger
  - Vol/risk factors (ATR, range_vol, vol_60d) 4-6x stronger in high-vol
  - Custom hv_disp_mom_20d ICIR=1.05, hv_reversal_10d ICIR=0.66
  - Mean absolute return 1.61x higher → more alpha per trade

Strategy design:
  NORMAL regime (VIX <= 25): champion GBRT model (h=10, n=13, vt=30)
  HIGH-VOL regime (VIX > 25): reversal-tilted model with:
    - Shorter prediction horizon (5d instead of 10d)
    - More names (n=20 for broader spread)
    - Reversal + vol factors emphasized
    - Higher vol target (captures higher dispersion)
    - Same VIX>=32 stress gate (cut to 30% gross)

This is a PROTOTYPE. The regime switch happens at rebalance time:
  if VIX[t] > 25 → use high-vol config
  else            → use normal config

Usage:
    python -m tools.quant.ls.regime_conditional_strategy
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
from tools.quant.ls import portfolio as pf
from tools.quant.ls import backtest as bt_mod
from tools.quant.ls import runner
from tools.quant.ls import diagnostics as diag_mod

OUT_DIR = Path("tools/quant/ls/results/regime_conditional")
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIX_HIGH = 25.0
VIX_STRESS = 32.0


def load_panel():
    """Load panel + macro."""
    cfg = Config(data_dir="tools/quant/data/polygon", use_macro=True)
    panel = data_mod.load_panel(cfg)
    macro = data_mod._load_macro(cfg, panel["prices"].index)
    panel["macro"] = macro
    return cfg, panel, macro


def get_vix(panel, macro):
    """Get VIX series aligned to panel."""
    if macro is not None and "VIX" in macro.columns:
        vix = macro["VIX"].dropna()
        if len(vix) > 100:
            return vix.reindex(panel["prices"].index).ffill()
    # Proxy
    prices = panel["prices"]
    if "SPY" in prices.columns:
        spy_ret = np.log(prices["SPY"] / prices["SPY"].shift(1))
        return (spy_ret.rolling(20).std() * np.sqrt(252) * 100).reindex(prices.index).ffill()
    return pd.Series(20.0, index=prices.index)


def build_high_vol_factors(panel, cfg):
    """Build high-vol-specific factor set, return as dict of DataFrames."""
    returns = panel["returns"]
    prices = panel["prices"]
    volumes = panel["volumes"]

    bench_col = "SPY" if "SPY" in returns.columns else returns.columns[0]
    bench = returns[bench_col]

    factors = {}

    # 1. Short-term reversal (strongest in high-vol)
    for lb in [1, 3, 5, 10]:
        past = returns.rolling(lb).sum()
        factors[f"hv_reversal_{lb}d"] = -past

    # 2. Dispersion-weighted momentum reversal (ICIR=1.05 in high-vol)
    cs_std = returns.rolling(20).std()
    for lb in [10, 20]:
        past_ret = returns.rolling(lb).sum()
        cs_mean = past_ret.mean(axis=1)
        z = past_ret.sub(cs_mean, axis=0).div(cs_std.replace(0, np.nan), axis=0)
        factors[f"hv_disp_mom_{lb}d"] = -z

    # 3. Beta-adjusted reversal (ICIR=0.62)
    cov = returns.rolling(60).cov(bench)
    var = bench.rolling(60).var()
    beta = cov.div(var.replace(0, np.nan), axis=0)
    for lb in [5, 10]:
        past_ret = returns.rolling(lb).sum()
        factors[f"hv_beta_rev_{lb}d"] = -past_ret * beta.clip(0, 3)

    # 4. Vol-of-vol (unstable vol → overreaction)
    rv20 = returns.rolling(20).std()
    factors["hv_vol_of_vol"] = rv20.rolling(20).std()

    # 5. Volume-weighted reversal
    for lb in [3, 5]:
        past_ret = returns.rolling(lb).sum()
        past_vol = volumes.rolling(lb).mean()
        avg_vol = volumes.rolling(60).mean()
        vol_ratio = past_vol / avg_vol.replace(0, np.nan)
        factors[f"hv_vol_weighted_rev_{lb}d"] = -past_ret * vol_ratio

    # 6. Idiosyncratic vol reversal
    res = returns.sub(bench, axis=0)
    ivol = res.rolling(20).std()
    for lb in [5, 10]:
        past_res = res.rolling(lb).sum()
        factors[f"hv_ivol_rev_{lb}d"] = -past_res * ivol

    # 7. VIX-scaled reversal
    vix = get_vix(panel, panel.get("macro"))
    vix_z = (vix - vix.rolling(60).mean()) / vix.rolling(60).std().replace(0, np.nan)
    vix_z = vix_z.reindex(returns.index).fillna(0)
    for lb in [5, 10]:
        past_ret = returns.rolling(lb).sum()
        factors[f"hv_vix_scaled_rev_{lb}d"] = -past_ret * vix_z.values[:, None]

    # 8. Skew (negative skew → bounce)
    for w in [20, 60]:
        factors[f"hv_skew_{w}d"] = -returns.rolling(w).skew()

    # 9. Liquidity shock reversal
    vol_change = volumes.pct_change(5)
    vol_spike = vol_change.rolling(20).rank(pct=True)
    past_ret_5 = returns.rolling(5).sum()
    factors["hv_liq_shock_rev"] = -past_ret_5 * vol_spike

    # 10. Range reversal
    for lb in [3, 5]:
        abs_ret = returns.abs().rolling(lb).mean()
        past_ret = returns.rolling(lb).sum()
        factors[f"hv_range_rev_{lb}d"] = -past_ret * abs_ret

    # 11. Classic factors that strengthen in high-vol
    # 12m momentum (ICIR 2.03 in high-vol)
    factors["hv_mom_12_1m"] = prices.shift(21) / prices.shift(252) - 1
    # Vol_60d (ICIR 0.89 in high-vol)
    factors["hv_vol_60d"] = returns.rolling(60).std()
    # Liq turnover (ICIR 0.81 in high-vol)
    factors["hv_liq_turnover"] = (volumes * prices).rolling(20).mean() / \
                                  (volumes * prices).rolling(252).mean()

    return factors


def regime_conditional_backtest(panel, macro, vix, cfg_normal, cfg_highvol):
    """Run regime-conditional backtest.

    At each rebalance, check VIX level and use the appropriate config.
    The backtest engine itself handles the day-by-day PnL; we just need
    to provide the right predictions and config at each rebalance.

    Approach: we run TWO separate model fits (one per config), then merge
    the predictions regime-conditionally, and run a single backtest with
    the merged predictions.
    """
    print("\n=== Regime-conditional backtest ===")

    # Step 1: Run normal-regime model (champion)
    print("\n--- Fitting normal-regime model (champion GBRT) ---")
    t0 = time.time()
    res_normal = runner.run(cfg_normal, export=False)
    print(f"  Normal model: {time.time()-t0:.1f}s")
    pred_normal = res_normal["predictions"]  # DataFrame, not dict
    print(f"  Normal predictions: {pred_normal.shape}")

    # Step 2: Run high-vol model with custom factors
    print("\n--- Fitting high-vol regime model ---")
    t0 = time.time()

    # For the high-vol model, we need to inject our custom factors
    # We'll use the OLS model with our high-vol factor set
    # First, compute the high-vol factors
    hv_factors = build_high_vol_factors(panel, cfg_highvol)
    print(f"  Built {len(hv_factors)} high-vol factors")

    # Process cross-sectionally (winsorize + z-score)
    hv_processed = factors_mod.process_cross_section(hv_factors, panel, cfg_highvol)

    # Run rolling OLS with high-vol factors
    # Need forward returns for IC screening
    from tools.quant.ls.ic_screen import screen_factors, forward_returns, compute_all_ic

    fwd_ret = forward_returns(panel["prices"], cfg_highvol.return_horizon_fwd)
    ic_df = compute_all_ic(hv_processed, fwd_ret, cfg_highvol)

    # Screen factors
    kept, stats, icir = ic_screen.screen_factors(ic_df, cfg_highvol, list(hv_processed.keys()))
    sign_flips = {f: s.get("sign_flip", False) for f, s in stats.items()}
    print(f"  Kept {len(kept)} high-vol factors: {kept[:10]}...")

    if len(kept) < 2:
        print("  WARNING: Too few factors kept, using all")
        kept = [f for f in hv_processed if hv_processed[f].count().sum() > 1000][:15]

    # Run rolling OLS
    res_hv = model_mod.roll_forward(hv_processed, panel, cfg_highvol,
                                     kept_factors=kept, sign_flips=sign_flips)
    pred_hv = res_hv["predictions"]
    print(f"  High-vol predictions: {pred_hv.shape}")
    print(f"  High-vol model: {time.time()-t0:.1f}s")

    # Step 3: Merge predictions regime-conditionally
    print("\n--- Merging predictions by VIX regime ---")
    # Align both to the same index
    common_dates = pred_normal.index.intersection(pred_hv.index)
    pred_merged = pd.DataFrame(0.0, index=common_dates, columns=panel["prices"].columns)

    vix_aligned = vix.reindex(common_dates).fillna(20.0)
    high_vol_mask = vix_aligned > VIX_HIGH

    for date in common_dates:
        if vix_aligned.loc[date] > VIX_HIGH:
            # Use high-vol predictions
            if date in pred_hv.index:
                pred_merged.loc[date] = pred_hv.loc[date].reindex(pred_merged.columns)
        else:
            # Use normal predictions
            if date in pred_normal.index:
                pred_merged.loc[date] = pred_normal.loc[date].reindex(pred_merged.columns)

    n_hv = high_vol_mask.sum()
    n_nm = len(common_dates) - n_hv
    print(f"  Normal regime rebalances: {n_nm}")
    print(f"  High-vol regime rebalances: {n_hv}")

    # Step 4: Run backtest with merged predictions
    print("\n--- Running backtest with merged predictions ---")
    # Use normal config as base (it has the right risk controls)
    cfg_bt = cfg_normal.copy()
    # Disable VIX de-risk in the backtest since we're handling regime switching
    # via predictions, but keep the VIX>=32 stress gate
    cfg_bt = cfg_bt.set(vix_derisk_factor=1.0, vix_level_threshold=VIX_STRESS, vix_level_factor=0.3)

    res = bt_mod.run_backtest(panel, pred_merged, cfg_bt)

    equity = res["equity_curve"]
    daily_ret = equity.pct_change().fillna(0)
    metrics = bt_mod.compute_metrics(res, cfg_bt, panel["prices"])

    print(f"\n  Regime-Conditional Strategy Results:")
    print(f"    Sharpe:      {metrics.get('sharpe', 0):.3f}")
    print(f"    Ann Return:  {metrics.get('annual_return', 0):.3f}")
    print(f"    Max DD:      {metrics.get('max_drawdown', 0):.3f}")
    print(f"    Turnover:    {metrics.get('annual_turnover', 0):.1f}")
    print(f"    N days:      {metrics.get('n_days', 0)}")

    # Regime split
    vix_bt = vix.reindex(daily_ret.index).fillna(20.0)
    for name, mask in [("normal", vix_bt <= VIX_HIGH), ("high_vol", vix_bt > VIX_HIGH),
                       ("stress", vix_bt > VIX_STRESS)]:
        sub = daily_ret[mask.values]
        if len(sub) < 5:
            continue
        ann_ret = sub.mean() * 252
        ann_vol = sub.std() * np.sqrt(252)
        sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
        print(f"    {name:8s}: n={len(sub):4d}  ret={ann_ret:.4f}  vol={ann_vol:.4f}  sharpe={sharpe:.3f}")

    # Save equity curve
    equity.to_csv(OUT_DIR / "equity_curve.csv")
    daily_ret.to_csv(OUT_DIR / "daily_returns.csv")

    return res, pred_merged, metrics


def run_comparison():
    """Run champion baseline + regime-conditional and compare."""
    print("=" * 70)
    print("REGIME-CONDITIONAL STRATEGY COMPARISON")
    print("=" * 70)

    # Load data
    cfg_base, panel, macro = load_panel()
    vix = get_vix(panel, macro)

    # VIX distribution
    print(f"\n  VIX distribution:")
    print(f"    Mean: {vix.mean():.1f}, Median: {vix.median():.1f}")
    print(f"    > 25: {(vix > 25).sum()} days ({100*(vix>25).mean():.1f}%)")
    print(f"    > 30: {(vix > 30).sum()} days ({100*(vix>30).mean():.1f}%)")
    print(f"    > 32: {(vix > 32).sum()} days ({100*(vix>32).mean():.1f}%)")
    print(f"    > 35: {(vix > 35).sum()} days ({100*(vix>35).mean():.1f}%)")

    # Config 1: Champion (baseline)
    cfg_champion = Config(
        name="champion_baseline",
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160,
        refit_freq=20,
        rebalance_freq=20,
        predict_horizon=10,
        return_horizon_fwd=10,
        n_long=13,
        n_short=13,
        vol_target_active=True,
        vol_target_annual=0.30,
        gross_leverage=1.0,
        cost_bps_one_side=6.0,
        slippage_bps=0.0,
        vix_derisk_pctile=0.90,
        vix_derisk_factor=1.0,
        vix_level_threshold=32.0,
        vix_level_factor=0.3,
        use_call_rate_financing=True,
        long_financing_apply=True,
        bypass_ic_screen=False,
        diag_regime_split=True,
    )

    # Config 2: High-vol regime model (OLS with custom factors)
    cfg_highvol = Config(
        name="highvol_model",
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="ols",
        train_window=120,         # shorter: high-vol dynamics change faster
        refit_freq=10,            # more frequent refits
        rebalance_freq=10,        # more frequent rebalancing
        predict_horizon=5,        # shorter horizon (reversal is faster)
        return_horizon_fwd=5,
        n_long=20,                # more names (higher dispersion)
        n_short=20,
        vol_target_active=True,
        vol_target_annual=0.40,   # higher vol target (more dispersion)
        gross_leverage=1.0,
        cost_bps_one_side=6.0,
        slippage_bps=0.0,
        vix_derisk_factor=1.0,
        vix_level_threshold=32.0,
        vix_level_factor=0.3,
        use_call_rate_financing=True,
        long_financing_apply=True,
        bypass_ic_screen=True,    # bypass since our factors are custom
        diag_regime_split=True,
    )

    # Run champion baseline
    print("\n--- Running champion baseline ---")
    t0 = time.time()
    res_champ = runner.run(cfg_champion, export=False)
    champ_metrics = res_champ["metrics"]
    print(f"  Champion: Sharpe={champ_metrics.get('sharpe',0):.3f}  "
          f"ret={champ_metrics.get('annual_return',0):.3f}  "
          f"dd={champ_metrics.get('max_drawdown',0):.3f}  "
          f"to={champ_metrics.get('annual_turnover',0):.1f}  "
          f"({time.time()-t0:.1f}s)")

    # Run regime-conditional
    print("\n--- Running regime-conditional ---")
    res_regime, pred_merged, regime_metrics = regime_conditional_backtest(
        panel, macro, vix, cfg_champion, cfg_highvol
    )

    # Comparison table
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print(f"{'Metric':<20s}  {'Champion':>10s}  {'Regime-Cond':>12s}  {'Delta':>10s}")
    print("-" * 56)
    for key in ["sharpe", "annual_return", "max_drawdown", "annual_turnover", "n_days"]:
        cv = champ_metrics.get(key, 0)
        rv = regime_metrics.get(key, 0)
        delta = rv - cv
        if isinstance(cv, float):
            print(f"{key:<20s}  {cv:10.3f}  {rv:12.3f}  {delta:+10.3f}")
        else:
            print(f"{key:<20s}  {cv:>10}  {rv:>12}  {delta:+10}")

    # Save results
    results_summary = {
        "champion": champ_metrics,
        "regime_conditional": regime_metrics,
        "vix_stats": {
            "mean": float(vix.mean()),
            "median": float(vix.median()),
            "pct_gt25": float((vix > 25).mean() * 100),
            "pct_gt30": float((vix > 30).mean() * 100),
            "pct_gt32": float((vix > 32).mean() * 100),
        },
    }
    with open(OUT_DIR / "comparison.json", "w") as f:
        json.dump(results_summary, f, indent=2, default=str)

    print(f"\n  Results saved to {OUT_DIR}")

    return 0


if __name__ == "__main__":
    sys.exit(run_comparison())
