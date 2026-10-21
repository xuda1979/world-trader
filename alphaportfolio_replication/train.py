
"""
train.py
--------
Direct policy-search (DRL) training of AlphaPortfolio on the real monthly panel.

Per the paper:
  - The policy pi_theta = LSP( PTF(Z;theta) ) maps each date's panel of lagged
    feature sequences to long-short portfolio weights (Eq 11 / Eq 18).
  - Objective: annualized Sharpe ratio of the resulting portfolio's realized
    monthly returns (path-dependent, optimized by direct policy search with
    pathwise gradients; no value-function / supervised return estimation).
  - Walk-forward: train on early period, validate for early stopping, test OOS.
"""
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

import model
from model import long_short_weights

FEATURES = None  # set by caller


def feat_to_tensor(x):
    arr = np.asarray(x, dtype=np.float32)
    if np.isnan(arr).any() or np.isinf(arr).any():
        arr = np.where(np.isfinite(arr), arr, 0.0)
    return torch.tensor(arr, dtype=torch.float32)


def build_date_batches(panel, features, K=11):
    """Return dict month -> (tensor (I,L,F), targets (I,), ids)."""
    p = panel.sort_values(["sym_or_id", "ym"]) if "sym_or_id" in p else panel
    return None


def standardize_panel(panel, feat_cols, ym_col, id_col=None):
    """Per-month cross-sectional z-score of the raw characteristics.

    Each month's features are normalized across the surviving cross-section in
    that month, matching the paper's reliance on cross-sectional characteristics.
    Because each month is standardized on its own assets only, there is no
    look-ahead leakage between train / val / test. Winsorized at 1/99 pct to tame
    outliers (e.g. spinoff returns).
    """
    p = panel.copy()
    feats = [c for c in feat_cols if p[c].notna().any()]
    for ym, g in p.groupby(ym_col):
        for c in feats:
            v = pd.to_numeric(g[c], errors="coerce").to_numpy(dtype=float)
            v = v[np.isfinite(v)]
            if v.size < 3:
                continue
            lo, hi = np.nanpercentile(v, 1), np.nanpercentile(v, 99)
            vc = np.clip(v, lo, hi)
            mu = vc.mean()
            sd = vc.std()
            if not np.isfinite(mu) or np.isnan(sd) or sd < 1e-8:
                continue
            mask = (p[ym_col] == ym).to_numpy()
            vals = pd.to_numeric(p.loc[mask, c], errors="coerce").to_numpy(dtype=float)
            vals = np.clip(vals, lo, hi)
            p.loc[mask, c] = (vals - mu) / sd
    return p


def prepare_dates(panel, feat_cols, id_col, ym_col, ret_col, K=11):
    """Create per-month data: seqs (I,K+1,F), next-ret targets, ids."""
    p = panel.sort_values([id_col, ym_col]).copy()
    p["_tnext"] = p.groupby(id_col)[ret_col].shift(-1)
    dates = {}
    for ym, g in p.groupby(ym_col):
        g = g.dropna(subset=feat_cols + ["_tnext"])
        if len(g) < 8:
            continue
        seqs, targs, ids = [], [], []
        for _, row in g.iterrows():
            hist = p[(p[id_col] == row[id_col]) & (p[ym_col] <= ym)].tail(K + 1)
            if len(hist) < 5:              # allow partial but require >=5 lags
                continue
            arr = hist[feat_cols].tail(K + 1).to_numpy(dtype=np.float32)
            pad = K + 1 - arr.shape[0]
            if pad > 0:
                arr = np.vstack([np.zeros((pad, arr.shape[1]), dtype=np.float32), arr])
            seqs.append(arr); targs.append(row["_tnext"]); ids.append(row[id_col])
        if len(seqs) >= 8:
            dates[ym] = dict(seqs=np.stack(seqs), targets=np.array(targs, dtype=np.float32), ids=ids)
    return dates


