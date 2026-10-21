
"""
evaluate.py
-----------
Evaluate alpha / risk metrics for a strategy's monthly returns and produce
Table 1/2-style output using the FREE Kenneth French factors for regressions.

Per the paper (Table 1/2): annualized Return, Std.Dev, Sharpe, Skewness,
Kurtosis, Turnover, MDD, and factor-adjusted alphas vs CAPM / FF3 / FF5 (and
momentum-augmented). All alpha t-stats (HAC/Newey-West) reported.
"""
import numpy as np
import pandas as pd


def annualize(monthly_rets, ppy=12):
    r = np.asarray(monthly_rets, dtype=float)
    ann_ret = (1 + r).prod() ** (ppy / len(r)) - 1
    ann_std = r.std(ddof=1) * np.sqrt(ppy)
    sharpe = ann_ret / (ann_std + 1e-9)
    return ann_ret, ann_std, sharpe


def perf_table(monthly_rets, name="Strategy"):
    r = np.asarray(monthly_rets, dtype=float)
    r = r[~np.isnan(r)]
    ann_ret, ann_std, sharpe = annualize(r)
    skew = pd.Series(r).skew()
    kurt = pd.Series(r).kurtosis()
    mdd = drawdown(r)
    return dict(
        Name=name, Return=f"{ann_ret*100:.2f}", StdDev=f"{ann_std*100:.2f}",
        Sharpe=f"{sharpe:.2f}", Skew=f"{skew:.2f}", Kurt=f"{kurt:.2f}",
        MaxDD=f"{mdd*100:.1f}%",
    )


def drawdown(r):
    nav = (1 + r).cumprod()
    peak = np.maximum.accumulate(nav)
    dd = nav / peak - 1
    return dd.min()


def load_factors():
    out = "/Users/daxu/software/world-trader/alphaportfolio_replication/data/factors"
    ff5 = pd.read_csv(f"{out}/ff5_factors.csv")
    ff5["ym"] = ff5["date"].astype(str).str[:7]
    mom = pd.read_csv(f"{out}/momentum_factor.csv")
    mom["ym"] = mom["date"].astype(str).str[:7]
    ff5 = ff5.merge(mom[["ym", "MOM"]], on="ym", how="left")
    ff5["RF"] = ff5["RF"] / 100.0
    for c in ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]:
        ff5[c] = ff5[c] / 100.0
    ff5["MOM"] = ff5["MOM"] / 100.0
    return ff5


def newy_west_se(y, X, L=6):
    """Newey-West HAC covariance with lag L."""
    n, k = X.shape
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    resid = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
    me = X * resid[:, None]
    S = me.T @ me
    for l in range(1, L + 1):
        w = 1 - l / (L + 1)
        G = me[l:].T @ me[:-l]
        S = S + w * (G + G.T)
    cov = np.linalg.inv(X.T @ X) @ S @ np.linalg.inv(X.T @ X)
    return np.sqrt(np.diag(cov))


def factor_alpha(monthly_rets, yms, model_name, factors_df, specs):
    """Run factor regressions; return alpha%, t-stat per spec."""
    r = pd.DataFrame({"ym": yms, "ret": monthly_rets})
    m = r.merge(factors_df, on="ym", how="inner").dropna()
    if len(m) < 24:
        return model_name, {}
    R = (m["ret"] - m["RF"]).to_numpy()
    out = {}
    for label, cols in specs.items():
        X = np.column_stack([np.ones(len(m)), m[cols].to_numpy()])
        beta = np.linalg.lstsq(X, R, rcond=None)[0]
        se = newy_west_se(R, X)
        alpha_ann = (1 + beta[0]) ** 12 - 1
        tstat = beta[0] / (se[0] + 1e-12)
        out[label] = f"{alpha_ann*100:.1f}% (t={tstat:.2f})"
    return model_name, out


def build_report(results, factors_df):
    """results: list of (name, monthly_rets, yms, is_ap)."""
    lines = []
    lines.append("=" * 78)
    lines.append("OUT-OF-SAMPLE PERFORMANCE (Table 1/2 style) - real free data, 2016-2026")
    lines.append("=" * 78)
    header = f"{'Model':<22}{'Ret%':>8}{'Std%':>8}{'Sharpe':>8}{'Skew':>7}{'Kurt':>7}{'MaxDD%':>8}"
    lines.append(header)
    lines.append("-" * 78)
    for name, r, yms, _ in results:
        p = perf_table(r, name)
        lines.append(f"{p['Name']:<22}{p['Return']:>8}{p['StdDev']:>8}"
                     f"{p['Sharpe']:>8}{p['Skew']:>7}{p['Kurt']:>7}{p['MaxDD']:>8}")
    lines.append("-" * 78)
    lines.append("")
    lines.append("FACTOR-ADJUSTED ALPHAS (annualized, Newey-West t):")
    specs = {
        "CAPM": ["Mkt-RF"],
        "FF3": ["Mkt-RF", "SMB", "HML"],
        "FF3+MOM": ["Mkt-RF", "SMB", "HML", "MOM"],
        "FF5": ["Mkt-RF", "SMB", "HML", "RMW", "CMA"],
    }
    for name, r, yms, _ in results:
        mn, out = factor_alpha(r, yms, name, factors_df, specs)
        lines.append(f"\n  {mn}:")
        for k, v in out.items():
            lines.append(f"     {k:<8} {v}")
    return "\n".join(lines)
