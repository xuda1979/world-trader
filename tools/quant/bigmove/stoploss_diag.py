"""Quantify how a 1% stop interacts with the strategy's winners vs losers.
Reuses the full walk-forward probabilities by re-running the prediction loop,
then analyses the no-stop outcome vs whether the intraday stop would have hit.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from pipeline_common import load_ohlcv
from features2 import build_features2
from features import to_xy

ROOT = "/Users/daxu/software/world-trader"
TRAIN_WIN = 252*3; REFIT=63; START="2018-01-01"; COST=0.0006

def main():
    print("loading...", flush=True)
    P = load_ohlcv(); close=P["close"]; open_=P["open"]; low=P["low"]; high=P["high"]
    print("building features...", flush=True)
    feats = build_features2(P)
    ret_next = close.pct_change().shift(-1)
    X_full, y_full, _, meta, _ = to_xy(feats, ret_next)
    X_full = X_full.replace([np.inf,-np.inf],np.nan)
    dates=meta["date"].to_numpy(); tickers=meta["ticker"].to_numpy()
    ud=np.unique(dates); start=pd.Timestamp(START)
    pd_=ud[ud>=np.datetime64(start)]; refit=np.arange(0,len(pd_),REFIT)
    prob=np.full(len(X_full),np.nan)
    for k,kk in enumerate(refit):
        d=pd_[kk]
        dmin=d-np.timedelta64(TRAIN_WIN,"D")
        tr=(dates<d)&(dates>=dmin); ok=np.isfinite(X_full.iloc[tr].to_numpy()).sum(axis=1)>0
        Xtr,ytr=X_full.iloc[tr].iloc[ok],y_full[tr][ok]
        m=HistGradientBoostingClassifier(max_iter=300,learning_rate=0.05,max_depth=6,
            max_leaf_nodes=31,l2_regularization=1.0,class_weight="balanced",
            early_stopping=True,validation_fraction=0.1,n_iter_no_change=15,random_state=42)
        m.fit(Xtr,ytr)
        d_end=pd_[kk+REFIT] if kk+REFIT<len(pd_) else pd_[-1]+np.timedelta64(1,"D")
        blk=(dates>=d)&(dates<d_end); Xb=X_full.iloc[blk]
        okb=np.isfinite(Xb.to_numpy()).sum(axis=1)>0
        pb=np.full(len(Xb),np.nan); pb[okb]=m.predict_proba(Xb.iloc[okb])[:,1]
        prob[blk]=pb
    mi=pd.MultiIndex.from_arrays([dates,tickers],names=["date","ticker"])
    def v(df,sh=0): return df.shift(sh).stack().reindex(mi).to_numpy()
    fr=pd.DataFrame({"date":dates,"ticker":tickers,"prob":prob,
        "entry":v(close),"no":v(close,-1),"lo":v(low,-1),"op":v(open,-1)})
    fr=fr.dropna(subset=["prob","entry","no","lo","op"])
    fr["ret_no"]=fr["no"]/fr["entry"]-1.0
    # stop analysis: would a 1% stop have been hit (next_low <= entry*(1-stop))?
    for stop in [0.01,0.03]:
        fr[f"stop_hit_{int(stop*100)}"]=(fr["lo"]<=fr["entry"]*(1-stop)).astype(int)
    d=fr[fr["prob"]>=0.9]
    print(f"trades @thr>=0.9: {len(d):,}")
    print(f"  no-stop win(>=+5%): {(d['ret_no']>=0.05).mean():.2%}")
    print(f"  no-stop loss(<=-5%): {(d['ret_no']<=-0.05).mean():.2%}")
    for stop in [1,3]:
        col=f"stop_hit_{stop}"
        hit=d[col]==1
        print(f"\n  STOP {stop}%: touched intraday {hit.mean():.2%} of trades")
        # of no-stop winners, how many regardless touched the stop intraday
        win=d['ret_no']>=0.05
        win_hit=(win&(d[col]==1))
        print(f"    among no-stop winners(>=+5%): {win.sum():,} trades, "
              f"of which {win_hit.sum():,} ({win_hit.sum()/max(win.sum(),1):.1%}) would have been stopped out")
        # avg ret of no-stop winners that DID get stopped vs those that didn't
        print(f"    avg ret of winners NOT stopped: {d[win&(d[col]==0)]['ret_no'].mean():.3%}")
        print(f"    avg ret of winners that WERE stopped: {d[win&(d[col]==1)]['ret_no'].mean():.3%}")
    # net effect summary per trade
    print("\n  PRIME: at stop=1%, 12bps round-trip, avg net/trade:")
    for stop in [1,3]:
        h=d[f"stop_hit_{stop}"]==1
        exit_px=np.where(d["op"]<=d["entry"]*(1-stop*0.01),d["op"],
                np.where(d["lo"]<=d["entry"]*(1-stop*0.01),d["entry"]*(1-stop*0.01),d["no"]))
        net=exit_px/d["entry"].to_numpy()-1-2*COST
        print(f"   stop={stop}%: avg net {net.mean():.4%} vs no-stop {d['ret_no'].mean()-2*COST:.4%}")
