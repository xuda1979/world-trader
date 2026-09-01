"""r7 Idea5: cross-asset momentum breadth - fraction of (oil,gold,bonds,FX,VIX-short)
in own uptrend (px>MA252). Charter: long SPX when breadth>=60%. Variant B: long the
cross-asset basket itself (orthogonal-by-construction check)."""
import sys; sys.path.insert(0,".")
import numpy as np, pandas as pd
from r7lib import *

wti=load(FRED+"wti_full.csv"); gold=load(FRED+"xau.csv")
dxy=load(FRED+"dxy.csv"); vix=load(FNEW+"VIXCLS.csv")
y10=load(FNEW+"DGS10.csv")
panel=pd.DataFrame({"OIL":wti,"GOLD":gold,"BOND":synth_bond_ret(y10).cumsum()+100,
                    "FX":-dxy,"VIXS":-vix}).reindex(IDX).ffill()
ma=panel.rolling(252,min_periods=126).mean()
up=(panel>ma).astype(float)
breadth=up.mean(axis=1)
SPX=load(FRED+"spx.csv").reindex(IDX).ffill()
RET_SPX=(SPX.pct_change()).to_frame("SPX")
RET_SPX["CASH"]=0.0; RET_SPX["CASH2"]=0.0
RET_PAN=panel.pct_change()
RET_PAN["CASH"]=0.0

if __name__=="__main__":
    for thr in [0.6,0.5,0.75]:
        # Charter variant: long SPX when breadth high
        w=(breadth>=thr).astype(float)
        Wt=pd.DataFrame({"SPX":w,"CASH":0.0,"CASH2":0.0},index=IDX)
        net,_=wback_rb(Wt,RET_SPX,wed_rbd(IDX))
        for st in ["2008-01-01"]:
            r=sret(net,st,0.10); g=gates6(r); g["corr_champ"]=xcorr(r,CH)
            print(f"SPX-long thr={thr} from={st[:4]}: SR={g['SR']} H1={g['H1']} H2={g['H2']} negYr={g['negYr']} worst={g['worst']} ann={g['ann']} corr={g['corr_champ']} days_on={w[w>0].shape[0]}",flush=True)
        # Variant B: long the 5 cross-asset legs (EW) when breadth high
        W2=pd.DataFrame(np.repeat((breadth>=thr).astype(float).values[:,None]/5,5,axis=1),
                        index=IDX,columns=panel.columns)
        net,_=wback_rb(W2,RET_PAN.drop(columns=["CASH"]),wed_rbd(IDX))
        r=sret(net,"2008-01-01",0.10); g=gates6(r); g["corr_champ"]=xcorr(r,CH)
        print(f"BASKET-long thr={thr}: SR={g['SR']} H1={g['H1']} H2={g['H2']} negYr={g['negYr']} worst={g['worst']} ann={g['ann']} corr={g['corr_champ']}",flush=True)
