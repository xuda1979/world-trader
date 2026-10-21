"""B4 idea1: NEW long-horizon XGB L/S book (H=42) using full feature6 set.
Causal T+1, 6bps/side, honest hold-H overlapping book, walk-forward refit.
Decorrelated from h21 champion via different target horizon & holding period.
"""
from __future__ import annotations
import os, sys, pickle, time
import numpy as np, pandas as pd
import xgboost as xgb

BIGMOVE="/Users/daxu/software/world-trader/tools/quant/bigmove"
sys.path.insert(0, BIGMOVE)
from xgb_horizon_portfolio import build_position_book, vol_target, stats
from xgb_multi_horizon import XGB_PARAMS

FRAME_CACHE="/tmp/featframe_full.pkl"
TRAIN_WIN=int(os.environ.get("TRAIN_WIN",252*3))
REFIT=int(os.environ.get("REFIT",63))
H=int(os.environ.get("HZ_H",42))
START=pd.Timestamp(os.environ.get("HZ_START","2014-01-01"))
K=int(os.environ.get("HZ_K",10))

def main():
    c=pickle.load(open(FRAME_CACHE,"rb")); frame,X,names=c["frame"],c["X"],c["names"]
    close=frame.groupby("ticker")["close"].transform(lambda s:s)
    # rebuild full close panel for forward returns
    fc=frame.copy(); dates=pd.to_datetime(fc["date"]); tk=fc["ticker"]
    close_p = fc.pivot(index="date",columns="ticker",values="close")
    fut=close_p.shift(-H)/close_p-1.0
    r=fut.stack()
    r.index.names=["date","ticker"]
    fc["retH"]=r.reindex(pd.MultiIndex.from_arrays([dates,tk])).to_numpy()
    Xn=X.to_numpy(); fin=np.isfinite(Xn)
    retH=fc["retH"].to_numpy()
    ud=np.array(sorted(np.unique(dates)))
    pd_=ud[ud>=np.datetime64(START)]
    refit=np.arange(0,len(pd_),REFIT)
    preds=np.full(len(fc),np.nan)
    max_h=H
    for k,kk in enumerate(refit):
        d=pd_[kk]; dmin=d-np.timedelta64(TRAIN_WIN,"D")
        tr=(dates.values<d)&(dates.values>=dmin)&(dates.values<d-np.timedelta64(max_h,"D"))
        tr_idx=np.where(tr)[0]
        fok=fin[tr_idx].sum(axis=1)>0; tr_idx=tr_idx[fok]
        np.random.seed(42); np.random.shuffle(tr_idx)
        nv=max(int(len(tr_idx)*0.1),1000); nv=min(nv,len(tr_idx)//4)
        val_idx,tr2=tr_idx[:nv],tr_idx[nv:]
        d_end=pd_[kk+REFIT] if kk+REFIT<len(pd_) else pd_[-1]+np.timedelta64(1,"D")
        blk=(dates.values>=d)&(dates.values<d_end)
        blk_idx=np.where(blk)[0]; bob=fin[blk_idx].sum(axis=1)>0; bb=blk_idx[bob]
        if len(bb)==0: continue
        ytr=retH[tr2]; yv=retH[val_idx]
        ok_t=np.isfinite(ytr); ok_v=np.isfinite(yv)
        if ok_t.sum()<500 or ok_v.sum()<200: continue
        m=xgb.XGBRegressor(**XGB_PARAMS())
        m.fit(Xn[tr2][ok_t],ytr[ok_t],eval_set=[(Xn[val_idx][ok_v],yv[ok_v])],verbose=False)
        pb=np.full(len(blk_idx),np.nan); pb[bob]=m.predict(Xn[bb])
        preds[blk_idx]=pb
    fw=fc.copy(); fw["pred"]=preds
    fw=fw[np.isfinite(fw["pred"])]
    res=build_position_book(fw,fw["pred"].to_numpy(),H,K=K,cost=0.0006).sort_index()
    rvt=vol_target(res.copy())
    print(f"H={H} K={K} RAW:",stats(res))
    print(f"H={H} K={K} VOLTARGET:",stats(rvt))
    pickle.dump({"frame":fw,"res":res,"rvt":rvt},open(f"/tmp/b4_h{H}.pkl","wb"))
    rvt.to_frame("ret").to_csv(f"/tmp/b4_h{H}_book.csv")
    print("saved /tmp/b4_h%d_book.csv"%H)
if __name__=="__main__": main()
