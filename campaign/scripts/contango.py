"""Contango carry sleeve (coordinator reproduction of A5's best): long SPX when
VIX<VIX3M with hysteresis 0.05, cash otherwise; T+1, 6bps, vt10 expanding."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from data import fred, save_sleeve, COST
from util import gates, cost
import pandas as pd, numpy as np

OUT = "/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/contango_spx.csv"
vix = pd.read_csv("/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix_daily.csv", index_col=0, parse_dates=True)["vix"]
v3m = pd.read_csv("/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix3m.csv", index_col=0, parse_dates=True)["vix3m"]
ratio = (vix/v3m).dropna()
spx = fred("spx")
ret = spx.pct_change()
idx = ret.index.intersection(ratio.index)
ret = ret.reindex(idx); ratio = ratio.reindex(idx).ffill()

# hysteresis state machine
state, pos = 0, []
r = ratio.values
for x in r:
    if state == 0 and x < 1.0 - 0.05:
        state = 1
    elif state == 1 and x > 1.0:
        state = 0
    pos.append(state)
pos = pd.Series(pos, index=idx).shift(1).fillna(0)   # T+1
gross = pos*ret
to = pos.diff().abs().fillna(0)
net = cost(gross, to)
vol = net.expanding(min_periods=126).std().shift(1)*np.sqrt(252)
lev = (0.10/vol).clip(0,2).fillna(0)
out = (net*lev).dropna()
out = out[out.index >= "2008-01-01"]
g = gates(out)
print("CONTANGO:", g)
yr = out.groupby(out.index.year).apply(lambda x:(1+x).prod()-1)
print({int(k): round(v*100,1) for k,v in yr.items()})
if g.get("pass_") or g.get("sr", 0) >= 0.7:   # coordinator note: near-miss kept for blend testing
    save_sleeve(out, OUT, "SPX contango carry (vix/vix3m hysteresis 0.05), vt10, 6bps T+1; near-miss w/ real signal (scramble p=0 per A5)")
