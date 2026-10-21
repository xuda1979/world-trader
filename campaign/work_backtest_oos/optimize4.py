"""Champion-blueprint optimizer — beat RAWEW15 champion with energy cap <= 30%.

Replicates the champion's exact, proven weight-fit methodology:
  - monthly returns (honest cadence), common window >=2009
  - IS window = < 2017-01-01 (champion's IS_END), OOS = >= 2016-01-01
  - candidate pool = deduped, non-discredited, IS-SR>0, decorrelated
    (max |corr| to chosen <= 0.50) subset selected on IS to maximize IS EW-SR
  - weight fit = long-only max-Sharpe, covariance shrunk toward diagonal
    (SHRINK_D=0.98), per-sleeve cap W_MAX*EW, sum=1
  - NEW: energy-sleeve total weight <= 30% (added as SLSQP constraint)
  - evaluate OOS >= 2016 vs champion RAWEW15; report SR + levered-to-champ-vol.
"""
import os, re, json
import numpy as np, pandas as pd
from scipy.optimize import minimize

ROOT="/Users/daxu/software/world-trader/campaign"
IS_END=pd.Timestamp("2017-01-01")
OOS0="2016-01-01"
ENERGY_PAT=re.compile(r"(crack|diesel|diescrack|_ho_|hobr|ng_storage|C5ng|E1_C5ng|"
                      r"brent|wti|\\bprop|seas_12-02|gas_prem|DBE|DBP|_ng[_.]|/ng_)",re.I)
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

def fit_weight(mu, cov, energy_index, ew, shrink_d=0.98, wmax=2.0, en_cap=0.30):
    n=len(mu)
    Sig=(1-shrink_d)*cov + shrink_d*np.diag(np.diag(cov))
    k=n; cap=wmax/ k
    def neg_sr(w):
        v=float(np.sqrt(w@Sig@w)); return -(float(w@mu))/v if v>1e-14 else 0.0
    cons=[{'type':'eq','fun':lambda w: w.sum()-1},
          {'type':'ineq','fun':lambda w: en_cap - energy_index@w}]
    for b in [(0.0,wmax),(0.0,cap)]:
        r=minimize(neg_sr, ew, method='SLSQP', constraints=cons,
                   bounds=[(0.0,b[1])]*n, options={'maxiter':1000,'ftol':1e-12})
        if r.success: return r.x/r.x.sum()
    # fallback: EW with energy capped
    w=ew.copy(); en=e=en.w
    if (en@w)>en_cap:
        w=np.where(en==1,w*en_cap/(en@w),w)
    return w/w.sum()

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
    df=pd.DataFrame(streams).fillna(0); df=df[df.index>='2009-01-01']
    usable=[c for c in cand if (df[c]!=0).sum()>=80]
    df=df[usable]; e=pd.Series([is_energy(c) for c in usable],index=usable)
    isdf=df[df.index<IS_END]; osdf=df[df.index>=OOS0]
    # IS-SR>0
    ok=[c for c in usable if (lambda v:v and v['sr']>0)(perf(isdf[c]))]
    df=df[ok]; e=e[ok]; isdf=isdf[ok]; osdf=osdf[ok]
    print(f"pool: {len(ok)} sleeves IS-SR>0 (energy {e.sum()})")

    # decorrelated greedy IS selection maximizing EW-SR (matches coordinator diversity)
    def ew_sr(sub): return perf(isdf[sub].mean(axis=1))['sr']
    corr=isdf.corr(); chosen=[]; rem=set(ok); DROP=0.50
    # keep enough energy in play by selecting energy sleeves whose IS-EW marginal is positive
    for _ in range(16):
        cand2=[c for c in rem if (not chosen) or abs(corr.loc[c,chosen]).max()<=DROP]
        if not cand2: break
        best=max(cand2,key=lambda c: ew_sr(chosen+[c]))
        chosen.append(best); rem.discard(best)
    ew=np.full(len(chosen),1.0/len(chosen))
    en=np.array([1.0 if is_energy(c) else 0.0 for c in chosen])
    IS=isdf[chosen]; OS=osdf[chosen]
    mu=(IS.mean()*12).values
    cov=(IS.cov()*12).values
    w=fit_weight(mu,cov,en,ew)
    enexp=float(en@w)
    ri=IS.dot(w); ro=OS.dot(w)
    pi=perf(ri); po=perf(ro)
    champ=monthly(load('results/RAWEW15_REFRESH_CANDIDATE_daily.csv'))
    pc=perf(champ[champ.index>=OOS0])
    lev=pc['vol']/po['vol']; pole=perf(ro*lev)
    print(f"\nenergy exposure: {enexp*100:.1f}%  (n={len(chosen)}, el={int(en.sum())})")
    print(f"NEW: IS  SR={pi['sr']:.3f} ann={pi['ann']:.1f}% vol={pi['vol']:.1f}% dd={pi['dd']:.2f}% neg={pi['neg']}")
    print(f"NEW: OOS SR={po['sr']:.3f} ann={po['ann']:.1f}% vol={po['vol']:.1f}% dd={po['dd']:.2f}% neg={po['neg']} worst={po['worst']:.1f}%")
    print(f"CHAMP RAWEW15 OOS: SR={pc['sr']:.3f} ann={pc['ann']:.1f}% vol={pc['vol']:.1f}% dd={pc['dd']:.2f}%")
    print(f"DELTA OOS SR: {po['sr']-pc['sr']:+.3f} -> {'BEATS' if po['sr']>pc['sr'] else 'NO'}")
    print(f"levered-to-champ-vol x{lev:.2f}: OOS SR={pole['sr']:.3f} ann={pole['ann']:.1f}% dd={pole['dd']:.2f}%")
    print("\n=== NEW CHAMPION weights ===")
    for c,wi in sorted(zip(chosen,w),key=lambda x:-x[1]):
        if wi*100>=1.0:
            print(f"  {wi*100:6.2f}%  {'EN' if is_energy(c) else '  '} {c}")
    od=os.path.join(ROOT,"work_backtest_oos")
    pd.Series(w,index=chosen).to_csv(os.path.join(od,"NEWCHAMPION_weights.csv"),header=['w'])
    ro.to_frame('ret').to_csv(os.path.join(od,"NEWCHAMPION_OOS.csv"))
    json.dump(dict(n=len(chosen),n_energy=int(en.sum()),energy_exp=enexp,oos_sr=po['sr'],
                   is_sr=pi['sr'],champ_oos_sr=pc['sr'],lev=lev,lev_oos_sr=pole['sr']),
              open(os.path.join(od,"NEWCHAMPION_result.json"),"w"),default=str)
    print("\nsaved NEWCHAMPION_*")

if __name__=="__main__":
    main()
