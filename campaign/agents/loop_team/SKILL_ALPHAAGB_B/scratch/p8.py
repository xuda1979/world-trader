"""P8: 3-book portfolio — USDJPY short-JPY weekday core + FX mom satellites, honest daily PnL.
Core pos: long USDJPY Mon-Wed, short Thu-Fri. Satellites: 63d FX trend (3 pairs). EW vt10 blend.
Then full battery on the blend."""
import sys; sys.path.insert(0,'.')
from libb import *
import libb, pandas as pd, numpy as np
ROOT2='/Users/daxu/software/world-trader/tools/quant/data/fx'
def fxr(n):
    df=pd.read_csv(f'{ROOT2}/{n}.csv',index_col=0,parse_dates=True)
    s=df.iloc[:,0]; s=pd.to_numeric(s,errors='coerce')
    return s[~s.index.duplicated(keep='last')].sort_index()
champ=F.load_champion()
jpy=fxr('USD_JPY').dropna()

# --- core book
r=jpy.pct_change()
pos=pd.Series(0.0,index=r.index)
for d,b in [(0,1),(1,1),(2,1),(3,-1),(4,-1)]: pos[r.index.dayofweek==d]=b  # long USDJPY M-W, short Th-F
g=F.net_of(pos,r)[0]
s=F.vol_target_scale(g,vt=0.10,min_days=60,cap=3.0,trailing_shift=1)
posv_core=pos*s
net_core=F.net_of(posv_core,r)[0]
print('core alone:', {k:(round(v,4) if isinstance(v,float) else v) for k,v in F.full_stats(net_core).items() if k in ('sr','ann_geo','mdd','negy')})

# --- satellites: FX trend 63d on 3 pairs, L/S vs 0
sats={}
for n in ['EUR_USD','GBP_USD','AUD_USD']:
    p=fxr(n).dropna(); rr=p.pct_change()
    tr=p-p.shift(63)
    ps=pd.Series(np.nan,index=p.index); ps[tr>0]=1.0; ps[tr<0]=-1.0; ps=ps.ffill().fillna(0.0)
    g2=F.net_of(ps,rr)[0]
    s2=F.vol_target_scale(g2,vt=0.10,min_days=60,cap=3.0,trailing_shift=1)
    posv=ps*s2; net=F.net_of(posv,rr)[0]
    sats[n]=(posv,rr,net)
    stt=F.full_stats(net)
    print(f'sat {n} tsmom63: SR {stt["sr"]:+.3f} ann {stt["ann_geo"]*100:+.1f}%')

# --- EW blend of 4 books (0.25 each, vt10 each already): renormalize
idx=net_core.index
parts=[net_core.reindex(idx).fillna(0)]
for n in sats: parts.append(sats[n][2].reindex(idx).fillna(0))
blend=sum(parts)/len(parts)
blend=blend[blend.index>='2008-01-01']
st=F.full_stats(blend); h1,h2=F.halves_sr(blend); fg=F.flatten_gates(blend); corr,nn=F.corr_to(blend,champ)
print(f"P8 blend: SR {st['sr']:+.3f} ann {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% negy {st['negy']} worst {st['worst']*100:.1f}% | H1 {h1:+.2f} H2 {h2:+.2f} | ac1 {fg['ac1']:+.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f}(n={nn})")
