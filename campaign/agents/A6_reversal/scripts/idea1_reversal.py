import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from lib6 import closes, COST_BPS

px = closes()
rets = px.pct_change(fill_method=None)
rets = rets.clip(-0.5, 0.5)  # cap data glitches
n_days = len(px)
print("panel", px.shape, px.index[0].date(), px.index[-1].date())

# data-quality mask: listed (non-NaN price) with 120d history
hist_cnt = px.notna().cumsum()
univ = px.notna() & (hist_cnt >= 120) & rets.notna()

# market = EW mean of universe rets
mkt = rets.where(univ).mean(axis=1)

# trailing 60d idio vol (single-factor residual, expanding regression approx):
# idio = r - beta*mkt ; beta via rolling 60d cov/var, min 40 obs
cov = rets.sub(mkt, axis=0).mul(rets.sub(mkt, axis=0))  # not needed; do proper:
def roll_idio_vol(rets, mkt, win=60, minobs=40):
    x = mkt
    out = {}
    r_ex = rets.sub(mkt, axis=0)
    var_m = x.rolling(win, min_periods=minobs).var()
    # rolling cov via sum of products
    for chunk in [rets]: pass
    # vectorized: E[ry]-E[r]E[y]
    m_r = rets.rolling(win, min_periods=minobs).mean()
    m_x = x.rolling(win, min_periods=minobs).mean()
    m_rx = (rets.mul(x, axis=0)).rolling(win, min_periods=minobs).mean()
    beta = (m_rx - m_r.mul(m_x, axis=0)).div(var_m, axis=0)
    resid = rets.sub(beta.mul(x, axis=0))
    ivol = resid.rolling(win, min_periods=minobs).std()
    return ivol

ivol = roll_idio_vol(rets, mkt)
ivol_lo = pd.Series(ivol.quantile(0.10, axis=1).values, index=rets.index)
ivol_hi = pd.Series(ivol.quantile(0.90, axis=1).values, index=rets.index)
iv_ok = ivol.ge(ivol_lo, axis=0) & ivol.le(ivol_hi, axis=0)   # exclude top/bottom 10% idio vol

def run(sig_df, rets, univ, tranche=1, cost_bps=COST_BPS):
    """sig_df: target weight matrix formed at t (data<=t). Holds across tranche days."""
    W = sig_df.where(univ)
    gross = (W.shift(1) * rets).sum(axis=1)
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1).fillna(0.0)
    net = gross - turn * cost_bps / 1e4
    return net, turn.mean(), (W.abs().sum(axis=1)).mean()

def xs_reversal_weights(rets, k=5, lo=0.2, hi=0.2, iv_ok=None, volscale=None, cadence=1):
    """Form weights every `cadence` days; between formations carry previous target."""
    mom = rets.rolling(k).sum()
    ok = rets.notna()
    if iv_ok is not None: ok = ok & iv_ok
    r = mom.where(ok)
    n = ok.sum(axis=1)
    q_lo = r.quantile(lo, axis=1)
    q_hi = r.quantile(1-hi, axis=1)
    short = r.ge(q_hi, axis=0) & ok          # best performers -> short
    long_ = r.le(q_lo, axis=0) & ok          # worst -> long
    w = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
    nl = (long_).sum(axis=1); ns = (short).sum(axis=1)
    if volscale is not None:
        # inverse-vol weights within each side
        inv = 1.0/volscale.where(ok)
        lsum = (long_ * inv).sum(axis=1).clip(lower=1e-12)
        ssum = (short * inv).sum(axis=1).clip(lower=1e-12)
        lw = (long_ * inv).div(lsum, axis=0).fillna(0.0)
        sw = (short * inv).div(ssum, axis=0).fillna(0.0)
    else:
        lw = long_.div(nl.clip(lower=1), axis=0).fillna(0.0)
        sw = short.div(ns.clip(lower=1), axis=0).fillna(0.0)
    w = 0.5*lw - 0.5*sw
    # cadence: only update on every cadence-th day
    if cadence > 1:
        mask = (np.arange(len(w)) % cadence == 0)
        Wt = w.copy()
        last = w.iloc[0]
        arr = w.values.copy()
        cur = arr[0]
        for i in range(len(arr)):
            if mask[i]: cur = arr[i]
            else: arr[i] = cur
        w = pd.DataFrame(arr, index=w.index, columns=w.columns)
    return w

vols = rets.rolling(20).std()
rows = []
grid = []
for k in [3, 5, 10]:
    for use_iv in [False, True]:
        for vs in [None, vols]:
            for cad in [1, 5, 10]:
                w = xs_reversal_weights(rets, k=k, iv_ok=(ivol_ok := iv_ok if use_iv else None),
                                        volscale=vs, cadence=cad)
                net, avgturn, grosslev = run(w, rets, univ)
                s = net[net.index >= '2007-01-01']
                st = s.std()*np.sqrt(252)*100
                sr = s.mean()/s.std()*np.sqrt(252) if s.std()>0 else 0
                grid.append((k, use_iv, vs is not None, cad, sr, st, avgturn*1e4))
g = pd.DataFrame(grid, columns=["k","ivfilter","invvol","cadence","SR","vol%","turn_bps/d"])
print(g.sort_values("SR", ascending=False).to_string(index=False))
