#!/usr/bin/env python3
"""Regime-conditional alpha research: which factors work when VIX > 25?

Goal: develop market-neutral strategies that ACTIVELY EXPLOIT high-volatility
regimes rather than just de-risking through them.

Research questions:
  R1: Factor IC decomposition — which factors have predictive power in
      high-VIX regimes vs normal regimes?
  R2: Do short-term reversal, liquidity, and volatility factors strengthen
      when VIX > 25? (Overreaction hypothesis)
  R3: Does cross-sectional dispersion increase in high-VIX, and can a
      dispersion-weighted strategy exploit it?
  R4: Can a regime-conditional strategy (different factors/params per
      regime) outperform the uniform champion?

Usage:
    python -m tools.quant.ls.regime_alpha_research
"""

import sys, os, time, json
import numpy as np
import pandas as pd
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from tools.quant.ls.config import Config
from tools.quant.ls import data as data_mod
from tools.quant.ls import factors as factors_mod
from tools.quant.ls import ic_screen
from tools.quant.ls import model as model_mod
from tools.quant.ls import backtest as bt_mod
from tools.quant.ls import runner

OUT_DIR = Path("tools/quant/ls/results/regime_alpha")
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIX_HIGH = 25.0  # threshold for "high vol" regime
VIX_STRESS = 32.0  # threshold for "stress" regime


def load_panel_and_vix():
    """Load the equity panel + VIX series."""
    cfg = Config(data_dir="tools/quant/data/polygon",
                 use_macro=True, vix_series="VIXCLS")
    panel = data_mod.load_panel(cfg)
    macro = data_mod._load_macro(cfg, panel["prices"].index)
    panel["macro"] = macro
    return cfg, panel, macro


def build_proxy_vix(prices):
    """Build a VIX proxy from SPY 20d realized vol if FRED is unavailable."""
    if "SPY" in prices.columns:
        spy_ret = np.log(prices["SPY"] / prices["SPY"].shift(1))
        rv = spy_ret.rolling(20).std() * np.sqrt(252) * 100
        return rv
    # Use cross-sectional mean return vol as fallback
    rets = np.log(prices / prices.shift(1))
    mean_ret = rets.mean(axis=1)
    rv = mean_ret.rolling(20).std() * np.sqrt(252) * 100
    return rv


def get_vix(panel, macro, cfg):
    """Get VIX series, falling back to proxy if FRED unavailable."""
    if macro is not None and "VIX" in macro.columns:
        vix = macro["VIX"].dropna()
        if len(vix) > 100:
            print(f"  Using FRED VIX: {vix.index.min().date()} to {vix.index.max().date()}, {len(vix)} obs")
            # Reindex to panel dates, forward-fill
            vix = vix.reindex(panel["prices"].index).ffill()
            return vix
    print("  FRED VIX unavailable, using proxy from SPY realized vol")
    proxy = build_proxy_vix(panel["prices"])
    proxy = proxy.reindex(panel["prices"].index).ffill()
    return proxy


def compute_all_factors(panel, cfg):
    """Compute raw + extra + OHLC + interaction factors."""
    raw = factors_mod.compute_raw_factors(panel, cfg)
    extra = factors_mod.compute_extra_raw_factors(panel, cfg)
    ohlc = factors_mod.compute_ohlc_factors(panel, cfg) if hasattr(factors_mod, 'compute_ohlc_factors') else {}
    interactions = factors_mod.compute_interaction_features(panel, cfg) if hasattr(factors_mod, 'compute_interaction_features') else {}

    all_raw = {}
    all_raw.update(raw)
    all_raw.update(extra)
    all_raw.update(ohlc)
    all_raw.update(interactions)

    processed = factors_mod.process_cross_section(all_raw, panel, cfg)
    return all_raw, processed


def compute_forward_returns(panel, horizons=(5, 10, 21)):
    """Compute forward returns at multiple horizons."""
    returns = panel["returns"]
    fwd = {}
    for h in horizons:
        fwd[h] = returns.shift(-h).rolling(h).sum()
        # Actually: sum of next h days = rolling sum then shift
        fwd[h] = returns.rolling(h).sum().shift(-h)
    return fwd


