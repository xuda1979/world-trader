"""Ensemble portfolio of successful L/S strategies.

Combines the financing-on, non-overfit strategies from the research sweeps
into an optimized portfolio. Uses the SAME annualization as backtest.py:
  ann_ret = (1 + daily_mean)^252 - 1   (geometric)
  ann_vol = std(daily, ddof=0) * sqrt(252)
  sharpe  = ann_ret / ann_vol

Output: tools/quant/ls/results/ensemble_portfolio/
"""
from __future__ import annotations
import os, sys, json
import pandas as pd
import numpy as np
from scipy.optimize import minimize

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

BASE = os.path.join(ROOT, "tools/quant/ls/results")
OUT = os.path.join(BASE, "ensemble_portfolio")
os.makedirs(OUT, exist_ok=True)

# Diversified subset of financing-on, non-overfit strategies
SELECTED = {
    "gbrt_s05_d2":  "gbrt_tune/s05_d2",        # GBRT d=2 s=0.5 (best)
    "gbrt_s07_d4":  "gbrt_tune/s07_d4",        # GBRT d=4 s=0.7
    "gbrt_d3":      "gbrt_vs_icir_test/gbrt_demean_zscore",
    "icir_mv_l05":  "h4_weighting/mean_var_l05",
    "icir_9f":      "extra_factors_test/9f_with_extra",
}

ANN = 252.0

def annualize(daily: pd.Series) -> dict:
    """Match backtest.py annualization exactly."""
    daily = daily.dropna()
    ann_ret = float((1 + daily.mean()) ** ANN - 1) if daily.mean() != 0 else 0.0
    ann_vol = float(daily.std(ddof=0) * np.sqrt(ANN))
    sharpe = float(ann_ret / ann_vol) if ann_vol > 0 else 0.0
    # Drawdown from cumulative compounded equity
    eq = (1 + daily).cumprod()
    running_max = eq.cummax()
    dd = float(((eq / running_max) - 1).min())
    return dict(ann_ret=ann_ret, ann_vol=ann_vol, sharpe=sharpe, max_dd=dd)


def load_returns():
    frames = {}
    for label, sub in SELECTED.items():
        p = os.path.join(BASE, sub, "daily_returns.csv")
        df = pd.read_csv(p, index_col=0, parse_dates=True)
        frames[label] = df["daily_return"]
    return pd.DataFrame(frames).dropna()


def opt_mean_var(mu, Sigma, cap=0.5, floor=0.0):
    n = len(mu)
    def neg_sharpe(w):
        r = w @ mu; v = np.sqrt(w @ Sigma @ w)
        return -r/v if v > 0 else 0
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    bounds = [(floor, cap)] * n
    res = minimize(neg_sharpe, np.ones(n)/n, method="SLSQP", bounds=bounds, constraints=cons,
                   options={"maxiter": 500, "ftol": 1e-10})
    return res.x

def opt_risk_parity(Sigma, cap=0.5, floor=0.05):
    n = len(Sigma)
    def rc_obj(w):
        pv = np.sqrt(w @ Sigma @ w)
        marginal = Sigma @ w / pv
        rc = w * marginal
        return ((rc - rc.mean())**2).sum()
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    bounds = [(floor, cap)] * n
    res = minimize(rc_obj, np.ones(n)/n, method="SLSQP", bounds=bounds, constraints=cons,
                   options={"maxiter": 500, "ftol": 1e-12})
    return res.x

def opt_min_var(Sigma, cap=0.5, floor=0.0):
    n = len(Sigma)
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    bounds = [(floor, cap)] * n
    res = minimize(lambda w: w @ Sigma @ w, np.ones(n)/n, method="SLSQP",
                   bounds=bounds, constraints=cons, options={"maxiter": 500, "ftol": 1e-12})
    return res.x


def main():
    rets = load_returns()
    print(f"Ensemble: {rets.shape[1]} strategies, {rets.shape[0]} days")
    print(f"Date range: {rets.index.min().date()} .. {rets.index.max().date()}\n")

    # Individual stats (backtest-consistent annualization)
    print(f"{'strategy':16s} {'sharpe':>8s} {'ann_ret':>9s} {'ann_vol':>8s} {'max_dd':>8s}")
    print("-"*55)
    indiv = {}
    for c in rets.columns:
        s = annualize(rets[c]); indiv[c] = s
        print(f"{c:16s} {s['sharpe']:>+8.3f} {s['ann_ret']:>+9.4f} {s['ann_vol']:>8.4f} {s['max_dd']:>+8.3f}")

    mu = np.array([indiv[c]["ann_ret"] for c in rets.columns])
    Sigma = rets.cov().values * ANN

    # Correlation
    corr = rets.corr()
    print(f"\nCorrelation matrix:\n{corr.round(3).to_string()}\n")

    # Optimization
    w_eq = np.ones(len(mu))/len(mu)
    w_mv = opt_mean_var(mu, Sigma, cap=0.5, floor=0.0)
    w_mv_div = opt_mean_var(mu, Sigma, cap=0.4, floor=0.10)  # enforced diversification
    w_rp = opt_risk_parity(Sigma, cap=0.5, floor=0.05)
    w_minvar = opt_min_var(Sigma, cap=0.5, floor=0.0)
    w_iv = 1/np.diag(Sigma); w_iv /= w_iv.sum()

    weights = {
        "equal_weight": w_eq,
        "mean_var_opt": w_mv,
        "mean_var_diversified": w_mv_div,
        "risk_parity": w_rp,
        "min_variance": w_minvar,
        "inv_variance": w_iv,
    }

    print(f"{'='*72}")
    print(f"PORTFOLIO WEIGHTS")
    print(f"{'='*72}")
    print(f"{'strategy':16s} " + " ".join(f"{n:>10s}" for n in weights))
    for i, c in enumerate(rets.columns):
        print(f"{c:16s} " + " ".join(f"{w[i]:>10.1%}" for w in weights.values()))

    print(f"\n{'='*72}")
    print(f"OPTIMIZED PORTFOLIO PERFORMANCE (annualized, financing on)")
    print(f"{'='*72}")
    print(f"{'portfolio':22s} {'sharpe':>8s} {'ann_ret':>9s} {'ann_vol':>8s} {'max_dd':>8s}")
    print("-"*60)
    results = {}
    for label, w in weights.items():
        port = (rets * w).sum(axis=1)
        s = annualize(port)
        results[label] = {**s, "weights": dict(zip(rets.columns, w.round(4)))}
        print(f"{label:22s} {s['sharpe']:>+8.3f} {s['ann_ret']:>+9.4f} {s['ann_vol']:>8.4f} {s['max_dd']:>+8.3f}")

    # Save
    port_mv = (rets * w_mv).sum(axis=1)
    port_eq = (rets * w_eq).sum(axis=1)
    pd.DataFrame({"equal_weight": port_eq, "mean_var_opt": port_mv,
                  "risk_parity": (rets * w_rp).sum(axis=1)}).to_csv(
        os.path.join(OUT, "ensemble_daily_returns.csv"))
    with open(os.path.join(OUT, "ensemble_metrics.json"), "w") as f:
        json.dump({"individual": {k: indiv[k] for k in rets.columns},
                   "portfolios": results,
                   "correlation": corr.round(4).to_dict()}, f, indent=2)
    print(f"\nSaved -> {OUT}/ensemble_daily_returns.csv + ensemble_metrics.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
