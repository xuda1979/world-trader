"""Hyperparameter + target sweep for the XGB next-day-return model.
Reuses cached feature matrix; runs walk-forward per config; reports
cross-sectional IC/IR AND the K=8 long-short backtest SR (correct both-leg cost).

Usage: python xgb_tune_harness.py [config_names...]
(Walk-forward 35 refits ~2.5min per config.)
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DYLD_LIBRARY_PATH","/Users/daxu/homebrew/opt/libomp/lib:"+os.environ.get("DYLD_LIBRARY_PATH",""))
import numpy as np, pandas as pd, xgboost as xgb

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT="/Users/daxu/software/world-trader"; OUT=os.path.join(ROOT,"tools/quant/reports")
X=pd.read_parquet(os.path.join(HERE,"data","xgb_scaled_feats.parquet")).to_numpy()
meta=pd.read_parquet(os.path.join(HERE,"data","xgb_scaled_feats_meta.parquet"))
dates=pd.to_datetime(meta["date"].to_numpy()); tickers=meta["ticker"].to_numpy()
rn=meta["rn"].to_numpy(); rv5=meta["rv_next5"].to_numpy()
TRAIN_WIN=756; REFIT=63; COST=0.0006; START=pd.Timestamp("2018-01-01")

def walk_forward(make_model, target_use="rn"):
    """target_use: 'rn' raw, 'rnrv' vol-normalized(rn/rv5). Returns pred array aligned."""
    y = rn/ (rv5+1e-9) if target_use=="rnrv" else rn
    ud=np.unique(dates); pd_=ud[ud>=np.datetime64(START)]; refit=np.arange(0,len(pd_),REFIT)
    pred=np.full(len(X),np.nan)
    for k,kk in enumerate(refit):
        d=pd_[kk]; dmin=d-np.timedelta64(TRAIN_WIN,"D")
        tr=(dates<d)&(dates>=dmin)
        featok=np.isfinite(X[tr]).sum(axis=1)>0; rok=np.isfinite(y[tr])
        tr_idx=np.where(tr)[0][featok & rok]
        np.random.seed(42); np.random.shuffle(tr_idx)
        nv=max(int(len(tr_idx)*0.1),1000); val,train=tr_idx[:nv],tr_idx[nv:]
        m=make_model()
        m.fit(X[train],y[train],eval_set=[(X[val],y[val])],verbose=False)
        d_end=pd_[kk+REFIT] if kk+REFIT<len(pd_) else pd_[-1]+np.timedelta64(1,"D")
        blk=(dates>=d)&(dates<d_end); okb=np.isfinite(X[blk]).sum(axis=1)>0
        pb=np.full(len(X[blk]),np.nan); pb[okb]=m.predict(X[blk][okb]); pred[blk]=pb
        if k%12==0: print(f"    [{k+1}/{len(refit)}]",end=" ",flush=True)
    print(flush=True)
    return pred

CONFIGS={
 "base": dict(n_estimators=400,learning_rate=0.05,max_depth=6,min_child_weight=5,
              subsample=0.8,colsample_bytree=0.8,reg_lambda=1.0,tree_method="hist",
              early_stopping_rounds=30,n_jobs=8,random_state=42),
 "deeper": dict(n_estimators=400,learning_rate=0.05,max_depth=9,min_child_weight=3,
              subsample=0.8,colsample_bytree=0.7,reg_lambda=2.0,tree_method="hist",
              early_stopping_rounds=30,n_jobs=8,random_state=42),
 "shallower_reg": dict(n_estimators=500,learning_rate=0.04,max_depth=4,min_child_weight=10,
              subsample=0.9,colsample_bytree=0.6,reg_lambda=8.0,tree_method="hist",
              early_stopping_rounds=30,n_jobs=8,random_state=42),
}

def ls_metrics(pred):
    live = (np.isfinite(pred)&np.isfinite(rn))
    d=pd.DataFrame({"date":dates[live],"pred":pred[live],"rn":rn[live]})
    d=d.sort_values(["date","pred"],ascending=False)
    K=8
    # cross-sectional IC
    d["icd"]=d.groupby("date")["pred"].rank(pct=True)
    ics=d.groupby("date").apply(lambda g: pd.Series({"ic":g["pred"].corr(g["rn"],method="pearson"),
                                                     "ir":g["pred"].corr(g["rn"],method="spearman")}) if len(g)>20 else None,include_groups=False).dropna()
    # long-short K=8
    rows=[]
    for date,g in d.groupby("date"):
        n=len(g)
        if n<2*K: continue
        li=g.index[:K]; si=g.index[-K:]
        rows.append((date, g.loc[li,"rn"].mean()-2*COST - (g.loc[si,"rn"].mean()-2*COST)))
    ds=pd.Series(dict(rows)).sort_index()
    full=pd.Series(0.0,index=pd.date_range(ds.index.min(),ds.index.max(),freq="B"))
    full.loc[ds.index]=ds; full=full.fillna(0)
    sr=(full.mean()/full.std())*np.sqrt(252); ann=(1+full).prod()**(252/len(full))-1
    eq=(1+full).cumprod(); dd=(eq/eq.cummax()-1).min()
    return {"ic":round(float(ics["ic"].mean()),5),"pearson_ir":round(float(ics["ic"].mean()/ics["ic"].std()*np.sqrt(252)),2),
            "ls_sr":round(float(sr),3),"ls_ann":round(float(ann),4),"ls_dd":round(float(dd),4)}

def main(argv):
    names=argv[1] if len(argv)>1 else None
    targets=[c for c in CONFIGS if names is None or c in names.split(",")]
    results={}
    # baseline current cache predictions for reference
    ref=pd.read_parquet(os.path.join(HERE,"data","xgb_scaled_pred.parquet"))
    ref["date"]=pd.to_datetime(ref["date"])
    m=pd.MultiIndex.from_arrays([pd.to_datetime(meta["date"]),meta["ticker"]])
    refm=ref.set_index(["date","ticker"])["pred_ret"].reindex(m).to_numpy()
    results["baseline_cache"]=ls_metrics(refm)
    print("baseline_cache:",results["baseline_cache"])
    for name in targets:
        print(f"## running {name} ...",flush=True)
        import time; t=time.time()
        pred=walk_forward(lambda c=name: xgb.XGBRegressor(**CONFIGS[c]))
        results[name]=ls_metrics(pred)
        print(f"{name}: {results[name]} ({time.time()-t:.0f}s)",flush=True)
    with open(os.path.join(OUT,"bigmove_xgb_tune.json"),"w") as f: json.dump(results,f,indent=2,default=str)
    print("\nsaved ->",os.path.join(OUT,"bigmove_xgb_tune.json"))

if __name__=="__main__":
    main(sys.argv)
