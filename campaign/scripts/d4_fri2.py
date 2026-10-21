import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/D4_microstruct')
import d4_lib as L
import numpy as np, pandas as pd

def leg_short_fri(px, w=1.0):
    px = px.dropna(); px = px[px>0]
    r = L.logret(px).dropna()
    i = r.index[r.index >= '2008-01-01']; r = r.reindex(i)
    pos = pd.Series(0.0, index=i); pos[i.dayofweek==4] = -w
    gross = L.t1_pnl(pos, r)
    to = pos.shift(1).fillna(0).diff().abs().fillna(0)
    net = gross - to*L.COST
    return net, len(i)

ho = L.newdata('DHOILNYH'); jt = L.newdata('DJFUELUSGULF')
nh, nj = leg_short_fri(ho), leg_short_fri(jt)
for nm,(n,k) in zip(['HO','JET'],[nh,nj]):
    s = L.full_stats(n); h1,h2 = L.halves_sr(n)
    print(f"{nm} short-Fri own-cal: SR {s['sr']:.2f} ann {s['ann']:.1f}% MDD {s['mdd']:.1f}% negy {s['negy']}/{s['years']} worst {s['worst']:.1f}% H1 {h1:.2f} H2 {h2:.2f} (n={k})")
print("corr leg nets:", nh[0].corr(nj[0], join='inner'))

# combined: average the two leg nets on inner join (each already net) -> VT
comb = ((nh[0] + nj[0]) / 2).dropna()
comb_vt = L.vt10(comb)
s = L.full_stats(comb_vt); h1,h2 = L.halves_sr(comb_vt)
cb,cc,nn = L.corr_blend(comb_vt)
print(f"COMB avg: SR {s['sr']:.2f} ann {s['ann']:.1f}% vol {s['vol']:.1f}% MDD {s['mdd']:.1f}% negy {s['negy']}/{s['years']} worst {s['worst']:.1f}% H1 {h1:.2f} H2 {h2:.2f} corrB {cb:.3f} corrC {cc:.3f} n={nn}")
yr = comb_vt.groupby(comb_vt.index.year).apply(lambda x:(1+x).prod()-1)
print("yearly:", {int(k):round(v*100,1) for k,v in yr.items()})
