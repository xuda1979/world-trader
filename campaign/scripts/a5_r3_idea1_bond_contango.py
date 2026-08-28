"""A5 r3 idea1: bond contango carry. Long 10y/30y synth TR when own yield in
contango-like downtrend (y < y[lb] ago) AND 2s10s slope stable/rising. T+1, 6bps, vt10."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from a5_r3_lib import gates_a_c_d, net_of_pos, stats, halves, scramble_sig
import data as D

y10 = D.fred("us10y"); y30 = D.fred("us30y"); y2 = D.fred("us2y")
Y = pd.DataFrame({"10": y10, "30": y30}).dropna()
Y = Y[Y.index >= "2006-01-01"]
slope = (y10 - y2).reindex(Y.index).ffill()

def synth_ret(y, dur):
    dy = y.diff() / 100.0
    carry = y.ffill() / 100.0 / 252.0
    return dur * (-dy) + carry

R = pd.DataFrame({"10": synth_ret(Y["10"], 7.5), "30": synth_ret(Y["30"], 15.0)})

def build(lb=63, sw=21, cadence="daily", slope_mode="up"):
    dn = Y > Y.shift(lb)          # yield rising -> short
    dn = (Y < Y.shift(lb)).astype(float) - (Y > Y.shift(lb)).astype(float)  # +1 long bonds
    sl_ok = (slope >= slope.shift(sw)).astype(float) if slope_mode == "up" \
        else (slope.diff(sw).abs() <= slope.diff(sw).std()).astype(float)
    sig = dn.mul(sl_ok, axis=0)   # zero when slope falling
    if cadence == "monthly":
        ms = sig.groupby([sig.index.year, sig.index.month]).tail(1).index
        sig = sig.loc[ms].reindex(sig.index).ffill()
    elif cadence == "weekly":
        ws = sig.groupby(pd.Grouper(freq="W-FRI")).tail(1).index
        sig = sig.loc[ws].reindex(sig.index).ffill()
    pos = sig[["10", "30"]] * 0.5
    pnl = (pos * R).sum(axis=1, min_count=1)
    return pos.sum(axis=1).rename("pos"), pnl

rows = []
for lb in (21, 63, 126):
    for sw in (21, 63):
        for cad in ("daily", "weekly", "monthly"):
            for sm in ("up",):
                pos, pnl = build(lb, sw, cad, sm)
                g = gates_a_c_d(f"bond lb{lb} sw{sw} {cad} {sm}", net_of_pos(pos, pnl))
                rows.append((lb, sw, cad, sm, g))
best = max(rows, key=lambda x: x[-1]["sr"])
print("BEST by SR:", best[:4], best[-1])
