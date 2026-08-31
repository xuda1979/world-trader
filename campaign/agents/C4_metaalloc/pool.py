"""C4_metaalloc: assemble deduped sleeve pool from library + all agents."""
import os, glob, hashlib
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
DIRS=[f"{ROOT}/campaign/results/sleeve_library", f"{ROOT}/campaign/agents"]

def load_pool(min_days=250, pos_sr=True, verbose=True):
    paths=[]
    for p in glob.glob(f"{DIRS[0]}/*.csv"): paths.append(p)
    for d in sorted(glob.glob(f"{DIRS[1]}/*/sleeves/*.csv")): paths.append(d)
    series={}; hashes={}
    for p in sorted(paths):
        name=os.path.basename(p)[:-4]
        try:
            df=pd.read_csv(p, parse_dates=[0], index_col=0)
        except Exception: continue
        if 'ret' not in df.columns: continue
        r=df['ret'].dropna()
        r=r[~r.index.duplicated()]
        if len(r)<min_days: continue
        if not np.isfinite(r).all(): continue
        h=hashlib.md5(r.round(10).to_csv().encode()).hexdigest()
        if h in hashes:  # exact duplicate content
            continue
        hashes[h]=name
        mu,sd=r.mean(),r.std(); sr=mu/sd*np.sqrt(252)
        if pos_sr and sr<=0: continue
        series[name]=r
    px=pd.DataFrame(series).sort_index()
    if verbose:
        print(f"pool: {px.shape[1]} sleeves, {px.index[0].date()}..{px.index[-1].date()}, {px.shape[0]} days")
    return px

def stats(r):
    r=r.dropna(); mu,sd=r.mean(),r.std()
    sr=mu/sd*np.sqrt(252) if sd>0 else 0
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(ann=mu*252, vol=sd*np.sqrt(252), sr=sr, mdd=dd,
                negy=int((yr<0).sum()), worst=yr.min(), n=len(r),
                yearly={int(k):v for k,v in yr.items()})

def fmt(s):
    return (f"ann {s['ann']*100:6.1f}% vol {s['vol']*100:5.1f}% SR {s['sr']:5.2f} "
            f"MDD {s['mdd']*100:6.1f}% negy {s['negy']:2d} worst {s['worst']*100:6.1f}% n {s['n']}")
