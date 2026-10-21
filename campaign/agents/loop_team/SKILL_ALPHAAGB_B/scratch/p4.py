"""P4: (a) 2s10s slope z-rev via us2y vs us10y duration-pnl; (b) QQQ/SPY + XLF/SPY ratio
z-rev books (long ratio at z-low); (c) WALCL liquidity level z momentum gate on SPY."""
import sys; sys.path.insert(0,'.')
from libb import *
import libb, pandas as pd, numpy as np
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
def fr(n):
    df=pd.read_csv(f'{FRED}/{n}.csv',index_col=0,parse_dates=True)
    s=pd.to_numeric(df.iloc[:,0],errors='coerce')
    return s[~s.index.duplicated(keep='last')].sort_index()
champ=F.load_champion()

def trade(pos,r,tag,champ=champ,vt=0.10):
    pos=pos.reindex(r.index).fillna(0.0)
    g0=F.net_of(pos,r)[0]
    s=F.vol_target_scale(g0,vt=vt,min_days=60,cap=3.0,trailing_shift=1)
    posv=pos*s
    net=F.net_of(posv,r)[0]
    st=F.full_stats(net); h1,h2=F.halves_sr(net); fg=F.flatten_gates(net); corr,nn=F.corr_to(net,champ)
    pl,_=libb.book_position_lag_p(posv.to_frame('p'),r.to_frame('r'),n=200)
    print(f"{tag}: SR {st['sr']:+.3f} ann {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% negy {st['negy']} worst {st['worst']*100:.1f}% | H1 {h1:+.2f} H2 {h2:+.2f} | poslag_p {pl:.3f} | ac1 {fg['ac1']:+.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f}(n={nn})")

def zrev(sig,entry=1.0,zwin=63):
    z=((sig-sig.rolling(zwin).mean())/sig.rolling(zwin).std())
    pos=pd.Series(0.0,index=sig.index)
    pos[z<-entry]=1.0; pos[z>entry]=-1.0
    return pos.replace(np.nan,0.0).ffill().fillna(0.0)

# (a) 2s10s slope
u2=fr('us2y'); u10=fr('us10y')
slope=(u10-u2).dropna()
r_sl=slope.diff()/10.0   # duration ~8yr, pnl per bp = pos*8*0.0001; approx via diff()*0.08/100... use d_yield_bp * 8 * 1e-4 * pos
r_sl=((u10-u2).diff())*8.0*1e-4   # long slope = long duration of 10y vs 2y
r_sl=r_sl.reindex(r_sl.index.intersection(pd.date_range('2008-01-01','2026-08-27')))
for zw in [63,126,252]:
    pos=zrev(slope,1.0,zw).reindex(r_sl.index)
    trade(pos,r_sl,f'2s10s_zrev{zw}')
# slope trend
for lb in [63,126]:
    tr=(slope-slope.shift(lb)).reindex(r_sl.index)
    pos=pd.Series(np.nan,index=r_sl.index); pos[tr>0]=1; pos[tr<0]=-1; pos=pos.ffill().fillna(0)
    trade(pos,r_sl,f'2s10s_mom{lb}')
