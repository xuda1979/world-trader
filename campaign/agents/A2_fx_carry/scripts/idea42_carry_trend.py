"""Charter 4: carry-trend blend. Carry W11 position, zeroed where 63d (or 126d) price trend
disagrees with carry sign; also continuous version. Full gates."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from r7_lib import *
import numpy as np, pandas as pd

R=load_pair_rets(); yd=load_ydiff(); acc=yd/100/252; Rf=R.fillna(0)
pos=carry_ls_pos(yd,top=1,bot=1,rule="W")

for lb in [21,63,126]:
    for mode in ["gate","continuous"]:
        mom=Rf.rolling(lb).sum().reindex(pos.index)
        sg_mom=np.sign(mom); sg_pos=np.sign(pos)
        if mode=="gate":
            p2=pos.where(sg_mom==sg_pos,0.0)
        else:
            agree=(sg_mom==sg_pos)
            p2=pos.where(agree,0.5*pos)
        net,to=backtest(p2,Rf)
        net=net+(p2*acc).sum(axis=1,min_count=1)
        metrics(net,f"carry-trend {mode} {lb}d")
# also: carry z1/b1 + JPY tsmom252 blend (50/50) as mission-4 alt
pos_t=tsmom_pos(Rf[["JPY"]],252,rule="W")
netc,_=backtest(pos,Rf); netc=netc+(pos*acc).sum(axis=1,min_count=1)
nett,_=backtest(pos_t,Rf)
blend=0.5*netc+0.5*nett
metrics(blend,"blend carryW11 + JPY tsmom252")