def regime_factor_ic(panel, processed, vix, horizons=(5, 10, 21)):
    """R1: Factor IC by VIX regime.

    For each factor and horizon, compute cross-sectional RankIC
    separately in high-VIX (VIX > 25) and normal-VIX periods.
    """
    print("\n=== R1: Factor IC by VIX regime ===")
    returns = panel["returns"]
    prices = panel["prices"]
    bench_col = "SPY" if "SPY" in returns.columns else returns.columns[0]

    # Forward returns
    fwd_returns = {}
    for h in horizons:
        fwd = returns.rolling(h).sum().shift(-h)
        fwd_returns[h] = fwd

    # Regime masks
    vix_aligned = vix.reindex(processed.index if hasattr(processed, 'index') else
                              list(processed.values())[0].index)
    high_vol = vix_aligned > VIX_HIGH
    normal = (vix_aligned <= VIX_HIGH) & (vix_aligned > 0)
    stress = vix_aligned > VIX_STRESS

    print(f"  High-VIX (VIX>{VIX_HIGH}): {high_vol.sum()} days ({100*high_vol.mean():.1f}%)")
    print(f"  Stress  (VIX>{VIX_STRESS}): {stress.sum()} days ({100*stress.mean():.1f}%)")
    print(f"  Normal:  {normal.sum()} days ({100*normal.mean():.1f}%)")

    # Compute IC for each factor in each regime
    factor_names = list(processed.keys()) if isinstance(processed, dict) else []
    results = []

    for h in horizons:
        fwd = fwd_returns[h]
        for fname in factor_names:
            fac = processed[fname]
            for regime_name, mask in [("normal", normal), ("high_vol", high_vol), ("stress", stress)]:
                # Align mask to factor dates
                m = mask.reindex(fac.index).fillna(False)
                if m.sum() < 10:
                    continue

                # Compute daily cross-sectional rank IC
                ic_vals = []
                for date in fac.index[m]:
                    f_row = fac.loc[date].dropna()
                    r_row = fwd.loc[date].dropna() if date in fwd.index else pd.Series(dtype=float)
                    common = f_row.index.intersection(r_row.index)
                    if len(common) < 10:
                        continue
                    f_vals = f_row.loc[common].values
                    r_vals = r_row.loc[common].values
                    valid = np.isfinite(f_vals) & np.isfinite(r_vals)
                    if valid.sum() < 10:
                        continue
                    from scipy.stats import spearmanr
                    rho, _ = spearmanr(f_vals[valid], r_vals[valid])
                    if np.isfinite(rho):
                        ic_vals.append(rho)

                if len(ic_vals) < 5:
                    continue

                ic_arr = np.array(ic_vals)
                ic_mean = ic_arr.mean()
                ic_std = ic_arr.std(ddof=0)
                icir = ic_mean / ic_std if ic_std > 1e-9 else 0.0
                t_stat = ic_mean / (ic_std / np.sqrt(len(ic_arr))) if ic_std > 1e-9 else 0.0

                results.append({
                    "factor": fname,
                    "horizon": h,
                    "regime": regime_name,
                    "n_days": len(ic_vals),
                    "ic_mean": ic_mean,
                    "ic_std": ic_std,
                    "icir": icir,
                    "t_stat": t_stat,
                    "hit_rate": (ic_arr > 0).mean() if ic_mean > 0 else (ic_arr < 0).mean(),
                })

    df = pd.DataFrame(results)
    df.to_csv(OUT_DIR / "regime_factor_ic.csv", index=False)

    # Summary: factors with strongest regime-conditional IC
    print("\n  Top factors by |ICIR| in HIGH-VOL regime (h=10):")
    hv = df[(df["regime"] == "high_vol") & (df["horizon"] == 10)].copy()
    hv["abs_icir"] = hv["icir"].abs()
    for _, row in hv.nlargest(15, "abs_icir").iterrows():
        # Compare to normal regime
        nr = df[(df["factor"] == row["factor"]) & (df["regime"] == "normal") & (df["horizon"] == 10)]
        nr_icir = nr["icir"].values[0] if len(nr) > 0 else np.nan
        ratio = row["icir"] / nr_icir if abs(nr_icir) > 1e-9 else np.nan
        print(f"    {row['factor']:25s} HV_ICIR={row['icir']:6.3f}  NM_ICIR={nr_icir:6.3f}  ratio={ratio:5.2f}  t={row['t_stat']:5.2f}")

    print("\n  Top factors by |ICIR| in NORMAL regime (h=10):")
    nm = df[(df["regime"] == "normal") & (df["horizon"] == 10)].copy()
    nm["abs_icir"] = nm["icir"].abs()
    for _, row in nm.nlargest(10, "abs_icir").iterrows():
        print(f"    {row['factor']:25s} NM_ICIR={row['icir']:6.3f}  t={row['t_stat']:5.2f}")

    # Find factors that are STRONGER in high-vol
    print("\n  Factors STRONGER in high-vol (HV_ICIR/NM_ICIR > 1.5, |HV_ICIR| > 0.05):")
    pivot = df[df["horizon"] == 10].pivot_table(index="factor", columns="regime", values="icir")
    if "high_vol" in pivot.columns and "normal" in pivot.columns:
        pivot["ratio"] = pivot["high_vol"] / pivot["normal"].replace(0, np.nan)
        pivot["abs_hv"] = pivot["high_vol"].abs()
        strong = pivot[(pivot["ratio"].abs() > 1.5) & (pivot["abs_hv"] > 0.05)].dropna(subset=["high_vol", "normal"])
        for fname, row in strong.nlargest(15, "abs_hv").iterrows():
            print(f"    {fname:25s} HV={row['high_vol']:6.3f}  NM={row['normal']:6.3f}  ratio={row['ratio']:5.2f}")

    return df


