"""XGBoost regression walk-forward using 93 features (adds FRED macro: VIX,
yield curve, DXY, rates, oil, credit, commodities). Compare vs 70-feature baseline.
No look-ahead (quarterly refit, 3y window). Metrics on active trade days,
annualized by sqrt(active days/yr).
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DYLD_LIBRARY_PATH", "/Users/daxu/homebrew/opt/libomp/lib:" + os.environ.get("DYLD_LIBRARY_PATH",""))
import numpy as np
import pandas as pd
import xgboost as xgb
import scipy.stats as st
from pipeline_common import load_ohlcv
from features4 import build_features4
from features import to_xy

ROOT="/Users/daxu/software/world-trader"; OUT=os.path.join(ROOT,"tools/quant/reports")
HERE=os.path.dirname(os.path.abspath(__file__))
CACHE=os.path.join(HERE,"data","xgb4_pred_frame.parquet")
TRAIN_WIN=252*3; REFIT=63; COST=0.0006; START="2018-01-01"

def main():
    if not os.path.exists(CACHE):
        print("Building 93-feature XGB regression walk-forward...", flush=True)
        P=load_ohlcv(); close=P["close"]; feats=build_features4(P)
        ret_next=close.pct_change().shift(-1)
        X_full,y_full,rn,meta,names=to_xy(feats,ret_next)
        X_full=X_full.replace([np.inf,-np.inf],np.nan)
        dates=meta["date"].to_numpy(); tickers=meta["ticker"].to_numpy()
        ud=np.unique(dates); start=pd.Timestamp(START)
        pd_=ud[ud>=np.datetime64(start)]; refit=np.arange(0,len(pd_),REFIT)
        print(f"{len(refit)} refits | {len(names)} features", flush=True)
        pred=np.full(len(X_full),np.nan)
        for k,kk in enumerate(refit):
            if k%8==0: print(f"  [{k+1}/{len(refit)}] refit", flush=True)
            d=pd_[kk]; dmin=d-np.timedelta64(TRAIN_WIN,"D")
            tr=(dates<d)&(dates>=dmin)
            featok=np.isfinite(X_full.iloc[tr].to_numpy()).sum(axis=1)>0
            rok=np.isfinite(rn[tr]); tr_idx=np.where(tr)[0][featok & rok]
            np.random.seed(42); np.random.shuffle(tr_idx)
            nv=max(int(len(tr_idx)*0.1),1000); val,train=tr_idx[:nv],tr_idx[nv:]
            m=xgb.XGBRegressor(n_estimators=400,learning_rate=0.05,max_depth=6,
                min_child_weight=5,subsample=0.8,colsample_bytree=0.8,
                tree_method="hist",early_stopping_rounds=30,n_jobs=8,random_state=42)
            m.fit(X_full.iloc[train],rn[train],eval_set=[(X_full.iloc[val],rn[val])],verbose=False)
            d_end=pd_[kk+REFIT] if kk+REFIT<len(pd_) else pd_[-1]+np.timedelta64(1,"D")
            blk=(dates>=d)&(dates<d_end); Xb=X_full.iloc[blk]
            okb=np.isfinite(Xb.to_numpy()).sum(axis=1)>0
            pb=np.full(len(Xb),np.nan); pb[okb]=m.predict(Xb.iloc[okb]); pred[blk]=pb
        fr=pd.DataFrame({"date":dates,"ticker":tickers,"pred_ret":pred,"rn":rn})
        fr.to_parquet(CACHE); print("cached",CACHE,flush=True)
    fr=pd.read_parquet(CACHE); fr["date"]=pd.to_datetime(fr["date"])
    live=fr[fr["pred_ret"].notna()].dropna()
    print(f"\ntradeable: {len(live):,}\n",flush=True)
    res={}
    for q in [0.95,0.99,0.995,0.997]:
        cut=live["pred_ret"].quantile(q); d=live[live["pred_ret"]>=cut]
        if len(d)==0: continue
        net=d["rn"].to_numpy()-2*COST
        daily=pd.Series(net,index=d["date"]).groupby(level=0).mean().sort_index()
        years=max((daily.index.max()-daily.index.min()).days/365.25,1/252)
        apy=len(daily)/years
        sr=(daily.mean()/daily.std())*np.sqrt(apy) if daily.std()>0 else 0.0
        eq=(1+daily).cumprod(); ann=eq.iloc[-1]**(1/years)-1; dd=(eq/eq.cummax()-1).min()
        t,p=st.ttest_1samp(net,0)
        res[f"top{1-q:.3f}"]={"n":int(len(d)),"win5":float((d["rn"]>=0.05).mean()),
            "avg_net":float(net.mean()),"perT_SR":float(net.mean()/net.std()) if net.std()>0 else 0,
            "active_days":int(len(daily)),"active_per_year":round(float(apy),1),
            "active_SR":round(float(sr),3),"ann":round(float(ann),4),"maxdd":round(float(dd),4),
            "t":round(float(t),2),"p":round(float(p),3)}
        print(f"top {1-q:.1%}: n={len(d):5,} win5={(d['rn']>=0.05).mean():.1%} "
              f"net={net.mean():+.4%} actSR={sr:.2f} ann={ann:.1%} t={t:.2f} p={p:.3f}",flush=True)
    with open(os.path.join(OUT,"bigmove_xgb4_results.json"),"w") as f: json.dump(res,f,indent=2,default=str)
    print("saved ->",os.path.join(OUT,"bigmove_xgb4_results.json"),flush=True)

if __name__=="__main__": main()
