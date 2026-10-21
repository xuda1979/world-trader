"""IDEA 2: cross-rate TRIANGLE books on twelvedata majors (2019-06..2026-08).
CFX4 trades (GBP/NZD, AUD/GBP, AUD/EUR, EUR/NZD) — all other synthetic crosses are new.
25 crosses: z-reversion, lb 21/42/63, T+1, 6bps/side, borrow 0.5%/yr.
"""
import sys, numpy as np, pandas as pd, itertools
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

P=pd.DataFrame({n:twelvedata(n) for n in
    ['AUD_USD','EUR_GBP','EUR_USD','GBP_USD','NZD_USD','USD_CAD','USD_CHF','USD_JPY']}).dropna(how='any')
print('common window',P.index[0].date(),P.index[-1].date(),len(P))

# per-USD value of currency c: EUR/GBP/AUD/NZD quoted USD-per-ccy; CAD/CHF/JPY ccy-per-USD
def usdv(c):
    n=f'{c}_USD'
    return P[n] if n in P.columns else 1.0/P[f'USD_{c}']
USDV={c:usdv(c) for c in ['AUD','EUR','GBP','NZD','CAD','CHF','JPY']}

majs=['AUD','EUR','GBP','NZD','CAD','CHF','JPY']
crosses={f'{b}{q}': USDV[q]/USDV[b] for b,q in itertools.combinations(majs,2)}
def ccret(c):
    return USDV[c].pct_change()

lp=np.log(pd.DataFrame(crosses))
champ=load_champion()
cfx=pd.read_csv(f'{ROOT}/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv',
                index_col=0,parse_dates=True).iloc[:,0]
rows=[]
for cname,(b,qqq) in [(c,(c[:3],c[3:])) for c in crosses]:
    sp=lp[cname]
    for lb in [21,42,63]:
        pos=zpos(sp,lb)
        rb, rq = ccret(b), ccret(qqq)
        r=net_of_book(pd.DataFrame({'b':pos,'q':-pos}),pd.DataFrame({'b':rb,'q':rq}))
        r8=r[r.index>='2019-10-01'].dropna()
        if len(r8)<1000: continue
        st=full_stats(r8); h1,h2=halves_sr(r8)
        corr,nc=corr_to(r8,champ); corrc,_=corr_to(r8,cfx)
        rows.append(dict(cross=cname,lb=lb,sr=round(st['sr'],3),h1=round(h1,2),h2=round(h2,2),
                         mdd=round(st['mdd']*100,1),ann=round(st['ann_geo']*100,2),negy=st['negy'],
                         corr14=round(corr,3),corr_cfx=round(corrc,3)))
df=pd.DataFrame(rows).sort_values('sr',ascending=False)
print(df.head(30).to_string(index=False))
df.to_csv(f'{ROOT}/campaign/agents/loop_team/HUNT_FXDEPO/scratch/s4_grid.csv',index=False)
