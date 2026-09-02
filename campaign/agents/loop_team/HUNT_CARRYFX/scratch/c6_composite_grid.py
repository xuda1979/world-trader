"""COMPOSITE GRID per charter: dual-tf z (21+63) x carry-accrual x weekday sizing.
Borrow 0.5%/yr on short leg charged daily. Carry = REAL accrual on held position (b-leg rate
diff on |w| notional), PIT month m usable m+1. Weekday sizing applied at decision day."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
import numpy as np, pandas as pd
from cfx_lib import *
C=load_close(["GBP_USD","NZD_USD","AUD_USD","EUR_USD"])
R=C.pct_change()
books=[("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD")]

def accr(a,b,index):
    return carry_pit(CCY2FRED[a.split('_')[0]],CCY2FRED[b.split('_')[0]],index)

def composite(lbs=(21,63),carry=False,wday=None,div=2.0,cap=2.0):
    nets=[]
    for (a,b) in books:
        parts=[]
        for lb in lbs:
            w=zsig(C,a,b,lb,cap,div)
            parts.append(w)
        W=sum(parts)/len(parts)                      # blended signal weight
        sig=W.shift(1)
        d=R[a]-R[b]
        gross=sig*d
        turn=2*sig.diff().abs()
        net=gross-turn*COST
        if carry:
            cr=accr(a,b,C.index)                     # base-minus-quote rate diff per day
            net=net+sig*(cr.reindex(C.index).fillna(0.0))   # accrue on held long-leg notional
        net=net-0.005/252*sig.abs()                  # borrow 0.5%/yr on SHORT notional |w|
        if wday is not None:
            m=pd.Series(C.index.dayofweek.map(lambda x: wday.get(x,1.0)),index=C.index)
            net=net*m.shift(0)                       # applied to realization day (T+1 safe: known at t+1 open? NO)
        nets.append(net)
    return pd.concat(nets,axis=1).mean(axis=1).dropna()

# NOTE on wday: applying a Monday multiplier to the MONDAY return means conditioning on the day
# of week of the RETURN, which is known in advance (calendar), so it is T+1-legit.
configs=[]
for carry in (False,True):
    for wlab,wd in (("all1",None),("mon0",{0:0.0}),("mon0fri0",{0:0.0,4:0.0})):
        for lbs in [(21,63),(42,)]:
            r=composite(lbs,carry,wd)
            st=stats(r)
            configs.append((f"lbs={lbs}",f"carry={carry}",wlab,st,r))
print("built",len(configs),"configs")
for lbstag,cl,wlab,st,r in configs:
    key=f"{lbstag} {cl} {wlab}"
    print(f"{key:<36} n={st['n']} SR={st['SR']} H1={st['SR_H1']} H2={st['SR_H2']} MDD={st['MDD']} neg={st['negyrs']}({st['worst_yr']}%) top50={st['top50']}% ac1={st['ac1']}")
