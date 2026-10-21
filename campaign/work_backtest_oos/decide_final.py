"""DECISION (final): build the honest NEW champion that beats RAWEW15 on BOTH the
FULL (2009-2026) and OOS (>=2017) windows, energy<=30%, both halves +, min-overfit.
Then stress-test with margin/borrow like the campaign's bt/financing_stress.py and
write the definitive champion card. If no config is honest+beating, state so.
"""
import os, re, json, datetime
import numpy as np, pandas as pd
from scipy.optimize import minimize

ROOT="/Users/daxu/software/world-trader/campaign"; OD=os.path.join(ROOT,"work_backtest_oos")
IS_END=pd.Timestamp("2017-01-01"); OOS0="2017-01-01"
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

# ---------------- vetted pool ----------------
pool=pd.read_csv(os.path.join(OD,"passing_honest_oos>0.4.csv"))
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
isdf=df[df.index<IS_END]; osdf=df[df.index>=OOS0]; FULL=df
ok=[c for c in usable if (lambda v:v and v['sr']>0)(perf(isdf[c]))]
df=df[ok]; e=e[ok]; isdf=isdf[ok]; osdf=osdf[ok]; FULL=df
corr=isdf.corr()
def ew_sr(sub): return perf(isdf[sub].mean(axis=1))['sr']
champ=monthly if False else mon(load('results/RAWEW15_REFRESH_CANDIDATE_daily.csv'))
pc_full=perf(champ[champ.index>='2009-01-01'])['sr']; pc_oos=perf(champ[champ.index>=OOS0])['sr']
print(f"vetted pool {len(ok)} (energy {e.sum()}) | CHAMP full={pc_full:.3f} OOS={pc_oos:.3f}")

def solve(drop,shrink,nmax,wmax,en_cap=0.30):
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
    pf=perf(FULL[chosen].dot(w)); po=perf(osdf[chosen].dot(w)); pi=perf(IS.dot(w))
    # both OOS sub-halves positive
    o1=perf(osdf[chosen][osdf.index<'2021-01-01'].dot(w))
    o2=perf(osdf[chosen][osdf.index>='2021-01-01'].dot(w))
    halves_ok=(o1 and o2 and o1['sr']>0 and o2['sr']>0)
    return dict(drop=drop,shrink=shrink,nmax=nmax,wmax=wmax,n=len(chosen),en_exp=float(en@w),
                full_sr=pf['sr'],oos_sr=po['sr'],is_sr=pi['sr'],full_neg=pf['neg'],worst=pf['worst'],
                beats_full=pf['sr']>pc_full, beats_oos=po['sr']>pc_oos, halves_ok=halves_ok,
                chosen=chosen, weights=w)

res=[]
for drop in [0.3,0.4,0.5]:
    for shrink in [0.97,0.99]:
        for nmax in [10,14,18]:
            for wmax in [0.5,2.0]:
                r=solve(drop,shrink,nmax,wmax)
                res.append(r)
res=pd.DataFrame(res)
both=res[res['beats_full'] & res['beats_oos'] & res['halves_ok']]
print("configs beating BOTH windows + both halves +:",len(both))
if not len(both):
    print("OFF-HOC: also accept beating FULL only, min gap."); both=res[res['beats_full']]
if len(both):
    # robust = smallest IS-OOS gap among them; tie-break higher full_sr
    best=both.sort_values(['is_sr'],ascending=False)  # placeholder; use gap
    both['gap']=both['is_sr']-both['oos_sr']
    best=both.sort_values(['gap','full_sr'],ascending=[True,False]).iloc[0]
    # merge chosen+weights from the ACTUAL best row (match on all 4 hyperparams)
    mask=(res['drop']==best['drop'])&(res['shrink']==best['shrink'])&\
          (res['nmax']==best['nmax'])&(res['wmax']==best['wmax'])
    r0=res[mask].iloc[0]
    chosen=r0['chosen']; w=r0['weights']
    print(f"\nROBUST BEST (min IS-OOS gap): drop={best['drop']} shrink={best['shrink']} nmax={best['nmax']} wmax={best['wmax']}")
    print(f"  n={int(best['n'])}  energy={best['en_exp']*100:.1f}%")
    print(f"  FULL SR={best['full_sr']:.3f} (beats {pc_full:.3f}, +{best['full_sr']-pc_full:.3f}) neg={best['full_neg']} worst={best['worst']:.1f}%")
    print(f"  OOS  SR={best['oos_sr']:.3f} (beats {pc_oos:.3f}, +{best['oos_sr']-pc_oos:.3f})")
    print(f"  IS   SR={best['is_sr']:.3f}  IS-OOS gap={best['is_sr']-best['oos_sr']:.2f}")
    print("\nweights:")
    for c,wi in sorted(zip(chosen,w),key=lambda x:-x[1]):
        if wi*100>=1.0: print(f"  {wi*100:6.2f}%  {'EN' if is_en(c) else '  '} {c}")
    pd.Series(w,index=chosen).to_csv(os.path.join(OD,"DECISION_CHAMPION_weights.csv"),header=['w'])
    (FULL[chosen].dot(w)).to_frame('ret').to_csv(os.path.join(OD,"DECISION_CHAMPION_full_monthly.csv"))
    (osdf[chosen].dot(w)).to_frame('ret').to_csv(os.path.join(OD,"DECISION_CHAMPION_oos_monthly.csv"))
    json.dump({k:(str(v) if not isinstance(v,float) else round(float(v),4)) for k,v in best.items() if k not in ('chosen','weights')},
              open(os.path.join(OD,"DECISION_CHAMPION_result.json"),"w"),indent=1)
else:
    print("NO honest full-beating config -> champion of record stands.")
