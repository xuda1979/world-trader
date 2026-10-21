"""Turtle config sweep — honest landscape across System1/System2/max_units."""
import sys, numpy as np, pandas as pd, os
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CN_FUTURES/scratch')
import turtle_lib as TL
ROOT="/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CN_FUTURES"; DATA=ROOT+"/data"
champ=E.champ_ref()
def load(s):
    df=pd.read_csv(f"{DATA}/{s}.csv",index_col=0,parse_dates=True)
    return df[['high','low','close']].astype(float).dropna(subset=['close'])
UNIV=[s for s in ['RB0','CU0','NI0','I0','M0','Y0','P0','SR0','MA0','TA0','FU0','SC0','CF0','AU0','AG0','RM0','OI0','HC0','AL0','ZN0','PP0'] if os.path.exists(f"{DATA}/{s}.csv")]
def port(entry,exit_len,max_units):
    books={}
    for s in UNIV:
        net,pos,turn=TL.sim_market(load(s),entry=entry,exit_len=exit_len,max_units=max_units)
        rv=net.rolling(60).std(); norm=(net/rv).dropna(); books[s]=norm
    b=pd.concat(books,axis=1).fillna(0)
    bw=b[b.abs().sum(axis=1)>0]; r=bw.sum(axis=1)/bw.replace(0,np.nan).notna().sum(axis=1)
    r=r['2009':].dropna(); nv,_=E.vol_target(r)
    return E.evaluate(nv,champ,'turtle')
print(f"{'cfg':16s} {'SR':>5s} {'ann%':>6s} {'MDD%':>6s} {'negy':>4s} {'worst%':>6s} {'H1':>5s} {'H2':>5s} {'corr':>6s}")
for (entry,ex,mu) in [(20,10,4),(20,10,1),(55,20,4),(55,20,1),(20,20,4),(55,10,4)]:
    st=port(entry,ex,mu)
    print(f"E{entry}L{ex}U{mu:2d}   {st['SR']:5.2f} {st['ann_geo']*100:6.1f} {st['MDD']*100:6.1f} {st['negyr']:4d} {st['worst']*100:6.1f} {st['H1_H2'][0]:5.2f} {st['H1_H2'][1]:5.2f} {st['corr_champ']:6.3f}")
