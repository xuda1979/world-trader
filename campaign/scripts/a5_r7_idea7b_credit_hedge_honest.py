"""A5 r7 idea 7b: HONEST version of idea 7 — hedge flag shift(1) (T+1), same as
positions. Idea-7 first draft was lookahead-contaminated (hedge used same-day
yield change on same-day return); discarded. Base: AA synth TR x tight-spread
gate. Hedge overlay: short UST TR when 21d dY10 z > c, flag shifted."""
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

z = (spr - spr.rolling(252).mean()) / spr.rolling(252).std()
p_tight = hysteresis_pos(z.reindex(TR_AA.index).ffill(), 0.5, 0.25)

dy = yu.diff(21)
zy = ((dy - dy.rolling(504).mean()) / dy.rolling(504).std()).reindex(TR_AA.index).ffill()

rows = []
for lb_z in (252, 504, 1260):
    dy_ = yu.diff(21)
    zy_ = ((dy_ - dy_.rolling(lb_z).mean()) / dy_.rolling(lb_z).std()).reindex(TR_AA.index).ffill()
    for c in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 99.0):
        hedge = (zy_ > c).astype(float).shift(1).fillna(0.0)   # T+1 honest
        R = TR_AA - hedge * TR_UST
        net, posf = build_net(p_tight, R)
        s = stats(net); h1, h2 = halves(net)
        rows.append((lb_z, c, int(hedge.sum()), s["sr"], h1, h2, s["ann"], s["neg_yr"], s["worst"], s["vol"]))
df = pd.DataFrame(rows, columns=["lb_z","c","n_hedge","SR","H1","H2","ann","negyr","worst","vol"]).sort_values("SR", ascending=False)
print(df.to_string())
b = df.iloc[0]
zy_ = ((dy - dy.rolling(int(b.lb_z)).mean()) / dy.rolling(int(b.lb_z)).std()).reindex(TR_AA.index).ffill()
hedge = (zy_ > b.c).astype(float).shift(1).fillna(0.0)
R = TR_AA - hedge * TR_UST
net, posf = build_net(p_tight, R)
ok, line, s = gates_r7("r7i7b", net, posf, R, extra=f"lb_z={int(b.lb_z)} c={b.c} T+1 hedge")
print(line); print("yearly:", s["yearly"])
ct, own = corr_all(net)
print("corr lib:", ct); print("corr own:", own)
