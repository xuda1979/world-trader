"""IDEA 1 grid: xs reversal, twelve_liq 98 names. RAW/VOLNORM x dir x bucket x lb. 2008+ net SR."""
import sys; sys.path.insert(0, ".")
from liqrev_lib import *
import numpy as np, pandas as pd
cl, op, vl = load_panel()
m = universe_mask(cl)
cl = cl.loc[:, m]; rets = cl.pct_change()
rv21 = rets.rolling(21).std()
def sr2008(net):
    r = net[net.index >= "2008-01-01"]
    return r.mean()/r.std()*np.sqrt(252)
def grid(direction, volnorm, bucket):
    out = []
    for lb in [1,2,3,5,10]:
        sig = (rets if not volnorm else rets / rv21.where(rv21 > 0))
        w = xs_weights(sig, lb=lb, direction=direction, bucket=bucket).loc[:, m]
        net, parts = run_book(w, rets)
        out.append((lb, round(float(sr2008(net)), 3)))
    return out
for lbl, d, vn, bk in [("RAW rev terc", -1, False, "tercile"), ("RAW cont terc", 1, False, "tercile"),
                        ("VN rev terc", -1, True, "tercile"), ("VN cont terc", 1, True, "tercile"),
                        ("RAW rev dec", -1, False, "decile"), ("VN rev dec", -1, True, "decile")]:
    print(f"{lbl:14s}", grid(d, vn, bk))
