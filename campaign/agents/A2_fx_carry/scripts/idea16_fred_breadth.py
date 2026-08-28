"""Idea 16 (charter 2): TSMOM breadth book across ALL usable FRED daily series.
Long if 252d mom>0 else short; vol-target 10% each (trailing only), EW avg, T+1, 6bps."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from a2_lib import px_series
from util import cost, vol_target, gates, halves_ok, yearly
import pandas as pd, numpy as np

ASSETS = ["SPY","QQQ","DXY","UST10","UST2","UST30","AAA","BAA","XAU","SLV",
          "WTI","BRENT","NATGAS","COPX","EUR","JPY","GBP","CAD"]

def tsmom_asset(name, mom_win, vt=True):
    px = px_series(name)
    r = px.pct_change()
    pos = np.sign(px / px.shift(mom_win) - 1).fillna(0)   # decided at t with data <= t
    fr = r.shift(-1)                                       # t->t+1
    gross = (pos * fr).dropna()
    to = pos.diff().abs().fillna(0)
    net = cost(gross, to)
    return vol_target(net, 0.10) if vt else net

def book(mom_win, assets=ASSETS, vt2=True):
    legs = {}
    for a in assets:
        legs[a] = tsmom_asset(a, mom_win)
    df = pd.DataFrame(legs)
    start = df.apply(lambda c: c.ne(0).idxmax()).max()   # start when all legs live
    combo = df.loc[df.index >= start].mean(axis=1)
    if vt2: combo = vol_target(combo, 0.10)
    return combo.dropna()

if __name__ == "__main__":
    for w in (63, 126, 252, 504):
        report2 = book(w)
        g = gates(report2)
        h1, h2 = halves_ok(report2)
        yr = yearly(report2)
        print(f"breadth w={w}: SR={g.get('sr',0):.2f} H1={h1:.2f} H2={h2:.2f} negyr={int((yr<0).sum())}/{len(yr)} "
              f"worst={yr.min()*100:.1f}% n={len(report2)} {report2.index[0].date()}..{report2.index[-1].date()} "
              f"ann={report2.mean()*252*100:.1f}% pass={g.get('pass_')}")
