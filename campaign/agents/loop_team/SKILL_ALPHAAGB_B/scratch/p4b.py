"""P4b/c: QQQ/SPY ratio z-rev, XLF/SPY ratio z-rev, WALCL z-gate on SPY."""
import sys; sys.path.insert(0,'.')
from libb import *
import libb, pandas as pd, numpy as np

import pandas as pd, numpy as np
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
def fr(n):
    df=pd.read_csv(f'{FRED}/{n}.csv',index_col=0,parse_dates=True)
    s=pd.to_numeric(df.iloc[:,0],errors='coerce')
    return s[~s.index.duplicated(keep='last')].sort_index()
def trade(pos,r,tag,vt=0.10):
    pos=pos.reindex(r.index).fillna(0.0)
    g0=F.net_of(pos,r)[0]
    s=F.vol_target_scale(g0,vt=vt,min_days=60,cap=3.0,trailing_shift=1)
    posv=pos*s
    net=F.net_of(posv,r)[0]
    st=F.full_stats(net); h1,h2=F.halves_sr(net); fg=F.flatten_gates(net); corr,nn=F.corr_to(net,champ)
    pl,_=libb.book_position_lag_p(posv.to_frame('p'),r.to_frame('r'),n=200)
    print(f"{tag}: SR {st['sr']:+.3f} ann {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% negy {st['negy']} worst {st['worst']*100:.1f}% | H1 {h1:+.2f} H2 {h2:+.2f} | poslag_p {pl:.3f} | ac1 {fg['ac1']:+.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f}(n={nn})")

champ=F.load_champion()
px=panel_closes('twelve_big')
qqq=px['QQQ'].dropna(); spy=px['SPY'].dropna(); xlf=px['XLF'].dropna()

def ratio_book(a,b,zwin=63,entry=1.0,tag=''):
    ra,rb=a.pct_change(),b.pct_change()
    ratio=(a/b)
    z=((ratio-ratio.rolling(zwin).mean())/ratio.rolling(zwin).std())
    pos=pd.Series(0.0,index=a.index)
    pos[z<-entry]=1.0; pos[z>entry]=-1.0
    pos=pos.replace(np.nan,0.0).ffill().fillna(0.0)
    r=ra-rb  # dollar-neutral: long a short b => r_a - r_b
    trade(pos.reindex(r.index),r,tag)

for zw in [21,63,126]:
    ratio_book(qqq,spy,zw,1.0,f'QQQSPY_zrev{zw}')
    ratio_book(xlf,spy,zw,1.0,f'XLFSPY_zrev{zw}')
# WALCL z-gate on SPY: long SPY when WALCL above trailing median (liquidity expansion)
wal=fr('WALCL').dropna()
med=wal.rolling(104).median()
z=wal/med-1
pos=pd.Series(np.nan,index=spy.index)
zz=z.reindex(spy.index).ffill()
pos[zz>0]=1.0; pos[zz<=0]=0.0
pos=pos.ffill().fillna(0.0)
r=spy.pct_change()
trade(pos.reindex(r.index),r,'WALCL_gate_spy')
