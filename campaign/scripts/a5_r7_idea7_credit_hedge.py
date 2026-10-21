"""A5 r7 idea 7: fix r7i3-A gate-d — targeted rate-shock hedge on AA carry.
Base: AA synth TR (dur 7) x tight-spread gate (lb252 th0.5 hyst0.25).
Hedge: subtract UST synth TR (dur 7.5) scaled by h(t); h(t)=1 only when
10y 21d change z > c (rate shock), z vs trailing 504d. Grid c for plateau.
Also: 50/50 blend of gated AA carry + gated pure spread carry."""
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

def tight_gate(s, lb=252, th=0.5, hyst=0.25):
    z = ((s - s.rolling(lb).mean()) / s.rolling(lb).std())
    return hysteresis_pos(z.reindex(TR_AA.index).ffill(), th, hyst)

p_tight = tight_gate(spr)

# base gated AA carry (r7i3-A) stats for reference
net_base, _ = build_net(p_tight, TR_AA)
sb = stats(net_base); hb1, hb2 = halves(net_base)
print(f"base r7i3-A: SR={sb['sr']:.2f} H1={hb1:.2f} H2={hb2:.2f} negyr={sb['neg_yr']} worst={sb['worst']:.1f}%")

print("\n== targeted rate-shock hedge grid (c = 21d dY10 z threshold, 504d trailing) ==")
dy = yu.diff(21)
zy = ((dy - dy.rolling(504).mean()) / dy.rolling(504).std()).reindex(TR_AA.index).ffill()
rows = []
for c in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 99.0):
    hedge = (zy > c).astype(float)
    p = p_tight  # position on AA carry unchanged; hedge is a return overlay
    gross = p * (TR_AA - hedge * TR_UST)
    net, posf = build_net(p, TR_AA - hedge * TR_UST)
    s = stats(net); h1, h2 = halves(net)
    rows.append((c, int(hedge.sum()), s["sr"], h1, h2, s["ann"], s["neg_yr"], s["worst"]))
df = pd.DataFrame(rows, columns=["c","n_hedge","SR","H1","H2","ann","negyr","worst"]).sort_values("SR", ascending=False)
print(df.to_string())

print("\n== 50/50 blend: gated AA carry + gated pure spread carry ==")
TR_SPR = (7.0 * (-spr.diff()) + spr / 252.0).dropna()
p_spr = tight_gate(TR_SPR.rolling(1).mean().dropna() * 0 + spr.reindex(TR_SPR.index))  # gate on level z
netA, _ = build_net(p_tight, TR_AA)
netS, _ = build_net(p_spr, TR_SPR)
j = pd.concat([netA, netS], axis=1, join="inner").dropna()
for w in (0.5, 0.6, 0.7):
    r = w * j.iloc[:, 0] + (1 - w) * j.iloc[:, 1]
    s = stats(r); h1, h2 = halves(r)
    print(f"w_AA={w}: SR={s['sr']:.2f} H1={h1:.2f} H2={h2:.2f} ann={s['ann']:.2f}% negyr={s['neg_yr']} worst={s['worst']:.1f}%")

# best hedge cell detail + gates + plateau
best_c = df.iloc[0]
for c in (best_c.c,):
    hedge = (zy > c).astype(float)
    net, posf = build_net(p_tight, TR_AA - hedge * TR_UST)
    ok, line, s = gates_r7("r7i7", net, posf, TR_AA - hedge * TR_UST, extra=f"c={c}")
    print(line); print("yearly:", s["yearly"])
    ct, own = corr_all(net)
    print("corr lib:", ct); print("corr own:", own)
