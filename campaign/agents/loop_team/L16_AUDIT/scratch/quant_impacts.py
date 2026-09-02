import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
Sn08=pd.DataFrame({n:vt(sn(p),0.08)[1] for n,p in POOL.items()}).dropna(how='all')
capW8=Sn08/N
def build8(TGT,THR,htb_skipna=True):
    V={};S={}
    for n in POOL:
        r=sn(POOL[n]); v,s=vt(r,0.08)
        V[n]=v-capW8[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4); S[n]=s
    Vn=pd.DataFrame(V); Sd=pd.DataFrame(S)
    W=Sn08.div(Sn08.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b,sb=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    r_out=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    htb=pd.Series(0.0,index=Sn08.index)
    for n in POOL:
        sf=SHORTF[n]
        if sf>0:
            gn=Sn08[n]/N*sc*sf; htb=htb+gn*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)
    if htb_skipna:
        # borrow charged only on sleeves present that day (mean over available) - keeps the row
        terms=[]
        for n in POOL:
            sf=SHORTF[n]
            if sf>0:
                gn=Sn08[n]/N*sc*sf*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)
                terms.append(gn)
        T=pd.concat(terms,axis=1)
        htb=T.mean(axis=1)*len(terms)/T.count(axis=1)  # scale? simpler: sum skipna
        htb=T.sum(axis=1,skipna=True)/len(terms)*0  # placeholder
        htb=T.mean(axis=1)*len([n for n in POOL if SHORTF[n]>0])  # skipna sum equivalent
    out=(r_out-htb/252)
    return out.dropna()

def stat(r):
    eq=(1+r).cumprod(); m=(1+r).resample('ME').prod()-1
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(n=len(r),ann=(eq.iloc[-1]**(252/len(r))-1)*100,srd=r.mean()/r.std()*np.sqrt(252),
                srm=m.mean()/m.std()*np.sqrt(12),mdd=(eq/eq.cummax()-1).min()*100,neg=int((yr<0).sum()),worst=yr.min()*100)

A_keep=build8(0.07,0.04,htb_skipna=True); B_keep=build8(0.091,0.03,htb_skipna=True); BAL_keep=((A_keep+B_keep)/2).dropna()
old=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
print("committed :",{k:round(v,3) for k,v in stat(old).items()})
print("rows-kept :",{k:round(v,3) for k,v in stat(BAL_keep).items()})
print("n diff:",len(BAL_keep)-len(old))

# FINANCING sensitivity on committed BAL
r=old
SnS=pd.read_csv(f"{ROOT}/campaign/agents/loop_team/L16_AUDIT/scratch/bal_gross_path.csv",index_col=0,parse_dates=True).iloc[:,0]
gs=SnS.reindex(r.index)
for rate,name,base in [(0.0475,"pub-def gross>1",1.0),(0.0475,"all-in gross (full)",0.0)]:
    if base==1.0: lev=(gs-1.0).clip(lower=0)
    else: lev=gs  # all-in mean 3.429 path needed; approximate with scaled pub-def? recompute properly below
    drag=lev*rate/252
    rf=r-drag
    s=stat(rf); print(f"financing {name} @4.75%: ann {s['ann']:.1f}% SR_d {s['srd']:.2f} MDD {s['mdd']:.2f}% neg {s['neg']} worst {s['worst']:.1f}%")
# all-in path recompute for BAL
