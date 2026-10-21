"""Scaled-up XGBoost regression walk-forward on the EXPANDED 304-asset universe
(294 US large/mid + 11 non-correlated: BTC, ETH, FX, commodities).
Same 93-feature macro pipeline, no-look-ahead. Compare active-days + Sharpe vs
the 285-stock baseline to test the "scale up for higher return/Sharpe" hypothesis.
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DYLD_LIBRARY_PATH","/Users/daxu/homebrew/opt/libomp/lib:"+os.environ.get("DYLD_LIBRARY_PATH",""))
import numpy as np, pandas as pd, xgboost as xgb
from scipy import stats
from universe_expand import build_panel
from features4 import build_features4
from features import to_xy

ROOT="/Users/daxu/software/world-trader"; OUT=os.path.join(ROOT,"tools/quant/reports")
HERE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(HERE,"data","xgb_scaled_pred.parquet")
TRAIN_WIN=252*3; REFIT=63; COST=0.0006; START="2018-01-01"

def main():
    if not os.path.exists(CACHE):
        print("Building scaled walk-forward on expanded universe...",flush=True)
        P=build_panel()[0]; close=P["close"]
        feats=build_features4(P,close)
        ret_next=close.pct_change().shift(-1)
        X_full,y_full,rn,meta,names=to_xy(feats,ret_next)
        X_full=X_full.replace([np.inf,-np.inf],np.nan)
        dates=meta["date"].to_numpy(); tickers=meta["ticker"].to_numpy()
        ud=np.unique(dates); start=pd.Timestamp(START)
        pd_=ud[ud>=np.datetime64(start)]; refit=np.arange(0,len(pd_),REFIT)
        nvalid=(np.isfinite(rn)).sum()
        print(f"universe={close.shape[1]} | {len(names)} feats | {len(X_full):,} rows | {len(refit)} refits | valid-ptgt {nvalid:,}",flush=True)
        pred=np.full(len(X_full),np.nan)
        for k,kk in enumerate(refit):
            if k%6==0: print(f"  [{k+1}/{len(refit)}]",flush=True)
            d=pd_[kk]; dmin=d-np.timedelta64(TRAIN_WIN,"D")
            tr=(dates<d)&(dates>=dmin); featok=np.isfinite(X_full.iloc[tr].to_numpy()).sum(axis=1)>0
            rok=np.isfinite(rn[tr]); tr_idx=np.where(tr)[0][featok & rok]
            np.random.seed(42); np.random.shuffle(tr_idx)
            nv=max(int(len(tr_idx)*0.1),1000); val,train=tr_idx[:nv],tr_idx[nv:]
            m=xgb.XGBRegressor(n_estimators=400,learning_rate=0.05,max_depth=6,min_child_weight=5,
                subsample=0.8,colsample_bytree=0.8,tree_method="hist",early_stopping_rounds=30,n_jobs=8,random_state=42)
            m.fit(X_full.iloc[train],rn[train],eval_set=[(X_full.iloc[val],rn[val])],verbose=False)
            d_end=pd_[kk+REFIT] if kk+REFIT<len(pd_) else pd_[-1]+np.timedelta64(1,"D")
            blk=(dates>=d)&(dates<d_end); Xb=X_full.iloc[blk]; okb=np.isfinite(Xb.to_numpy()).sum(axis=1)>0
            pb=np.full(len(Xb),np.nan); pb[okb]=m.predict(Xb.iloc[okb]); pred[blk]=pb
        fr=pd.DataFrame({"date":dates,"ticker":tickers,"pred_ret":pred,"rn":rn})
        fr.to_parquet(CACHE); print("cached",CACHE,flush=True)
    fr=pd.read_parquet(CACHE); fr["date"]=pd.to_datetime(fr["date"])
    live=fr[fr["pred_ret"].notna()].dropna()
    print(f"\ntradeable: {len(live):,}\n",flush=True)
    res={}
    for q in [0.97,0.99,0.995]:
        d=live[live["pred_ret"]>=live["pred_ret"].quantile(q)]
        if len(d)==0: continue
        net=d["rn"].to_numpy()-2*COST
        daily=pd.Series(net,index=d["date"]).groupby(level=0).mean().sort_index()
        years=max((daily.index.max()-daily.index.min()).days/365.25,1/252); apy=len(daily)/years
        sr=(daily.mean()/daily.std())*np.sqrt(apy) if daily.std()>0 else 0.0
        eq=(1+daily).cumprod(); ann=eq.iloc[-1]**(1/years)-1; dd=(eq/eq.cummax()-1).min()
        t,p=stats.ttest_1samp(net,0)
        m2=pd.Series(net,index=d["date"]); ci=block_ci(net,d["date"])
        res[f"top{1-q:.3f}"]={"n":int(len(d)),"win5":float((d["rn"]>=0.05).mean()),
            "avg_net":float(net.mean()),"active_days":int(len(daily)),"active_per_year":round(float(apy),1),
            "active_SR":round(float(sr),3),"ann":round(float(ann),4),"maxdd":round(float(dd),4),
            "unique_days":int(d["date"].nunique()),"t":round(float(t),2),"p":round(float(p),3),"blockCI":list(np.round(ci,4))}
        print(f"top {1-q:.1%}: n={len(d):6,} win5={((d['rn']>=0.05).mean()):.1%} net={net.mean():+.4%} "
              f"actSR={sr:.2f} ann={ann:.1%} uniq_days={d['date'].nunique()} t={t:.2f} p={p:.3f} blockCI=[{ci[0]:+.4f},{ci[1]:+.4f}]",flush=True)
    with open(os.path.join(OUT,"bigmove_scaled_results.json"),"w") as f: json.dump(res,f,indent=2,default=str)
    print("saved ->",os.path.join(OUT,"bigmove_scaled_results.json"),flush=True)

def block_ci(net,dates,blk=10):
    s=pd.Series(net,index=dates); daily=s.groupby(level=0).mean(); arr=daily.to_numpy(); di=len(arr)
    rng=np.random.default_rng(0); nb=di//blk
    samp=np.array([arr[rng.integers(0,di-blk,size=nb)[:,None]+np.arange(blk)[None,:]].ravel().mean() for _ in range(2000)])
    return np.percentile(samp,[2.5,97.5])

if __name__=="__main__": main()
