"""r7 Idea1: commodity value/mean-reversion - 126d z-score reversion on WTI/Brent/gold/natgas.
Long cheap (low z) / short rich (high z), weekly (Wed) rebalance, vt10, T+1, 6bps."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from r7lib import *

def build_prices():
    px={}
    px["WTI"]=load(FRED+"wti_full.csv")
    px["BRENT"]=load(FRED+"brent.csv")
    px["GOLD"]=load(FRED+"xau.csv")
    px["NATGAS"]=load(R7D+"DHHNGSP.csv")
    P=pd.DataFrame(px).reindex(IDX).ffill()
    return P.dropna(how="all")

def zsig(P,lb):
    m=P.rolling(lb,min_periods=lb//2).mean(); sd=P.rolling(lb,min_periods=lb//2).std()
    return (P-m)/sd.replace(0,np.nan)

def builder_factory(zcap=2.0):
    def b(sig):
        z=sig.clip(-zcap,zcap)
        n=(~sig.isna()).sum(axis=1).replace(0,np.nan)
        Wt=-z.div(zcap,axis=0).div(n,axis=0)
        return Wt, wed_rbd(sig.index)
    return b

if __name__=="__main__":
    P=build_prices()
    RET_P=P.ffill().pct_change()
    print("window:",P.dropna().index[0].date(),"->",P.dropna().index[-1].date(),
          "names:",[c for c in P.columns if P[c].notna().any()])
    grid=[]
    for lb in [63,126,252]:
        for zcap in [1.5,2.0,3.0]:
            sig=zsig(P,lb); b=builder_factory(zcap)
            Wt,rbd=b(sig); net,_=wback_rb(Wt,RET_P,rbd)
            r=sret(net,"2008-01-01",0.10)
            g=gates6(r)
            g["corr_champ"]=xcorr(r,CH)
            grid.append((lb,zcap,g["SR"],g["H1"],g["H2"],g["negYr"],g["worst"],g["corr_champ"]))
            print(f"lb={lb} zcap={zcap}: SR={g['SR']} H1={g['H1']} H2={g['H2']} negYr={g['negYr']} worst={g['worst']} corr={g['corr_champ']}",flush=True)
    df=pd.DataFrame(grid,columns=["lb","zcap","SR","H1","H2","negYr","worst","corr_champ"])
    df.to_csv("r7_idea1_grid.csv",index=False)
