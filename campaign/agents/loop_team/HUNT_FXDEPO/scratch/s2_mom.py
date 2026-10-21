"""IDEA 4 (proper redo): per-currency TS momentum on the 10-cross DEX USD panel.
coord_emfx's EM-basket rows were broken by inner-join (n=5 rows) — never actually evaluated.
Here: EW of per-ccy books, no intersection collapse. USD-per-local: r_local = -pct_change(px).
Sign: mom lb → long local ccy if trailing local return >0.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

names=['DEXBZUS','DEXMXUS','DEXKOUS','DEXINUS','DEXSIUS','DEXJPUS','DEXNOUS','DEXSDUS','DEXSFUS','DEXDNUS']
px=pd.DataFrame({n:dex(n) for n in names})
rloc=-px.pct_change()   # local currency return vs USD

def mom_book(lb, rebal=1, gate=None):
    sig=np.sign(px.pct_change(lb))
    if rebal>1:
        sig=sig.iloc[::rebal].reindex(px.index).ffill()
    if gate is not None:
        sig=sig.where(gate,0.0)
    return net_of_book(sig, rloc)

rows=[]
for lb in [10,21,42,63,126,252]:
    for reb in [1,5]:
        r=mom_book(lb,reb)
        r8=r[r.index>='2008-01-01'].dropna()
        st=full_stats(r8); h1,h2=halves_sr(r8)
        corr,nc=corr_to(r8, load_champion())
        rows.append(dict(lb=lb,reb=reb,sr=st['sr'],h1=h1,h2=h2,mdd=st['mdd']*100,
                         ann=st['ann_geo']*100,negy=st['negy'],corr=corr,n=len(r8)))
df=pd.DataFrame(rows).sort_values('sr',ascending=False)
print(df.to_string(index=False))
