"""Charter 1 sweep: monthly carry+accrual variants (plateau check) + JPY-only long-history proxies."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from r7_lib import *
import numpy as np, pandas as pd

R = load_pair_rets(); yd = load_ydiff(); acc = yd/100.0/252.0
Rf = R.fillna(0)

def run_carry(rule, top, bot, label, extra_gate=None):
    pos = carry_ls_pos(yd, top=top, bot=bot, rule=rule)
    net, to = backtest(pos, Rf)
    net = net + (pos*acc).sum(axis=1, min_count=1)
    nv, g, sr = metrics(net, label)
    return nv, g, sr, pos

# plateau sweep around the best (top1/bot1 monthly)
res={}
for rule in ["M","Q","W"]:
    for top,bot in [(1,1),(2,1),(1,2),(2,2),(4,0)]:
        nv,g,sr,pos = run_carry(rule,top,bot,f"carry {rule} top{top}/bot{bot}")
        if rule=="M": res[(top,bot)]=(sr,g)

print()
# JPY-only long-history (1998+ spot, US2y-JP10y scaled, no foreign data pre-2018 beyond monthly jp10y? check: jp10y monthly starts 2018)
# Honest: no JP rate pre-2018 on disk. Use DTB3 (US) only => 'carry' = short JPY earn US rate. Test regimes.
us2=new_s("DGS2"); dff=new_s("DFF"); dtb3=new_s("DTB3")
jp=R["JPY"].dropna().index
jpR=R[["JPY"]].fillna(0)

def jpy_test(sig,label):
    pos=pd.DataFrame({"JPY":sig.reindex(jpR.index).fillna(0).values},index=jpR.index)
    net,to=backtest(pos,jpR)
    accr=(pos*(us2.reindex(pos.index).ffill()/100/252)).sum(axis=1,min_count=1)  # earn US rate on short-JPY notional? only when short
    net2=net+accr.clip(lower=0)*pos.clip(upper=0).abs().sum(axis=1)  # only accrue when actually short
    metrics(net2,label)

sig=(us2.reindex(jp).ffill()/4.0).clip(0,1)   # short JPY size by US rate/4pp
jpy_test(-sig,"JPY short s(US2y/4) + US accrual")
sig0=sig.where(sig>0,0)
jpy_test(-sig0,"JPY short flat-if-0 + accrual")
# DFF regime long/short
reg=pd.Series(np.where(dff.reindex(jp).ffill()>2.0,-1.0,1.0),index=jp)
jpy_test(reg,"JPY DFF>2 short else long (no accrual)")
# long-JPY crisis hedge variant: long JPY when VIX high, else short-carry
vix=old_s("vix")
sigv=pd.Series(np.where(vix.reindex(jp).ffill()>25,1.0,-1.0),index=jp)
jpy_test(sigv,"JPY VIX>25 long else short")
