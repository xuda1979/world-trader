"""A5 r7 idea 8: 3-way credit blend (all legs honest T+1, vt10):
  L1 = tight-gated AA carry (lb252 th0.5 hyst0.25)
  L2 = tight-gated DV01-neutral spread carry (same z gate on spread)
  L3 = L1 + honest T+1 rate-shock UST hedge (21d dY10 z>0.75 vs 504d)
Coarse weight grid (step .25) -> gate d (<=2 negYr, >-5%) feasibility."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd, itertools
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
p_tight = hysteresis_pos(z, 0.5, 0.25)
dy = yu.diff(21)
zy = ((dy - dy.rolling(504).mean()) / dy.rolling(504).std()).reindex(TR_AA.index).ffill()
hedge = (zy > 0.75).astype(float).shift(1).fillna(0.0)          # T+1 honest

netA, _ = build_net(p_tight, TR_AA)
netS, _ = build_net(p_tight, TR_SPR)
netH, _ = build_net(p_tight, TR_AA - hedge * TR_UST)
legs = {"A": netA, "S": netS, "H": netH}
for k, v in legs.items():
    s = stats(v); print(f"leg {k}: SR={s['sr']:.2f} ann={s['ann']:.2f}% negyr={s['neg_yr']} worst={s['worst']:.1f}%")

rows = []
for wA in (0.0, 0.25, 0.5, 0.75, 1.0):
    for wS in (0.0, 0.25, 0.5, 0.75, 1.0):
        for wH in (0.0, 0.25, 0.5, 0.75, 1.0):
            W = wA + wS + wH
            if W == 0: continue
            r = (wA * netA + wS * netS + wH * netH) / W
            s = stats(r); h1, h2 = halves(r)
            rows.append((wA/W, wS/W, wH/W, s["sr"], h1, h2, s["ann"], s["neg_yr"], s["worst"],
                         s["neg_yr"] <= 2 and s["worst"] > -5.0))
df = pd.DataFrame(rows, columns=["wA","wS","wH","SR","H1","H2","ann","negyr","worst","d_ok"]).sort_values("SR", ascending=False)
print(df.head(18).to_string())
print("\ncells passing gate d:")
print(df[df.d_ok].to_string())
