import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
oldA=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_SAFE_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
oldB=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_AGGRESSIVE_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
old=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]

def build_sn(TGT,THR,SNTGT):
    V={}
    Snx=pd.DataFrame({n:vt(sn(p),SNTGT)[1] for n,p in POOL.items()}).dropna(how='all')
    capWx=Snx/N
    for n in POOL:
        r=sn(POOL[n]); v,s=vt(r,0.08)
        V[n]=v-capWx[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
    Vn=pd.DataFrame(V)
    W=Snx.div(Snx.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b=vt(blend,TGT)[0]
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    r_out=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    htb=pd.Series(0.0,index=Snx.index)
    for n in POOL:
        sf=SHORTF[n]
        if sf>0:
            gn=Snx[n]/N*sc*sf; htb=htb+gn*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)
    return (r_out-htb/252).dropna()

for SNT in [0.10,0.08,0.09]:
    A=build_sn(0.07,0.04,SNT); B=build_sn(0.091,0.03,SNT); BAL=((A+B)/2).dropna()
    ja=pd.concat([oldA.rename('o'),A.rename('n')],axis=1,join='inner').dropna()
    jb=pd.concat([oldB.rename('o'),B.rename('n')],axis=1,join='inner').dropna()
    jc=pd.concat([old.rename('o'),BAL.rename('n')],axis=1,join='inner').dropna()
    print(f"SnTGT={SNT}: SAFE {float((ja.o-ja.n).abs().max()):.3e}  AGGR {float((jb.o-jb.n).abs().max()):.3e}  BAL {float((jc.o-jc.n).abs().max()):.3e}")
