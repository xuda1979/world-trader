"""P3 (CROSSREGIME dead-agent slate): macro-regime single-asset timing books.
(a) real-rate (DFII10) change -> gold; (b) DXY 63d trend -> gold inverse; (c) T10YIE
breakeven z -> gold inflation-hedge long. All trailing-only, T+1, 6.4bps, borrow."""
import sys; sys.path.insert(0,'.')
from libb import *
import libb
import pandas as pd, numpy as np
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
def fr(n):
    df=pd.read_csv(f'{FRED}/{n}.csv',index_col=0,parse_dates=True)
    s=df.iloc[:,0]; s=s[~s.index.duplicated(keep='last')].sort_index()
    return pd.to_numeric(s,errors='coerce')
gold=fr('xau'); gold=gold.dropna()

champ=F.load_champion()

def zrev_book(sig, px, zwin=63, entry=1.0, name=''):
    """z-reversion on sig -> position in px (long when z low). All trailing."""
    z=((sig-sig.rolling(zwin).mean())/sig.rolling(zwin).std()).reindex(px.index)
    pos=pd.Series(0.0,index=px.index)
    pos[z.fillna(0)<-entry]=1.0; pos[z.fillna(0)>entry]=-1.0
    pos=pos.replace(np.nan,0.0).ffill().fillna(0.0)
    r=px.pct_change().reindex(pos.index)
    g0=F.net_of(pos,r)[0]
    s=F.vol_target_scale(g0,vt=0.10,min_days=60,cap=3.0,trailing_shift=1)
    posv=pos*s
    net=F.net_of(posv,r)[0]
    return net,posv,r

def mom_book(sig, px, lb=63, name=''):
    """trend book: long px when sig trend up."""
    pos=pd.Series(np.nan,index=px.index)
    trend=(sig-sig.shift(lb)).reindex(px.index)
    pos[trend>0]=1.0; pos[trend<0]=-1.0
    pos=pos.ffill().fillna(0.0)
    r=px.pct_change().reindex(pos.index)
    g0=F.net_of(pos,r)[0]
    s=F.vol_target_scale(g0,vt=0.10,min_days=60,cap=3.0,trailing_shift=1)
    posv=pos*s
    net=F.net_of(posv,r)[0]
    return net,posv,r

def rep(net,posv,r,champ,tag):
    st=F.full_stats(net); h1,h2=F.halves_sr(net); fg=F.flatten_gates(net); corr,nn=F.corr_to(net,champ)
    pl,_=libb.book_position_lag_p(posv.to_frame('p'),r.to_frame('r'),n=200)
    yr=(1+net).groupby(net.index.year).prod()-1
    print(f"{tag}: SR {st['sr']:+.3f} ann {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% negy {st['negy']} worst {st['worst']*100:.1f}% | H1 {h1:+.2f} H2 {h2:+.2f} | poslag_p {pl:.3f} | ac1 {fg['ac1']:+.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f}(n={nn})")
    return st

d10=fr('DFII10').dropna()
dxy=fr('dxy').dropna()
be=fr('T10YIE').dropna()

# (a) real-rate level-change -> gold: z-rev on 21d change of real yield (long gold when real rates FALLING fast = z low)
for zw in [63,126]:
    ch=d10.diff(21)
    net,posv,r=zrev_book(ch,gold,zwin=zw,entry=1.0)
    rep(net,posv,r,champ,f'realrate_chg_zrev_gold_zw{zw}')
# (b) DXY trend -> gold inverse
for lb in [63,126]:
    net,posv,r=mom_book(-dxy,gold,lb=lb)
    rep(net,posv,r,champ,f'dxy_inv_mom_gold_lb{lb}')
# (c) breakeven z -> gold
net,posv,r=mom_book(be,gold,lb=63)
rep(net,posv,r,champ,'be_gold_mom63')
net,posv,r=zrev_book(be,gold,zwin=126,entry=1.0)
rep(net,posv,r,champ,'be_gold_zrev126')
