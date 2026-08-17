"""GKX-style purged walk-forward ML + decile L/S backtest.

Monthly OOS: for prediction month m (predict return in m+1), train on months
<= m-1 (PURGED: no label overlap), rolling 7y window, refit yearly.
Models: Ridge (standardized), XGBoost GBRT, MLP (3-layer, GKX-style).
Portfolio: long top decile / short bottom decile, EW and market-cap-weighted,
gross AND net (6bp/side full cycle = 24bp/mo). Reports OOS SR per model.
"""
from __future__ import annotations
import os, sys, json, time
import numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
os.environ.setdefault("DYLD_LIBRARY_PATH","/Users/daxu/homebrew/opt/libomp/lib:"+os.environ.get("DYLD_LIBRARY_PATH",""))
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
import xgboost as xgb

TRAIN_MONTHS=84   # 7y
START="2009-01-01"
COST=0.0006

def load_panel():
    df=pd.read_parquet(f"{HERE}/data/gkx_monthly_panel.parquet")
    df["month"]=pd.to_datetime(df["month"])
    names=json.load(open(f"{HERE}/data/gkx_names.json"))
    return df,names

def run_model(df,names,model_fn,label):
    df=df.dropna(subset=["ret_next"]).copy()
    X=df[names].replace([np.inf,-np.inf],np.nan)
    months=np.sort(df["month"].unique())
    ud=months[months>=pd.Timestamp(START)]
    refits=np.arange(0,len(ud),12)  # yearly refit
    pred=np.full(len(df),np.nan); t0=time.time()
    for k,kk in enumerate(refits):
        if k%6==0: print(f"  [{label}] refit {k+1}/{len(refits)} @ {pd.Timestamp(ud[kk]).date()} ({time.time()-t0:.0f}s)",flush=True)
        m=ud[kk]
        tr=(df["month"]<=m-pd.DateOffset(months=1)) & (df["month"]>m-pd.DateOffset(months=TRAIN_MONTHS+1))
        tr_idx=np.where(tr)[0]
        Xtr=X.iloc[tr_idx].to_numpy(); ytr=df["ret_next"].iloc[tr_idx].to_numpy()
        ok=np.isfinite(Xtr).sum(axis=1)>0
        Xtr,ytr=Xtr[ok],ytr[ok]
        ok2=np.isfinite(ytr); Xtr,ytr=Xtr[ok2],ytr[ok2]
        if len(Xtr)<2000: continue
        # impute NaN with TRAIN column medians (causal), applied to train & predict
        meds=np.nanmedian(Xtr,axis=0); meds=np.where(np.isnan(meds),0.0,meds)
        Xtr=np.where(np.isnan(Xtr),meds,Xtr)
        model=model_fn()
        model.fit(Xtr,ytr)
        # predict months m .. m+11
        blk=(df["month"]>m) & (df["month"]<=m+pd.DateOffset(months=12))
        bi=np.where(blk)[0]
        Xb=X.iloc[bi].to_numpy(); Xb=np.where(np.isnan(Xb),meds,Xb)
        bok=np.isfinite(Xb).sum(axis=1)>0
        p=np.full(len(bi),np.nan)
        if bok.sum()>0: p[bok]=model.predict(Xb[bok])
        pred[bi]=p
    df["pred"]=pred
    return df

def decile_ls(df,weight_col=None,cost=COST):
    """Monthly decile L/S. weight_col: None=EW, or 'log_mcap'-weighted long leg."""
    rows=[]
    for m,g in df.groupby("month"):
        g=g.dropna(subset=["pred","ret_next"])
        n=len(g)
        if n<40: continue
        g=g.sort_values("pred",ascending=False)
        nq=max(int(n*0.1),5)
        longs=g.iloc[:nq]; shorts=g.iloc[-nq:]
        lw=1.0/nq if weight_col is None else (longs[weight_col]/longs[weight_col].sum())
        sw=1.0/nq
        lg=(longs["ret_next"]*lw).sum(); sg=(shorts["ret_next"]*sw).sum()
        # full-cycle cost: 6bp/side x 4 (open+close, both legs) on unit equity
        rows.append((m,lg-sg-4*cost))
    s=pd.Series(dict(rows)).sort_index()
    return s

def stats(s):
    s=s.dropna()
    if len(s)<12 or s.std()==0: return None
    eq=(1+s).cumprod(); sr=s.mean()/s.std()*np.sqrt(12)
    ann=(1+s).prod()**(12/len(s))-1; dd=(eq/eq.cummax()-1).min()
    return {"sr":round(float(sr),2),"ann":round(float(ann),4),"dd":round(float(dd),4),
            "n":int(len(s)),"win":round(float((s>0).mean()),3)}

def main():
    df,names=load_panel()
    print(f"panel {df.shape} | {len(names)} chars | months {df['month'].min().date()}..{df['month'].max().date()}",flush=True)
    results={}
    models={
        "ridge": lambda: Ridge(alpha=10),
        "xgb": lambda: xgb.XGBRegressor(n_estimators=300,learning_rate=0.05,max_depth=4,
                min_child_weight=10,subsample=0.8,colsample_bytree=0.8,tree_method="hist",
                n_jobs=8,random_state=42),
        "mlp": lambda: MLPRegressor(hidden_layer_sizes=(32,16,8),activation="relu",
                alpha=1e-3,max_iter=200,random_state=42),
    }
    for label,fn in models.items():
        print(f"\n=== {label} ===",flush=True)
        dfp=run_model(df,names,fn,label)
        for wname,wcol in [("EW",None),("VW",None if False else "log_mcap")]:
            s_gross=decile_ls(dfp,weight_col=wcol,cost=0)
            s_net=decile_ls(dfp,weight_col=wcol,cost=COST)
            if wcol=="log_mcap":
                # value-weight the long leg only (GKX VW), short EW
                pass
            print(f"  {wname} gross: {stats(s_gross)}")
            print(f"  {wname} net24:  {stats(s_net)}")
            results[f"{label}_{wname}"]={"gross":stats(s_gross),"net":stats(s_net)}
        # save preds for this model
        dfp.to_parquet(f"{HERE}/data/gkx_preds_{label}.parquet")
    json.dump(results,open(f"{HERE}/../reports/xgb_horizons/gkx_results.json","w"),indent=1,default=str)
    print("\nsaved gkx_results.json")

if __name__=="__main__":
    main()
