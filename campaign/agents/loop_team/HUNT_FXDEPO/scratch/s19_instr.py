"""Tradeability documentation for FXD1_KRWTRI: instruments + price paths for the audit.
KRW/SEK etc are NDF/spot crosses. Verify price-path reconstruction: DEXKOUS/DEXSDUS spread
path vs what the engine traded; sample of the largest trades; realistic cost check (KRW NDF
costs 5-15bps at bank level; we charge 6.4bps total per side-pair? Document honestly)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

px=pd.DataFrame({n:dex(n) for n in ['DEXKOUS','DEXSDUS','DEXSFUS','DEXNOUS']})
lp=np.log(px)
sp=lp['DEXKOUS']-lp['DEXSDUS']
print('KRW/SEK cross rate: mean %.4f min %.4f max %.4f (KRW per SEK via USD)'%(
    (px['DEXKOUS']/px['DEXSDUS']).mean(),(px['DEXKOUS']/px['DEXSDUS']).min(),(px['DEXKOUS']/px['DEXSDUS']).max()))
sp2=lp['DEXKOUS']-lp['DEXSFUS']
print('KRW/CHF cross: mean %.4f; KRW/NOK mean %.4f'%((px['DEXKOUS']/px['DEXSFUS']).mean(),(px['DEXKOUS']/px['DEXNOUS']).mean()))
# largest 5-day contributions (trade record sample)
books=[('DEXKOUS','DEXSDUS'),('DEXKOUS','DEXSFUS'),('DEXKOUS','DEXNOUS')]
rs=[]
for a,b in books:
    pos=sum(zpos(lp[a]-lp[b],lb,2.0) for lb in (21,63))/2
    rs.append(net_of_book(pd.DataFrame({a:pos,b:-pos}),pd.DataFrame({a:px[a].pct_change(),b:px[b].pct_change()})).fillna(0))
r=pd.concat(rs,axis=1).sum(axis=1)/3
big=r.abs().nlargest(10)
print('\ntop-10 |daily PnL| days (trade-record anchors):')
for d,v in big.items(): print(f'  {d.date()}: {v*100:+.3f}%')
print('\nzero-run check (flatten gate):')
z=(r==0).astype(int); mx=c=0
for v in z: c=c+1 if v else 0; mx=max(mx,c)
print('  max zero-run days:',mx,' (continuous-weight book, no gates -> expected 1)')
