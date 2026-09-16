import numpy as np, pandas as pd
def load_ret(rel):
    p = "/Users/daxu/software/world-trader/campaign/"+rel
    df = pd.read_csv(p, index_col=0); df.index = pd.to_datetime(df.index)
    col = "ret" if "ret" in df.columns else df.columns[0]
    return df[col].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
def to_monthly(s): return (1+s).resample("ME").prod()-1
def perf(r, freq="M"):
    r=r.dropna(); r=r[r.abs()<0.4]
    if len(r)<30: return None
    ann=12 if freq=="M" else 252
    sr=r.mean()/r.std()*np.sqrt(ann)
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(sr=sr, ret=r.mean()*ann, dd=dd, neg=int((yr<0).sum()), worst=yr.min())
