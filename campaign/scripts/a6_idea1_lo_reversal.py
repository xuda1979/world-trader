"""A6 Idea 1 near-miss (NOT saved as sleeve — fails gate d): LO weekly reversal.
Long worst-decile 10d losers, idio-vol middle-80% universe, 5d cadence, T+1, 6bps/side.
Net SR 0.67 raw / 0.63 vol-tgt; fails yearly gate (2008 -5.6%, 2022 -5.3%).
Reference implementation for r2 iteration."""
import sys, os
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import closes, stats, halves_sr, vol_target

px = closes()
rets = px.pct_change(fill_method=None).clip(-0.5, 0.5)
hist = px.notna().cumsum()
mkt = rets.mean(axis=1)
m_r = rets.rolling(60, min_periods=40).mean(); m_x = mkt.rolling(60, min_periods=40).mean()
m_rx = (rets.mul(mkt, axis=0)).rolling(60, min_periods=40).mean()
beta = (m_rx - m_r.mul(m_x, axis=0)).div(mkt.rolling(60, min_periods=40).var(), axis=0)
ivol = rets.sub(beta.mul(mkt, axis=0)).rolling(60, min_periods=40).std()
ok = (rets.notna() & (hist >= 120)
      & ivol.ge(ivol.quantile(0.10, axis=1), axis=0).fillna(False)
      & ivol.le(ivol.quantile(0.90, axis=1), axis=0).fillna(False))
r10 = rets.rolling(10).sum().where(ok)
L = r10.le(r10.quantile(0.2, axis=1), axis=0) & ok
w = L.div(L.sum(axis=1).clip(lower=1), axis=0).fillna(0.0)
arr = np.array(w.values); cur = arr[0]
for i in range(len(arr)):
    if (np.arange(len(arr)) % 5 == 0)[i]: cur = arr[i]
    else: arr[i] = cur
W = pd.DataFrame(arr, index=w.index, columns=w.columns)
gross = (W.shift(1) * rets).sum(axis=1)["2007-01-01":]
turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
net = gross - turn * 6 / 1e4
vt, lev = vol_target(net, 0.10)
s = stats(vt); h = halves_sr(vt)
print(f"LO-rev vol-tgt: SR={s['sr']:.2f} H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']} worst={s['worst_year']:.1f}%")
