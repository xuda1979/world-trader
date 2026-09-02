import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
oldA=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_SAFE_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
oldB=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_AGGRESSIVE_daily.csv",index_col=0,parse_dates=True).iloc[:,0]

def build_v(TGT,THR):
    V={}
    for n in POOL:
        r=sn(POOL[n]); v,s=vt(r,0.08)
        V[n]=v-capW[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
    Vn=pd.DataFrame(V)
    W=Sn.div(Sn.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b=vt(blend,TGT)[0]
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    r_out=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    htb=pd.Series(0.0,index=Sn.index)
    for n in POOL:
        sf=SHORTF[n]
        if sf>0:
            gn=Sn[n]/N*sc*sf; htb=htb+gn*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)
    return (r_out-htb/252).dropna()

A=build_v(0.07,0.04); B=build_v(0.091,0.03)
# try BAL variants: dropna vs index intersection; reindex on union
cands={
 "halfsum_dropna":((A+B)/2).dropna(),
 "halfsum_reindexA":((A+B)/2).reindex(A.index).dropna(),
 "halfsum_reindexB":((A+B)/2).reindex(B.index).dropna(),
}
for name,c in cands.items():
    j=pd.concat([oldB.rename('o'),c.rename('n')],axis=1,join='inner').dropna()
    print(name,len(j),f"max|d|={float((j.o-j.n).abs().max()):.3e}")
# SAFE/AGGR individually (loop terminal prints from earlier show A at 1.885e-2? recheck vs each csv)
for nm,r,csv in [("SAFE",A,oldA),("AGGR",B,oldB)]:
    j=pd.concat([csv.rename('o'),r.rename('n')],axis=1,join='inner').dropna()
    print(nm,len(j),f"max|d|={float((j.o-j.n).abs().max()):.3e}")
# maybe L16 kept global vt TGT at 0.085/0.11 (champion_build defaults) with perslv 0.08?
A2=build_v(0.085,0.04); B2=build_v(0.11,0.03)
for nm,r,csv in [("SAFE@085",A2,oldA),("AGGR@11",B2,oldB)]:
    j=pd.concat([csv.rename('o'),r.rename('n')],axis=1,join='inner').dropna()
    print(nm,len(j),f"max|d|={float((j.o-j.n).abs().max()):.3e}")