def analyze_dispersion(panel, vix):
    """R3: Cross-sectional dispersion analysis.

    Does cross-sectional return dispersion increase when VIX > 25?
    If so, a dispersion-weighted strategy can exploit it.
    """
    print("\n=== R3: Cross-sectional dispersion by VIX regime ===")
    returns = panel["returns"]
    vix_aligned = vix.reindex(returns.index).fillna(20.0)

    # Daily cross-sectional dispersion
    cs_std = returns.std(axis=1)  # cross-sectional std of daily returns
    cs_range = (returns.max(axis=1) - returns.min(axis=1))  # cross-sectional range
    cs_mean_abs = returns.abs().mean(axis=1)  # mean absolute return

    # Rolling 20d average dispersion
    cs_std_20d = cs_std.rolling(20).mean()

    # Split by regime
    high_vol = vix_aligned > VIX_HIGH
    normal = (vix_aligned <= VIX_HIGH) & (vix_aligned > 0)

    print(f"  Daily cross-sectional std:")
    print(f"    Normal:  mean={cs_std[normal].mean():.4f}  median={cs_std[normal].median():.4f}")
    print(f"    HighVol: mean={cs_std[high_vol].mean():.4f}  median={cs_std[high_vol].median():.4f}")
    print(f"    Ratio:   {cs_std[high_vol].mean() / cs_std[normal].mean():.2f}x")

    print(f"  20d avg cross-sectional std:")
    print(f"    Normal:  mean={cs_std_20d[normal].mean():.4f}")
    print(f"    HighVol: mean={cs_std_20d[high_vol].mean():.4f}")
    print(f"    Ratio:   {cs_std_20d[high_vol].mean() / cs_std_20d[normal].mean():.2f}x")

    print(f"  Mean absolute return:")
    print(f"    Normal:  mean={cs_mean_abs[normal].mean():.4f}")
    print(f"    HighVol: mean={cs_mean_abs[high_vol].mean():.4f}")
    print(f"    Ratio:   {cs_mean_abs[high_vol].mean() / cs_mean_abs[normal].mean():.2f}x")

    # Save dispersion series
    disp_df = pd.DataFrame({
        "cs_std": cs_std,
        "cs_range": cs_range,
        "cs_mean_abs": cs_mean_abs,
        "cs_std_20d": cs_std_20d,
        "vix": vix_aligned,
        "regime": np.where(high_vol, "high_vol", "normal"),
    })
    disp_df.to_csv(OUT_DIR / "dispersion_by_regime.csv")

    return disp_df


