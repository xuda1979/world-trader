import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
oldA=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_SAFE_daily.csv",index_col=0,parse_dates=True).iloc[:,0]

def build_v(TGT,THR,borrow_mult=1.0,cost_mult=1.0,htb_scale_sc=True,borrow_on_out_idx=False):
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
    r_out=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4*cost_mult
    htb=pd.Series(0.0,index=Sn.index)
    for n in POOL:
        sf=SHORTF[n]
        if sf>0:
            gn=Sn[n]/N*(sc if htb_scale_sc else 1.0)*sf
            htb=htb+gn*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)
    h=htb*borrow_mult/252
    if borrow_on_out_idx: h=h.reindex(r_out.index).fillna(0)
    return (r_out-h).dropna(), (tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4, h

A,tc,h=build_v(0.07,0.04)
j=pd.concat([oldA.rename('o'),A.rename('n')],axis=1,join='inner').dropna()
d=j.o-j.n
hc=h.reindex(j.index).fillna(0); tcc=tc.reindex(j.index).fillna(0)
print("corr(d, borrow_component):",d.corr(hc))
print("corr(d, total_cost):",d.corr(tcc))
print("mean d:",d.mean()," mean h on idx:",hc.mean()," mean tc:",tcc.mean())
# regress d = a + b*h + c*tc
X=np.vstack([np.ones(len(j)),hc.values,tcc.values]).T
beta,_,_,_=np.linalg.lstsq(X,d.values,rcond=None)
print("lstsq d~1+h+tc:",beta, "residmax:",abs(d.values-X@beta).max())
