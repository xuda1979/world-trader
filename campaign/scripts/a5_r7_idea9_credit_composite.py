"""A5 r7 idea 9 (final candidate): single-signal credit composite 1990+.
Signal: hysteresis long when DAAA-DBAA spread z (252d) < 0.5, exit > 0.75.
Composite return: wA*TR_AA + wS*TR_SPR + wH*(TR_AA - hedge_t*TR_UST),
hedge_t = 1[21d dY10 z(504d) > c]_{t-1} (T+1 honest). One build_net: T+1,
6bps on turnover, vt10 expanding min60 clip2. Fine weight map -> robust cell."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from a5_r7_lib import *

aaa = fred_new("DAAA"); baa = fred_new("DBAA"); y10 = fred_new("DGS10")
for s in (aaa, baa, y10): s.index = s.index.tz_localize(None)
cr = pd.concat([aaa.rename("a"), baa.rename("b"), y10.rename("y")], axis=1, join="inner").ffill()
spr = (cr.b - cr.a) / 100.0
ya = cr.a / 100.0; yu = cr.y / 100.0
TR_AA = (7.0 * (-ya.diff()) + ya / 252.0).dropna()
TR_UST = (7.5 * (-yu.diff()) + yu / 252.0).reindex(TR_AA.index).fillna(0.0)
TR_SPR = (7.0 * (-spr.diff()) + spr / 252.0).reindex(TR_AA.index).fillna(0.0)
z = ((spr - spr.rolling(252).mean()) / spr.rolling(252).std()).reindex(TR_AA.index).ffill()
p = hysteresis_pos(z, 0.5, 0.25)
dy = yu.diff(21)
zy = ((dy - dy.rolling(504).mean()) / dy.rolling(504).std()).reindex(TR_AA.index).ffill()
hedge = (zy > 0.75).astype(float).shift(1).fillna(0.0)

def cell(wA, wS, wH, c=0.75, lb_z=504):
    hz = hedge if (c == 0.75 and lb_z == 504) else (
        ((dy - dy.rolling(lb_z).mean()) / dy.rolling(lb_z).std()).reindex(TR_AA.index).ffill() > c
    ).astype(float).shift(1).fillna(0.0)
    R = wA * TR_AA + wS * TR_SPR + wH * (TR_AA - hz * TR_UST)
    net, posf = build_net(p, R)
    s = stats(net); h1, h2 = halves(net)
    return net, posf, R, s, h1, h2

rows = []
for wS in np.arange(0.2, 0.8, 0.1):
    for wH in np.arange(0.1, 0.7, 0.1):
        wA = round(1 - wS - wH, 2)
        if wA < -0.01: continue
        net, posf, R, s, h1, h2 = cell(wA, wS, round(wH,2))
        rows.append((wA, round(wS,2), round(wH,2), s["sr"], h1, h2, s["ann"], s["neg_yr"], s["worst"]))
df = pd.DataFrame(rows, columns=["wA","wS","wH","SR","H1","H2","ann","negyr","worst"]).sort_values("SR", ascending=False)
print(df.to_string())
