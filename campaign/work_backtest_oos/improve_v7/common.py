import pandas as pd, numpy as np, os, pickle, warnings
warnings.filterwarnings('ignore')
ROOT="/Users/daxu/software/world-trader/campaign"; OD="/Users/daxu/software/world-trader/campaign/work_backtest_oos"
with open(os.path.join(OD,"audit_v5","v7_shared.pkl"),"rb") as f: D=pickle.load(f)
def sr(r,f=12):
    r=r.dropna(); r=r[r.abs()<0.5]
    return r.mean()/r.std()*np.sqrt(f) if len(r)>1 and r.std()>0 else 0
def save(name,obj):
    json.dump(obj,open(f"agents/{name}.json","w"),indent=1,default=str)
import json
