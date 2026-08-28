"""A6 Idea 2 near-miss (NOT saved as sleeve — fails gate d on 2022 -12.9%):
residual momentum long tercile + MA150 confirm-10 hysteresis gate. SR 1.03 net.
Reference implementation for r2 / coordinator blending."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import closes, stats, halves_sr, vol_target
from idea234_engine import resid_momentum, weights_long, rets, px

_, resid_mom, _ = resid_momentum()
W = weights_long(resid_mom, rets.notna() & (px.notna().cumsum() >= 120), frac=1/3, cadence=21)
mkt_px = px.mean(axis=1)
ma = mkt_px.rolling(150, min_periods=75).mean()
above = (mkt_px > ma).values; below = (mkt_px < ma * 0.98).values
state = np.zeros(len(mkt_px)); s = 0; cnt = 0
for i in range(len(mkt_px)):
    if np.isnan(ma.iloc[i]): s = 0; cnt = 0
    else:
        if s == 1 and below[i]: s = 0; cnt = 0
        elif s == 0:
            cnt = cnt + 1 if above[i] else 0
            if cnt >= 10: s = 1
    state[i] = s
gate = pd.Series(state, index=mkt_px.index)
Wg = W.mul(gate.reindex_like(px).fillna(0.0), axis=0)
gross = (Wg.shift(1) * rets).sum(axis=1)["2007-01-01":]
turn = (Wg.shift(1) - Wg.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
net = gross - turn * 6 / 1e4
vt, _ = vol_target(net, 0.10)
s = stats(vt); h = halves_sr(vt)
print(f"gated resid-mom vol-tgt: SR={s['sr']:.2f} H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']} worst={s['worst_year']:.1f}%")
