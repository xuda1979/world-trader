import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
old=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]

def sn2(p):
    r=load(p).dropna()
    keep=np.array([(d.dayofweek<5 and d.date() not in hol) for d in r.index])
    out=pd.Series(0.0,index=r.index[keep]); cu=0.0; ki=0; v=r.values
    for i in range(len(r)):
        cu+=v[i]
        if keep[i]: out.iloc[ki]=cu; cu=0.0; ki+=1
    return out.iloc[:ki]

for perslv in [0.08, 0.0795, 0.079, 0.081, 0.08105]:
    V={}
    for n in POOL:
        r=sn2(POOL[n]); v,s=vt(r,perslv)
        V[n]=v-capW[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
    Vn=pd.DataFrame(V)
    W=Sn.div(Sn.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b=vt(blend,0.07)[0]
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-0.04,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    r_out=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    A=(r_out-htb_dummy(0) if False else r_out)
    # add borrow
    htb=pd.Series(0.0,index=Sn.index)
    for n in POOL:
        sf=SHORTF[n]
        if sf>0:
            gn=Sn[n]/N*sc*sf; htb=htb+gn*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)
    A=(r_out-htb/252).dropna()
    print(f"perslv={perslv}: max|d| vs SAFE-csv")
    oldA=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_SAFE_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
    j=pd.concat([oldA.rename('o'),A.rename('n')],axis=1,join='inner').dropna()
    print("   ",f"max|new-old|={float((j.o-j.n).abs().max()):.3e}")
