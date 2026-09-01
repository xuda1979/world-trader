"""Charter 1/2 JPY long-history: 1990+ DEXJPUS spot. No foreign-rate data pre-2018 on disk,
so 'carry' = US rate only. Also JPY tsmom/momentum on 36y history (charter 2)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from r7_lib import *
import numpy as np, pandas as pd

R=load_pair_rets()
jpR=R[["JPY"]].fillna(0)
us2=new_s("DGS2"); dff=new_s("DFF"); vix=old_s("vix")

def run(pos,label,accrue_short=False):
    net,to=backtest(pos,jpR)
    if accrue_short:
        rate=us2.reindex(pos.index).ffill()/100/252
        net=net+(pos.clip(upper=0).abs()).mul(rate,axis=0).sum(axis=1,min_count=1)
    metrics(net,label)

# JPY momentum/tsmom 1990+ (36y!)
for lb in [21,63,126,252,504]:
    mom=R["JPY"].rolling(lb).sum()
    for rule in ["W","M"]:
        pos=tsmom_pos(R[["JPY"]].fillna(0),lb,rule=rule)
        run(pos,f"JPY tsmom {lb}d {rule}")

# carry proxies on JPY (US-rate-only)
sig=(us2.reindex(jpR.index).ffill()/4.0).clip(0,1)
run(pd.DataFrame({"JPY":-sig.values},index=jpR.index),"JPY shortJPY s(US2y/4)+accr",True)
run(pd.DataFrame({"JPY":-sig.where(sig>0,0).values},index=jpR.index),"JPY shortJPY only>0 +accr",True)
reg=pd.Series(np.where(dff.reindex(jpR.index).ffill()>2.0,-1.0,1.0),index=jpR.index)
run(pd.DataFrame({"JPY":reg.values},index=jpR.index),"JPY DFF-regime")
run(pd.DataFrame({"JPY":reg.where(reg>0,0).values},index=jpR.index),"JPY long-only DFF<2")
sigv=pd.Series(np.where(vix.reindex(jpR.index).ffill()>25,1.0,-1.0),index=jpR.index)
run(pd.DataFrame({"JPY":sigv.values},index=jpR.index),"JPY VIX>25 long else short")