def analyze_reversal_strength(panel, vix, horizons=(1, 3, 5, 10)):
    """R2: Short-term reversal strength by VIX regime.

    In high-vol regimes, overreaction is amplified → reversal should be stronger.
    Test: IC of 1-day / 3-day / 5-day past return with forward return.
    """
    print("\n=== R2: Short-term reversal strength by VIX regime ===")
    returns = panel["returns"]
    vix_aligned = vix.reindex(returns.index).fillna(20.0)
    high_vol = vix_aligned > VIX_HIGH
    normal = (vix_aligned <= VIX_HIGH) & (vix_aligned > 0)

    results = []
    for lookback in horizons:
        # Past return (reversal signal)
        past_ret = returns.rolling(lookback).sum()

        for fwd_h in [5, 10]:
            fwd_ret = returns.rolling(fwd_h).sum().shift(-fwd_h)

            for regime_name, mask in [("normal", normal), ("high_vol", high_vol)]:
                m = mask.reindex(past_ret.index).fillna(False)
                ic_vals = []

                for date in past_ret.index[m]:
                    p_row = past_ret.loc[date].dropna()
                    r_row = fwd_ret.loc[date].dropna() if date in fwd_ret.index else pd.Series(dtype=float)
                    common = p_row.index.intersection(r_row.index)
                    if len(common) < 10:
                        continue
                    p_vals = p_row.loc[common].values
                    r_vals = r_row.loc[common].values
                    valid = np.isfinite(p_vals) & np.isfinite(r_vals)
                    if valid.sum() < 10:
                        continue
                    from scipy.stats import spearmanr
                    rho, _ = spearmanr(p_vals[valid], r_vals[valid])
                    if np.isfinite(rho):
                        ic_vals.append(rho)

                if len(ic_vals) < 5:
                    continue

                ic_arr = np.array(ic_vals)
                ic_mean = ic_arr.mean()
                ic_std = ic_arr.std(ddof=0)
                icir = ic_mean / ic_std if ic_std > 1e-9 else 0.0

                results.append({
                    "lookback": lookback,
                    "fwd_horizon": fwd_h,
                    "regime": regime_name,
                    "n_days": len(ic_vals),
                    "ic_mean": ic_mean,
                    "ic_std": ic_std,
                    "icir": icir,
                    "reversal_icir": -icir,  # positive = reversal works (negative IC = buy losers)
                })

    df = pd.DataFrame(results)
    df.to_csv(OUT_DIR / "reversal_strength_by_regime.csv", index=False)

    print("\n  Reversal ICIR (positive = reversal alpha):")
    for _, row in df.iterrows():
        print(f"    lookback={row['lookback']:2d}d  fwd={row['fwd_horizon']:2d}d  "
              f"regime={row['regime']:8s}  ICIR={row['icir']:6.3f}  "
              f"reversal_ICIR={row['reversal_icir']:6.3f}  n={row['n_days']}")

    return df


