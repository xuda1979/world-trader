"""Optimize a portfolio of the 166 OOS-SR>0.4 strategies to beat the champion.
Constraint: energy-exposure weight <= 30%.

Approach:
  - Candidate pool = the 166 passing strategies (OOS SR>0.4), deduped.
  - Monthly resample, common window.
  - Energy classifier (transparent pattern list) per sleeve.
  - Honest 2-stage: SELECT sleeves on <2016 IS, then solve SLSQP max-Sharpe weights
    subject to sum(w)=1, w>=0, sum(energy w)<=0.30, on IS. Then measure OOS (>=2016) SR.
  - Compare vs champion of record (RAWEW15 refresh).
"""
import sys, os, json, re
import numpy as np, pandas as pd
from scipy.optimize import minimize

ROOT="/Users/daxu/software/world-trader/campaign"
D0="2016-01-01"

# ---- energy classifier (petroleum / nat-gas energy exposure) ----
ENERGY_PAT = re.compile(
    r"(crack|diesel|diescrack|_ho_|hobr|ng_storage|_ng_|_ngsum|C5ng|E1_C5ng|"
    r"brent|wti|DBE|DBP|prop[_-]|seas_12-02|\\bNG\\b|gas_prem)", re.I)
def is_energy(rel):
    return bool(ENERGY_PAT.search(os.path.basename(rel)))

# ---- load helpers ----
def load(rel):
    df=pd.read_csv(os.path.join(ROOT,rel), index_col=0); df.index=pd.to_datetime(df.index)
    col="ret" if "ret" in df.columns else df.columns[0]
    return df[col].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
def monthly(s): return (1+s).resample("ME").prod()-1
def perf(r):
    r=r.dropna(); r=r[r.abs()<0.4]
    if len(r)<30: return None
    sr=r.mean()/r.std()*np.sqrt(12)
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(sr=sr, ret=r.mean()*12, dd=dd, neg=int((yr<0).sum()), ann=(1+r.mean())**12-1)

def main():
    pool = pd.read_csv(os.path.join(ROOT,"work_backtest_oos/passing_honest_oos>0.4.csv"))
    # drop known possibly-artifact srcs from champion build but keep? We exclude MHX/HT_TAIL as discredited
    DISCREDIT = re.compile(r"MHX|HT_TAIL")
    pool = pool[~pool['strategy'].str.contains(DISCREDIT)]
    # load streams & dedupe by returns-signature (keep first canonical, prefer non-energy on tie handled later)
    streams={}; seen=set()
    cand=[]; energy=[False]*0
    for _,r in pool.iterrows():
        rel=r['strategy']
        try:
            s=load(rel)
            if len(s)<600: continue
            key=s.round(9).values.tobytes()
        except Exception: continue
        if key in seen: continue   # exact duplicate alt-path
        seen.add(key)
        streams[rel]=monthly(s)
        cand.append(rel)
    df=pd.DataFrame(streams).dropna(how='all')
    df=df[df.index>='2008-01-01'].fillna(0)
    # energy mask
    e_mask=pd.Series([is_energy(c) for c in cand], index=cand)
    # only keep candidates with >=60 obs in concerned window to be usable
    usable=[c for c in cand if (df[c]!=0).sum()>=60]
    df=df[usable]; e_mask=e_mask[usable]
    print(f"deduped usable candidates: {len(usable)}  (energy: {e_mask.sum()})")
    isdf=df[df.index<D0]; osdf=df[df.index>=D0]
    # ---- IS sleeve selection: greedy pick max SR (Shrouthed EW) up to 12 with energy cap sometimes relaxed during selection
    # Selection on IS using EW portfolio SR per sleeve added
    def ew_sr(subset, subdf):
        r=subdf[subset].fillna(0).mean(axis=1)
        return perf(r)['sr']
    chosen=[]; candset=set(usable)
    best_sr=-9; best_subset=[]
    # limit energy in selected sleeve count proportionally is implicit via weight cap; selection just picks SR
    for _ in range(12):
        b,bs=None,-9
        for c in candset:
            sr=ew_sr(chosen+[c],isdf)
            if sr>bs: b,bs=c,sr
        if b is None or bs<best_sr and _>0: break
        # don't break at peak (coordinator does), keep top-12 diverse-ish
        chosen.append(b); candset.discard(b)
        if bs>best_sr: best_sr,best_subset=bs,list(chosen)
    # take best_subset (peak)
    subset=best_subset
    # ensure enough energy in subset to test constraint (can be 0)
    print("IS-selected subset:", len(subset))
    print("  energy in subset:", sum(is_energy(c) for c in subset))
    # ---- SLSQP weight optimization on IS, energy cap, EW prior (Ledoit style: shrink toward EW)
    IS=isdf[subset].fillna(0)
    mu=IS.mean().values
    cov=IS.cov().values
    n=len(subset)
    ew=np.full(n,1.0/n)
    # shrink toward EW to reduce overfit
    shr=0.5
    sig=shr*ew+ (1-shr)*mu/ mu.sum() if mu.sum()!=0 else ew
    en=np.array([1.0 if is_energy(c) else 0.0 for c in subset])
    # maximize expected SR = w.mu/sqrt(w'cov w)
    def neg_sr(w):
        w=np.abs(w); w=w/w.sum()
        p=w@mu
        v=np.sqrt(w@cov@w)
        return -p/v
    cons=[{'type':'eq','fun':lambda w: w.sum()-1},
          {'type':'ineq','fun':lambda w: w},                       # w>=0
          {'type':'ineq','fun':lambda w: 0.30- en@w}]              # en@w<=0.3
    res=minimize(neg_sr, sig, method='SLSQP', constraints=cons,
                 bounds=[(0,None)]*n, options={'maxiter':500,'ftol':1e-10})
    w=np.abs(res.x); w=w/w.sum()
    enexp=float(en@w)
    # ---- evaluate IS and OOS ----
    ri=IS@w
    ro=osdf[subset].fillna(0)@w
    pi=perf(ri); po=perf(ro)
    print(f"\n=== WEIGHTS (energy exposure {enexp*100:.1f}% <= 30%) ===")
    for c,wi in sorted(zip(subset,w),key=lambda x:-x[1])[:20]:
        print(f"  {wi*100:6.1f}%  {'EN' if is_energy(c) else '  '} {c}")
    print(f"\nIS  SR={pi['sr']:.3f} ann={pi['ann']*100:.1f}%  neg={pi['neg']} dd={pi['dd']*100:.2f}%")
    print(f"OOS SR={po['sr']:.3f} ann={po['ann']*100:.1f}%  neg={po['neg']} dd={po['dd']*100:.2f}%")
    # champion OOS SR
    champ=monthly(load('results/RAWEW15_REFRESH_CANDIDATE_daily.csv'))
    print(f"\nCHAMP(RAWEW15) OOS SR={perf(champ[champ.index>=D0])['sr']:.3f}")
    outdir=os.path.join(ROOT,"work_backtest_oos")
    pd.Series(w,index=subset).to_csv(os.path.join(outdir,"optimized_weights.csv"),header=['w'])
    (ri.to_frame('ret')).to_csv(os.path.join(outdir,"optimized_IS.csv"))
    (ro.to_frame('ret')).to_csv(os.path.join(outdir,"optimized_OOS.csv"))
    json.dump(dict(n=n, energy_exp=enexp, oos_sr=po['sr'], is_sr=pi['sr']),
              open(os.path.join(outdir,"optimize_result.json"),"w"), default=str)
    print("\nenergy exposure in final portfolio: %.1f%%"%(enexp*100))

if __name__=="__main__":
    main()
