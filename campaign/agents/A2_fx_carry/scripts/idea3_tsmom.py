"""Idea 3: FX ts-momentum 63d & 126d, sign(mom)/vol, gross=1, vol-target 10%. T+1, 6bps/side."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A2_fx_carry/scripts")
import numpy as np, pandas as pd
import fx_lib as F

def build(px, L, monthly):
    mom = px.pct_change(L)
    vol = px.pct_change().rolling(21).std()*np.sqrt(252)
    raw = np.sign(mom) / vol.clip(0.02)
    pos = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)  # gross=1
    if monthly:
        m = pos.groupby([pos.index.year, pos.index.month]).head(1).index
        pos = pos.loc[m].reindex(pos.index).ffill().fillna(0.0)
    return pos.loc["2000-06-01":]

for L in (63, 126):
    for monthly in (True, False):
        px = F.spots("2000-01-01")
        pos = build(px, L, monthly)
        r = F.net_of(F.t1_pnl(pos, px), pos)
        F.report(f"tsmom{L}_{'mon' if monthly else 'day'}", r)
