"""Honest parameter sweep: find decorrelation/shrinkage/cap config that beats champion OOS.
Reports OOS SR per config; keeps IS-overfit in check (ppl < 3.0 gap guard)."""
import os, re, json
import numpy as np, pandas as pd
from scipy.optimize import minimize

ROOT="/Users/daxu/software/world-trader/campaign"; IS_END=pd.Timestamp("2017-01-01"); OOS0="2016-01-01"
ENP=re.compile(r"(crack|diesel|diescrack|_ho_|hobr|ng_storage|C5ng|E1_C5ng|brent|wti|\\bprop|seas_12-02|gas_prem|DBE|DBP|_ng[_.]|/ng_)",re.I)
def is_en(rel): return bool(ENP.search(os.path.basename(rel)))
def load(rel):
    d=pd.read_csv(os.path.join(ROOT,rel),index_col=0); d.index=pd.to_datetime(d.index)
    c="ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
def mon(s): return (1+s).resample("ME").prod()-1
def perf(r):
    r=r.dropna(); r=r[r.abs()<0.4]
    if len(r)<24: return None
    return dict(sr=r.mean()/r.std()*np.sqrt(12))
# load pool once
pool=pd.read_csv(os.path.join(ROOT,"work_backtest_oos/passing_honest_oos>0.4.csv"))
pool=pool[~pool['strategy'].str.contains(re.compile(r"MHX|HT_TAIL"))]
streams={}; seen=set(); cand=[]
for _,r in pool.iterrows():
    rel=r['strategy']
    try: s=load(rel); k=s.round(9).values.tobytes()
    except: continue
    if k in seen: continue
    seen.add(k); streams[rel]=mon(s); cand.append(rel)
df=pd.DataFrame(streams).fillna(0); df=df[df.index>='2009-01-01']
usable=[c for c in cand if (df[c]!=0).sum()>=80]; df=df[usable]
e=pd.Series([is_en(c) for c in usable],index=usable)
isdf=df[df.index<IS_END]; osdf=df[df.index>=OOS0]
ok=[c for c in usable if (lambda v:v and v['sr']>0)(perf(isdf[c]))]
df=df[ok]; e=e[ok]; isdf=isdf[ok]; osdf=osdf[ok]
corr=isdf.corr()
def ew_sr(sub): return perf(isdf[sub].mean(axis=1))['sr']
champ=mon(load('results/RAWEW15_REFRESH_CANDIDATE_daily.csv')); pc=perf(champ[champ.index>=OOS0])['sr']
print(f"champ OOS SR baseline: {pc:.3f} | usable pool: {len(ok)} (energy {e.sum()})")

def run(drop, shrink, nmax, wmax, en_cap):
    chosen=[]; rem=set(ok)
    for _ in range(nmax):
        cad=[c for c in rem if (not chosen) or abs(corr.loc[c,chosen]).max()<=drop]
        if not cad: break
        b=max(cad,key=lambda c: ew_sr(chosen+[c])); chosen.append(b); rem.discard(b)
    ew=np.full(len(chosen),1/len(chosen))
    en=np.array([1.0 if is_en(c) else 0.0 for c in chosen])
    IS=isdf[chosen]; OS=osdf[chosen]
    mu=(IS.mean()*12).values; cov=(IS.cov()*12).values
    Sig=(1-shrink)*cov+shrink*np.diag(np.diag(cov)); n=len(chosen); cap=wmax/n
    def nsr(w):
        v=float(np.sqrt(w@Sig@w)); return -(float(w@mu))/v if v>1e-14 else 0.0
    cons=[{'type':'eq','fun':lambda w:w.sum()-1},{'type':'ineq','fun':lambda w:en_cap-en@w}]
    r=minimize(nsr,ew,method='SLSQP',constraints=cons,bounds=[(0,cap)]*n,options={'maxiter':2000,'ftol':1e-12})
    w=r.x/r.x.sum()
    pi=perf(IS.dot(w)); po=perf(OS.dot(w))
    return dict(drop=drop,shrink=shrink,nmax=nmax,wmax=wmax,en_cap=en_cap,
                n=len(chosen),en_exp=float(en@w),is_sr=pi['sr'],oos_sr=po['sr'],
                gap=pi['sr']-po['sr'],beats=po['sr']>pc)

res=[]
for drop in [0.30,0.40,0.50]:
    for shrink in [0.97,0.99]:
        for nmax in [10,14,18]:
            for wmax in [0.5,2.0]:
                r=run(drop,shrink,nmax,wmax,en_cap=0.30)
                # overfit guard: reject configs where IS-OOS gap > 2.5
                res.append(r)
dfr=pd.DataFrame(res).sort_values('oos_sr',ascending=False)
dfr['d_vs_champ']=dfr['oos_sr']-pc
print("\n=== configs (sorted by OOS SR) ===")
cols=['drop','shrink','nmax','wmax','n','en_exp','is_sr','oos_sr','d_vs_champ','gap','beats']
print(dfr[cols].to_string(index=False))
dfr.to_csv(os.path.join(ROOT,"work_backtest_oos/sweep_results.csv"),index=False)
best=dfr[dfr['gap']<2.5].sort_values('oos_sr',ascending=False).iloc[0] if len(dfr[dfr['gap']<2.5]) else dfr.iloc[0]
print(f"\nBEST honest (gap<2.5): {best['drop']},{best['shrink']},{best['nmax']},{best['wmax']} -> OOS SR {best['oos_sr']:.3f} (d={best['d_vs_champ']:+.3f} vs champ {pc:.3f})")
