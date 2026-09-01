"""r7 Idea4: inflation-sensitive - CPIAUCSL YoY acceleration -> long commodity basket
(WTI/Brent/gold/natgas/copper), flat otherwise. Monthly, CPI lagged 1 month (publication PIT)."""
import sys; sys.path.insert(0,".")
import numpy as np, pandas as pd
from r7lib import *

def build_prices():
    px={"WTI":load(FRED+"wti_full.csv"),"BRENT":load(FRED+"brent.csv"),
        "GOLD":load(FRED+"xau.csv"),"NATGAS":load(R7D+"DHHNGSP.csv"),
        "CU":load(FRED+"copper_monthly.csv")}
    return pd.DataFrame(px).reindex(IDX).ffill()

if __name__=="__main__":
    P=build_prices(); RET_P=P.ffill().pct_change()
    cpi=load(FNEW+"CPIAUCSL.csv")
    yoy=cpi.pct_change(12)*100
    # publication PIT: value for month M usable from M+1 (FRED stamp implies lag; add 1m safety)
    yoy_lag=yoy.shift(2)  # shift 2 months: t+1 publication + no-lookahead margin
    yoy_lag=yoy_lag.reindex(IDX).ffill()
    chg=yoy_lag.diff(21)  # ~1 month of daily-freq change
    rets=[]
    for sign,lbl in [(+1,"long-when-rising"),(-1,"long-when-falling")]:
        for thr in [0.0]:
            w=(sign*chg>thr).astype(float)*0.2  # EW across 5 commodities
            Wt=pd.DataFrame(np.repeat(w.values[:,None],len(RET_P.columns),axis=1),
                            index=IDX,columns=RET_P.columns)
            net,_=wback_rb(Wt,RET_P,month_rbd(IDX))
            for st in ["2000-01-01","2008-01-01"]:
                r=sret(net,st,0.10); g=gates6(r); g["corr_champ"]=xcorr(r,CH)
                print(f"{lbl} from={st[:4]}: SR={g['SR']} H1={g['H1']} H2={g['H2']} negYr={g['negYr']} worst={g['worst']} ann={g['ann']} corr={g['corr_champ']}",flush=True)
    # baseline: always-long commodity basket EW
    Wt=pd.DataFrame(0.2,index=IDX,columns=RET_P.columns)
    net,_=wback_rb(Wt,RET_P,month_rbd(IDX))
    for st in ["2000-01-01","2008-01-01"]:
        r=sret(net,st,0.10); g=gates6(r); g["corr_champ"]=xcorr(r,CH)
        print(f"always-long basket from={st[:4]}: SR={g['SR']} H1={g['H1']} H2={g['H2']} negYr={g['negYr']} worst={g['worst']} ann={g['ann']} corr={g['corr_champ']}")
