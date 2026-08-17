"""Union price panel: merge all local daily panels into one aligned close/open/
high/low/vol frame (prefer twelve_big > twelvedata > twelve_liq > polygon >
polygon_v2), excluding ETFs/FX. ~660 names, 2006-2026."""
from __future__ import annotations
import os, glob
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
BASE=os.path.join(ROOT,"tools/quant/data")
DIRS=["twelve_big","twelvedata","twelve_liq","polygon","polygon_v2","twelve_extend"]
ETFS={'SPY','QQQ','XLF','DIA','IWM','GLD','TLT','IEF','EWA','EWC','XLB','XLE','XLI','CIBR','EMCB'}
def load_union():
    # find best file per symbol
    best={}
    for d in DIRS:
        for fp in glob.glob(os.path.join(BASE,d,"*.csv")):
            s=os.path.basename(fp)[:-4]
            if s in ETFS or '_' in s or len(s)>5: continue
            if s not in best: best[s]=fp
    frames={f:{} for f in ["open","high","low","close","vol"]}
    for s,fp in best.items():
        try:
            df=pd.read_csv(fp,parse_dates=["date"]).sort_values("date").drop_duplicates("date").set_index("date")
            if len(df)<60: continue
            for f in frames:
                frames[f][s]=df[f]
        except Exception:
            continue
    P={f:pd.DataFrame(v).sort_index() for f,v in frames.items()}
    return P
if __name__=="__main__":
    P=load_union()
    print("union panel:", P["close"].shape, P["close"].index.min(), P["close"].index.max())
