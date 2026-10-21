import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])

old=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
A,ma=build(0.07,0.04); B,mb=build(0.091,0.03); BAL=((A+B)/2).dropna()
j=pd.concat([old.rename('old'),BAL.rename('new')],axis=1).dropna()
d=(j.old-j.new)
print("diff describe:", d.abs().describe())
big=d.abs().sort_values(ascending=False).head(15)
print("top diffs:"); print(big)
print("diff by year:"); print(d.abs().groupby(d.index.year).mean()*1e4, )
# variant: borrow without throttle sc
def build2(TGT,THR,nosc_borrow=True):
    V={}
    for n in POOL:
        r=sn(POOL[n]); v,s=vt(r,0.08)
        V[n]=v-capW[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
    Vn=pd.DataFrame(V)
    W=Sn.div(Sn.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b,sb=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    r_out=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    htb=pd.Series(0.0,index=Sn.index)
    for n in POOL:
        sf=SHORTF[n]
        if sf>0:
            gn=Sn[n]/N*(1.0 if nosc_borrow else sc)*sf
            htb=htb+gn*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)
    return (r_out-htb/252).dropna()
for nosc in [True,False]:
    A2=build2(0.07,0.04,nosc); B2=build2(0.091,0.03,nosc); BAL2=((A2+B2)/2).dropna()
    j2=pd.concat([old.rename('old'),BAL2.rename('new')],axis=1).dropna()
    print(f"variant nosc_borrow={nosc}: max|diff|={float((j2.old-j2.new).abs().max()):.3e}")
