"""Idea 17: multi-horizon TSMOM (+12.3 no-504) with sign-constraint variant.
12m/6m/3m each sign(own momentum), EW of legs, then EW of horizons."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from a2_lib import px_series
from util import cost, vol_target, gates, halves_ok, yearly
import pandas as pd, numpy as np

ASSETS = ["SPY","QQQ","DXY","UST10","UST2","UST30","AAA","BAA","XAU","SLV","WTI","BRENT","NATGAS","COPX","EUR","JPY","GBP","CAD"]

def leg(name, w):
    px = px_series(name)
    pos = np.sign(px / px.shift(w) - 1).fillna(0)
    gross = (pos * px.pct_change().shift(-1)).dropna()
    return vol_target(cost(gross, pos.diff().abs().fillna(0)), 0.10)

def book(ws, constraint=None, start="2007-01-01"):
    horizons = {}
    for w in ws:
        legs = pd.DataFrame({a: leg(a, w) for a in ASSETS})
        if constraint:  # only long if own mom>0 else flat (cross-sectional tilt)
            pass
        horizons[w] = legs.loc[legs.index >= start].mean(axis=1)
    combo = pd.DataFrame(horizons).mean(axis=1)
    return vol_target(combo, 0.10).dropna()

if __name__ == "__main__":
    for ws in ([63,126], [126,252], [63,126,252], [21,63,126,252]):
        r = book(ws)
        g = gates(r); h1,h2 = halves_ok(r); yr = yearly(r)
        print(f"multi {ws}: SR={g.get('sr',0):.2f} H1={h1:.2f} H2={h2:.2f} negyr={int((yr<0).sum())}/{len(yr)} worst={yr.min()*100:.1f}% n={len(r)} pass={g.get('pass_')}")