def build_high_vol_factors(panel, vix):
    """Build factors specifically designed for high-vol regimes.

    These factors exploit phenomena that are amplified when VIX > 25:
    1. Overreaction-reversal: stronger weight on recent losers/winners
    2. Vol-of-vol: stocks with unstable vol get overreacted to
    3. Volume spike reversal: high-volume moves reverse harder
    4. Range-based reversal: intraday range signals overreaction
    5. Cross-sectional skew: negative-skew stocks bounce harder
    6. Beta-adjusted reversal: high-beta stocks overreact more
    """
    print("\n=== Building high-vol-specific factors ===")
    returns = panel["returns"]
    prices = panel["prices"]
    volumes = panel["volumes"]

    factors = {}

    # 1. Enhanced short-term reversal (3d, 5d)
    for lb in [1, 3, 5, 10]:
        past = returns.rolling(lb).sum()
        factors[f"hv_reversal_{lb}d"] = -past  # negative of past return = reversal signal

    # 2. Vol-of-vol: rolling std of rolling vol → unstable vol stocks
    rv20 = returns.rolling(20).std()
    vol_of_vol = rv20.rolling(20).std()
    factors["hv_vol_of_vol"] = vol_of_vol

    # 3. Volume-weighted reversal: high-volume moves reverse more
    for lb in [3, 5]:
        past_ret = returns.rolling(lb).sum()
        past_vol = volumes.rolling(lb).mean()
        avg_vol = volumes.rolling(60).mean()
        vol_ratio = past_vol / avg_vol.replace(0, np.nan)
        # Volume-weighted reversal = -past_ret * vol_ratio (high-volume losers bounce more)
        factors[f"hv_vol_weighted_rev_{lb}d"] = -past_ret * vol_ratio

    # 4. Range-based overreaction: large intraday range → overreaction
    if all(c in prices.columns for c in []) and "high" in panel:
        # Use OHLC if available
        pass
    # Use daily return magnitude as proxy
    for lb in [3, 5]:
        abs_ret = returns.abs().rolling(lb).mean()
        past_ret = returns.rolling(lb).sum()
        factors[f"hv_range_rev_{lb}d"] = -past_ret * abs_ret

    # 5. Cross-sectional skew: negative-skew stocks bounce harder
    for w in [20, 60]:
        factors[f"hv_skew_{w}d"] = -returns.rolling(w).skew()  # negative skew = buy signal

    # 6. Beta-adjusted reversal: high-beta stocks overreact more
    bench_col = "SPY" if "SPY" in returns.columns else returns.columns[0]
    bench = returns[bench_col]
    for lb in [5, 10]:
        # Rolling beta
        cov = returns.rolling(60).cov(bench)
        var = bench.rolling(60).var()
        beta = cov.div(var.replace(0, np.nan), axis=0)
        past_ret = returns.rolling(lb).sum()
        # Reversal weighted by beta (high-beta overreacters)
        factors[f"hv_beta_rev_{lb}d"] = -past_ret * beta.clip(0, 3)

    # 7. Idiosyncratic vol reversal: high-ivol stocks overreact
    for lb in [5, 10]:
        # Residual return after market
        res = returns.sub(bench, axis=0)
        ivol = res.rolling(20).std()
        past_res = res.rolling(lb).sum()
        factors[f"hv_ivol_rev_{lb}d"] = -past_res * ivol

    # 8. Dispersion-weighted momentum: in high-dispersion regimes, momentum extremes reverse
    cs_std = returns.rolling(20).std()
    for lb in [10, 20]:
        past_ret = returns.rolling(lb).sum()
        # Z-score of past return cross-sectionally
        z = past_ret.sub(past_ret.mean(axis=1), axis=0).div(cs_std.replace(0, np.nan), axis=0)
        factors[f"hv_disp_mom_{lb}d"] = -z  # reverse extreme momentum

    # 9. Liquidity shock reversal: sudden volume spike + price drop = overreaction
    vol_change = volumes.pct_change(5)
    vol_spike = vol_change.rolling(20).rank(pct=True)
    past_ret = returns.rolling(5).sum()
    factors["hv_liq_shock_rev"] = -past_ret * vol_spike

    # 10. VIX-regime interaction: scale reversal strength by VIX level
    vix_aligned = vix.reindex(returns.index).fillna(20.0)
    vix_z = (vix_aligned - vix_aligned.rolling(60).mean()) / vix_aligned.rolling(60).std().replace(0, np.nan)
    for lb in [5, 10]:
        past_ret = returns.rolling(lb).sum()
        # Stronger reversal when VIX is elevated
        factors[f"hv_vix_scaled_rev_{lb}d"] = -past_ret * vix_z.reindex(returns.index).fillna(0).values[:, None]

    print(f"  Built {len(factors)} high-vol-specific factors")
    for name, fac in factors.items():
        valid = fac.count().sum()
        print(f"    {name:30s}  valid_obs={valid}")

    return factors


