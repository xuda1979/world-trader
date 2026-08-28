"""A5 r3 idea2 (charter): long SPY when VIX>thr (capitulation), hard max-hold, stop on
VIX re-spike or drawdown. Event-driven reversion, decorrelated from trend followers."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from a5_r3_lib import gates_a_c_d, net_of_pos, scramble_sig, lib_corr, corr_summary, stats
import data as D

V = D.fred("vix")
spy = D.closes()["SPY"]; spy.index = spy.index.tz_localize(None)
r1 = spy.pct_change()
df = pd.DataFrame({"vix": V, "r": r1}).dropna()
df = df[df.index >= "2007-01-01"]
VIX, R = df["vix"], df["r"]

def build(thr, maxhold, stop_pct):
    """Enter at close when VIX>=thr (state ON from next bar); exit after maxhold days,
    or early when VIX falls below thr*0.7 (calm resume). Position flat otherwise."""
    n = len(df); pos = np.zeros(n); held = 0; entry = 0.0
    v = VIX.values; s = spy.reindex(df.index).ffill().values
    on = False
    for t in range(n):
        if not on:
            if v[t] >= thr: on = True; held = 0; entry = s[t]
        else:
            held += 1
            if held >= maxhold or v[t] < thr*0.7 or s[t] < entry*(1-stop_pct):
                on = False
        pos[t] = 1.0 if on else 0.0   # decided at t using v[t],s[t] -> T+1 in net_of_pos
    return pd.Series(pos, index=df.index)

print("thr x maxhold x stop grid")
for thr in (35, 40, 45):
    for mh in (10, 21, 42):
        for sp in (0.05, 0.10):
            sig = build(thr, mh, sp)
            net = net_of_pos(sig, R)
            g = gates_a_c_d(f"vix>{thr} mh{mh} stop{sp}", net)
