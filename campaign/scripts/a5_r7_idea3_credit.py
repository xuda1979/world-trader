"""A5 r7 idea 3: Credit spread 1990+ (DAAA-DBAA).
A) Value book (charter): long AA-synth TR (dur 7.0: 7*(-dDAAA)+DAAA/252) when
   spread (DBAA-DAAA) is WIDE vs trailing z (cheap), flat when tight. Grid lb x
   th x direction (wide-long per charter; also tight-long as honesty check).
B) Credit-conditions gate on equity: long SPY when spread z < th (calm), flat
   when wide (stress). Hysteresis."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from a5_r7_lib import *

aaa = fred_new("DAAA"); baa = fred_new("DBAA")
for s in (aaa, baa): s.index = s.index.tz_localize(None)
df = pd.concat([aaa.rename("aaa"), baa.rename("baa")], axis=1).dropna().ffill()
spr = (df.baa - df.aaa)
y = df.aaa / 100.0
TR_AA = (7.0 * (-y.diff()) + y / 252.0).dropna()
R_sp = spy93()

rows = []
for lb in (126, 252, 504, 1260):
    z = ((spr - spr.rolling(lb).mean()) / spr.rolling(lb).std()).ffill()
    for th in (-0.5, -0.25, 0.0, 0.25, 0.5):
        for hyst in (0.1, 0.25):
            for direc in ("wide", "tight"):
                p = hysteresis_pos(z, th, hyst) if direc == "tight" else hysteresis_pos(-z, -th, hyst)
                net, posf = build_net(p, TR_AA)
                s = stats(net); h1, h2 = halves(net)
                rows.append(("A", lb, th, hyst, direc, s["sr"], h1, h2, s["ann"], s["neg_yr"], s["worst"]))
dfA = pd.DataFrame(rows, columns=["fam","lb","th","hyst","dir","SR","H1","H2","ann","negyr","worst"]).sort_values("SR", ascending=False)
print("== A: synth AA carry gated by spread =="); print(dfA.head(12).to_string())
print("always-long AA synth reference:")
net0, _ = build_net(pd.Series(1.0, index=TR_AA.index), TR_AA)
s0 = stats(net0); h1, h2 = halves(net0)
print(f"  SR={s0['sr']:.2f} ann={s0['ann']:.2f}% H1={h1:.2f} H2={h2:.2f} negyr={s0['neg_yr']} worst={s0['worst']:.1f}% n={s0['n']}")

rows = []
for lb in (126, 252, 504, 1260):
    z = ((spr - spr.rolling(lb).mean()) / spr.rolling(lb).std()).reindex(R_sp.index).ffill()
    for th in (0.0, 0.25, 0.5, 0.75, 1.0):
        for hyst in (0.1, 0.25):
            p = hysteresis_pos(-z, -th, hyst)  # long SPY when z<th (calm)
            net, posf = build_net(p, R_sp)
            s = stats(net); h1, h2 = halves(net)
            rows.append(("B", lb, th, hyst, s["sr"], h1, h2, s["ann"], s["neg_yr"], s["worst"]))
dfB = pd.DataFrame(rows, columns=["fam","lb","th","hyst","SR","H1","H2","ann","negyr","worst"]).sort_values("SR", ascending=False)
print("\n== B: SPY gated by credit spread z (top 12) =="); print(dfB.head(12).to_string())
