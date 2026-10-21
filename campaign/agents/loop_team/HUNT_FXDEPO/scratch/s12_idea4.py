"""IDEA 4 last variant: FX MOMENTUM at SHORT horizon (3/5/10d) per-ccy + EW, and
TIME-SERIES reversion 3/5d (often works in FX at weekly scale as RSI-fade). Cheap to test,
closes charter idea 4 fully."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

names=['DEXBZUS','DEXMXUS','DEXKOUS','DEXINUS','DEXSIUS','DEXJPUS','DEXNOUS','DEXSDUS','DEXSFUS','DEXDNUS']
px=pd.DataFrame({n:dex(n) for n in names})
rloc=-px.pct_change()
champ=load_champion()
def show(tag,r):
    r8=r[r.index>='2008-01-01'].dropna()
    if len(r8)<800: print(tag,'short'); return
    st=full_stats(r8); h1,h2=halves_sr(r8); corr,nc=corr_to(r8,champ)
    print(f'{tag:40s} SR {st["sr"]:+.3f} H1 {h1:+.2f} H2 {h2:+.2f} ann {st["ann_geo"]*100:+6.2f}% MDD {st["mdd"]*100:6.1f}% negy {st["negy"]:2d} corr {corr:+.3f}')

for lb in [3,5,10]:
    sig=np.sign(px.pct_change(lb)).shift(1)          # mom
    show(f'per-ccy MOM lb{lb}', net_of_book(sig.fillna(0),rloc.reindex(px.index).fillna(0)))
    sig=-np.sign(px.pct_change(lb)).shift(1)         # reversion
    show(f'per-ccy REV lb{lb}', net_of_book(sig.fillna(0),rloc.reindex(px.index).fillna(0)))
# RSI-style: reversion on 2-day move
for lb in [2]:
    sig=-np.sign(px.pct_change(lb)).shift(1)
    show(f'per-ccy REV lb{lb} (2d)', net_of_book(sig.fillna(0),rloc.reindex(px.index).fillna(0)))
