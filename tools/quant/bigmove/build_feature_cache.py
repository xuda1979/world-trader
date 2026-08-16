"""Materialize + cache the full scaled feature matrix once (X, y, rn, meta)
so hyperparameter sweeps / target experiments don't rebuild features each time.
Cache: data/xgb_scaled_feats.parquet (wide) plus meta parquet.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DYLD_LIBRARY_PATH","/Users/daxu/homebrew/opt/libomp/lib:"+os.environ.get("DYLD_LIBRARY_PATH",""))
import numpy as np, pandas as pd
from universe_expand import build_panel
from features4 import build_features4
from features import to_xy

HERE=os.path.dirname(os.path.abspath(__file__))
XOUT=os.path.join(HERE,"data","xgb_scaled_feats.parquet")
MOUT=os.path.join(HERE,"data","xgb_scaled_feats_meta.parquet")
if os.path.exists(XOUT):
    print("feature cache exists already", XOUT); sys.exit(0)
P=build_panel()[0]; close=P["close"]; feats=build_features4(P,close)
ret_next=close.pct_change().shift(-1)
X,y,rn,meta,names=to_xy(feats,ret_next)
X=X.replace([np.inf,-np.inf],np.nan)
meta["rn"]=rn; meta["y_big"]=(rn>=0.05).astype(int)
# add realized-vol for target engineering later
rv5=close.pct_change().rolling(5).std().shift(-1)
sr=rv5.stack().reindex(pd.MultiIndex.from_arrays([meta["date"].to_numpy(),meta["ticker"].to_numpy()]))
meta["rv_next5"]=sr.to_numpy()
X.columns=[f"f{i}" for i in range(X.shape[1])]
X.to_parquet(XOUT)
meta.to_parquet(MOUT)
print("saved",XOUT,X.shape,"and",MOUT,meta.shape,"nfeat",len(names))
