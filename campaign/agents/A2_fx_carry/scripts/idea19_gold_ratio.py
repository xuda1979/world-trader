"""Idea 19 (charter 3): gold/silver ratio mean reversion + gold trend combo."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from a2_lib import px_series
from util import cost, vol_target, gates, halves_ok, yearly, scramble_test
import pandas as pd, numpy as np

xau, slv = px_series("XAU"), px_series("SLV")
px = pd.DataFrame({"xau": xau, "slv": slv}).dropna()
ratio = px["xau"] / px["slv"]

def mr_leg(zwin, zthr, hold):
    z = (ratio - ratio.rolling(zwin).mean()) / ratio.rolling(zwin).std()
    # short ratio (short gold/long silver) when z high; long when z low; exit at |z|<hold
    pos = pd.Series(0.0, index=z.index)
    pos[z > zthr] = -1.0
    pos[z < -zthr] = 1.0
    # hold until |z| < hold (fade band)
    pos[(z.abs() < hold)] = 0.0
    pos = pos.replace(0, np.nan).ffill().fillna(0.0)  # keep last non-zero between bands
    # actually: enter beyond thr, exit only when |z|<hold; implement via state machine lite:
    state = pd.Series(0.0, index=z.index)
    cur = 0.0
    zv = z.values; thr_l, thr_h = -zthr, zthr
    for i, zz in enumerate(zv):
        if np.isnan(zz): state.iloc[i] = cur; continue
        if cur == 0:
            if zz > thr_h: cur = -1.0
            elif zz < thr_l: cur = 1.0
        else:
            if abs(zz) < hold: cur = 0.0
        state.iloc[i] = cur
    pos = state
    ret = ratio.pct_change()  # approx: long ratio = long gold short silver 50/50; ret ~ d(ln ratio)
    gross = (pos * ret.shift(-1)).dropna()
    net = cost(gross, pos.diff().abs().fillna(0) * 1.0)   # ratio trade = 2 legs? count 2x turnover below
    net2 = net - pos.diff().abs().fillna(0) * 6.0/1e4     # second leg cost
    return vol_target(net2, 0.10)

def gold_trend(w):
    r = xau.pct_change()
    pos = np.sign(xau / xau.shift(w) - 1).fillna(0)
    gross = (pos * r.shift(-1)).dropna()
    return vol_target(cost(gross, pos.diff().abs().fillna(0)), 0.10)

if __name__ == "__main__":
    mr_legs = {}
    for zwin in (126, 252, 504):
        for zthr in (1.5, 2.0):
            r = mr_leg(zwin, zthr, 0.5)
            g = gates(r); h1, h2 = halves_ok(r)
            print(f"gold/slv MR zwin={zwin} thr={zthr}: SR={g.get('sr',0):.2f} H1={h1:.2f} H2={h2:.2f} pass={g.get('pass_')} [{g.get('why','')}]")
            mr_legs[(zwin,zthr)] = r
    for w in (126, 252):
        r = gold_trend(w)
        g = gates(r); h1, h2 = halves_ok(r); yr = yearly(r)
        print(f"gold trend w={w}: SR={g.get('sr',0):.2f} H1={h1:.2f} H2={h2:.2f} negyr={int((yr<0).sum())}/{len(yr)} pass={g.get('pass_')} [{g.get('why','')}]")
    # combo: MR (252,2.0) + gold trend 126, 50/50 then vt
    combo = vol_target(pd.DataFrame({"mr": mr_legs[(252,2.0)], "gt": gold_trend(126)}).mean(axis=1), 0.10).dropna()
    g = gates(combo); h1, h2 = halves_ok(combo); yr = yearly(combo)
    print(f"COMBO mr+gt: SR={g.get('sr',0):.2f} H1={h1:.2f} H2={h2:.2f} negyr={int((yr<0).sum())}/{len(yr)} worst={yr.min()*100:.1f}% pass={g.get('pass_')} [{g.get('why','')}]")
