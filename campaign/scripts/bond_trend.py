"""Bond trend sleeve: 10Y & 30Y Treasury duration-approximated total returns
from FRED yields, then 63/252d dual trend. T+1, 6bps on switches, vt10.
TR approximation: daily ret = duration * (-delta_yield) + carry(yield/252)."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from data import fred, save_sleeve
from util import gates, cost
import numpy as np
import pandas as pd

OUT = "/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/bond_trend.csv"

def synth_tr(yld, dur=8.0):
    dy = yld.diff() / 100.0          # yield in % -> decimal, daily change
    carry = yld.ffill() / 100.0 / 252.0
    return dur * (-dy) + carry

def build():
    y10 = fred("us10y"); y30 = fred("us30y")
    r10 = synth_tr(y10, dur=7.5); r30 = synth_tr(y30, dur=15.0)
    px10 = (1 + r10.fillna(0)).cumprod(); px30 = (1 + r30.fillna(0)).cumprod()
    out = {}
    for nm, px in [("10y", px10), ("30y", px30)]:
        mom252 = px / px.shift(252) - 1
        mom63 = px / px.shift(63) - 1
        sig = ((mom252 > 0) & (mom63 > 0)).astype(float) - ((mom252 < 0) & (mom63 < 0)).astype(float)
        out[nm] = sig
    sig = pd.DataFrame(out).mean(axis=1)          # avg position -1..1 across the two
    r_daily = pd.DataFrame({"10y": r10, "30y": r30}).mean(axis=1)
    pos = sig.shift(1).fillna(0)                   # T+1 execution
    gross = pos * r_daily
    to = pos.diff().abs().fillna(0)                # one-side turnover in units of nav
    r_net = cost(gross, to)
    vol = r_net.expanding(min_periods=126).std().shift(1)*np.sqrt(252)
    lev = (0.10/vol).clip(0,3).fillna(0)
    r = (r_net*lev).dropna()
    return r[r.index >= "2008-01-01"]

if __name__ == "__main__":
    r = build()
    g = gates(r)
    print("BOND TREND:", g)
    if g.get("pass_"):
        save_sleeve(r, OUT, "Dual-trend on synthesized 10Y+30Y TR (FRED yields), vt10, 6bps")
