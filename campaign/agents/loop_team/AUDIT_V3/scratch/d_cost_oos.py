"""6.4bps stress on V3 BAL + OOS17 + worst-3y; FF2 internal turnover uplift."""
import sys, numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V3/scratch")
from a_rebuild import load, POOL, NEW3, make, vt, SHORTF, stats

Sd,capW,blend,tw,wts=make(NEW3)
def build(cost,execadj):
    b,gb=vt(blend,0.07); b2,gb2=vt(blend,0.091)
    outs=[]
    for TGT,b_,gb_ in [(0.07,b,gb),(0.091,b2,gb2)]:
        eq=(1+b_.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
        sc=pd.Series(np.where(tdd<-{0.07:0.04,0.091:0.03}[TGT],0.5,1.0),index=b_.index); bb=b_*sc
        dsc=sc.diff().abs()*0.5
        full=capW.mul(gb_,axis=0).mul(sc,axis=0)
        reb=full.diff().abs().sum(axis=1)
        r=bb-(tw.reindex(bb.index).fillna(0)+dsc.fillna(0))*cost-reb.reindex(bb.index).fillna(0)*cost
        terms=[capW[n]*sc*SHORTF[n]*0.005 for n in POOL if SHORTF[n]>0]
        r=r-pd.concat(terms,axis=1).sum(axis=1).reindex(r.index).fillna(0)/252
        outs.append(r.dropna(how='all'))
    return ((outs[0]+outs[1])/2).dropna()

base=build(6e-4,6.0)
r64=build(6.4e-4,6.4)
# extra 0.4bps on FF2's own turnover (delivered file is net at 6bps; one-side turn 1.92%/day per meta)
ff2turn=pd.Series(0.0192,index=r64.index)
r64=r64-ff2turn*0.4e-4
stats(base,"V3 BAL baseline 6.0bps")
stats(r64,  "V3 BAL @6.4bps/side all turnover surfaces")
print("delta ann (arith): %.3f%%/yr"%((base.mean()-r64.mean())*252*100))

bal=base; oos=bal[bal.index>='2017-01-01']
print(f"OOS17+ arith {oos.mean()*252*100:.2f}%  SR {oos.mean()/oos.std()*np.sqrt(252):.2f}  n={len(oos)}")
eq=(1+bal).cumprod(); dd=(eq/eq.cummax()-1)
w3y=dd.rolling(756).min().min()
print(f"worst rolling-3y (756d) DD: {w3y*100:.2f}%  full MDD {dd.min()*100:.2f}%")
# SR monthly for completeness
m=(1+bal).resample('ME').prod()-1
print(f"SR_m {m.mean()/m.std()*np.sqrt(12):.3f}")
