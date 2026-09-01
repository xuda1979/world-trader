"""Charter 1 final engineering: US-rate proxy plateau (DGS1/DTB3/DFF/DGS2), rule blend W/M/Q,
per-pair attribution, pre-specified scramble arbiter (n=1000, seed 7), corr to champion."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from r7_lib import *
import numpy as np, pandas as pd

R=load_pair_rets(); Rf=R.fillna(0)
jp10=monthly_to_daily(old_s("jp10y")); ez10=monthly_to_daily(old_s("ez10y"))
gb10=monthly_to_daily(old_s("gb10y")); ca10=monthly_to_daily(old_s("ca10y"))

def ydiff_us(us):
    return pd.concat({"JPY":jp10-us,"EUR":ez10-us,"GBP":gb10-us,"CAD":ca10-us},axis=1).sort_index()

def carry_acc(yd,rule="W",top=1,bot=1):
    acc=yd/100/252
    pos=carry_ls_pos(yd,top=top,bot=bot,rule=rule)
    net,to=backtest(pos,Rf)
    net=net+(pos*acc).sum(axis=1,min_count=1)
    return net,pos,to

print("== US-rate proxy plateau (W top1/bot1) ==")
for usn in ["DGS1","DGS2","DFF","DTB3","DGS10"]:
    yd=ydiff_us(new_s(usn))
    net,pos,to=carry_acc(yd)
    metrics(net,f"carry W11 US={usn}")

print("== rule blend (avg of W/M/Q positions, US=DGS2) ==")
yd=ydiff_us(new_s("DGS2")); acc=yd/100/252
possum=None
for rule in ["W","M","Q"]:
    p=carry_ls_pos(yd,top=1,bot=1,rule=rule)
    possum=p if possum is None else possum+p
pos=possum/3.0
net,to=backtest(pos,Rf); net=net+(pos*acc).sum(axis=1,min_count=1)
metrics(net,"carry rule-blend W/M/Q")

print("== per-pair attribution of W11 (US=DGS2): SR contribution ==")
posw=carry_ls_pos(yd,top=1,bot=1,rule="W")
for c in Rf.columns:
    net1,to1=backtest(posw[[c]],Rf[[c]])
    net1=net1+(posw[[c]]*yd[[c]]/100/252).sum(axis=1,min_count=1)
    nv=U.vol_target(net1,0.10); r=nv.dropna()
    print(f"  {c}: SR={r.mean()/r.std()*np.sqrt(252):.2f} ann={r.mean()*252*100:.1f}%")

print("== PRE-SPECIFIED scramble arbiter: W11 US=DGS2, n=1000, seed 7 (pre-vt) ==")
net,pos,to=carry_acc(yd)
real,p=scramble_df(pos,Rf,n=1000,seed=7)
print(f"real={real:.3f} p={p:.4f} -> {'PASS' if p<0.05 else 'FAIL'}")

print("== corr to champion ==")
ch=pd.read_csv("/Users/daxu/software/world-trader/campaign/results/CHAMPION_FINAL_daily.csv",index_col=0,parse_dates=True)
chc=ch.iloc[:,0]
nv=U.vol_target(net,0.10)
j=pd.concat([nv.rename("a"),chc.rename("b")],axis=1).dropna()
print("corr to champion:", round(j["a"].corr(j["b"]),3), "n=",len(j))
