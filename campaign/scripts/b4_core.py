"""B4 core: parameterized new XGB L/S book. Causal T+1, 6bps/side, honest
hold-H overlapping book, walk-forward refit. Variance via feature subset +
horizon + K. Decorrelates from champion h21 (full features) by using pure-price
feature subsets and/or different horizons.
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

PURE_PRICE = ['absret_ma10','absret_ma5','amihud','autocorr_20','beta_60',
 'big_norm_vol','bigret_prev1','bigup_prev1','bigup_prev5','close_pos',
 'close_vs_hi20','dist_hi252','dist_hi5','dist_lo252','dist_lo5','dist_ma20',
 'dist_ma200','dist_ma5','dist_ma60','down_vol_ratio','gap','histbig_freq_250',
 'histbig_freq_60','kurt_20','logvol','mom_1','mom_2','mom_3','mom_5','mom_10',
 'mom_20','mom_60','mom_120','normmom_1','normmom_3','normmom_5','normmom_10',
 'range_pct','range_pct_ma10','rank_mom_20','rank_mom_60','rel_mom_5','rel_mom_20',
 'rel_ret_1','ret_x_volratio','rsi_14','rvol_5','rvol_10','rvol_20','rvol_60',
 'sharpe_5','sharpe_20','skew_20','trend_250','up_streak','vol_of_vol',
 'vol_ratio_5','vol_ratio_20','vol_ratio_60','vol_trend_20_60','vol_z']

EXCLUDE_WORDS = ['mkt_','ff_','xs_','btc_','eurusd','fx_','wti','natgas','xau',
                 'slv_','copx','dxy','ch10y','gb10y','jp10y','ez10y','au10y',
                 'ca10y','us30y','tbill3m','baa_aaa','vix_','month_','earn_']

def filter_feats(names, mode):
    if mode=="pure_price":
        return [n for n in names if n in PURE_PRICE]
    if mode=="no_tiled":  # exclude all tiled market-wide (still FF/mkt regressors)
        return [n for n in names if not any(w in n for w in EXCLUDE_WORDS)]
    return list(names)

def _getparams(H):
    p=dict(XGB_PARAMS())
    dp=os.environ.get("HZ_DEPTH")
    if dp: p["max_depth"]=int(dp)
    lr=os.environ.get("HZ_LR")
    if lr: p["learning_rate"]=float(lr)
    ne=os.environ.get("HZ_NE")
    if ne: p["n_estimators"]=int(ne)
    return p

def run(H, mode, K, vol_target_ann=0.13):
    c=pickle.load(open(FRAME_CACHE,"rb")); frame,X,names=c["frame"],c["X"],c["names"]
    sel=filter_feats2(names,mode)
    idx=[names.index(s) for s in sel]
    Xs=X.iloc[:,idx]; names_s=sel
    fc=frame.copy(); dates=pd.to_datetime(fc["date"]); tk=fc["ticker"]
    close_p=fc.pivot(index="date",columns="ticker",values="close")
    fut=close_p.shift(-H)/close_p-1.0
    r=fut.stack(); r.index.names=["date","ticker"]
    fc["retH"]=r.reindex(pd.MultiIndex.from_arrays([dates.values,tk])).to_numpy()
    Xn=Xs.to_numpy().astype(float); fin=np.isfinite(Xn)
    retH=fc["retH"].to_numpy()
    TRAIN_WIN=int(os.environ.get("TRAIN_WIN",252*3))
    REFIT=int(os.environ.get("REFIT",63))
    START=pd.Timestamp(os.environ.get("HZ_START","2014-01-01"))
    ud=np.array(sorted(np.unique(dates.values)))
    pd_=ud[ud>=np.datetime64(START)]
    refit=np.arange(0,len(pd_),REFIT)
    preds=np.full(len(fc),np.nan); max_h=H
    t0=time.time()
    for k,kk in enumerate(refit):
        d=pd_[kk]; dmin=d-np.timedelta64(TRAIN_WIN,"D")
        tr=(dates.values<d)&(dates.values>=dmin)&(dates.values<d-np.timedelta64(max_h,"D"))
        tr_idx=np.where(tr)[0]; fok=fin[tr_idx].sum(axis=1)>0; tr_idx=tr_idx[fok]
        np.random.seed(42); np.random.shuffle(tr_idx)
        nv=max(int(len(tr_idx)*0.1),1000); nv=min(nv,len(tr_idx)//4)
        val_idx,tr2=tr_idx[:nv],tr_idx[nv:]
        d_end=pd_[kk+REFIT] if kk+REFIT<len(pd_) else pd_[-1]+np.timedelta64(1,"D")
        blk=(dates.values>=d)&(dates.values<d_end); blk_idx=np.where(blk)[0]
        bob=fin[blk_idx].sum(axis=1)>0; bb=blk_idx[bob]
        if len(bb)==0: continue
        ytr=retH[tr2]; yv=retH[val_idx]
        ok_t=np.isfinite(ytr); ok_v=np.isfinite(yv)
        if ok_t.sum()<500 or ok_v.sum()<200: continue
        m=xgb.XGBRegressor(**_getparams(H))
        m.fit(Xn[tr2][ok_t],ytr[ok_t],eval_set=[(Xn[val_idx][ok_v],yv[ok_v])],verbose=False)
        pb=np.full(len(blk_idx),np.nan); pb[bob]=m.predict(Xn[bb]); preds[blk_idx]=pb
    fw=fc.copy(); fw["pred"]=preds; fw=fw[np.isfinite(fw["pred"])]
    res=build_position_book(fw,fw["pred"].to_numpy(),H,K=K,cost=0.0006).sort_index()
    rvt=vol_target(res.copy(), ann_target=vol_target_ann)
    print(f"mode={mode} H={H} K={K} nfeat={len(sel)} RAW:",stats(res),flush=True)
    print(f"mode={mode} H={H} K={K} VT:",stats(rvt),"time %.0fs"%(time.time()-t0),flush=True)
    name=f"b4_{mode}_h{H}_k{K}"
    pickle.dump({"frame":fw,"res":res,"rvt":rvt},open(f"/tmp/{name}.pkl","wb"))
    rvt.to_frame("ret").to_csv(f"/tmp/{name}_book.csv")
    return name

def filter_feats2(names, mode):
    if mode=="core_econ":
        drop=['btc_','eurusd','fx_','wti','natgas','xau_','slv_','copx','dxy','dxy_']
        keep=[n for n in names if not any(w in n for w in drop)]
        return keep
    return filter_feats(names, mode)

if __name__=="__main__":
    H=int(os.environ.get("HZ_H",21)); mode=os.environ.get("HZ_MODE","pure_price")
    K=int(os.environ.get("HZ_K",10))
    run(H,mode,K)
