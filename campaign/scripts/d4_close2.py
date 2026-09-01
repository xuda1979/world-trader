import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/D4_microstruct')
import d4_lib as L
import numpy as np, pandas as pd

for nm in ['DHOILNYH','DJFUELUSGULF','DPROPANEMTXCF']:
    px = L.newdata(nm)
    px = px.dropna(); px = px[px>0]
    r = L.logret(px).dropna(); i = r.index[r.index >= '2008-01-01']
    r = r.reindex(i)
    best = (0, None)
    for dow in range(5):
        for sgn in [1,-1]:
            p = pd.Series(0.0, index=i); p[i.dayofweek==dow] = sgn
            g = L.t1_pnl(p, r)
            if g.std()>0:
                t = g.mean()/g.std()*np.sqrt(len(g))
                if abs(t) > abs(best[0]): best = (t, (dow, sgn))
    dow, sgn = best[1]
    p = pd.Series(0.0, index=i); p[i.dayofweek==dow] = sgn
    net = L.vt10(L.net_turnover(p, r)); s2 = L.full_stats(net); h1,h2 = L.halves_sr(net)
    print(f"{nm} best leg dow{dow} sgn{sgn}: t {best[0]:.2f} -> book SR {s2['sr']:.2f} ann {s2['ann']:.1f}% negy {s2['negy']}/{s2['years']} H1 {h1:.2f} H2 {h2:.2f}")
