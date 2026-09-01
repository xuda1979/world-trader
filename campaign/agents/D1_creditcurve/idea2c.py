"""IDEA 2 salvage-2: (a) circuit-breaker demotion after |leg|>0.5% days; (b) 2-pair basket
(2v5 + 10v30 steepeners, equal vol share). Honest units throughout."""
import sys; sys.path.insert(0,'.')
import numpy as np, pandas as pd
from d1_lib import *

def carry_leg(a,b,Da,Db):
    ya,yb=yld(a),yld(b)
    df=pd.concat([ya.rename('a'),yb.rename('b')],axis=1,sort=True).dropna()
    w=Db/Da
    leg=w*rfn(df['a'],Da)-rfn(df['b'],Db)
    gn=1+w
    return df.index, leg, gn

def run(legs_gns, name, breaker=None):
    idx=None
    total=pd.Series(0.0); gnt=0
    for idx,leg,gn in legs_gns:
        total=total.add(leg,fill_value=0) if len(total)>1 else leg
        gnt+=gn
    total=total/len(legs_gns); gnt=gnt/len(legs_gns)
    idx=total.index
    rfc=rf_daily().reindex(idx).fillna(0)
    pos=pd.Series(1.0,index=idx).shift(1).fillna(0)
    if breaker:
        bad=(total.abs()>breaker).astype(float)
        # demote 5 days after each break (trailing: shift bad by 1..5)
        demo=pd.Series(0.0,index=idx)
        for k in range(1,6): demo=demo+bad.shift(k).fillna(0)
        pos=pos*(1-0.5*(demo>0).astype(float))
    to=pos.diff().abs().fillna(0)*gnt
    net=vt(pos*total.shift(1)*0+pos*total-to*COST)  # leg is daily TR, pos already T+1
    s=stats(net); h=halves(net); cb=corr_to(net,CHAMP)
    print(f"{name}: SR={s['sr']:.2f} ann={s['ann']:.1f}% mdd={s['mdd']:.1f}% negy={s['negy']} worst={s['worst']:.1f}% H1={h[0]:.2f} H2={h[1]:.2f} corr_champ={cb:.3f}")
    return net

pairs=[('DGS2','DGS5',DUR['DGS2'],DUR['DGS5']),('DGS10','DGS30',DUR['DGS10'],DUR['DGS30'])]
lg=[carry_leg(*p) for p in pairs]
run(lg,"basket 2v5+10v30")
run([carry_leg('DGS2','DGS10',DUR['DGS2'],DUR['DGS10'])],"2s10s breaker 0.5%",breaker=0.005)
run(lg,"basket breaker 0.5%",breaker=0.005)
