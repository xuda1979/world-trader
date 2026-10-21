"""P6: standalone short-VIX regime book (QAxasts attribution: VIX leg alone SR 1.08).
Mechanism: vol mean-reversion/regime: short 'vol' (VIX spot proxy) below MA189, long above.
NOTE (honesty): VIX spot is NOT tradeable; VIX futures roll cost is real on short side.
Test BOTH the raw claim (spot proxy) and a futures-realism haircut variant. Also test
MA grid 126/189/252 and a vol-of-vol dampener."""
import sys; sys.path.insert(0,'.')
from libb import *
import libb, pandas as pd, numpy as np
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
def fr(n):
    df=pd.read_csv(f'{FRED}/{n}.csv',index_col=0,parse_dates=True)
    s=pd.to_numeric(df.iloc[:,0],errors='coerce')
    return s[~s.index.duplicated(keep='last')].sort_index()
champ=F.load_champion()
vix=fr('VIXCLS').dropna()
vix=vix[vix>0]
r_v=vix.pct_change()  # proxy pnl = -pos * vix %chg (short below MA)

def run(ma=189, damp=0.0, tag='', roll_haircut=0.0):
    m=vix.rolling(ma).mean()
    pos=pd.Series(np.nan,index=vix.index)
    pos[vix<m]=-1.0   # short vol
    pos[vix>m]=1.0    # long vol
    pos=pos.ffill().fillna(0.0)
    if damp>0:
        z=(vix-m)/vix.rolling(ma).std()
        pos=pos*(1-damp*(z.abs()>2).astype(float))
    g=F.net_of(-pos,r_v)[0]
    if roll_haircut>0:
        g=g-roll_haircut/252
    s=F.vol_target_scale(g,vt=0.10,min_days=60,cap=3.0,trailing_shift=1)
    posv=-pos*s
    net=F.net_of(posv,r_v)[0]
    if roll_haircut>0: net=net-roll_haircut/252
    st=F.full_stats(net); h1,h2=F.halves_sr(net); fg=F.flatten_gates(net); corr,nn=F.corr_to(net,champ)
    pl,_=libb.book_position_lag_p(posv.to_frame('p'),r_v.to_frame('r'),n=200)
    yr=(1+net).groupby(net.index.year).prod()-1
    print(f"{tag} ma{ma} damp{damp} hc{roll_haircut}: SR {st['sr']:+.3f} ann {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% negy {st['negy']} worst {st['worst']*100:.1f}% | H1 {h1:+.2f} H2 {h2:+.2f} | poslag_p {pl:.3f} | ac1 {fg['ac1']:+.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f}(n={nn})")

for ma in [126,189,252]:
    run(ma=ma,tag='VIXSW')
run(ma=189,damp=0.5,tag='VIXSW')
run(ma=189,roll_haircut=0.03,tag='VIXSW')
run(ma=189,roll_haircut=0.08,tag='VIXSW')