def regime_conditional_backtest(panel, processed, vix, cfg_base):
    """R4: Backtest regime-conditional strategy.

    Uses the champion GBRT model but with regime-dependent parameters:
    - Normal regime (VIX <= 25): champion config (h=10, n=13, vt=30)
    - High-vol regime (VIX > 25): shorter horizon, more names, reversal-tilted
    """
    print("\n=== R4: Regime-conditional backtest ===")

    # We can't easily modify the backtest engine mid-run for regime-dependent
    # params, so we'll test the simpler approach: does the champion model
    # perform differently in high-vol vs normal periods?

    # Run champion config
    cfg = Config(**cfg_base)
    res = runner.run(cfg, export=False)

    equity = res["equity_curve"]
    daily_ret = equity.pct_change().fillna(0)

    # Regime split
    vix_aligned = vix.reindex(daily_ret.index).fillna(20.0)
    high_vol = vix_aligned > VIX_HIGH
    normal = (vix_aligned <= VIX_HIGH) & (vix_aligned > 0)
    stress = vix_aligned > VIX_STRESS

    print(f"\n  Champion strategy performance by VIX regime:")
    for name, mask in [("normal", normal), ("high_vol", high_vol), ("stress", stress)]:
        sub = daily_ret[mask]
        if len(sub) < 5:
            print(f"    {name:8s}: n={len(sub)} (too few days)")
            continue
        ann_ret = sub.mean() * 252
        ann_vol = sub.std() * np.sqrt(252)
        sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
        print(f"    {name:8s}: n={len(sub):4d}  ann_ret={ann_ret:.4f}  ann_vol={ann_vol:.4f}  sharpe={sharpe:.3f}")

    return res


def high_vol_factor_ic_detailed(panel, hv_factors, vix):
    """Detailed IC analysis of high-vol-specific factors in each regime."""
    print("\n=== High-vol factor IC analysis ===")
    returns = panel["returns"]
    vix_aligned = vix.reindex(returns.index).fillna(20.0)
    high_vol = vix_aligned > VIX_HIGH
    normal = (vix_aligned <= VIX_HIGH) & (vix_aligned > 0)

    results = []
    for fname, fac in hv_factors.items():
        for fwd_h in [5, 10]:
            fwd_ret = returns.rolling(fwd_h).sum().shift(-fwd_h)

            for regime_name, mask in [("normal", normal), ("high_vol", high_vol)]:
                m = mask.reindex(fac.index).fillna(False)
                ic_vals = []

                for date in fac.index[m]:
                    f_row = fac.loc[date].dropna()
                    r_row = fwd_ret.loc[date].dropna() if date in fwd_ret.index else pd.Series(dtype=float)
                    common = f_row.index.intersection(r_row.index)
                    if len(common) < 10:
                        continue
                    f_vals = f_row.loc[common].values
                    r_vals = r_row.loc[common].values
                    valid = np.isfinite(f_vals) & np.isfinite(r_vals)
                    if valid.sum() < 10:
                        continue
                    from scipy.stats import spearmanr
                    rho, _ = spearmanr(f_vals[valid], r_vals[valid])
                    if np.isfinite(rho):
                        ic_vals.append(rho)

                if len(ic_vals) < 5:
                    continue

                ic_arr = np.array(ic_vals)
                ic_mean = ic_arr.mean()
                ic_std = ic_arr.std(ddof=0)
                icir = ic_mean / ic_std if ic_std > 1e-9 else 0.0
                t_stat = ic_mean / (ic_std / np.sqrt(len(ic_arr))) if ic_std > 1e-9 else 0.0

                results.append({
                    "factor": fname,
                    "fwd_horizon": fwd_h,
                    "regime": regime_name,
                    "n_days": len(ic_vals),
                    "ic_mean": ic_mean,
                    "ic_std": ic_std,
                    "icir": icir,
                    "t_stat": t_stat,
                })

    df = pd.DataFrame(results)
    df.to_csv(OUT_DIR / "hv_factor_ic.csv", index=False)

    # Show best factors in high-vol
    print("\n  Top high-vol factors by ICIR (h=10, high_vol regime):")
    hv = df[(df["regime"] == "high_vol") & (df["fwd_horizon"] == 10)].copy()
    hv["abs_icir"] = hv["icir"].abs()
    for _, row in hv.nlargest(15, "abs_icir").iterrows():
        nr = df[(df["factor"] == row["factor"]) & (df["regime"] == "normal") & (df["fwd_horizon"] == 10)]
        nr_icir = nr["icir"].values[0] if len(nr) > 0 else np.nan
        print(f"    {row['factor']:30s}  HV_ICIR={row['icir']:6.3f}  NM_ICIR={nr_icir:6.3f}  t={row['t_stat']:5.2f}")

    return df


