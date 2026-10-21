"""r7 Idea3: credit-cycle rotation - DAAA-DBAA spread percentile gates long-AAA-proxy vs flat.
AAA proxy TR = synth_bond_ret(DAAA yields, dur=12). Spread high-pct (stress) -> flat."""
import sys; sys.path.insert(0,".")
import numpy as np, pandas as pd
from r7lib import *

aaa=load(FNEW+"DAAA.csv").reindex(IDX).ffill()
baa=load(FNEW+"DBAA.csv").reindex(IDX).ffill()
spr=(baa-aaa)
RET_A=synth_bond_ret(aaa,dur=12)
RET_P=pd.DataFrame({"AAA":RET_A,"CASH1":0.0,"CASH2":0.0},index=IDX)

def builder(thr):
    def b(sig):
        w=(sig<=thr).astype(float)   # long when spread below thr percentile
        return pd.DataFrame({"AAA":w,"CASH1":0.0,"CASH2":0.0},index=sig.index), month_rbd(sig.index)
    return b

if __name__=="__main__":
    res=[]
    for lb in [252,504,1008,2016]:
        pct=spr.rolling(lb,min_periods=lb//2).rank(pct=True).reindex(IDX)
        for thr in [0.7,0.8,0.9]:
            b=builder(thr)
            Wt,rbd=b(pct); net,_=wback_rb(Wt,RET_P,rbd)
            for st in ["1990-01-01","2008-01-01"]:
                r=sret(net,st,0.10); g=gates6(r)
                g["corr_champ"]=xcorr(r,CH)
                print(f"lb={lb} thr={thr} from={st[:4]}: SR={g['SR']} H1={g['H1']} H2={g['H2']} negYr={g['negYr']} worst={g['worst']} ann={g['ann']} corr={g['corr_champ']}",flush=True)
                res.append((lb,thr,st[:4],g))
    # diagnostic: always-long AAA proxy (pure carry, no gate) at vt10
    Wt=pd.DataFrame({"AAA":1.0,"CASH1":0.0,"CASH2":0.0},index=IDX)
    net,_=wback_rb(Wt,RET_P,month_rbd(IDX)); r=sret(net,"1990-01-01",0.10); g=gates6(r)
    print(f"always-long AAA dur12: SR={g['SR']} ann={g['ann']} vol={g['vol']} negYr={g['negYr']} worst={g['worst']}")
