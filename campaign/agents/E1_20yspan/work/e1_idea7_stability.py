"""E1 idea7: IS-argmax stability across IS-ends + candidate BAL variants (ann vs DD frontier)."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/work')
import numpy as np, pandas as pd
from e1_idea6_blend20y import construct, stats

# stability: for each IS end year, argmax IS SR over grid s.t. IS MDD<=8
for endy in [2016,2019,2022,2023,2025]:
    best=None
    for TGT in [0.055,0.065,0.075,0.085,0.095]:
        for THR in [0.03,0.04,0.05]:
            r=construct(TGT,THR)
            i=r[r.index<f"{endy+1}-01-01"]
            eq=(1+i).cumprod(); mdd=(eq/eq.cummax()-1).min()
            if mdd<-0.08: continue
            sr=i.mean()/i.std()*np.sqrt(252)
            if best is None or sr>best[0]: best=(sr,TGT,THR)
    print(f"IS-end {endy}: argmax TGT={best[1]} THR={best[2]} (IS SR {best[0]:.2f})")

print("\nBAL variants (0.5x+0.5y) and singles — full window:")
cands={
 "BAL(.065/.04 + .085/.03)": (0.065,0.04,0.085,0.03),
 "BAL(.065/.04 + .075/.03)": (0.065,0.04,0.075,0.03),
 "BAL(.075/.03 + .085/.03)": (0.075,0.03,0.085,0.03),
 "single .075/.03": None,
 "single .085/.04": None,
}
for nm,(t1,h1_,t2,h2_) in [(k,v) for k,v in cands.items() if v]:
    A=construct(t1,h1_); B=construct(t2,h2_); r=((A+B)/2).dropna()
    s=stats(r)
    print(f" {nm}: ann={s['ann']}% SR={s['sr']} MDD={s['mdd']}% negy={s['negy']} worst={s['worst']}% OOS ann={s['oos_ann']}% SR={s['oos_sr']}")
for nm,(tt,hh) in [("single .075/.03",(0.075,0.03)),("single .085/.04",(0.085,0.04))]:
    r=construct(tt,hh); s=stats(r)
    print(f" {nm}: ann={s['ann']}% SR={s['sr']} MDD={s['mdd']}% negy={s['negy']} worst={s['worst']}% OOS ann={s['oos_ann']}% SR={s['oos_sr']}")
