"""P7: USD/JPY weekday seasonality (uncovered by A2 FX carry/C5 NG weekday work).
Mechanism: repatriation/invoice flows create day-of-week drift in JPY crosses.
Long JPY (short USDJPY) on specific days, T+1 calendar-known, full weekday-map grid
+ LOO validation (the honest way to avoid 5-way multiple-testing)."""
import sys; sys.path.insert(0,'.')
from libb import *
import libb, pandas as pd, numpy as np
ROOT2='/Users/daxu/software/world-trader/tools/quant/data/fx'
def fx(n):
    df=pd.read_csv(f'{ROOT2}/{n}.csv',index_col=0,parse_dates=True)
    s=pd.to_numeric(df.iloc[:,0],errors='coerce') if not isinstance(df.iloc[:,0],pd.core.series.Series) else df.iloc[:,0]
    return s[~s.index.duplicated(keep='last')].sort_index()
champ=F.load_champion()
jpy=fx('USD_JPY').dropna()
r=jpy.pct_change()  # long USDJPY
import itertools

def wd_book(days_long, tag, vt=0.10):
    pos=pd.Series(0.0,index=r.index)
    for d in days_long: pos[r.index.dayofweek==d]=-1.0   # long JPY = short USDJPY
    for d in [x for x in range(5) if x not in days_long]: pos[r.index.dayofweek==d]=1.0
    g=F.net_of(pos,r)[0]
    s=F.vol_target_scale(g,vt=vt,min_days=60,cap=3.0,trailing_shift=1)
    posv=pos*s; net=F.net_of(posv,r)[0]
    st=F.full_stats(net); h1,h2=F.halves_sr(net)
    corr,nn=F.corr_to(net,champ)
    return net,posv,st,h1,h2,corr,nn,tag

best=None
rows=[]
# single-day L/S and combos: all 2^5 - 2 = 30 sign maps
for bits in itertools.product([-1,1],repeat=5):
    if all(b==1 for b in bits) or all(b==-1 for b in bits): continue
    pos=pd.Series(0.0,index=r.index)
    for d,b in enumerate(bits): pos[r.index.dayofweek==d]=b
    g=F.net_of(pos,r)[0]
    s=F.vol_target_scale(g,vt=0.10,min_days=60,cap=3.0,trailing_shift=1)
    posv=pos*s; net=F.net_of(posv,r)[0]
    st=F.full_stats(net)
    rows.append((st["sr"],bits))
rows.sort(reverse=True)
print('top 5 maps by SR (of 30) — MULTIPLE TESTING HAZARD, need LOO:')
for sr,bits in rows[:5]:
    days_long=[d for d,b in enumerate(bits) if b==-1]
    net,posv,st,h1,h2,corr,nn,tag=wd_book(days_long,'map')
    print(f"  longJPY days {days_long}: SR {st['sr']:+.3f} H1 {h1:+.2f} H2 {h2:+.2f} corr {corr:+.3f}")
# day-of-week mean returns raw (sanity)
dow_mean=r.groupby(r.index.dayofweek).mean()*1e4
print('USDJPY mean bp/day by dow:',dow_mean.round(2).to_dict())
