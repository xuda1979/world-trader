"""Overfitting diagnostics (rule X).

1. Regime split: divide history into bull / sideways / bear using benchmark
   trend, compute Sharpe in each.  A robust strategy should be positive in
   at least 2 of 3 regimes.

2. Window sensitivity: re-run with train_window in {100, 120, 140} and
   report Sharpe.  Large drop (>50% from best) = overfitting flag.

3. Factor weight stability: std(beta_f) / |mean(beta_f)| across refits.
   High value = weights swinging = overfitting flag.

4. ICIR decay: compare first-half ICIR vs second-half ICIR per factor.
"""
from __future__ import annotations
import os, sys
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# --------------------------------------------------------------------- regime split
def classify_regimes(benchmark_ret: pd.Series, window: int = 60) -> pd.Series:
    """Classify each date as 'bull', 'sideways', or 'bear' based on the
    rolling 60d return of the benchmark.

    bull:     rolling 60d return > +5%
    bear:     rolling 60d return < -5%
    sideways: else
    """
    roll_ret = benchmark_ret.rolling(window, min_periods=20).apply(
        lambda x: (1 + x).prod() - 1, raw=False
    )
    regime = pd.Series("sideways", index=benchmark_ret.index)
    regime[roll_ret > 0.05] = "bull"
    regime[roll_ret < -0.05] = "bear"
    return regime


def regime_performance(daily_ret: pd.Series, regime: pd.Series) -> pd.DataFrame:
    """Compute Sharpe per regime."""
    out = {}
    for r in ["bull", "sideways", "bear"]:
        mask = regime == r
        if mask.sum() < 5:
            out[r] = {"n_days": int(mask.sum()), "sharpe": np.nan, "ann_ret": np.nan, "ann_vol": np.nan}
            continue
        sub = daily_ret[mask]
        ann_ret = float((1 + sub.mean()) ** 252 - 1) if sub.mean() != 0 else 0.0
        ann_vol = float(sub.std(ddof=0) * np.sqrt(252))
        sharpe = float(ann_ret / ann_vol) if ann_vol > 0 else 0.0
        out[r] = {"n_days": int(mask.sum()), "sharpe": sharpe,
                  "ann_ret": ann_ret, "ann_vol": ann_vol}
    return pd.DataFrame(out).T


# --------------------------------------------------------------------- window sweep
def window_sweep(panel: Dict, processed: Dict, cfg, kept_factors: List[str],
                 sign_flips: Dict[str, bool]) -> Dict[int, Dict]:
    """Re-run the model + backtest for each train_window in cfg.diag_window_sweep.

    Returns {window: {metrics, sharpe}}.
    """
    from . import model, backtest
    results = {}
    for w in cfg.diag_window_sweep:
        cfg_w = cfg.copy(train_window=w, name=f"sweep_{w}")
        out_w = model.roll_forward(processed, panel, cfg_w,
                                   kept_factors=kept_factors, sign_flips=sign_flips)
        if out_w["predictions"].empty:
            results[w] = {"sharpe": np.nan, "n_pred": 0}
            continue
        bt_w = backtest.run_backtest(panel, out_w["predictions"], cfg_w)
        m_w = backtest.compute_metrics(bt_w, cfg_w, panel["prices"])
        results[w] = {**m_w, "factor_weights": out_w["weights"]}
    return results


# --------------------------------------------------------------------- weight stability
def factor_weight_stability(weights: pd.DataFrame) -> pd.DataFrame:
    """For each factor, compute mean, std, and std/|mean| across refits.

    High std/|mean| (>2.0) = unstable weight = overfitting flag.
    """
    if weights.empty:
        return pd.DataFrame()
    out = []
    for col in weights.columns:
        vals = weights[col].dropna()
        if len(vals) < 5:
            out.append({"factor": col, "mean": np.nan, "std": np.nan, "cv": np.nan,
                        "flag": "insufficient"})
            continue
        mu = float(vals.mean())
        sd = float(vals.std(ddof=0))
        cv = float(sd / abs(mu)) if abs(mu) > 1e-8 else np.inf
        flag = "unstable" if cv > 2.0 else "ok"
        out.append({"factor": col, "mean": mu, "std": sd, "cv": cv, "flag": flag})
    return pd.DataFrame(out).set_index("factor")


