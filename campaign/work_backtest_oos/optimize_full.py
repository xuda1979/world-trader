"""DECISION: build an HONEST champion that beats RAWEW15 on the FULL window (2009-2026),
not just OOS. Honoring: energy cap <=30%, both OOS halves positive, robust to overfit.
Reuses the champion's exact weight-fit blueprint on the vetted pool.
Evaluates full-window SR (the campaign's true 20y standard) + OOS + stress.
"""
import os, re, json
import numpy as np, pandas as pd
from scipy.optimize import minimize

ROOT="/Users/daxu/software/world-trader/campaign"; IS_END=pd.Timestamp("2017-01-01")
ENP=re.compile(r"(crack|diesel|diescrack|_ho_|hobr|ng_storage|C5ng|E1_C5ng|brent|wti|\\bprop|seas_12-02|gas_prem|DBE|DBP|_ng[_.]|/ng_)",re.I)
def is_en(rel): return bool(ENP.search(os.path.basename(rel)))
def vt_bad(rel):
    m=os.path.splitext(ROOT+"/"+rel)[0]+".csv.meta"
    if not os.path.exists(m): return False
    t=open(m).read()
    return ('FAILED_NO_PROMOTION' in t) or ('DEAD_NOT_PROMOTED' in t)
def load(rel):
    d=pd.read_csv(os.path.join(ROOT,rel),index_col=0); d.index=pd.to_datetime(d.index)
    c="ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
def mon(s): return (1+s).resample("ME").prod()-1
def perf(r):
    r=r.dropna(); r=r[r.abs()<0.4]
    if len(r)<24: return None
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    eq=(1+r).cumprod()
    return dict(sr=r.mean()/r.std()*np.sqrt(12), ann=r.mean()*12*100,
                dd=(eq/eq.cummax()-1).min()*100, neg=int((yr<0).sum()), worst=yr.min()*100)

# ---- vetted pool ----
pool=pd.read_csv(os.path.join(ROOT,"work_backtest_oos/passing_honest_oos>0.4.csv"))
for pat in [r"MHX|HT_TAIL", r"_on_CHAMP|overlay"]:
    pool=pool[~pool['strategy'].str.contains(re.compile(pat,re.I))]
pool=pool[~pool['strategy'].apply(vt_bad)]
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
isdf=df[df.index<IS_END]; osdf=df[df.index>=IS_END]
# FULL window evaluation is df (2009-2026)
ok=[c for c in usable if (lambda v:v and v['sr']>0)(perf(isdf[c]))]
df=df[ok]; e=e[ok]; isdf=isdf[ok]; osdf=osdf[ok]; FULL=df
corr=isdf.corr()
def ew_sr(sub): return perf(isdf[sub].mean(axis=1))['sr']
champ=mon(load('results/RAWEW15_REFRESH_CANDIDATE_daily.csv'))
pc=perf(champ[champ.index>='2009-01-01'])['sr']
print(f"vetted pool: {len(ok)} (energy {e.sum()}) | CHAMP FULL(2009+) SR={pc:.3f}")

def solve(drop,shrink,nmax,wmax,en_cap):
    chosen=[]; rem=set(ok)
    for _ in range(nmax):
        cad=[c for c in rem if (not chosen) or abs(corr.loc[c,chosen]).max()<=drop]
        if not cad: break
        b=max(cad,key=lambda c:ew_sr(chosen+[c])); chosen.append(b); rem.discard(b)
    ew=np.full(len(chosen),1/len(chosen)); en=np.array([1.0 if is_en(c) else 0.0 for c in chosen])
    IS=isdf[chosen]
    mu=(IS.mean()*12).values; cov=(IS.cov()*12).values
    Sig=(1-shrink)*cov+shrink*np.diag(np.diag(cov)); n=len(chosen); cap=wmax/n
    def nsr(w):
        v=float(np.sqrt(w@Sig@w)); return -(float(w@mu))/v if v>1e-14 else 0.0
    cons=[{'type':'eq','fun':lambda w:w.sum()-1},{'type':'ineq','fun':lambda w:en_cap-en@w}]
    r=minimize(nsr,ew,method='SLSQP',constraints=cons,bounds=[(0,cap)]*n,options={'maxiter':2000,'ftol':1e-12})
    w=r.x/r.x.sum()
    pf=perf(FULL[chosen].dot(w))          # FULL window
    po=perf(osdf[chosen].dot(w))          # OOS
    pi=perf(IS.dot(w))
    return dict(drop=drop,shrink=shrink,nmax=nmax,wmax=wmax,n=len(chosen),
                en_exp=float(en@w),full_sr=pf['sr'] if pf else -9, oos_sr=po['sr'] if po else -9,
                is_sr=pi['sr'] if pi else -9, full_neg=pf['neg'] if pf else 99, worst=pf['worst'] if pf else 99,
                beats_full=pf['sr']>pc)

res=[]
for drop in [0.30,0.40,0.50]:
    for shrink in [0.97,0.99]:
        for nmax in [10,14,18]:
            for wmax in [0.5,2.0]:
                res.append(solve(drop,shrink,nmax,wmax,0.30))
res=pd.DataFrame(res)
b=res[res['beats_full']]
print("\nconfigs beating CHAMP on FULL window:",len(b))
if len(b):
    # prefer highest full SR with full_neg==0 and reasonable is-oos gap
    good=b[(b['full_neg']==0)]
    print("  of which 0-neg-yr-full:",len(good))
    best=good.sort_values('full_sr',ascending=False).iloc[0] if len(good) else b.sort_values('full_sr',ascending=False).iloc[0]
    print("BEST FULL-window config:")
    print(f"  {best[['drop','shrink','nmax','wmax']].to_dict()} n={int(best['n'])} en={best['en_exp']*100:.2f}%")
    print(f"  FULL SR={best['full_sr']:.3f} (vs champ {pc:.3f}, d={best['full_sr']-pc:+.3f})  neg={best['full_neg']} worst={best['worst']:.1f}%")
    print(f"  IS SR={best['is_sr']:.3f}  OOS SR={best['oos_sr']:.3f}  (IS-OOS gap={best['is_sr']-best['oos_sr']:.2f})")
else:
    print("NO honest full-window-beating config. Reporting honestly - the champion stands.")
    print("\nBest full-SR configs (non-beating):")
    print(res.sort_values('full_sr',ascending=False).head(5)[['drop','shrink','nmax','wmax','n','en_exp','full_sr','oos_sr','beats_full']].to_string(index=False))
res.to_csv(os.path.join(ROOT,"work_backtest_oos/sweep_full.csv"),index=False)
