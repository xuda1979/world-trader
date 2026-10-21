"""XGBoost walk-forward for next-day >=5% prediction with EXOGENOUS signals.

Trains XGBClassifier (P(next-day >=5%)) walk-forward (quarterly refit, 3y window)
using 70 features (per-stock + market/regime + cross-sectional + FF + crypto/FX).
Caches OOS predictions. Emits per-trade edge stats + calendar-time Sharpe.

Also trains an XGBRegressor for next-day return magnitude as a secondary signal.
No look-ahead.
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DYLD_LIBRARY_PATH",
                      "/Users/daxu/homebrew/opt/libomp/lib:" + os.environ.get("DYLD_LIBRARY_PATH",""))
import numpy as np
import pandas as pd
import xgboost as xgb

from pipeline_common import load_ohlcv
from features3 import build_features3
from features import to_xy

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports")
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "xgb_pred_frame.parquet")
os.makedirs(os.path.dirname(CACHE), exist_ok=True)
os.makedirs(OUT, exist_ok=True)

TRAIN_WIN = 252*3; REFIT = 63; COST = 0.0006
START = "2018-01-01"; TRADING_DAYS = 252


def XGB_PARAMS(cls):
    d = dict(n_estimators=400, learning_rate=0.05, max_depth=6, min_child_weight=5,
             subsample=0.8, colsample_bytree=0.8,
             tree_method="hist", early_stopping_rounds=30, n_jobs=8, random_state=42)
    if cls:
        d["objective"] = "binary:logistic"
        d["scale_pos_weight"] = 1.0   # we'll rely on class_weight-like via sample? use balanced-ish
        d["eval_metric"] = "auc"
    else:
        d["objective"] = "reg:squarederror"
        d["eval_metric"] = "rmse"
    return d


def stats_calendar(daily):
    if daily.std() == 0: return 0.0, 0.0, 0.0
    s = (daily.mean()/daily.std())*np.sqrt(TRADING_DAYS)
    ann = (1+daily).prod()**(TRADING_DAYS/len(daily))-1
    eq = (1+daily).cumprod(); dd = (eq/eq.cummax()-1).min()
    return s, ann, dd


def get_frame(force=False):
    if os.path.exists(CACHE) and not force:
        return pd.read_parquet(CACHE)
    print("Building 70-feature XGB walk-forward...", flush=True)
    P = load_ohlcv(); close = P["close"]
    feats = build_features3(P)
    ret_next = close.pct_change().shift(-1)
    X_full, y_full, rn, meta, names = to_xy(feats, ret_next)
    X_full = X_full.replace([np.inf,-np.inf],np.nan)
    dates = meta["date"].to_numpy(); tickers = meta["ticker"].to_numpy()
    ud = np.unique(dates); start = pd.Timestamp(START)
    pd_ = ud[ud>=np.datetime64(start)]; refit = np.arange(0,len(pd_),REFIT)
    if os.environ.get("BIGMOVE_QUICK"):
        refit = refit[:4]   # ~1 quarter of predictions for validation
    print(f"OOS {pd.Timestamp(pd_[0]).date()}..{pd.Timestamp(pd_[-1]).date()} | "
          f"{len(refit)} refits | {len(feats)} features", flush=True)
    prob = np.full(len(X_full), np.nan)
    pred_reg = np.full(len(X_full), np.nan)
    for k,kk in enumerate(refit):
        if k%8==0: print(f"  [{k+1}/{len(refit)}] refit @ {pd.Timestamp(pd_[kk]).date()}", flush=True)
        d = pd_[kk]; dmin = d - np.timedelta64(TRAIN_WIN,"D")
        tr = (dates<d)&(dates>=dmin)
        ok = np.isfinite(X_full.iloc[tr].to_numpy()).sum(axis=1)>0
        # split within-train for early stopping (keep time order: last 10% = val)
        tr_idx = np.where(tr)[0]
        # keep rows with finite features AND finite labels for both tasks
        feat_ok = np.isfinite(X_full.iloc[tr_idx].to_numpy()).sum(axis=1) > 0
        cls_ok = np.isfinite(y_full[tr_idx])
        reg_ok = np.isfinite(rn[tr_idx])
        tr_idx = tr_idx[feat_ok & cls_ok & reg_ok]
        np.random.seed(42); np.random.shuffle(tr_idx)
        nv = max(int(len(tr_idx)*0.1), 1000)
        val_idx, tr_idx2 = tr_idx[:nv], tr_idx[nv:]
        Xtr2, ytr2 = X_full.iloc[tr_idx2], y_full[tr_idx2].astype(int)
        Xv2, yv2 = X_full.iloc[val_idx], y_full[val_idx].astype(int)
        # classifier
        c = xgb.XGBClassifier(**XGB_PARAMS(True))
        cp = ytr2.mean(); c.set_params(scale_pos_weight=(1-cp)/max(cp,1e-6))
        c.fit(Xtr2, ytr2, eval_set=[(Xv2,yv2)], verbose=False)
        # regression (target = raw next-day return, finite by construction)
        r = xgb.XGBRegressor(**XGB_PARAMS(False))
        r.fit(Xtr2, rn[tr_idx2],
              eval_set=[(Xv2, rn[val_idx])], verbose=False)
        d_end = pd_[kk+REFIT] if kk+REFIT<len(pd_) else pd_[-1]+np.timedelta64(1,"D")
        blk = (dates>=d)&(dates<d_end); Xb = X_full.iloc[blk]
        okb = np.isfinite(Xb.to_numpy()).sum(axis=1)>0
        pb = np.full(len(Xb),np.nan); pr = np.full(len(Xb),np.nan)
        if okb.sum()>0:
            pb[okb] = c.predict_proba(Xb.iloc[okb])[:,1]
            pr[okb] = r.predict(Xb.iloc[okb])
        prob[blk] = pb; pred_reg[blk] = pr

    mi = pd.MultiIndex.from_arrays([dates,tickers],names=["date","ticker"])
    def v(df,sh=0): return df.shift(sh).stack().reindex(mi).to_numpy()
    frame = pd.DataFrame({"date":dates,"ticker":tickers,"prob":prob,"pred_ret":pred_reg,
                          "entry":v(close),"next_close":v(close,-1)})
    frame = frame.dropna(subset=["prob","entry","next_close"])
    frame["rn"] = frame["next_close"]/frame["entry"]-1.0
    frame.to_parquet(CACHE)
    print(f"Cached {len(frame):,} -> {CACHE}", flush=True)
    return frame


def main():
    fr = get_frame()
    live = fr[fr["pred_ret"].notna()]
    print(f"\ntradeable obs: {len(fr):,}\n")

    # ---- per-trade edge & calendar portfolio across thresholds (classif prob) ----
    results = {}
    eq_log = {}
    for thr in [0.5,0.6,0.7,0.8,0.9]:
        d = fr[fr["prob"]>=thr]
        n=len(d)
        if n==0: results[f"cls_thr{thr}"]={"n":0}; continue
        net = d["rn"]-2*COST
        daily = (net).groupby(d["date"]).mean().reindex(fr["date"].unique(),fill_value=0).sort_index()
        s,ann,dd = stats_calendar(daily)
        import scipy.stats as st
        t,p = st.ttest_1samp(net.to_numpy(),0)
        results[f"cls_thr{thr}"] = {"n":int(n),"win5":float((d['rn']>=0.05).mean()),
            "avg_net":float(net.mean()),"per_trade_SR":float(net.mean()/net.std()) if net.std()>0 else 0,
            "t_stat":float(t),"p":float(p),"cal_SR":round(s,3),"ann":round(ann,4),"maxdd":round(float(dd),4)}
        eq_log[f"cls_thr{thr}"] = (1+daily).cumprod()
        print(f"cls thr>={thr}: n={n} win5={(d['rn']>=0.05).mean():.1%} "
              f"avg_net={net.mean():.4%} perT_SR={results[f'cls_thr{thr}']['per_trade_SR']:.3f} "
              f"t={t:.2f} p={p:.3f} calSR={s:.2f} ann={ann:.1%} dd={dd:.0%}", flush=True)

    # ---- regression-based signal (top predicted next-day return) ----
    print("\nRegression (XGB next-day return) signal:")
    for q in [0.99, 0.995, 0.999]:
        cut = live["pred_ret"].quantile(q)
        d = live[live["pred_ret"]>=cut]
        n=len(d)
        if n==0: continue
        net = d["rn"]-2*COST
        daily = net.groupby(d["date"]).mean().reindex(fr["date"].unique(),fill_value=0).sort_index()
        s,ann,dd = stats_calendar(daily)
        import scipy.stats as st
        t,p = st.ttest_1samp(net.to_numpy(),0)
        results[f"reg_q{q}"]={"n":int(n),"win5":float((d['rn']>=0.05).mean()),
            "avg_net":float(net.mean()),"per_trade_SR":float(net.mean()/net.std()) if net.std()>0 else 0,
            "t_stat":float(t),"p":float(p),"cal_SR":round(s,3),"ann":round(ann,4),"maxdd":round(float(dd),4)}
        print(f"  reg top{q}: n={n} win5={(d['rn']>=0.05).mean():.1%} avg_net={net.mean():.4%} "
              f"perT_SR={results[f'reg_q{q}']['per_trade_SR']:.3f} t={t:.2f} p={p:.3f} "
              f"calSR={s:.2f} ann={ann:.1%}", flush=True)

    pd.DataFrame(eq_log).to_csv(os.path.join(OUT,"bigmove_xgb_equity.csv"))
    with open(os.path.join(OUT,"bigmove_xgb_results.json"),"w") as f:
        json.dump(results,f,indent=2,default=str)
    print(f"\nsaved -> {OUT}/bigmove_xgb_results.json", flush=True)


if __name__=="__main__":
    main()
