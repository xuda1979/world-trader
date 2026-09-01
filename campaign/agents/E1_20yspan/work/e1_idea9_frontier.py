"""E1 idea9: final config frontier under FULL MDD>=-8% envelope; pick max ann; save champion + gates."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/work')
import numpy as np, pandas as pd
from campaign.harness.data import save_sleeve, ff_factors, ff_mom
from campaign.agents.B2_highfreq.gates import full_stats, halves_sr
import e1_frontier_lib as L

# costed-B3 pool frontier (honest pool): constraint MDD >= -8.0, maximize ann
print("costed-B3 pool frontier:")
best=None
for TGT in [0.065,0.075,0.085]:
    for THR in [0.035,0.04,0.045]:
        for FR in [0.4,0.5]:
            r=L.construct(TGT,THR,FR)
            eq=(1+r).cumprod(); mdd=(eq/eq.cummax()-1).min()
            ann=r.mean()*252*100; sr=r.mean()/r.std()*np.sqrt(252)
            flag="  <== DD breach" if mdd<-0.08 else ""
            if mdd>=-0.08 and (best is None or ann>best[0]): best=(ann,sr,mdd,TGT,THR,FR)
            print(f"  .{int(TGT*1000)}/thr{THR}/fr{FR}: ann={ann:.1f}% SR={sr:.2f} MDD={mdd*100:.1f}%{flag}")
print("BEST within envelope:", best)
# same for uncosted-B3 pool (coordinator convention)
import e1_idea6_blend20y as U
print("uncosted-B3 pool frontier:")
best2=None
for TGT in [0.065,0.075,0.085]:
    for THR in [0.035,0.04,0.045]:
        for FR in [0.4,0.5]:
            r=U.construct(TGT,THR,FR)
            eq=(1+r).cumprod(); mdd=(eq/eq.cummax()-1).min()
            ann=r.mean()*252*100; sr=r.mean()/r.std()*np.sqrt(252)
            if mdd>=-0.08 and (best2 is None or ann>best2[0]): best2=(ann,sr,mdd,TGT,THR,FR)
            print(f"  .{int(TGT*1000)}/thr{THR}/fr{FR}: ann={ann:.1f}% SR={sr:.2f} MDD={mdd*100:.1f}%")
print("BEST within envelope:", best2)
a,sr_,mdd_,T1,H1_,F1=best; a2,sr2,mdd2,T2,H2_,F2=best2
RC=L.construct(T1,H1_,F1); RU=U.construct(T2,H2_,F2)
save_sleeve(RC,f"{L.ROOT}/campaign/agents/E1_20yspan/sleeves/E1_CHAMPION20Y_BALANCED_costedB3.csv",
f"E1 CHAMPION20Y BALANCED candidate, HONEST pool (B3momhml charged 6bps one-side on sign flips). Config TGT={T1} THR={H1_} FR={F1} LB=126, start 2006-10-02, 12-pool de-truncated (see campaign/scripts/e1_champion20y_build.py).")
save_sleeve(RU,f"{L.ROOT}/campaign/agents/E1_20yspan/sleeves/E1_CHAMPION20Y_BALANCED_uncostB3.csv",
f"E1 CHAMPION20Y BALANCED candidate, coordinator-B3 convention (uncosted). Config TGT={T2} THR={H2_} FR={F2} LB=126, start 2006-10-02, 12-pool de-truncated.")
for nm,r in [("costedB3",RC),("uncostB3",RU)]:
    st=full_stats(r); h1,h2=halves_sr(r)
    o=r[r.index>="2017-01-01"]
    print(f"{nm}: SR={st['sr']:.2f} ann={st['ann']:.1f}% vol={st['vol']:.1f}% MDD={st['mdd']:.1f}% negy={st['negy']}/{st['years']} worst={st['worst']:.1f}% H1={h1:.2f} H2={h2:.2f} OOS ann={o.mean()*252*100:.1f}% SR={o.mean()/o.std()*np.sqrt(252):.2f}")
