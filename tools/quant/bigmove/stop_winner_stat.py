"""LIGHT: single-split version to quantify 'of next-day +5% winners, how many
touch a 1% stop intraday?' — explains why a stop hurts a big-up strategy.
Train on <=2020, test on >=2020. Fast (one model).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from pipeline_common import load_ohlcv
from features2 import build_features2
from features import to_xy

print("load...", flush=True)
P = load_ohlcv(); close=P["close"]; open_=P["open"]; low=P["low"]
print("feat...", flush=True)
feats = build_features2(P)
ret_next = close.pct_change().shift(-1)
X_full,y_full,_,meta,_ = to_xy(feats,ret_next)
X_full=X_full.replace([np.inf,-np.inf],np.nan)
dates=meta["date"].to_numpy(); tickers=meta["ticker"].to_numpy()
CUT=pd.Timestamp("2020-01-01"); tr=dates<np.datetime64(CUT)
ok=np.isfinite(X_full.iloc[tr].to_numpy()).sum(axis=1)>0
Xtr,ytr=X_full.iloc[tr].iloc[ok],y_full[tr][ok]
print("train...", flush=True)
m=HistGradientBoostingClassifier(max_iter=300,learning_rate=0.05,max_depth=6,
    max_leaf_nodes=31,l2_regularization=1.0,class_weight="balanced",
    early_stopping=True,validation_fraction=0.1,n_iter_no_change=15,random_state=42)
m.fit(Xtr,ytr)
te=dates>=np.datetime64(CUT); Xte=X_full.iloc[te]; ok2=np.isfinite(Xte.to_numpy()).sum(axis=1)>0
proba=np.full(len(Xte),np.nan); proba[ok2]=m.predict_proba(Xte.iloc[ok2])[:,1]
dt=dates[te]; tk=tickers[te]
mi=pd.MultiIndex.from_arrays([dt,tk],names=["date","ticker"])
def v(df,sh): return df.shift(sh).stack().reindex(mi).to_numpy()
fr=pd.DataFrame({"date":dt,"ticker":tk,"prob":proba,
    "entry":v(close,0),"no":v(close,-1),"lo":v(low,-1),"op":v(open_,-1)})
fr=fr.dropna(subset=["prob","entry","no","lo","op"])
fr["rn"]=fr["no"]/fr["entry"]-1
for st in [0.01,0.03]:
    fr[f"hit{int(st*100)}"]=(fr["lo"]<=fr["entry"]*(1-st)).astype(int)
d=fr[fr["prob"]>=0.9]
print(f"\nTEST >=2020, trades@thr>=0.9: {len(d):,}")
print(f"  no-stop win(>=+5%): {(d['rn']>=0.05).mean():.2%}")
for st in [1,3]:
    col=f"hit{st}"
    w=d['rn']>=0.05
    wstop=w&(d[col]==1)
    print(f"  STOP {st}%: touched intraday {(d[col]==1).mean():.2%} of all trades")
    print(f"    no-stop winners: {w.sum():,} ({w.mean():.2%}), "
          f"of which stopped-out: {wstop.sum():,} ({wstop.sum()/max(w.sum(),1):.1%})")
    print(f"    avg ret winners NOT stopped {d[w&(d[col]==0)]['rn'].mean():.3%} "
          f"| winners stopped {d[wstop]['rn'].mean():.3%}")
