"""Idea 18 (charter 1c): positioning-extreme trend-conflict exits on top of 63/126 TSMOM.
Plus charter 1a-c hybrid: trend + COT extreme as veto overlay."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from a2_lib import px_series, cot_weekly, daily_align, weekly_pos_from_z
from util import cost, vol_target, gates, halves_ok, yearly
from idea17_tsmom_multi import leg
import pandas as pd, numpy as np

ASSETS = ["SPY","QQQ","DXY","UST10","UST2","UST30","XAU","SLV","WTI","BRENT","NATGAS","COPX","EUR","JPY","GBP","CAD"]
COTMAP = {"SPY":"SPY","QQQ":"QQQ","UST10":"UST10","UST2":"UST2","UST30":"UST30",
          "EUR":"EUR","JPY":"JPY","GBP":"GBP","CAD":"CAD"}

def leg_veto(name, w, cot_z, mode):
    """trend position, vetoed when positioning extreme conflicts (mode=conflict) or is extreme (mode=fade)."""
    px = px_series(name)
    pos = np.sign(px / px.shift(w) - 1).fillna(0)
    if name in COTMAP and cot_z.get(name) is not None:
        z = cot_z[name].reindex(px.index).ffill()          # z as of release, PIT (release index)
        if mode == "conflict":
            flip = ((pos > 0) & (z < -2.0)) | ((pos < 0) & (z > 2.0))
            pos = pos.where(~flip, 0.0)
        elif mode == "fade":
            ext = z.abs() > 2.0
            pos = pos.where(~ext, 0.0)
    gross = (pos * px.pct_change().shift(-1)).dropna()
    net = cost(gross, pos.diff().abs().fillna(0))
    return vol_target(net, 0.10)

def run(ws=(63,126), mode=None):
    lf = cot_weekly("tff", "lf")
    zs = {}
    for a, net in lf.items():
        z = (net - net.rolling(104).mean()) / net.rolling(104).std()
        zs[a] = z.shift(1)   # release Fri -> usable next week
    horizons = []
    for w in ws:
        legs = pd.DataFrame({a: leg_veto(a, w, zs, mode) for a in ASSETS})
        horizons.append(legs.mean(axis=1))
    combo = pd.DataFrame(dict(zip(ws, horizons))).mean(axis=1)
    return vol_target(combo[combo.index >= "2007-01-01"], 0.10).dropna()

if __name__ == "__main__":
    for mode in (None, "conflict", "fade"):
        r = run(mode=mode)
        g = gates(r); h1, h2 = halves_ok(r); yr = yearly(r)
        print(f"veto mode={mode}: SR={g.get('sr',0):.2f} H1={h1:.2f} H2={h2:.2f} negyr={int((yr<0).sum())}/{len(yr)} worst={yr.min()*100:.1f}% pass={g.get('pass_')} [{g.get('why','')}]")
