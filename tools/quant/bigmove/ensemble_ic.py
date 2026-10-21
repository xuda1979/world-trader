"""Ensemble XGB + LightGBM to raise IC -> higher honest Sharpe.
Same causal walk-forward (train strictly before pred block, 3y window, quarterly
refit) on the cached 93-feature matrix. Predicts raw next-day return.
Outputs per-model and averaged-ensemble predictions; computes honest (Lo-adj)
K=8 long-short Sharpe for each.
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DYLD_LIBRARY_PATH","/Users/daxu/homebrew/opt/libomp/lib:"+os.environ.get("DYLD_LIBRARY_PATH",""))
import numpy as np, pandas as pd, xgboost as xgb, lightgbm as lgb
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT="/Users/daxu/software/world-trader"; OUT=os.path.join(ROOT,"tools/quant/reports")
X=pd.read_parquet(os.path.join(HERE,"data","xgb_scaled_feats.parquet")).to_numpy()
meta=pd.read_parquet(os.path.join(HERE,"data","xgb_scaled_feats_meta.parquet"))
dates=pd.to_datetime(meta["date"].to_numpy()); rn=meta["rn"].to_numpy()
TRAIN_WIN=756; REFIT=63; START=pd.Timestamp("2018-01-01")
ud=np.unique(dates); pd_=ud[ud>=np.datetime64(START)]; refit=np.arange(0,len(pd_),REFIT)

def walk(algo):
    pred=np.full(len(X),np.nan)
    for kk in refit:
        d=pd_[kk]; dmin=d-np.timedelta64(TRAIN_WIN,"D")
        tr=(dates<d)&(dates>=dmin); featok=np.isfinite(X[tr]).sum(axis=1)>0; rok=np.isfinite(rn[tr])
        tr_idx=np.where(tr)[0][featok & rok]; np.random.seed(42); np.random.shuffle(tr_idx)
        nv=max(int(len(tr_idx)*0.1),1000); val,train=tr_idx[:nv],tr_idx[nv:]
        if algo=="xgb":
            m=xgb.XGBRegressor(n_estimators=400,learning_rate=0.05,max_depth=6,min_child_weight=5,
                subsample=0.8,colsample_bytree=0.8,tree_method="hist",early_stopping_rounds=30,
                n_jobs=8,random_state=42)
            m.fit(X[train],rn[train],eval_set=[(X[val],rn[val])],verbose=False)
        else:
            m=lgb.LGBMRegressor(n_estimators=400,learning_rate=0.05,num_leaves=31,min_child_samples=50,
                subsample=0.8,colsample_bytree=0.8,max_bin=255,verbose=-1,random_state=42)
            m.fit(X[train],rn[train],eval_set=[(X[val],rn[val])],callbacks=[lgb.early_stopping(30)],eval_metric="l2")
        pos=np.where(refit==kk)[0][0]; nxt=refit[pos+1] if pos+1<len(refit) else len(pd_)
        d_end=pd_[nxt] if nxt<len(pd_) else pd_[-1]+np.timedelta64(1,"D")
        blk=(dates>=d)&(dates<d_end); okb=np.isfinite(X[blk]).sum(axis=1)>0
        pb=np.full(len(X[blk]),np.nan); pb[okb]=m.predict(X[blk][okb]); pred[blk]=pb
        if kk==refit[0] or kk% (REFIT*8)==0: print(f"    [{algo}] refit@{np.datetime_as_string(d,unit='D')}",flush=True)
    return pred

def honest_ls(pred, K=8):
    live=np.isfinite(pred)&np.isfinite(rn)
    d=pd.DataFrame({"date":dates[live],"pred":pred[live],"rn":rn[live]})
    rows=[]
    for date,g in d.groupby("date"):
        g=g.sort_values("pred",ascending=False); n=len(g)
        if n<2*K: continue
        li=g.index[:K]; si=g.index[-K:]
        rows.append((date, g.loc[li,"rn"].mean()-2*0.0006-(g.loc[si,"rn"].mean()-2*0.0006)))
    s=pd.Series(dict(rows)).sort_index(); full=s.reindex(pd.date_range(s.index.min(),s.index.max(),freq="B")).fillna(0)
    # daily Pearson IC
    ic=d.groupby("date").apply(lambda g: g["pred"].corr(g["rn"]) if len(g)>20 else None,include_groups=False).dropna()
    return full, float(ic.mean())

def lo(r,maxlag):
    mu=r.mean(); sd=r.std()
    if sd==0 or np.isnan(sd): return 0.0
    q=1.0
    for k in range(1,maxlag+1):
        rho=r.autocorr(k)
        if np.isnan(rho): break
        q+=2*(1-k/(maxlag+1))*rho
    return mu/sd*np.sqrt(252)/np.sqrt(max(q,1e-9))

if __name__=="__main__":
    res={}
    for algo in ["xgb","lgbm"]:
        print(f">>> running {algo} walk-forward...",flush=True)
        p=walk(algo)
        np.save(os.path.join(HERE,"data",f"pred_{algo}.npy"),p)
        full, ic = honest_ls(p)
        lo_v = lo(full.rolling(10).mean(),9)
        res[algo]={"ic":round(ic,5),"perday_lo_sr":round(lo(full,10),3),"overlap10_lo_sr":round(lo_v,3)}
        print(f"    {algo}: IC={ic:.5f} perday Lo-SR={res[algo]['perday_lo_sr']} overlap10 Lo-SR={lo_v:.3f}",flush=True)
    px=np.load(os.path.join(HERE,"data","pred_xgb.npy")); pl=np.load(os.path.join(HERE,"data","pred_lgbm.npy"))
    # rank-average ensemble (robust to scale)
    m=pd.MultiIndex.from_arrays([pd.to_datetime(meta["date"]),meta["ticker"]])
    da=pd.DataFrame({"x":px,"l":pl},index=m)
    def rank_norm(seq):
        s=pd.Series(seq)
        ok=s.notna()
        out=s.copy(); out[ok]=s[ok].rank(pct=True)
        return out.to_numpy()
    rx=rank_norm(px); rl=rank_norm(pl)
    ens=0.5*rx+0.5*rl
    full,ic=honest_ls(ens)
    res["ens"]={"ic":round(ic,5),"perday_lo_sr":round(lo(full,10),3),"overlap10_lo_sr":round(lo(full.rolling(10).mean(),9),3)}
    print(f"    ENSEMBLE: IC={ic:.5f} perday Lo-SR={res['ens']['perday_lo_sr']} overlap10 Lo-SR={res['ens']['overlap10_lo_sr']}",flush=True)
    json.dump(res,open(os.path.join(OUT,"bigmove_ensemble_ic.json"),"w"),indent=2)
    print("saved bigmove_ensemble_ic.json")
