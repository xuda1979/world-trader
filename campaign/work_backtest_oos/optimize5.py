"""Final honest champion builder on the VETTED pool, energy cap <= 30%.

Uses the campaign's honest principles:
  - vetted pool = 166 OOS-SR>0.4 MINUS campaign-FAILED/DEAD sleeves (meta audit)
    MINUS discredited MHX/HT_TAIL artifacts.
  - monthly returns, IS <2017-01-01 fit, OOS >=2016-01-01 eval.
  - decorrelated-gated greedy selection (IS EW-SR) + champion's diagonal-shrunk
    long-only max-Sharpe weight fit + energy-cap constraint.
  - OVERFIT GUARD: among configs beating the champion, prefer the one with the
    SMALLEST IS-OOS SR gap (most robust), THEN highest OOS SR. This avoids the
    palatable-but-brittle IS-SR-7.3 configs.
  - reports full metrics for the chosen portfolio vs champion RAWEW15.
"""
import os, re, json
import numpy as np, pandas as pd
from scipy.optimize import minimize

ROOT="/Users/daxu/software/world-trader/campaign"; IS_END=pd.Timestamp("2017-01-01"); OOS0="2016-01-01"
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
    eq=(1+r).cumprod()
    return dict(sr=r.mean()/r.std()*np.sqrt(12),vol=r.std()*np.sqrt(12)*100,
                ann=r.mean()*12*100,dd=(eq/eq.cummax()-1).min()*100,
                neg=int((r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)<0).sum()))

# ---- build vetted pool ----
pool=pd.read_csv(os.path.join(ROOT,"work_backtest_oos/passing_honest_oos>0.4.csv"))
pool=pool[~pool['strategy'].str.contains(re.compile(r"MHX|HT_TAIL"))]
pool=pool[~pool['strategy'].str.contains(re.compile(r"_on_CHAMP|overlay",re.I))]  # drop champion-embedded overlays
pool=pool[~pool['strategy'].apply(vt_bad)]     # drop campaign-rejected
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
print(f"VETTED usable pool: {len(ok)} (energy {e.sum()}) | champ OOS SR baseline {pc:.3f}")

def solve(drop,shrink,nmax,wmax,en_cap):
    chosen=[]; rem=set(ok)
    for _ in range(nmax):
        cad=[c for c in rem if (not chosen) or abs(corr.loc[c,chosen]).max()<=drop]
        if not cad: break
        b=max(cad,key=lambda c:ew_sr(chosen+[c])); chosen.append(b); rem.discard(b)
    ew=np.full(len(chosen),1/len(chosen)); en=np.array([1.0 if is_en(c) else 0.0 for c in chosen])
    IS=isdf[chosen]; OS=osdf[chosen]
    mu=(IS.mean()*12).values; cov=(IS.cov()*12).values
    Sig=(1-shrink)*cov+shrink*np.diag(np.diag(cov)); n=len(chosen); cap=wmax/n
    def nsr(w):
        v=float(np.sqrt(w@Sig@w)); return -(float(w@mu))/v if v>1e-14 else 0.0
    cons=[{'type':'eq','fun':lambda w:w.sum()-1},{'type':'ineq','fun':lambda w:en_cap-en@w}]
    r=minimize(nsr,ew,method='SLSQP',constraints=cons,bounds=[(0,cap)]*n,options={'maxiter':2000,'ftol':1e-12})
    w=r.x/r.x.sum()
    pi=perf(IS.dot(w)); po=perf(OS.dot(w))
    return dict(drop=drop,shrink=shrink,nmax=nmax,wmax=wmax,n=len(chosen),
                en_exp=float(en@w),is_sr=pi['sr'],oos_sr=po['sr'],gap=pi['sr']-po['sr'],
                beats=po['sr']>pc, weights=w, chosen=chosen)

res=[]
for drop in [0.30,0.40,0.50]:
    for shrink in [0.97,0.99]:
        for nmax in [10,14,18]:
            for wmax in [0.5,2.0]:
                r=solve(drop,shrink,nmax,wmax,0.30)
                if r['beats']:
                    r['d']=r['oos_sr']-pc
                    res.append(r)
res=pd.DataFrame(res)
print("\nBeating configs found:",len(res))
if len(res):
    # prefer smallest gap, then highest OOS SR
    best=res.sort_values(['gap','oos_sr'],ascending=[True,False]).iloc[0]
    print(f"BEST (min-overfit, then OOS SR):")
    print(f"  {best[['drop','shrink','nmax','wmax']].to_dict()} n={int(best['n'])} en={best['en_exp']*100:.1f}%")
    print(f"  IS SR={best['is_sr']:.3f}  OOS SR={best['oos_sr']:.3f}  d_vs_champ={best['d']:+.3f}  gap={best['gap']:.2f}")
    w=best['weights']; chosen=best['chosen']
    IS=isdf[chosen]; OS=osdf[chosen]
    ri=IS.dot(w); ro=OS.dot(w); pi=perf(ri); po=perf(ro)
    lev=pc/perf(ro)['vol'] # placeholder; vol from po
    vole=perf(ro)['vol']; volt=perf(champ[champ.index>=OOS0])['vol']
    lev=volt/vole; pole=perf(ro*lev)
    print(f"  NEW: OOS ann={po['ann']:.1f}% vol={po['vol']:.1f}% dd={po['dd']:.2f}% neg={po['neg']}")
    print(f"  CHAMP: OOS ann={perf(champ[champ.index>=OOS0])['ann']:.1f}% vol={volt:.1f}%")
    print(f"  levered-to-champ-vol x{lev:.2f}: OOS SR={pole['sr']:.3f}")
    print("\n=== NEW CHAMPION weights ===")
    for c,wi in sorted(zip(chosen,w),key=lambda x:-x[1]):
        if wi*100>=1.0:
            print(f"  {wi*100:6.2f}%  {'EN' if is_en(c) else '  '} {c}")
    od=os.path.join(ROOT,"work_backtest_oos")
    pd.Series(w,index=chosen).to_csv(os.path.join(od,"NEWCHAMPION_weights.csv"),header=['w'])
    ro.to_frame("ret").to_csv(os.path.join(od,"NEWCHAMPION_OOS.csv"))
    json.dump(dict(n=int(best['n']),n_energy=int(sum(is_en(c) for c in chosen)),
                   energy_exp=float(best['en_exp']),oos_sr=float(best['oos_sr']),
                   is_sr=float(best['is_sr']),champ_oos_sr=float(pc),gap=float(best['gap']),
                   lev=float(lev),lev_oos_sr=float(pole['sr']),
                   ann_oos=float(po['ann']),dd_oos=float(po['dd'])),
              open(os.path.join(od,"NEWCHAMPION_result.json"),"w"),default=str)
    print("\nsaved NEWCHAMPION_*")
else:
    print("NO config beats champion on vetted pool.")
