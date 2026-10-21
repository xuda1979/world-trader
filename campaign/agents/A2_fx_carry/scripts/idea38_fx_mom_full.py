"""Charter 2: FX momentum on full 1990/1999+ history. 4 pairs (JPY 1990+, EUR 1999+, GBP/CAD 2000+).
Book uses only pairs with data; momentum = past return sign; daily & weekly & monthly rebal."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from r7_lib import *
import numpy as np, pandas as pd

R=load_pair_rets()
Rf=R.copy()
start=Rf.dropna(how="all").index.min()

for lb in [63,126,252]:
    for rule in ["D","W","M"]:
        pos=tsmom_pos(Rf,lb,rule=rule)
        net,to=backtest(pos,Rf.fillna(0))
        metrics(net,f"FX4 tsmom {lb}d {rule} (from {start.date()})")
# vol-weighted daily
mom=Rf.rolling(126).sum()
vol=Rf.rolling(63).std()
w=np.sign(mom)/vol
w=w.div(w.abs().sum(axis=1),axis=0).fillna(0)
net,to=backtest(w,Rf.fillna(0))
metrics(net,"FX4 tsmom126 volwt daily")
# EUR+JPY only from 1999
R2=Rf[["JPY","EUR"]].dropna(how="all")
for lb in [126,252]:
    pos=tsmom_pos(R2,lb,rule="W")
    net,to=backtest(pos,R2.fillna(0))
    metrics(net,f"JPYEUR tsmom {lb}d W (1999+)")
