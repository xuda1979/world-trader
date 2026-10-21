"""P9: FX day-of-week microstructure. P7 found USDJPY Tue +7.94bp/d raw. Test:
(1) per-dow t-stats USDJPY; (2) dow means across all 8 pairs (is it FX-wide?);
(3) honest book: long JPY-exposure days only, flat otherwise, weekday-map-scramble +
year LOO + multiple-testing-aware verdict."""
import sys; sys.path.insert(0,'.')
from libb import *
import libb, pandas as pd, numpy as np
ROOT2='/Users/daxu/software/world-trader/tools/quant/data/fx'
def fxr(n):
    df=pd.read_csv(f'{ROOT2}/{n}.csv',index_col=0,parse_dates=True)
    s=pd.to_numeric(df.iloc[:,0],errors='coerce')
    return s[~s.index.duplicated(keep='last')].sort_index().dropna()
champ=F.load_champion()
pairs=['USD_JPY','EUR_USD','GBP_USD','USD_CAD','AUD_USD','NZD_USD','USD_CHF','EUR_GBP']
R={}
for n in pairs:
    p=fxr(n); R[n]=p.pct_change()
    r=R[n]
    m=r.groupby(r.index.dayofweek).agg(['mean','std','count'])
    t=m['mean']/(m['std']/np.sqrt(m['count']))
    print(n, {d:round(v*1e4,1) for d,v in m['mean'].items()}, 't:',{d:round(v,2) for d,v in t.items()})
# USDJPY tue t-stat detail
r=R['USD_JPY']; tue=r[r.index.dayofweek==2].dropna()
print('USDJPY Tue: mean %.2f bp, t %.2f, n %d, span %s..%s'%(tue.mean()*1e4, tue.mean()/tue.std()*np.sqrt(len(tue)), len(tue), tue.index.min().date(), tue.index.max().date()))
# yearly tue mean
yt=tue.groupby(tue.index.year).agg(['mean','count'])
yt['bp']=yt['mean']*1e4
print('USDJPY Tue bp by year:'); print(yt['bp'].round(1).to_string())
