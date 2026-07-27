"""IC/ICIR screening: rolling cross-sectional RankIC + per-factor gate.

For each factor f and each date t:
  IC_{f,t} = Spearman rank correlation between factor_t and forward_return_t+h

Then:
  ICIR_f = mean(IC_f over rolling window) / std(IC_f over rolling window)

A factor is *kept* if:
  |ICIR_f| >= icir_threshold AND |mean IC_f| >= ic_mean_threshold
  (Bonferroni adjustment applied to the mean-IC t-test if ic_bonferroni=True)

Sign convention: if IC is consistently negative, we flip the factor's sign
in the model so that 'high factor = high future return' always holds.

All IC/ICIR time series are exportable as CSV (per `save_intermediate`).
"""
from __future__ import annotations
import os, sys
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from .data import FutureFunctionError


# --------------------------------------------------------------------- core
def forward_returns(prices: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Forward h-day simple returns: P_{t+h} / P_t - 1.

    IMPORTANT: at time t, this return is ONLY known at time t+h.  We align
    the value to the *signal* date t (so IC_t correlates factor_t with
    forward_ret_t).  When fitting the model, we must NOT use rows where the
    forward return overlaps with the test period (handled in model.py).
    """
    fwd = (prices.shift(-horizon) / prices) - 1.0
    fwd = fwd.replace([np.inf, -np.inf], np.nan)
    return fwd


def rolling_rank_ic(factor: pd.DataFrame, fwd_ret: pd.DataFrame,
                    window: int, min_obs: int = 30) -> pd.DataFrame:
    """Rolling cross-sectional Spearman RankIC for one factor.

    At each date t, IC_t = spearman(factor_t[valid], fwd_ret_t[valid]).
    Returns a Series indexed by t (NaN where insufficient overlap).
    """
    # Align indices
    factor, fwd_ret = factor.align(fwd_ret, join="inner", axis=0)
    n_dates, n_tickers = factor.shape
    ic = np.full(n_dates, np.nan)

    f_vals = factor.values
    r_vals = fwd_ret.values

    for t in range(n_dates):
        fv = f_vals[t]
        rv = r_vals[t]
        mask = np.isfinite(fv) & np.isfinite(rv)
        if mask.sum() < min_obs:
            continue
        # Spearman = Pearson on ranks
        fr = stats.rankdata(fv[mask])
        rr = stats.rankdata(rv[mask])
        # Pearson correlation of ranks
        fr_centered = fr - fr.mean()
        rr_centered = rr - rr.mean()
        denom = np.sqrt((fr_centered ** 2).sum() * (rr_centered ** 2).sum())
        if denom == 0:
            continue
        ic[t] = (fr_centered * rr_centered).sum() / denom

    return pd.Series(ic, index=factor.index, name=factor.columns[0] if hasattr(factor, "columns") else "ic")


def compute_all_ic(processed: Dict[str, pd.DataFrame], fwd_ret: pd.DataFrame,
                   cfg) -> pd.DataFrame:
    """Compute IC time series for every factor.  Returns DataFrame[T, F]."""
    out = {}
    for name, df in processed.items():
        out[name] = rolling_rank_ic(df, fwd_ret, cfg.ic_window,
                                    min_obs=max(10, cfg.ic_min_obs // 4))
    return pd.DataFrame(out)


def icir_series(ic_df: pd.DataFrame, window: int, min_obs: int = 30) -> pd.DataFrame:
    """Rolling ICIR = rolling mean / rolling std of IC.

    Returns DataFrame[T, F] of ICIR values.
    """
    rolling_mean = ic_df.rolling(window, min_periods=min_obs).mean()
    rolling_std = ic_df.rolling(window, min_periods=min_obs).std(ddof=0)
    # Avoid div by 0
    rolling_std = rolling_std.replace(0, np.nan)
    icir = rolling_mean / rolling_std
    return icir


def screen_factors(ic_df: pd.DataFrame, cfg, factor_names: List[str]
                   ) -> Tuple[List[str], Dict[str, Dict], pd.DataFrame]:
    """Apply the ICIR + mean-IC + Bonferroni gate to select factors.

    Returns (kept_factors, stats_per_factor, icir_df).

    The screening uses the FULL SAMPLE of IC observations up to the point
    we're screening.  In a true walk-forward we'd screen using only data up
    to t; here we provide a *full-sample* screen for the initial factor
    list, and the model.py does the rolling refit on the kept set.

    NOTE: To avoid look-ahead in the screening itself, the runner calls this
    once on the training portion only (or on a rolling basis inside the
    model loop).  See model.roll_forward.
    """
    stats_per = {}
    n_factors = len(factor_names)
    # Bonferroni-adjusted alpha
    alpha_bonf = cfg.ic_alpha_familywise / max(1, n_factors) if cfg.ic_bonferroni else cfg.ic_alpha_familywise
    # Two-sided t critical value (approx, large sample)
    n_obs = len(ic_df)
    if n_obs < 5:
        return [], {f: {"status": "too_few_obs"} for f in factor_names}, pd.DataFrame()
    # Use normal approx for large n; for small n, use t
    if n_obs >= 30:
        z_crit = stats.norm.ppf(1 - alpha_bonf / 2)
    else:
        z_crit = stats.t.ppf(1 - alpha_bonf / 2, df=n_obs - 1)

    icir_full = icir_series(ic_df, cfg.ic_window, min_obs=cfg.ic_min_obs)
    # Use the latest ICIR value (or full-sample stats) for screening
    kept = []
    for name in factor_names:
        if name not in ic_df.columns:
            stats_per[name] = {"status": "missing"}
            continue
        ic_series = ic_df[name].dropna()
        if len(ic_series) < cfg.ic_min_obs:
            stats_per[name] = {"status": "too_few_obs", "n_obs": len(ic_series)}
            continue
        mean_ic = ic_series.mean()
        std_ic = ic_series.std(ddof=0)
        icir = mean_ic / std_ic if std_ic and std_ic > 0 else 0.0
        # t-statistic (full-sample)
        t_stat = mean_ic / (std_ic / np.sqrt(len(ic_series))) if std_ic and std_ic > 0 else 0.0
        # Latest rolling ICIR (for monitoring)
        last_icir = icir_full[name].dropna().iloc[-1] if not icir_full[name].dropna().empty else np.nan

        # Sign flip detection
        sign_flip = False
        if cfg.ic_sign_check and mean_ic < 0:
            sign_flip = True  # we'll flip in model

        # Gate
        passes_icir = abs(icir) >= cfg.icir_threshold
        passes_mean = abs(mean_ic) >= cfg.ic_mean_threshold
        passes_bonf = abs(t_stat) >= z_crit
        kept_flag = passes_icir and passes_mean and passes_bonf

        stats_per[name] = {
            "status": "kept" if kept_flag else "rejected",
            "mean_ic": float(mean_ic),
            "std_ic": float(std_ic),
            "icir": float(icir),
            "t_stat": float(t_stat),
            "n_obs": int(len(ic_series)),
            "last_rolling_icir": float(last_icir) if np.isfinite(last_icir) else None,
            "sign_flip": sign_flip,
            "passes_icir": passes_icir,
            "passes_mean": passes_mean,
            "passes_bonf": passes_bonf,
            "z_crit": float(z_crit),
        }
        if kept_flag:
            kept.append(name)

    return kept, stats_per, icir_full


# --------------------------------------------------------------------- export
def export_ic_tables(ic_df: pd.DataFrame, icir_df: pd.DataFrame,
                     stats_per: Dict, out_dir: str, tag: str = "") -> None:
    """Write IC, ICIR, and screening stats to CSV."""
    os.makedirs(out_dir, exist_ok=True)
    tag = f"_{tag}" if tag else ""
    ic_df.to_csv(os.path.join(out_dir, f"ic_series{tag}.csv"))
    icir_df.to_csv(os.path.join(out_dir, f"icir_series{tag}.csv"))
    pd.DataFrame(stats_per).T.to_csv(os.path.join(out_dir, f"factor_stats{tag}.csv"))


# --------------------------------------------------------------------- test
if __name__ == "__main__":
    # Quick smoke test
    import sys
    sys.path.insert(0, "/Users/daxu/software/world-trader")
    from .data import load_panel
    from .factors import all_factors
    from .config import Config
    cfg = Config()
    panel = load_panel(cfg)
    proc, stacked, names = all_factors(panel, cfg)
    fwd = forward_returns(panel["prices"], cfg.return_horizon_fwd)
    ic_df = compute_all_ic(proc, fwd, cfg)
    print("IC tail:")
    print(ic_df.iloc[-5:].round(3))
    kept, stats, icir = screen_factors(ic_df, cfg, names)
    print(f"\nKept factors ({len(kept)}):", kept)
    for f, s in stats.items():
        print(f"  {f:14s} status={s['status']:8s} mean_ic={s.get('mean_ic',0):.4f} icir={s.get('icir',0):.3f}")
