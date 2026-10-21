"""A5 r7 idea 4: Vol-terror regime (TEDRATE high + VIX high -> defensive cash,
else risky) + combo with r7i3 AA carry. TEDRATE ends 2022-01: after that, TED
treated as 0 (regime = VIX-only), noted honestly in meta."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from a5_r7_lib import *

R = spy93()
vix = fred_new("VIXCLS").reindex(R.index).ffill()
ted = fred_new("TEDRATE")
ted.index = ted.index.tz_localize(None)
# TED ends 2022-01; extend as 0 (post-2022 TED discontinued at ~0.08-0.09)
ted = ted.reindex(R.index)
ted_l = ted.ffill().fillna(0.0)

aaa = fred_new("DAAA"); baa = fred_new("DBAA")
cr = pd.concat([aaa, baa], axis=1, join="inner").ffill()
spr = (cr.iloc[:, 1] - cr.iloc[:, 0])

# AA synth carry (idea-3 best construction) with tight gate
y = cr.iloc[:, 0] / 100.0
TR_AA = (7.0 * (-y.diff()) + y / 252.0).dropna()
z_spr = ((spr - spr.rolling(252).mean()) / spr.rolling(252).std()).reindex(TR_AA.index).ffill()
p_tight = hysteresis_pos(z_spr, 0.5, 0.25)

def yearly(net):
    s = stats(net)
    return s

print("== r7i3-A reference (tight-gated AA carry 252/0.5/0.25) ==")
net3, pos3 = build_net(p_tight, TR_AA)
ok, line, s3 = gates_r7("r7i3A", net3, pos3, TR_AA, extra="lb=252 th=0.5 hyst=0.25 tight")
print(line); print("yearly:", s3["yearly"])
ct, own = corr_all(net3)
print("corr lib:", ct); print("corr own:", own)

# idea 4: vol-terror regime -> risky SPY vs cash
print("\n== idea 4: vol-terror regime switch on SPY ==")
rows = []
for vth in (25, 30, 35):
    for tth in (0.5, 1.0):
        terror = ((vix > vth) & (ted_l > tth)).astype(float)
        p = 1.0 - terror  # risky unless terror
        net, posf = build_net(p, R)
        s = stats(net); h1, h2 = halves(net)
        rows.append((vth, tth, s["sr"], h1, h2, s["ann"], s["neg_yr"], s["worst"], int(terror.sum())))
df = pd.DataFrame(rows, columns=["vth","tth","SR","H1","H2","ann","negyr","worst","n_terror"]).sort_values("SR", ascending=False)
print(df.to_string())
print(f"(SPY vt10 reference always-long: SR={[round(stats(build_net(pd.Series(1.0,index=R.index),R)[0])['sr'],2)]})")

# combo: AA tight-carry AND vol-terror off-switch (defensive overlay)
print("\n== combo: AA tight carry gated by vol-terror ==")
vix_a = fred_new("VIXCLS").reindex(TR_AA.index).ffill()
ted_a = ted.reindex(TR_AA.index).ffill().fillna(0.0)
rows = []
for vth in (25, 30, 35, 40):
    for tth in (0.5, 1.0):
        terror = ((vix_a > vth) & (ted_a > tth)).astype(float).reindex(p_tight.index).ffill().fillna(0.0)
        p = p_tight * (1 - terror)
        net, posf = build_net(p, TR_AA)
        s = stats(net); h1, h2 = halves(net)
        rows.append((vth, tth, s["sr"], h1, h2, s["ann"], s["neg_yr"], s["worst"], int(terror.sum())))
dfc = pd.DataFrame(rows, columns=["vth","tth","SR","H1","H2","ann","negyr","worst","n_terror"]).sort_values("SR", ascending=False)
print(dfc.to_string())
