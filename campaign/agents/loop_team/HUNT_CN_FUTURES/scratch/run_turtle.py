"""Turtle Trading on China commodity futures — honest gate evaluation.
Event-driven pyramid book per market (System1 20/10 + System2-length robust), risk-normalized,
then equal-vol-weight across markets, vol-target 0.08, full costs, gate battery.
"""
import sys, numpy as np, pandas as pd, glob, os
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CN_FUTURES/scratch')
import turtle_lib as TL
ROOT="/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CN_FUTURES"
DATA=f"{ROOT}/data"; champ=E.champ_ref()

def load(sym):
    df=pd.read_csv(f"{DATA}/{sym}.csv", index_col=0, parse_dates=True)
    return df[['open','high','low','close']].astype(float).dropna(subset=['close'])

# universe: liquid, long-history, exclude financial (IF/IH/IC per turtle rule "剔除股指期货")
UNIV=[s for s in ['RB0','CU0','NI0','I0','M0','Y0','P0','SR0','MA0','TA0','FU0','SC0','CF0',
                  'AU0','AG0','RM0','OI0','HC0','AL0','ZN0','PP0'] if os.path.exists(f"{DATA}/{s}.csv")]

print("=== TURTLE — System1 (20d entry/10d exit), risk-normalized EW, per market ===")
books={}
for sym in UNIV:
    px=load(sym)
    try:
        net,pos,turn=TL.sim_market(px, entry=20, exit_len=10, max_units=4)
        # risk-normalize each market: scale by rolling realized vol of its P&L
        rv=net.rolling(60).std()
        norm=(net/rv).dropna()   # per-market ~unit vol
        books[sym]=norm
        print(f"  {sym:5s} n={len(net.dropna()):5d} SR(solo,raw)={net.dropna().mean()/net.dropna().std()*np.sqrt(252):+.2f} "
              f"max_units={pos.abs().max():.0f}")
    except Exception as e:
        print(f"  {sym:5s} ERR {type(e).__name__} {str(e)[:40]}")

book=pd.concat(books,axis=1).fillna(0)
# equal weight each market (each already normalized to similar vol), but only sum where nonempty
book_w=book[book.abs().sum(axis=1)>0]
book_ret=book_w.sum(axis=1)/book_w.replace(0,np.nan).notna().sum(axis=1)
b08=book_ret['2009':].dropna()
# vol-target
netvt,_=E.vol_target(b08,vt_ann=0.08)
st=E.evaluate(netvt,champ,'turtle_cn')
print("\n=== TURTLE portfolio (uniform across %d markets), 2009+, 1x gross ===" % len(UNIV))
for k in ['SR','ann_geo','MDD','negyr','worst','H1_H2','negyr_pass','ac1','uniqR','corr_champ']:
    print(f"  {k:14s} = {st[k]}")
# position-rotation scramble
def roll(p,r):
    g=(p*r).dropna(); t=p.diff().abs().reindex(g.index).fillna(0); n=g-t*6.4/1e4
    n,_=E.vol_target(n); return n.dropna()
# build pos for the book (sum of market positions)
posbook=pd.concat([(TL.sim_market(load(s),entry=20,exit_len=10,max_units=4)[1]) for s in UNIV],axis=1).fillna(0).sum(axis=1)
ret_px=pd.concat([TL.sim_market(load(s),entry=20,exit_len=10,max_units=4)[0] for s in UNIV],axis=1)
# risk-normalized ret book for scramble
import numpy as np
rng=np.random.default_rng(0); T=len(b08); values=b08.values; realv=netvt.mean()/netvt.std()*np.sqrt(252); cnt=0
for _ in range(120):
    lag=int(rng.integers(21,max(T-21,22))); rc=np.concatenate([values[lag:],values[:lag]])
    if rc.std()>0 and rc.mean()/rc.std()*np.sqrt(252)>=realv: cnt+=1
print(f"  series-shift scramble_p = {cnt/120:.3f}")
# save
E.save_sleeve(netvt, f"{ROOT}/sleeves/turtle_cn_EW.csv")
print("saved turtle_cn_EW.csv")
