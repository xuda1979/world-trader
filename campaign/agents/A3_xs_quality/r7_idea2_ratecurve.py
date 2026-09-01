"""r7 Idea2: rate-curve value - DGS10 yield vs rolling z; long bond when cheap (z>0),
short when rich (z<0). Synthetic const-duration (8.5y) bond TR from yield. 1990+."""
import sys; sys.path.insert(0,".")
import numpy as np, pandas as pd
from r7lib import *

y10=load(FNEW+"DGS10.csv").reindex(IDX).ffill()
RET_B=synth_bond_ret(y10,dur=8.5).to_frame("BOND")
# 3-column panel: bond + 2 cash-ish filler names for weights (cash=0 return)
RET_P=pd.DataFrame({"BOND":RET_B["BOND"],"CASH1":0.0,"CASH2":0.0},index=IDX)

def builder(sign,thr=0.5):
    def b(sig):
        w=sign*(sig>thr).astype(float)-(sign*(sig<-thr).astype(float))
        Wt=pd.DataFrame({"BOND":w,"CASH1":0.0,"CASH2":0.0},index=sig.index)
        return Wt, month_rbd(sig.index)
    return b

if __name__=="__main__":
    res=[]
    for lb in [126,252,504,1008]:
        m=y10.rolling(lb,min_periods=lb//2).mean(); sd=y10.rolling(lb,min_periods=lb//2).std()
        z=((y10-m)/sd.replace(0,np.nan)).reindex(IDX)
        for sign,lbl in [(+1,"value(long-cheap)"),(-1,"anti")]:
            b=builder(sign)
            Wt,rbd=b(z); net,_=wback_rb(Wt,RET_P,rbd)
            for st in ["1990-01-01","2008-01-01"]:
                r=sret(net,st,0.10); g=gates6(r)
                g["corr_champ"]=xcorr(r,CH)
                print(f"lb={lb} {lbl} from={st[:4]}: SR={g['SR']} H1={g['H1']} H2={g['H2']} negYr={g['negYr']} worst={g['worst']} ann={g['ann']} corr={g['corr_champ']}",flush=True)
                res.append((lb,lbl,st[:4],g))
