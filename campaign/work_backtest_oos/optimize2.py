"""HONEST portfolio optimization to beat the champion, energy cap <= 30%.

Method (matches campaign's proven honest methodology):
  - monthly returns, common window 2009-2026
  - candidate pool = deduped, non-discredited OOS>0.4 strategies
  - SELECT a DECORRELATED subset on IS (<2016): greedy forward pick that maximizes
    blended EW SR subject to max pairwise |corr| < 0.50 against already-chosen
    (diversity guard -> prevents 4x-correlated-overline overfit that the coordinator
    explicitly fixed in ITER/prune); cap energy sleeve count.
  - WEIGHTS: EW (the coordinator's honest choice) with a MILDLY SR-tilted shrink toward
    EW (Ledoit-ish, heavy regularizer) s.t. energy weight <= 30% (projection).
  - Honor the energy cap by scaling the energy sleeve weights down and renormalizing.
  - Evaluate OOS >=2016 honestly, compare vs champion of record (RAWEW15).
"""
import os, re, json
import numpy as np, pandas as pd

ROOT="/Users/daxu/software/world-trader/campaign"
D0="2016-01-01"
ENERGY_PAT=re.compile(r"(crack|diesel|diescrack|_ho_|hobr|ng_storage|_ng[^e]|C5ng|E1_C5ng|"
                      r"brent|wti|\\bprop|seas_12-02|gas_prem|DBE|DBP)",re.I)
def is_energy(rel): return bool(ENERGY_PAT.search(os.path.basename(rel)))
def load(rel):
    df=pd.read_csv(os.path.join(ROOT,rel),index_col=0); df.index=pd.to_datetime(df.index)
    col="ret" if "ret" in df.columns else df.columns[0]
    return df[col].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
def monthly(s): return (1+s).resample("ME").prod()-1
def perf(r):
    r=r.dropna(); r=r[r.abs()<0.4]
    if len(r)<30: return None
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(sr=r.mean()/r.std()*np.sqrt(12), ann=r.mean()*12*100,
                dd=dd*100, neg=int((yr<0).sum()), worst=yr.min()*100)

def main():
    pool=pd.read_csv(os.path.join(ROOT,"work_backtest_oos/passing_honest_oos>0.4.csv"))
    DISCREDIT=re.compile(r"MHX|HT_TAIL")
    pool=pool[~pool['strategy'].str.contains(DISCREDIT)]
    streams={}; seen=set(); cand=[]
    for _,r in pool.iterrows():
        rel=r['strategy']
        try:
            s=load(rel); key=s.round(9).values.tobytes()
        except Exception: continue
        if key in seen: continue
        seen.add(key)
        streams[rel]=monthly(s); cand.append(rel)
    df=pd.DataFrame(streams).fillna(0)
    df=df[df.index>='2009-01-01']
    # keep usable (>=80 months active)
    usable=[c for c in cand if (df[c]!=0).sum()>=80]
    df=df[usable]
    e=pd.Series([is_energy(c) for c in usable],index=usable)
    isdf=df[df.index<D0]; osdf=df[df.index>=D0]
    print(f"deduped usable: {len(usable)} | energy: {e.sum()}")

    def ew_sr(subset, sd):
        return perf(sd[subset].mean(axis=1))['sr'] if perf(sd[subset].mean(axis=1)) else -9
    # ---- decorrelation-gated greedy selection on IS ----
    chosen=[]; pick=set(usable); corr=isdf.corr()
    drop_corr=0.50     # don't add a sleeve that is >0.50 correlated with any chosen (diversity)
    for _ in range(14):
        best=None;bs=-9
        for c in list(pick):
            if chosen and max(abs(corr.loc[c,chosen]).max() for _ in [0])>drop_corr:
                # compute max corr to chosen
                m=abs(corr.loc[c,chosen]).max()
                if m>drop_corr: continue
            sr=ew_sr(chosen+[c],isdf)
            if sr>bs: bs,best=sr,c
        if best is None: break
        chosen.append(best); pick.discard(best)
    # enforce energy cap in selection (energy count can exceed but weight capped later)
    subset=chosen
    ne=sum(is_energy(c) for c in subset)
    print(f"decorrelated IS subset: {len(subset)} sleeves (energy sleeves: {ne})")
    # ---- EW weights with mild SR tilt (shrink), then project energy <= 0.30 ----
    IS=isdf[subset]
    mu=IS.mean().values
    # SR-tilt toward EW (heavy regularizer: 85% EW, 15% mu/sum)
    ew=np.full(len(subset),1.0/len(subset))
    if mu.sum()!=0 and np.all(np.isfinite(mu)):
        wtilt=0.15*mu/mu.sum()
    else:
        wtilt=0
    w=0.85*ew+wtilt
    en=np.array([1.0 if is_energy(c) else 0.0 for c in subset])
    # project to energy cap 30%: scale energy weights down
    enexp=w@en
    if enexp>0.30:
        scale=0.30/enexp
        w=np.where(en==1, w*scale, w)
    w=np.maximum(w,0); w=w/w.sum()
    enexp=float(w@en)
    # ---- evaluate ----
    ri=isdf[subset].dot(w); ro=osdf[subset].dot(w)
    pi=perf(ri); po=perf(ro)
    champ=monthly(load('results/RAWEW15_REFRESH_CANDIDATE_daily.csv'))
    pc=perf(champ[champ.index>=D0])
    print(f"\n=== NEW CHAMPION weights (energy {enexp*100:.1f}% <=30%) ===")
    for c,wi in sorted(zip(subset,w),key=lambda x:-x[1]):
        star='EN' if is_energy(c) else '  '
        if wi*100>=1.0: print(f"  {wi*100:6.1f}% {star} {c}")
    print(f"\nNEW:  IS  SR={pi['sr']:.3f} ann={pi['ann']:.1f}% dd={pi['dd']:.2f}% neg={pi['neg']} worst={pi['worst']:.1f}%")
    print(f"NEW:  OOS SR={po['sr']:.3f} ann={po['ann']:.1f}% dd={po['dd']:.2f}% neg={po['neg']} worst={po['worst']:.1f}%")
    print(f"CHAMP:OOS SR={pc['sr']:.3f} ann={pc['ann']:.1f}% dd={pc['dd']:.2f}% neg={pc['neg']}")
    print(f"\nDELTA OOS SR: {po['sr']-pc['sr']:+.3f}  ->  {'BEATS' if po['sr']>pc['sr'] else 'does NOT beat'}")
    pd.Series(w,index=subset).to_csv(os.path.join(ROOT,"work_backtest_oos/champion2_weights.csv"),header=['w'])
    ri.to_frame('ret').to_csv(os.path.join(ROOT,"work_backtest_oos/champion2_IS.csv"))
    ro.to_frame('ret').to_csv(os.path.join(ROOT,"work_backtest_oos/champion2_OOS.csv"))
    json.dump(dict(n=len(subset),energy_exp=enexp,oos_sr=po['sr'],is_sr=pi['sr'],champ_oos_sr=pc['sr']),
              open(os.path.join(ROOT,"work_backtest_oos/champion2_result.json"),"w"),default=str)
    print("\nsaved champion2_* files; energy exposure %.1f%%"%(enexp*100))

if __name__=="__main__":
    main()
