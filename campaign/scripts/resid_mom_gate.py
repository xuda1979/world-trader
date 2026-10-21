"""Residual momentum with MA-gate (coordinator build; A6 idea-4 recipe).
12m residual returns (vs FF3+MOM rolling regression), long top tercile,
SPX>MA150 gate (continuous confirm=10d), T+1, 6bps, vt10."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from data import closes, ff_factors, ff_mom, fred, save_sleeve
from util import gates, cost
import pandas as pd, numpy as np

OUT = "/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/residmom_gated.csv"
px = closes()
ret = px.pct_change(fill_method=None)
ff = ff_factors(); mom = ff_mom()
F = pd.concat([ff[["Mkt-RF","SMB","HML"]], mom], axis=1).reindex(ret.index).ffill()

# residual: r - F @ beta (rolling 252d, min 200)
resid = pd.DataFrame(index=ret.index, columns=ret.columns, dtype=float)
for c in ret.columns:
    r = ret[c]
    ok = r.notna() & F["Mkt-RF"].notna()
    # rolling multi-factor via cumulative approach per window is heavy; use monthly approx:
    resid[c] = np.nan
# vectorized: expand F with const, solve per rolling window in chunks of 63d
import numpy.linalg as la
Fm = pd.concat([pd.Series(1.0, index=F.index, name="const"), F], axis=1)
vals = Fm.values
res = np.full(ret.shape, np.nan)
R = ret.values
win, step = 252, 21
for s in range(0, len(ret)-win, step):
    sl = slice(s, s+win)
    W = vals[sl]
    mask = ~np.isnan(R[sl])
    for j in range(R.shape[1]):
        m = mask[:, j]
        if m.sum() < 200: continue
        try:
            b, *_ = la.lstsq(W[m], R[sl, j][m], rcond=None)
            pred = np.nanmean((R[sl, j] - W @ b)[~m]) if (~m).any() else 0
            res[s+win-1, j] = np.nanmean(R[sl, j][m] - (W[m] @ b))
        except Exception:
            pass
# rolling residual-mom: use last window's mean residual as of each step; forward-fill daily
resid_df = pd.DataFrame(res, index=ret.index, columns=ret.columns)
resid_12m = resid_df.rolling(528, min_periods=300).sum()  # ~12 windows of residual means
sig = resid_12m
# rank monthly
mend = pd.to_datetime(pd.Series(ret.index).groupby(ret.index.to_period("M")).max().values)
sig_m = sig.reindex(mend)
w = pd.DataFrame(0.0, index=mend, columns=px.columns)
for t in mend:
    row = sig_m.loc[t].dropna()
    if len(row) < 60: continue
    k = max(len(row)//3, 1)
    top = row.nlargest(k).index
    w.loc[t, top] = 1.0/len(top)
pos_d = w.reindex(ret.index).ffill()
# MA gate
spx = fred("spx").reindex(ret.index).ffill()
ma = spx.rolling(150).mean()
gate = (spx > ma).astype(float).rolling(10, min_periods=1).mean()  # 10d confirm
pos_exec = (pos_d.shift(1) * gate.shift(1).fillna(0)).fillna(0)
pnl = (pos_exec*ret).sum(axis=1, min_count=1)
to = pos_exec.diff().abs().sum(axis=1).fillna(0)
net = cost(pnl, to)
vol = net.expanding(min_periods=126).std().shift(1)*np.sqrt(252)
lev = (0.10/vol).clip(0,2).fillna(0)
out = (net*lev).dropna()
out = out[out.index >= "2008-01-01"]
g = gates(out)
print("RESIDMOM gated:", g)
yr = out.groupby(out.index.year).apply(lambda x:(1+x).prod()-1)
print({int(k): round(v*100,1) for k,v in yr.items()})
if g.get("pass_"):
    save_sleeve(out, OUT, "12m residual momentum, top tercile, SPX>MA150 10d-confirm gate, vt10, 6bps T+1")