# --------------------------------------------------------------------- ICIR decay
def icir_decay(ic_df: pd.DataFrame, cfg) -> pd.DataFrame:
    """Compare first-half vs second-half ICIR per factor.

    Large divergence = factor decayed = overfitting flag.
    """
    if ic_df.empty:
        return pd.DataFrame()
    n = len(ic_df)
    mid = n // 2
    out = []
    for col in ic_df.columns:
        s1 = ic_df[col].iloc[:mid].dropna()
        s2 = ic_df[col].iloc[mid:].dropna()
        if len(s1) < 10 or len(s2) < 10:
            out.append({"factor": col, "icir_h1": np.nan, "icir_h2": np.nan,
                        "decay": np.nan, "flag": "insufficient"})
            continue
        icir1 = float(s1.mean() / s1.std(ddof=0)) if s1.std(ddof=0) > 0 else 0.0
        icir2 = float(s2.mean() / s2.std(ddof=0)) if s2.std(ddof=0) > 0 else 0.0
        decay = float(icir2 - icir1)
        flag = "decayed" if (icir1 > 0.1 and icir2 < icir1 * 0.5) else "ok"
        out.append({"factor": col, "icir_h1": icir1, "icir_h2": icir2,
                    "decay": decay, "flag": flag})
    return pd.DataFrame(out).set_index("factor")


# --------------------------------------------------------------------- full report
def run_diagnostics(result: Dict, panel: Dict, predictions: pd.DataFrame,
                    weights: pd.DataFrame, ic_df: pd.DataFrame,
                    processed: Dict, cfg, kept_factors: List[str],
                    sign_flips: Dict[str, bool]) -> Dict:
    """Run all overfitting diagnostics and return a structured report."""
    daily_ret = result["daily_returns"]
    bench_col = cfg.benchmark if cfg.benchmark in panel["returns"].columns else None
    report = {}

    # 1. Regime split
    if cfg.diag_regime_split and bench_col:
        regime = classify_regimes(panel["returns"][bench_col])
        report["regime_split"] = regime_performance(daily_ret, regime)
    else:
        report["regime_split"] = pd.DataFrame()

    # 2. Window sweep
    if cfg.diag_window_sweep:
        report["window_sweep"] = window_sweep(panel, processed, cfg,
                                              kept_factors, sign_flips)

    # 3. Weight stability
    if cfg.diag_weight_vol_flag:
        report["weight_stability"] = factor_weight_stability(weights)
    else:
        report["weight_stability"] = pd.DataFrame()

    # 4. ICIR decay
    report["icir_decay"] = icir_decay(ic_df, cfg)

    # Summary verdict
    flags = []
    if not report["regime_split"].empty:
        n_positive_regimes = int((report["regime_split"]["sharpe"] > 0).sum())
        if n_positive_regimes < 2:
            flags.append(f"regime_persistence_weak ({n_positive_regimes}/3 positive)")
    if isinstance(report["window_sweep"], dict) and report["window_sweep"]:
        sharpes = [v.get("sharpe", np.nan) for v in report["window_sweep"].values()]
        sharpes = [s for s in sharpes if np.isfinite(s)]
        if sharpes and max(sharpes) != 0:
            drop = (max(sharpes) - min(sharpes)) / abs(max(sharpes))
            if drop > 0.5:
                flags.append(f"window_sensitivity_high (drop={drop:.1%})")
    if not report["weight_stability"].empty:
        unstable = report["weight_stability"][report["weight_stability"]["flag"] == "unstable"]
        if len(unstable) > 0:
            flags.append(f"unstable_weights: {list(unstable.index)}")
    if not report["icir_decay"].empty:
        decayed = report["icir_decay"][report["icir_decay"]["flag"] == "decayed"]
        if len(decayed) > 0:
            flags.append(f"factor_decay: {list(decayed.index)}")

    report["verdict"] = {
        "overfitting_flags": flags,
        "n_flags": len(flags),
        "assessment": "likely_overfit" if len(flags) >= 2 else ("watch" if len(flags) == 1 else "ok"),
    }
    return report
