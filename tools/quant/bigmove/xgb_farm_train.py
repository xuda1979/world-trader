"""Parametrized 21-day XGB walk-forward trainer for the decorrelated engine farm.

Generates ONE decorrelated h21 prediction book per call. Variation knobs:
  - SEED      : model random_state (fresh noise -> decorrelated trees)
  - FEAT_SET  : comma-separated feature-name substrings to KEEP (subsetting the
                141 causal features -> faster + semantically-differentiated models)
  - NJOBS     : xgb threads (leave headroom for siblings)
  - TRAIN_WIN / REFIT : walk-forward schedule (defaults 3y / quarterly)
Saves preds to HZ_PRED_CACHE as pickle {frame, preds:{21:...}}.
Usage:
  HZ_PRED_CACHE=/tmp/cache_seedX.pkl SEED=X FEAT_SET=mom,vol NJOBS=4 python3 xgb_farm_train.py
"""
import os, sys, time, pickle
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, pandas as pd, xgboost as xgb
from pipeline_common import load_ohlcv
from features6 import build_features6
from features import to_xy

ROOT = "/Users/daxu/software/world-trader"
PRED_CACHE = os.environ.get("HZ_PRED_CACHE",
                 os.path.join(HERE,"data","farm_cache.pkl"))
SEED = int(os.environ.get("SEED", 42))
FEAT_SET = os.environ.get("FEAT_SET", "").lower()
NJOBS = int(os.environ.get("NJOBS", 4))
TRAIN_WIN = int(os.environ.get("TRAIN_WIN", 252*3))
REFIT = int(os.environ.get("REFIT", 63))
START = os.environ.get("HZ_START", "2008-09-01")
H = 21

def build_frame():
    P = load_ohlcv(); close = P["close"]
    feats = build_features6(P)   # 141 causal features
    ret_next = close.pct_change().shift(-1)
    X_full, _, _, meta, names = to_xy(feats, ret_next)
    X_full = X_full.replace([np.inf,-np.inf], np.nan)
    if FEAT_SET:
        subs = [c for c in X_full.columns if FEAT_SET in str(c).lower()]
        if subs:
            X_full = X_full[subs]
    dates = pd.to_datetime(meta["date"].to_numpy()); tickers = meta["ticker"].to_numpy()
    frame = pd.DataFrame({"date": dates, "ticker": tickers}).set_index(["date","ticker"])
    close_long = close.stack().rename("close"); close_long.index.names=["date","ticker"]
    base = close_long.reindex(frame.index); frame["close"] = base.to_numpy()
    fut = close.shift(-H).stack().rename(f"ret_{H}"); fut.index.names=["date","ticker"]
    r = fut.reindex(frame.index)/base - 1.0
    frame[f"ret_{H}"] = r.to_numpy()
    frame = frame.reset_index()
    return X_full, frame

def walkforward_predict(X_full, frame):
    dates = frame["date"].to_numpy(); tickers = frame["ticker"].to_numpy()
    ud = np.unique(dates); pd_ = ud[ud >= np.datetime64(pd.Timestamp(START))]
    refit = np.arange(0, len(pd_), REFIT)
    print(f"OOS {pd.Timestamp(pd_[0]).date()}..{pd.Timestamp(pd_[-1]).date()} "
          f"| {len(refit)} refits | {X_full.shape[1]} feats | seed {SEED}", flush=True)
    Xn = X_full.to_numpy(); fin = np.isfinite(Xn)
    pred = np.full(len(frame), np.nan)
    retc = frame[f"ret_{H}"].to_numpy()
    t0=time.time()
    for k, kk in enumerate(refit):
        if k % 6 == 0:
            print(f"  refit {k+1}/{len(refit)} @ {pd.Timestamp(pd_[kk]).date()} ({time.time()-t0:.0f}s)", flush=True)
        d = pd_[kk]; dmin = d - np.timedelta64(TRAIN_WIN,"D")
        tr = (dates < d) & (dates >= dmin) & (dates < d - np.timedelta64(H, "D"))
        tr_idx = np.where(tr)[0]; fok = fin[tr_idx].sum(axis=1)>0; tr_idx=tr_idx[fok]
        np.random.seed(SEED+np.random.randint(0,1000)); np.random.shuffle(tr_idx)
        nv = max(int(len(tr_idx)*0.1),1000); nv=min(nv,len(tr_idx)//4)
        val_idx, tr2 = tr_idx[:nv], tr_idx[nv:]
        ytr = retc[tr2]; yv = retc[val_idx]
        ok_t = np.isfinite(ytr); ok_v = np.isfinite(yv)
        if ok_t.sum()<500 or ok_v.sum()<200: continue
        d_end = pd_[kk+REFIT] if kk+REFIT<len(pd_) else pd_[-1]+np.timedelta64(1,"D")
        blk_idx = np.where((dates>=d)&(dates<d_end))[0]; bob = fin[blk_idx].sum(axis=1)>0
        bb = blk_idx[bob]
        if len(bb)==0: continue
        m = xgb.XGBRegressor(n_estimators=500, learning_rate=0.05, max_depth=5,
            min_child_weight=8, subsample=0.8, colsample_bytree=0.8,
            tree_method="hist", early_stopping_rounds=40, n_jobs=NJOBS,
            random_state=SEED, objective="reg:squarederror", eval_metric="rmse")
        m.fit(Xn[tr2][ok_t], ytr[ok_t], eval_set=[(Xn[val_idx][ok_v], yv[ok_v])], verbose=False)
        pb = np.full(len(blk_idx), np.nan); pb[bob]=m.predict(Xn[bb])
        pred[blk_idx]=pb
    return pred

def main():
    print(f"Building frame feat_subset='{FEAT_SET}' seed={SEED}...", flush=True)
    X_full, frame = build_frame()
    print(f"frame {frame.shape} | X {X_full.shape}", flush=True)
    pred = walkforward_predict(X_full, frame)
    os.makedirs(os.path.dirname(PRED_CACHE) or ".", exist_ok=True)
    with open(PRED_CACHE,"wb") as fh: pickle.dump({"frame":frame,"preds":{H:pred}},fh)
    print(f"cached -> {PRED_CACHE}", flush=True)

if __name__=="__main__":
    main()