def portfolio_returns_for(model_, dates, G_frac=0.25, device="cpu"):
    """Compute one portfolio return per month given current weights."""
    rets = []
    model_.eval()
    with torch.no_grad():
        for ym, d in dates.items():
            X = feat_to_tensor(d["seqs"]).to(device)
            s = model_(X).detach().cpu().numpy()
            w = long_short_weights(s, G=G_frac)
            # targets are in percent; convert to decimal → consistent with benchmarks
            rt = float(np.dot(w, d["targets"])) / 100.0
            rets.append(rt)
    return np.array(rets)


def compute_sharpe(monthly_rets, rf_ann=0.0, ppy=12):
    ex = monthly_rets - rf_ann / ppy
    return float(np.mean(ex) / (np.std(ex) + 1e-8) * np.sqrt(ppy))


def train_step(model_, dates, opt, G_frac=0.25, device="cpu"):
    """One optimizer step maximizing the differentiable annualized Sharpe."""
    model_.train()
    # forward all months, detaching nothing (full autograd over the trajectory)
    monthly = []
    for ym, d in dates.items():
        X = feat_to_tensor(d["seqs"]).to(device)
        s = model_(X)
        # differentiable long-short weights
        w = differentiable_weights(s, G_frac)
        rt = torch.dot(w, torch.tensor(d["targets"], dtype=torch.float32, device=device))
        monthly.append(rt)
    r = torch.stack(monthly)
    mu = r.mean()
    sd = r.std(unbiased=False) + 1e-8
    sharpe = (mu / sd) * np.sqrt(12)
    neg = -sharpe
    opt.zero_grad()
    neg.backward()
    torch.nn.utils.clip_grad_norm_(model_.parameters(), 5.0)
    opt.step()
    return float(sharpe.item())


def differentiable_weights(scores, G_frac=0.25):
    """Differentiable version of the LSP long-short generator (Eq 11)."""
    I = scores.shape[0]
    G = max(1, int(round(G_frac * I)))
    # top-G long, bottom-G short via hard selection in forward, straight-through grad
    order = torch.argsort(-scores, dim=0)
    long_idx = order[:G]
    short_idx = order[-G:]
    es = torch.exp(scores - scores.max())
    es = es.clamp(max=1e8)
    lw = es[long_idx] / (es[long_idx].sum() + 1e-8)
    sw = es[short_idx] / (es[short_idx].sum() + 1e-8)
    w = torch.zeros(I, dtype=scores.dtype, device=scores.device)
    w = w.index_copy(0, long_idx, lw).index_copy(0, short_idx, -sw)
    # normalize gross
    w = w / (w.abs().sum() + 1e-8)
    return w


def train(model_, train_dates, val_dates, epochs=60, lr=2e-3,
          G_frac=0.25, device="cpu", print_every=10, weight_decay=1e-5,
          patience=10):
    opt = torch.optim.Adam(model_.parameters(), lr=lr, weight_decay=weight_decay)
    best_val, best_state = -1e9, None
    hist = []
    best_ep = 0
    no_impr = 0
    for ep in range(1, epochs + 1):
        tr_sr = train_step(model_, train_dates, opt, G_frac, device)
        val_sr = compute_sharpe(portfolio_returns_for(model_, val_dates, G_frac, device))
        hist.append((ep, tr_sr, val_sr))
        if val_sr > best_val:
            best_val = val_sr
            best_state = {k: v.detach().cpu().clone() for k, v in model_.state_dict().items()}
            best_ep = ep
            no_impr = 0
        else:
            no_impr += 1
        if ep % print_every == 0 or ep == 1:
            print(f"  epoch {ep:3d}: train Sharpe {tr_sr:6.3f} | val Sharpe {val_sr:6.3f}")
        if no_impr >= patience:
            print(f"  early stop at epoch {ep} (best val {best_val:.3f} @ epoch {best_ep})")
            break
    if best_state is not None:
        model_.load_state_dict(best_state)
        print(f"  restored best-val model from epoch {best_ep} (val Sharpe {best_val:.3f})")
    return hist
