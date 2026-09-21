import pandas as pd, numpy as np, os, pickle, warnings
warnings.filterwarnings('ignore')
AD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(os.path.dirname(AD), "audit_v5", "v4c_shared.pkl"), "rb") as f:
    D = pickle.load(f)
def sr(r):
    r=r.dropna(); r=r[r.abs()<0.5]
    return r.mean()/r.std()*np.sqrt(12) if len(r)>1 and r.std()>0 else 0
def dd_f(r):
    r=r.dropna(); eq=(1+r).cumprod()
    return (eq/eq.cummax()-1).min()*100
def neg_yr(r):
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return int((yr<0).sum())
ROOT="/Users/daxu/software/world-trader/campaign"
