"""A5 r7 idea 1: VIX term-structure 1990-style — VIXCLS 21d z vs 252d trailing
dist; long SPX when calm (z<th), flat when stressed (z>th+hyst). T+1, 6bps,
vt10 expanding min-60d clip2. Grid for plateau."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from a5_r7_lib import *

R = spy93()
vix = fred_new("VIXCLS")
vix.index = vix.index.tz_localize(None)

def zpos(smooth, lb, th, hyst):
    v = vix.rolling(smooth).mean()
    m = v.rolling(lb).mean(); s = v.rolling(lb).std()
    z = (v - m) / s
    z = z.reindex(R.index).ffill()
    return hysteresis_pos(z, th, hyst)

rows = []
for smooth in (1, 5, 21):
    for lb in (126, 252, 504):
        for th in (-0.25, 0.0, 0.25, 0.5, 0.75, 1.0):
            for hyst in (0.0, 0.1, 0.25):
                p = zpos(smooth, lb, th, hyst)
                net, posf = build_net(p, R)
                s = stats(net)
                rows.append((smooth, lb, th, hyst, s["sr"], s["ann"], s["neg_yr"], s["worst"], s["n"]))
df = pd.DataFrame(rows, columns=["smooth","lb","th","hyst","SR","ann","negyr","worst","n"]).sort_values("SR", ascending=False)
print(df.head(15).to_string())
print("...")
print(df.tail(5).to_string())
best = df.iloc[0]
print("\nBEST:", dict(best))
# plateau check around best on (th, hyst) at its smooth/lb
sub = df[(df.smooth == best.smooth) & (df.lb == best.lb)]
print(sub.pivot_table(index="th", columns="hyst", values="SR").round(2).to_string())
# gates on best
p = zpos(int(best.smooth), int(best.lb), best.th, best.hyst)
net, posf = build_net(p, R)
ok, line, s = gates_r7("r7i1_vixz", net, posf, R, extra=f"smooth={best.smooth} lb={best.lb} th={best.th} hyst={best.hyst}")
print(line)
print("yearly:", {k: v for k, v in s["yearly"].items()})
ct, own = corr_all(net)
print("corr lib:", ct)
print("corr own:", own)
