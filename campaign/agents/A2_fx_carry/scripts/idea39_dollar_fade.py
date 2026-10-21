"""Charter 3: dollar-fade. DTWEXBGS 126d z -> long risky FX (EUR,GBP,CAD / short JPY) when dollar cheap.
Also equity overlay (SPY from data_fred spx) timing, which is what 'dollar cheap -> risk on' really predicts."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from r7_lib import *
import numpy as np, pandas as pd

R=load_pair_rets(); Rf=R.fillna(0)
cols=["EUR","GBP","CAD","JPY"]
z=dollar_z(126)
z63=dollar_z(63); z252=dollar_z(252)

def run(pos,R_,label):
    net,to=backtest(pos,R_.fillna(0)); metrics(net,label)

# FX basket: weights fixed basket sign by -z (short dollar)
basket=pd.Series({"EUR":1.0,"GBP":1.0,"CAD":1.0,"JPY":-1.0})
for zzz,lab in [(z,"z126"),(z63,"z63"),(z252,"z252")]:
    zz=zzz.clip(-1.5,1.5)/2.0
    w=pd.DataFrame({c:(basket[c]*zz).where(Rf[c].notna(),0) for c in cols},index=zz.index)
    w=w.where(~w.isna(),0.0)
    run(w,Rf,f"FX dollar-fade {lab}")

# binary: short USD when z>1 (dollar rich), long when z<-1, flat between
zz=z.reindex(Rf.index).ffill()
sig=pd.Series(0.0,index=Rf.index); sig[zz>1]=-1.0; sig[zz<-1]=1.0
w=pd.DataFrame({c:(basket[c]*sig).where(Rf[c].notna(),0) for c in cols},index=Rf.index)
run(w,Rf,"FX dollar-fade binary +-1z")

# SPY timing: long SPY when dollar z<0, flat/half when z>0
import pandas as pd
spx=old_s("spx"); ret=spx.pct_change()
for zz_,lab in [(z,"z126"),(z252,"z252")]:
    s=zz_.reindex(ret.index).ffill()
    sig=pd.Series(np.where(s<0,1.0,0.0),index=ret.index)
    pos=pd.DataFrame({"SPX":sig})
    net,to=backtest(pos,pd.DataFrame({"SPX":ret}).fillna(0))
    metrics(net,f"SPY long when dollar cheap {lab}")

# carry W11 gated by dollar z (mission 4 cousin): halve carry when dollar z>1 (crowded long usd)
yd=load_ydiff(); acc=yd/100/252
pos=carry_ls_pos(yd,top=1,bot=1,rule="W")
net,_,_=backtest(pos,Rf); net=net+(pos*acc if isinstance(pos*acc,pd.DataFrame) else pos*acc).sum(axis=1,min_count=1)
