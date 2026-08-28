"""Idea 20 (charter 4): (a) WTI-Brent spread mean reversion; (b) copper/gold ratio trend."""
import sys; sys.path.insert(0, "campaign/agents/A2_fx_carry/scripts")
sys.path.insert(0, "campaign/scripts"); sys.path.insert(0, "campaign/harness")
from a2_lib import px_series
from util import cost, vol_target, gates, halves_ok, yearly
import pandas as pd, numpy as np

wti, brent = px_series("WTI"), px_series("BRENT")
spr = (wti - brent).dropna()          # spread in $ level
spr = spr[spr.abs() < 60]             # sanity (2020 glitch guard)
spr_ret = spr.diff().dropna()         # pnl of long spread = change in spread ($ terms) — normalize by wti px
spr_ret = spr.diff() / wti.reindex(spr.index).ffill()   # scale by crude price for vol stability

def spread_mr(zwin, zthr):
    z = (spr - spr.rolling(zwin).mean()) / spr.rolling(zwin).std()
    pos = np.sign(-z).where(z.abs() > zthr, 0.0)
    pos = pos.replace(0, np.nan)
    pos = pos.where(z.abs() > zthr*0.5, 0).ffill().fillna(0)
    gross = (pos * spr_ret.shift(-1)).dropna()
    net = cost(gross, pos.diff().abs().fillna(0))
    net = net - pos.diff().abs().fillna(0) * 6.0/1e4    # 2nd leg
    return vol_target(net, 0.10)

def cu_au(w):
    cu, au = px_series("COPX"), px_series("XAU")
    ratio = (cu / au).dropna()
    pos = np.sign(ratio / ratio.shift(w) - 1).fillna(0)
    ret = ratio.pct_change()
    gross = (pos * ret.shift(-1)).dropna()
    net = cost(gross, pos.diff().abs().fillna(0))
    net = net - pos.diff().abs().fillna(0) * 6.0/1e4
    return vol_target(net, 0.10)

sr = lambda x: x.mean()/x.std()*np.sqrt(252) if x.std()>0 else 0
print("== WTI-Brent spread MR ==")
for zwin in (63, 126, 252):
    for zthr in (1.0, 1.5, 2.0):
        r = spread_mr(zwin, zthr)
        if len(r) < 800: print(f"  zwin={zwin} thr={zthr}: too short n={len(r)}"); continue
        h1, h2 = halves_ok(r)
        print(f"  zwin={zwin} thr={zthr}: SR={sr(r):5.2f} H1={h1:5.2f} H2={h2:5.2f} n={len(r)} {r.index[0].date()}..{r.index[-1].date()}")
print("== copper/gold ratio trend ==")
for w in (63, 126, 252):
    r = cu_au(w); h1, h2 = halves_ok(r)
    print(f"  w={w}: SR={sr(r):5.2f} H1={h1:5.2f} H2={h2:5.2f} n={len(r)} {r.index[0].date()}..{r.index[-1].date()}")