def main():
    print("=" * 70)
    print("REGIME-CONDITIONAL ALPHA RESEARCH (VIX > 25)")
    print("=" * 70)

    t0 = time.time()

    # Step 1: Load data
    print("\n--- Step 1: Loading panel ---")
    cfg, panel, macro = load_panel_and_vix()
    vix = get_vix(panel, macro, cfg)

    # Step 2: Compute all factors
    print("\n--- Step 2: Computing factors ---")
    all_raw, processed = compute_all_factors(panel, cfg)
    print(f"  Computed {len(all_raw)} raw factors, {len(processed)} processed")

    # Step 3: R1 — Factor IC by regime
    ic_results = regime_factor_ic(panel, processed, vix)

    # Step 4: R2 — Reversal strength by regime
    rev_results = analyze_reversal_strength(panel, vix)

    # Step 5: R3 — Dispersion analysis
    disp_results = analyze_dispersion(panel, vix)

    # Step 6: Build & test high-vol-specific factors
    print("\n--- Step 6: Building high-vol factors ---")
    hv_factors = build_high_vol_factors(panel, vix)
    hv_ic_results = high_vol_factor_ic_detailed(panel, hv_factors, vix)

    # Step 7: R4 — Regime-conditional backtest (champion split)
    # Use champion config
    cfg_base = dict(
        name="regime_split_champion",
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
        vol_target=30,
        gross_leverage=1.0,
        cost_bps_one_side=6.0,
        slippage_bps=0.0,
        vix_derisk_pctile=0.90,
        vix_derisk_factor=1.0,
        vix_level_threshold=32.0,
        vix_level_factor=0.3,
        use_call_rate_financing=True,
        long_financing_apply=True,
    )
    # regime_conditional_backtest(panel, processed, vix, cfg_base)  # Skip for now, too slow

    # Summary
    print("\n" + "=" * 70)
    print("RESEARCH SUMMARY")
    print("=" * 70)
    print(f"\n  Total time: {(time.time()-t0)/60:.1f} min")
    print(f"  Output dir: {OUT_DIR}")
    print(f"  Files written:")
    for f in OUT_DIR.glob("*.csv"):
        print(f"    {f.name}")

    print("\n--- Key findings ---")
    # Load and summarize key findings
    if (OUT_DIR / "regime_factor_ic.csv").exists():
        df = pd.read_csv(OUT_DIR / "regime_factor_ic.csv")
        hv = df[(df["regime"] == "high_vol") & (df["horizon"] == 10)]
        nm = df[(df["regime"] == "normal") & (df["horizon"] == 10)]
        if len(hv) > 0 and len(nm) > 0:
            merged = hv.merge(nm, on="factor", suffixes=("_hv", "_nm"))
            merged["ratio"] = merged["icir_hv"].abs() / merged["icir_nm"].abs().replace(0, 0.01)
            stronger = merged[(merged["ratio"] > 1.5) & (merged["icir_hv"].abs() > 0.05)]
            print(f"  Factors stronger in high-vol: {len(stronger)}")
            for _, r in stronger.nlargest(10, "icir_hv", ).iterrows():
                print(f"    {r['factor']:25s}  HV={r['icir_hv']:.3f}  NM={r['icir_nm']:.3f}  ratio={r['ratio']:.2f}")

    if (OUT_DIR / "hv_factor_ic.csv").exists():
        df = pd.read_csv(OUT_DIR / "hv_factor_ic.csv")
        hv = df[(df["regime"] == "high_vol") & (df["fwd_horizon"] == 10)]
        if len(hv) > 0:
            top = hv.nlargest(5, hv["icir"].abs() if False else "icir")
            print(f"\n  Best high-vol-specific factors (h=10):")
            for _, r in top.iterrows():
                print(f"    {r['factor']:30s}  ICIR={r['icir']:.3f}  t={r['t_stat']:.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
