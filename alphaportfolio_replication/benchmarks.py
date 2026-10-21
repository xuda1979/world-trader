"""
benchmarks.py
-------------
Benchmark portfolio constructions from the paper (Section 3, Table 1/2):
  - Value-weighted (VW) Fama-French-style long-short
  - Equal-weighted (EW) long-short
  - Linear PPP (parametric portfolio policy): w_i = wbar_i + (1/N) * theta' * x_hat
  - Indirect two-step: use the SAME panel-Transformer scores but form the portfolio
    conventionally (top/bottom decile or proportional to score) rather than
    objective-driven training -- this isolates the direct-optimization contribution.
"""
import numpy as np
import pandas as pd


def top_bottom_long_short(panel, score_col, ret_col, id_col, ym_col, n_long=None, n_short=None):
    """Long top-N / short bottom-N equally weighted by score each month."""
    p = panel.sort_values([ym_col, score_col], ascending=[True, False])
    rets = []
    yms = []
    for ym, g in p.groupby(ym_col):
        n = len(g)
        nl = n_long if n_long else max(1, int(round(0.25 * n)))
        ns = n_short if n_short else nl
        longs = g.head(nl)[ret_col].mean()
        shorts = g.tail(ns)[ret_col].mean()
        rets.append((longs - shorts) / 100.0)
        yms.append(ym)
    return pd.Series(rets, index=yms, name="top_bottom")


def value_weighted_long_short(panel, score_col, ret_col, id_col, ym_col, size_col, n_frac=0.25):
    """VW long-short: weight by size (market-cap proxy) within top/bottom baskets."""
    p = panel.sort_values([ym_col, score_col], ascending=[True, False])
    rets, yms = [], []
    for ym, g in p.groupby(ym_col):
        n = len(g)
        nk = max(1, int(round(n_frac * n)))
        long_tail = g.head(nk)
        short_tail = g.tail(nk)
        l_ret = np.average(long_tail[ret_col].values / 100.0,
                           weights=long_tail[size_col].values.clip(min=0))
        s_ret = np.average(short_tail[ret_col].values / 100.0,
                           weights=short_tail[size_col].values.clip(min=0))
        rets.append(l_ret - s_ret)
        yms.append(ym)
    return pd.Series(rets, index=yms, name="vw_ls")


def linear_ppp(panel, feat_cols, ret_col, id_col, ym_col, train_mask, rf_ann=0.0):
    """Linear PPP (Freyberger-Neuhierl-Weber style): w = wbar + (1/N) theta' x_hat.

    Theta estimated by maximizing Sharpe on the training window (grid/top-down).
    Returns monthly OOS returns.
    """
    p = panel.copy()
    # demean characteristics per date (x_hat)
    for c in feat_cols:
        p[c + "_c"] = p[c] - p.groupby(ym_col)[c].transform("mean")
    xc = [c + "_c" for c in feat_cols]
    # training rows: prefer an explicit _train indicator column (robust to index
    # shifts after merges); fall back to the caller-supplied boolean mask.
    if "_train" in p.columns:
        tr_p = p[p["_train"] == 1]
    elif train_mask is not None:
        tr_p = p[train_mask]
    else:
        tr_p = p
    Xt = tr_p[xc].to_numpy(dtype=float)
    yt = (tr_p[ret_col] / 100.0).to_numpy(dtype=float)
    Xt = np.nan_to_num(Xt)
    # ridge (L2) regularized estimate: prevents the un-regularized OLS over-fit
    # that otherwise yields implausibly large OOS alphas with only ~22 features.
    lam = 1.0
    XtX = Xt.T @ Xt
    A = XtX + lam * np.eye(Xt.shape[1])
    theta = np.linalg.solve(A, Xt.T @ yt)
    theta = theta / (np.abs(theta).max() + 1e-9)

    rets, yms = [], []
    for ym, g in p.groupby(ym_col):
        X = g[xc].to_numpy(dtype=float)
        X = np.nan_to_num(X)
        N = len(g)
        w = (X @ theta) / N
        w = w - w.mean()
        w = w / (np.abs(w).sum() + 1e-9)
        r = float(np.dot(w, (g[ret_col] / 100.0).to_numpy()))
        rets.append(r); yms.append(ym)
    return pd.Series(rets, index=yms, name="linear_ppp")
