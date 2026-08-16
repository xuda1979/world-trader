"""Seed-ensemble (bagging): average base-config XGB across multiple random seeds
per refit to decorrelate predictions -> modest IC/SR lift. Test 3-seed ensemble
vs single-seed baseline."""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DYLD_LIBRARY_PATH","/Users/daxu/homebrew/opt/libomp/lib:"+os.environ.get("DYLD_LIBRARY_PATH",""))
import numpy as np, pandas as pd, xgboost as xgb
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT="/Users/daxu/software/world-trader"; OUT=os.path.join(ROOT,"tools/quant/reports")
X=pd.read_parquet(os.path.join(HERE,"data","xgb_scaled_feats.parquet")).to_numpy()
meta=pd.read_parquet(os.path.join(HERE,"data","xgb_scaled_feats_meta.parquet"))
dates=pd.to_datetime(meta["date"].to_numpy()); rn=meta["rn"].to_numpy()
TRAIN_WIN=756; REFIT=63; COST=0.0006; START=pd.Timestamp("2018-01-01")
BASE=dict(n_estimators=400,learning_rate=0.05,max_depth=6,min_child_weight=5,subsample=0.8,
          colsample_bytree=0.8,tree_method="hist",early_stopping_rounds=30,n_jobs=8)

def walk_ensemble(nseed):
    ud=np.unique(dates); pd_=ud[ud>=np.datetime64(START)]; refit=np.arange(0,len(pd_),REFIT)
    pred=np.zeros(len(X)); cnt=np.zeros(len(X))
    for seed in range(nseed):
        p=np.full(len(X),np.nan)
        for kk in refit:
            d=pd_[kk]; dmin=d-np.timedelta64(TRAIN_WIN,"D")
            tr=(dates<d)&(dates>=dmin); featok=np.isfinite(X[tr]).sum(axis=1)>0; rok=np.isfinite(rn[tr])
            tr_idx=np.where(tr)[0][featok & rok]; np.random.seed(42+seed); np.random.shuffle(tr_idx)
            nv=max(int(len(tr_idx)*0.1),1000); val,train=tr_idx[:nv],tr_idx[nv:]
            cp=dict(BASE); cp["random_state"]=1000+seed
            m=xgb.XGBRegressor(**cp)
            m.fit(X[train],rn[train],eval_set=[(X[val],rn[val])],verbose=False)
            pos=np.where(refit==kk)[0][0]; nxt=refit[pos+1] if pos+1<len(refit) else len(pd_)
            d_end=pd_[nxt] if nxt<len(pd_) else pd_[-1]+np.timedelta64(1,"D")
            blk=(dates>=d)&(dates<d_end); okb=np.isfinite(X[blk]).sum(axis=1)>0
            pb=np.full(len(X[blk]),np.nan); pb[okb]=m.predict(X[blk][okb]); p[blk]=pb
        ok=np.isfinite(p); pred[ok]+=p[ok]; cnt[ok]+=1
    pred=np.where(cnt>0,pred/np.maximum(cnt,1),np.nan)
    return pred

def ls(pred):
    live=np.isfinite(pred)&np.isfinite(rn)
    d=pd.DataFrame({"date":dates[live],"pred":pred[live],"rn":rn[live]}).sort_values(["date","pred"],ascending=False)
    ic=d.groupby("date").apply(lambda g: g["pred"].corr(g["rn"]) if len(g)>20 else None,include_groups=False).dropna()
    rows=[]
    for date,g in d.groupby("date"):
        n=len(g); K=8
        if n<2*K: continue
        li=g.index[:K]; si=g.index[-K:]
        rows.append((date, g.loc[li,"rn"].mean()-2*COST-(g.loc[si,"rn"].mean()-2*COST)))
    ds=pd.Series(dict(rows)).sort_index(); full=pd.Series(0.0,index=pd.date_range(ds.index.min(),ds.index.max(),freq="B")); full.loc[ds.index]=ds; full=full.fillna(0)
    sr=(full.mean()/full.std())*np.sqrt(252); ann=(1+full).prod()**(252/len(full))-1; eq=(1+full).cumprod(); dd=(eq/eq.cummax()-1).min()
    return {"ic":round(float(ic.mean()),5),"sr":round(float(sr),3),"ann":round(float(ann),4),"dd":round(float(dd),4)}

import time
res={}
for ns in [3]:
    t=time.time(); p=walk_ensemble(ns); r=ls(p); res[f"ens{ns}"]=r
    print(f"ens{ns}",r,f"{time.time()-t:.0f}s",flush=True)
json.dump(res,open(os.path.join(OUT,"bigmove_xgb_ensemble.json"),"w"),indent=2)
print("saved bigmove_xgb_ensemble.json")
