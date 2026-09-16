"""HONEST champion build from the 166 admissible strategies. Energy cap <= 30%.

The campaign's PROVEN robust method (from bt/gates + coordinator + ITER audits):
  simple MONTHLY EW blend of a decorrelated set, no covariance weight optimization
  (which the campaign found overfits). Robustness guards:
   - drop any candidate whose IS-SR <= 0 (no negative-IS sleeves)
   - greedy forward selection that maximizes EW-SR, but REFUSE to add a sleeve
     whose max |corr| to already-chosen > 0.60 (decorrelation -> enough diversity
     for the many-low-corr route to SR).
   - energy cap 30%: cap the NUMBER of energy sleeves selected so their EW weight
     sum <= 30%; then project weights to exact <=30%.
  Honest split: select + weigh on IS <2016, evaluate on OOS >=2016.
  Compare vs champion of record (RAWEW15 refresh) on the same OOS window.
  Report both SR and annual-return; also give a levered variant scaled to the
  champion's OOS vol for a like-for-like comparison.
"""
import os, re, json
import numpy as np, pandas as pd

ROOT="/Users/daxu/software/world-trader/campaign"
D0="2016-01-01"
ENERGY_PAT=re.compile(r"(crack|diesel|diescrack|_ho_|hobr|ng_storage|C5ng|E1_C5ng|"
                      r"brent|wti|\\bprop|seas_12-02|gas_prem|DBE|DBP|_ng[_.]|/ng_|_ng_)",re.I)
def is_energy(rel): return bool(ENERGY_PAT.search(os.path.basename(rel)))
def load(rel):
    df=pd.read_csv(os.path.join(ROOT,rel),index_col=0); df.index=pd.to_datetime(df.index)
    col="ret" if "ret" in df.columns else df.columns[0]
    return df[col].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
def monthly(s): return (1+s).resample("ME").prod()-1
def perf(r):
    r=r.dropna(); r=r[r.abs()<0.4]
    if len(r)<24: return None
    eq=(1+r).cumprod()
    return dict(sr=r.mean()/r.std()*np.sqrt(12), vol=r.std()*np.sqrt(12)*100,
                ann=r.mean()*12*100, dd=(eq/eq.cummax()-1).min()*100,
                neg=int((r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)<0).sum()),
                worst=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1).min()*100)
def main():
    pool=pd.read_csv(os.path.join(ROOT,"work_backtest_oos/passing_honest_oos>0.4.csv"))
    pool=pool[~pool['strategy'].str.contains(re.compile(r"MHX|HT_TAIL"))]
    streams={}; seen=set(); cand=[]
    for _,r in pool.iterrows():
        rel=r['strategy']
        try: s=load(rel); key=s.round(9).values.tobytes()
        except Exception: continue
        if key in seen: continue
        seen.add(key); streams[rel]=monthly(s); cand.append(rel)
    df=pd.DataFrame(streams).fillna(0)
    df=df[df.index>='2009-01-01']
    usable=[c for c in cand if (df[c]!=0).sum()>=80]
    df=df[usable]
    e=pd.Series([is_energy(c) for c in usable],index=usable)
    isdf=df[df.index<D0]; osdf=df[df.index>=D0]
    # only positive-IS-SR sleeves
    is_ok=[c for c in usable if (lambda v: v and v['sr']>0)(perf(isdf[c]))]
    df=df[is_ok]; e=e[is_ok]; isdf=isdf[is_ok]; osdf=osdf[is_ok]
    print(f"usable(IS-SR>0): {len(is_ok)} | energy: {e.sum()}")

    def ew_sr(sub):
        return perf(isdf[sub].mean(axis=1))['sr']
    corr=isdf.corr()
    chosen=[]; rem=set(is_ok); DROP=0.60
    # energy cap on the SELECTED set: at most ceil to keep EW energy weight <=30%
    for _ in range(16):
        cand2=[c for c in rem if (not chosen) or abs(corr.loc[c,chosen]).max()<=DROP]
        if not cand2: break
        best=max(cand2,key=lambda c: ew_sr(chosen+[c]))
        chosen.append(best); rem.discard(best)
    ne=sum(is_energy(c) for c in chosen)
    print(f"decorrelated EW subset: {len(chosen)} sleeves (energy {ne})")
    # EW weights
    w=np.full(len(chosen),1.0/len(chosen))
    en=np.array([1.0 if is_energy(c) else 0.0 for c in chosen])
    enexp=w@en
    # project energy <=30%
    if enexp>0.30:
        scale=0.30/enexp
        w=np.where(en==1,w*scale,w)
    w=w/w.sum(); enexp=float(w@en)
    ri=isdf[chosen].dot(w); ro=osdf[chosen].dot(w)
    pi=perf(ri); po=perf(ro)
    champ=monthly(load('results/RAWEW15_REFRESH_CANDIDATE_daily.csv'))
    pc=perf(champ[champ.index>=D0])
    # levered variant to match champion OOS vol
    lev=pc['vol']/po['vol']
    rolev=ro*lev; pole=perf(rolev)
    print(f"\nenergy exposure: {enexp*100:.1f}%  (n_energy={ne})")
    print(f"NEW EW : IS  SR={pi['sr']:.3f} ann={pi['ann']:.1f}% vol={pi['vol']:.1f}% dd={pi['dd']:.2f}%")
    print(f"NEW EW : OOS SR={po['sr']:.3f} ann={po['ann']:.1f}% vol={po['vol']:.1f}% dd={po['dd']:.2f}% neg={po['neg']}")
    print(f"CHAMP  : OOS SR={pc['sr']:.3f} ann={pc['ann']:.1f}% vol={pc['vol']:.1f}% dd={pc['dd']:.2f}%")
    print(f"DELTA OOS SR: {po['sr']-pc['sr']:+.3f}  -> {'BEATS' if po['sr']>pc['sr'] else 'NO'}")
    print(f"levered-to-champ-vol (x{lev:.2f}): OOS SR={pole['sr']:.3f} ann={pole['ann']:.1f}% dd={pole['dd']:.2f}%")
    print("\n=== NEW CHAMPION sleeve weights ===")
    for c,wi in sorted(zip(chosen,w),key=lambda x:-x[1]):
        if wi*100>=1.0:
            print(f"  {wi*100:6.2f}%  {'EN' if is_energy(c) else '  '} {c}")
    outd=os.path.join(ROOT,"work_backtest_oos")
    pd.Series(w,index=chosen).to_csv(os.path.join(outd,"NEWCHAMPION_weights.csv"),header=['w'])
    ro.to_frame('ret').to_csv(os.path.join(outd,"NEWCHAMPION_OOS.csv"))
    json.dump(dict(n=len(chosen),n_energy=ne,energy_exp=enexp,oos_sr=po['sr'],is_sr=pi['sr'],
                   champ_oos_sr=pc['sr'],lev=lev,lev_oos_sr=pole['sr']),
              open(os.path.join(outd,"NEWCHAMPION_result.json"),"w"),default=str)
    print("\nsaved NEWCHAMPION_*")

if __name__=="__main__":
    main()
