"""HONEST11 balanced at real 1.6x + verify claims 2/4 (V2 exists as committed; 2006 stub)."""
import sys, numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
import honest11_build as h11
import honest13_build as h13
NEW2=h13.NEW2; POOL=h13.POOL; EXEC=h13.EXEC; SHORTF=h13.SHORTF

# --- HONEST11 at 1.6x ---
Sd,capW,blend,tw,wts = h13.make(POOL)
def build(cost=6e-4,htb=False,TGT=0.07,THR=0.04):
    b,gb=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    full=capW.mul(gb,axis=0).mul(sc,axis=0); reb=full.diff().abs().sum(axis=1)
    r=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*cost-reb.reindex(b.index).fillna(0)*cost
    terms=[capW[n]*sc*SHORTF[n]*(0.005+(0.006 if n=='dualmom' else 0.0)) for n in POOL if SHORTF[n]>0]
    r=r-pd.concat(terms,axis=1).sum(axis=1).reindex(r.index).fillna(0)/252
    return r.dropna(how='all'),full
A,fullA=build(TGT=0.07,THR=0.04); B,fullB=build(TGT=0.091,THR=0.03)
BAL=((A+B)/2).dropna(); idx=BAL.index
g=((fullA.fillna(0).abs().sum(axis=1)+fullB.fillna(0).abs().sum(axis=1))/2).reindex(idx).fillna(0)
live=g[g.index>='2008-03-31']
print(f"POOL11 BAL gross: mean {live.mean():.3f}x p95 {np.percentile(live,95):.3f}x")
f=(1.6/live).clip(upper=1.0); fin=(live*f-1).clip(lower=0)*0.045/252
r16=(BAL*f-fin.reindex(idx).fillna(0)).dropna()
def stats(r,label,start='2008-03-31'):
    rr=r[r.index>=start]; eq=(1+rr).cumprod()
    yr=rr.groupby(rr.index.year).apply(lambda x:(1+x).prod()-1)
    m=(1+rr).resample('ME').prod()-1
    print(f"{label}: ann_arith {rr.mean()*252*100:.2f}% ann_geo {((eq.iloc[-1])**(252/len(rr))-1)*100:.2f}% SR_d {rr.mean()/rr.std()*np.sqrt(252):.3f} SR_m {m.mean()/m.std()*np.sqrt(12):.3f} MDD {((eq/eq.cummax())-1).min()*100:.2f}% neg {int((yr<0).sum())}/{yr.size}")
stats(r16,"POOL11 BAL @1.6x+4.5%margin")
f0=(1.6/live).clip(upper=1.0); r16b=(BAL*f0).dropna()
stats(r16b,"POOL11 BAL @1.6x no margin")

# --- claim 2/4: committed files exist? ---
import os
for fn in ["GOAL100_HONEST14V3_BALANCED_daily.csv","GOAL100_HONEST13V2_BALANCED_daily.csv"]:
    p=f"{ROOT}/campaign/results/{fn}"; print(fn,"exists" if os.path.exists(p) else "MISSING", os.path.getsize(p) if os.path.exists(p) else "")
# --- 2006 stub decomposition ---
def load(rel):
    df=pd.read_csv(f"{ROOT}/{rel}",index_col=0); df.index=pd.to_datetime(df.index)
    return df.iloc[:,0].astype(float)
v3=load("campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv")
st=v3[v3.index<'2007-01-01']
print(f"2006 stub: n={len(st)} span {st.index[0].date()}..{st.index[-1].date()} cum {(1+st).prod()-1:+.3%}")
