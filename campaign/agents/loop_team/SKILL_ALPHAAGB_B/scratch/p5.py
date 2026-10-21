"""P5: credit z-reversion via baa-aaa spread with synthetic duration on SPY-hedge-free book.
Mechanism: spread widening overshoots; reversion long credit (SPY proxy) when z high.
Credits: spread z as signal, position on SPY (credit-risk proxy)."""
import sys; sys.path.insert(0,'.')
from libb import *
import libb, pandas as pd, numpy as np
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
def fr(n):
    df=pd.read_csv(f'{FRED}/{n}.csv',index_col=0,parse_dates=True)
    s=pd.to_numeric(df.iloc[:,0],errors='coerce')
    return s[~s.index.duplicated(keep='last')].sort_index()
champ=F.load_champion()
px=panel_closes('twelve_big'); spy=px['SPY'].dropna()
baa=fr('baa'); aaa=fr('aaa')
spr=(baa-aaa).dropna()
r=spy.pct_change()

def trade(pos,r,tag,vt=0.10):
    pos=pos.reindex(r.index).fillna(0.0)
    g0=F.net_of(pos,r)[0]
    s=F.vol_target_scale(g0,vt=vt,min_days=60,cap=3.0,trailing_shift=1)
    posv=pos*s; net=F.net_of(posv,r)[0]
    st=F.full_stats(net); h1,h2=F.halves_sr(net); fg=F.flatten_gates(net); corr,nn=F.corr_to(net,champ)
    pl,_=libb.book_position_lag_p(posv.to_frame('p'),r.to_frame('r'),n=200)
    print(f"{tag}: SR {st['sr']:+.3f} ann {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% negy {st['negy']} worst {st['worst']*100:.1f}% | H1 {h1:+.2f} H2 {h2:+.2f} | poslag_p {pl:.3f} | ac1 {fg['ac1']:+.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f}(n={nn})")

for zw in [63,126]:
    z=((spr-spr.rolling(zw).mean())/spr.rolling(zw).std())
    # mean-reversion of spread: short SPY when spread z high (credit stress hits equities), long when low
    pos=pd.Series(0.0,index=spr.index); pos[z>1.0]=-1.0; pos[z<-1.0]=1.0
    pos=pos.replace(np.nan,0.0).ffill().fillna(0.0)
    trade(pos,r,f'credit_z{zw}_spyrev')
    # momentum variant: follow spread direction (credit trend => equity risk)
    pos2=pd.Series(np.nan,index=spr.index)
    tr=spr.diff(21); pos2[tr>0]=-1.0; pos2[tr<0]=1.0; pos2=pos2.ffill().fillna(0.0)
    trade(pos2,r,f'credit_mom21_spy')
# also raw z as continuous signal
z126=((spr-spr.rolling(126).mean())/spr.rolling(126).std()).clip(-2,2)
pos3=(-z126/2).reindex(r.index).ffill().fillna(0.0)
trade(pos3,r,'credit_z126_cont_spy')
