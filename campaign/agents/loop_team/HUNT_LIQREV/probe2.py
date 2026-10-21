"""IDEA 2/3: overnight-gap and intraday cross-sectional books on twelve_liq.
IDEA 2: sig = overnight ret (open_t/close_{t-1}-1); continuation + fade both tried.
IDEA 3: sig = intraday (close_t/open_t -1); short strong intraday (fade) + continuation.
IDEA 4: + dollar-vol liquidity filter (drop bottom-liquidity tercile).
All T+1 via w decided at close t earning r_{t+1}; 6.4bps/side; borrow; vt10 cap3."""
import sys; sys.path.insert(0, ".")
from liqrev_lib import *
import numpy as np, pandas as pd
cl, op, vl = load_panel()
m = universe_mask(cl)
cl = cl.loc[:, m]; op = op.loc[:, m]; vl = vl.loc[:, m]
rets = cl.pct_change()
on = op / cl.shift(1) - 1.0          # overnight ret of day t (known at open t; fully known at close t)
ic = cl / op - 1.0                   # intraday ret of day t (known at close t)
dvol = (vl * cl).rolling(21).median()
liqmask = dvol.rank(axis=1, pct=True) >= 1/3   # skip low-liquidity tercile (IDEA 4)
def sr2008(net):
    r = net[net.index >= "2008-01-01"]
    return float(r.mean()/r.std()*np.sqrt(252)) if r.std() > 0 else float("nan")
def book(sig, direction, bucket="tercile", liq=False, name=""):
    s = sig * direction
    w = xs_weights(s, lb=1, direction=1, bucket=bucket)
    if liq: w = w.where(liqmask, 0.0)
    net, parts = run_book(w, rets)
    print(f"{name:34s} SR2008+ {sr2008(net):+.3f}  turn/day {parts['turn']['2008-01-01':].mean():.2f}")
    return net
print("== IDEA2 overnight continuation (long big ON gainers):")
book(on, +1, name="ON cont terc"); book(on, +1, "decile", name="ON cont dec")
print("== IDEA2 overnight fade:")
book(on, -1, name="ON fade terc"); book(on, -1, "decile", name="ON fade dec")
print("== IDEA3 intraday fade (short strong-intraday):")
book(ic, -1, name="IC fade terc"); book(ic, -1, "decile", name="IC fade dec")
print("== IDEA3 intraday continuation:")
book(ic, +1, name="IC cont terc")
print("== IDEA4 with liquidity filter:")
book(on, +1, liq=True, name="ON cont terc liq"); book(ic, -1, liq=True, name="IC fade terc liq")
book(on, -1, liq=True, name="ON fade terc liq"); book(ic, +1, liq=True, name="IC cont terc liq")
# ON-IC spread book (charter idea 3 variant)
sig = on - ic
book(sig, +1, name="ON-IC spread cont terc"); book(sig, -1, name="ON-IC spread fade terc")
