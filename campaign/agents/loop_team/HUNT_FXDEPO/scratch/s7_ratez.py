"""Deposit-rate domain engines (charter-named): DGS3MO level/changes as FX signals (PIT)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

us=pd.read_csv(f'{FR}/DGS3MO.csv',index_col=0,parse_dates=True).iloc[:,0]
us=pd.to_numeric(us,errors='coerce').dropna()
names=['DEXBZUS','DEXMXUS','DEXKOUS','DEXINUS','DEXSIUS','DEXJPUS','DEXNOUS','DEXSDUS','DEXSFUS','DEXDNUS']
px=pd.DataFrame({n:dex(n) for n in names})
rloc=(-px.pct_change())
champ=load_champion()
usz=(us-us.rolling(252).mean())/us.rolling(252).std()

def show(tag,r):
    r8=r[r.index>='2008-01-01'].dropna()
    if len(r8)<800: print(tag,'short',len(r8)); return
    st=full_stats(r8); h1,h2=halves_sr(r8); corr,nc=corr_to(r8,champ)
    print(f'{tag:46s} SR {st["sr"]:+.3f} H1 {h1:+.2f} H2 {h2:+.2f} ann {st["ann_geo"]*100:6.2f}% MDD {st["mdd"]*100:6.1f}% negy {st["negy"]:2d} corr {corr:+.3f}')

em=['DEXBZUS','DEXMXUS','DEXKOUS','DEXINUS','DEXSIUS']
emb=rloc[em].mean(axis=1)
uszD=usz.reindex(emb.index).ffill()

for thr in [0.0,0.5,1.0]:
    sig=pd.Series(np.where(uszD.shift(1).fillna(0)<thr,1.0,0.0),index=emb.index)
    r=net_of_book(pd.DataFrame({'em':sig}),pd.DataFrame({'em':emb}))
    show(f'EM basket long when usz<{thr}',r)
    sig3=pd.Series(np.where(uszD.shift(1).fillna(0)<thr,1.0,np.where(uszD.shift(1).fillna(0)>thr,-1.0,0.0)),index=emb.index)
    r3=net_of_book(pd.DataFrame({'em':sig3}),pd.DataFrame({'em':emb}))
    show(f'EM basket smile-sign usz thr{thr}',r3)

dmaj=rloc[['DEXJPUS','DEXNOUS','DEXSDUS','DEXSFUS','DEXDNUS','DEXSIUS','DEXKOUS','DEXBZUS','DEXMXUS','DEXINUS']].mean(axis=1)
for d in [21,63]:
    dc=us.diff(d).reindex(dmaj.index).ffill()
    sigm=(-pd.Series(np.sign(dc.shift(1)),index=dmaj.index).fillna(0.0))
    r=net_of_book(pd.DataFrame({'us':sigm}),pd.DataFrame({'us':dmaj}))
    show(f'USD vs basket when {d}d rate-diff sign',r)
    big=dc.abs().shift(1)>us.rolling(252).std().reindex(dmaj.index).ffill()*0.5
    r2=net_of_book(pd.DataFrame({'us':sigm.where(big,0.0)}),pd.DataFrame({'us':dmaj}))
    show(f'USD vs basket {d}d rate-diff, |chg|>0.5sd gate',r2)

# 3. carry-rank rotation: rank EM ccys by trailing 63d USD-appreciation (proxy for carry crash risk):
# long the STRONGEST 3 (winners) — classic EM cross-sectional momentum at 63d, weekly rebal.
for lb in [21,63,126]:
    mom=px.pct_change(lb)  # USD per local: negative mom = strong local
    sig=(-np.sign(mom.shift(1))).reindex(px.index)  # long local if local strong
    r=net_of_book(sig.fillna(0.0), rloc.reindex(px.index).fillna(0.0))
    show(f'EW per-ccy mom sign lb{lb} (verify vs s2)',r)
