import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
Sn08=pd.DataFrame({n:vt(sn(p),0.08)[1] for n,p in POOL.items()}).dropna(how='all')
capW8=Sn08/N
def build8(TGT,THR,keep=False):
    V={};S={}
    for n in POOL:
        r=sn(POOL[n]); v,s=vt(r,0.08)
        V[n]=v-capW8[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4); S[n]=s
    Vn=pd.DataFrame(V)
    W=Sn08.div(Sn08.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b,sb=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    r_out=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    nb=[n for n in POOL if SHORTF[n]>0]
    terms=[Sn08[n]/N*sc*SHORTF[n]*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2) for n in POOL if SHORTF[n]>0]
    T=pd.concat(terms,axis=1)
    htb = T.sum(axis=1,skipna=True) if keep else T.sum(axis=1,skipna=False)
    out=(r_out-htb/252)
    return out.dropna(),T.index

A,_=build8(0.07,0.04); B,_=build8(0.091,0.03); BAL=((A+B)/2).dropna()
Ak,Tidx=build8(0.07,0.04,keep=True); Bk,_=build8(0.091,0.03,keep=True); BALk=((Ak+Bk)/2).dropna()
yr=BALk.groupby(BALk.index.year).apply(lambda x:(1+x).prod()-1)
print("kept-rows yearly:"); print((yr*100).round(2))
import numpy as _np
dropped=Tidx[_np.array([d not in BAL.index for d in Tidx])]
dropped=[d for d in dropped if d>=pd.Timestamp('2008-03-31')]
print("n dropped rows >=2008-03-31:",len(dropped))
# daily mean ret of committed on days adjacent to dropped days vs all
old=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
print("committed mean daily:",f"{old.mean()*1e4:.3f}bp  kept mean daily: {BALk.mean()*1e4:.3f}bp")

# verify infeasibility claim: TGT 0.11/0.14 at per-sleeve 0.08 (L16 convention)
X,_=build8(0.11,0.14); Y,_=build8(0.12,0.15); XBal=((X+Y)/2).dropna()
def st(r):
    eq=(1+r).cumprod(); m=(1+r).resample('ME').prod()-1
    y=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(ann=round((eq.iloc[-1]**(252/len(r))-1)*100,1),srd=round(r.mean()/r.std()*np.sqrt(252),2),
                srm=round(m.mean()/m.std()*np.sqrt(12),2),mdd=round((eq/eq.cummax()-1).min()*100,2),neg=int((y<0).sum()))
print("TGT .11/.14 (perslv .08) BAL:",st(XBal))
