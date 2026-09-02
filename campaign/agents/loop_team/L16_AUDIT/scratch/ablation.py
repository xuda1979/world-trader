import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
Sn08=pd.DataFrame({n:vt(sn(p),0.08)[1] for n,p in POOL.items()}).dropna(how='all')
capW8=Sn08/N

def build8(TGT,THR,keep=False,pool=None):
    pool = pool or POOL
    V={};S={}
    for n in pool:
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
    terms=[Sn08[n]/N*sc*SHORTF[n]*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2) for n in POOL if SHORTF[n]>0]
    T=pd.concat(terms,axis=1)
    htb = T.sum(axis=1,skipna=True) if keep else T.sum(axis=1,skipna=False)
    return (r_out-htb/252).dropna(),sb

def st(r):
    eq=(1+r).cumprod(); m=(1+r).resample('ME').prod()-1
    y=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    y=y[y.index>=2008]
    return dict(ann=round((eq.iloc[-1]**(252/len(r))-1)*100,1),srd=round(r.mean()/r.std()*np.sqrt(252),2),
                srm=round(m.mean()/m.std()*np.sqrt(12),2),mdd=round((eq/eq.cummax()-1).min()*100,2),
                neg=int((y<0).sum()),worst=round(y.min()*100,1))

A,_=build8(0.07,0.04); B,_=build8(0.091,0.03); BAL=((A+B)/2).dropna()
Ak,sbA=build8(0.07,0.04,keep=True); Bk,_=build8(0.091,0.03,keep=True); BALk=((Ak+Bk)/2).dropna()
BALk_w=BALk[BALk.index>='2008-03-31']
print("kept-rows restricted to committed window:",st(BALk_w))
# PnL on the dropped days themselves: reconstruct blend without dropna
V={}
for n in POOL:
    r=sn(POOL[n]); v,s=vt(r,0.08)
    V[n]=v-capW8[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
Vn=pd.DataFrame(V)
W=Sn08.div(Sn08.sum(axis=1),axis=0).fillna(0)
blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
dropped_days=[d for d in BAL.index.to_list()]
allidx=blend[blend.index>='2008-03-31'].index
missing=[d for d in allidx if d not in BAL.index]
md_blend=blend.reindex(missing)
print(f"n missing in-window {len(missing)}, blend mean on those days {md_blend.mean()*1e4:.2f}bp vs overall {blend[blend.index>='2008-03-31'].mean()*1e4:.2f}bp")

# ablation: drop one sleeve at a time
print("\nablation (BAL):")
for n in POOL:
    pool2={k:v for k,v in POOL.items() if k!=n}
    A2,_=build8(0.07,0.04,pool=pool2); B2,_=build8(0.091,0.03,pool=pool2); BAL2=((A2+B2)/2).dropna()
    s=st(BAL2)
    print(f" -{n:9s}: ann {s['ann']:5.1f}% SR_m {s['srm']:.2f} MDD {s['mdd']:6.2f}% neg {s['neg']}")

# gross for the 80% variant X (TGT .11/.14)
X,_=build8(0.11,0.14); Y,_=build8(0.12,0.15); XB=((X+Y)/2).dropna()
Sd=pd.DataFrame({n:vt(sn(p),0.08)[1] for n,p in POOL.items()})
# recompute global scales for XB via same build: use sbA-like from build8 at .11/.14
Xs=pd.Series(dtype=float); Ys=pd.Series(dtype=float)
# quick: recompute scale scalar path
def gscale(TGT):
    b,sb=vt(blend,TGT)
    return sb
sbX=gscale(0.11); sbY=gscale(0.12)
gX=Sd.mean(axis=1)*sbX; gY=Sd.mean(axis=1)*sbY
print("\nTGT .11/.14 variant: ann %.1f%% all-in gross mean %.2fx max %.2fx"%(st(XB)['ann'],(0.5*(gX+gY)).mean(),(0.5*(gX+gY)).max()))
