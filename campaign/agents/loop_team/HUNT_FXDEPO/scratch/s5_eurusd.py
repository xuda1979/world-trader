"""Sanity: reproduce CFX4 books on the SAME harness to validate that my engine reproduces
their edge (validates harness), then test the EURO-USD and GBP-USD books themselves
(the two pairs with clean opens; FXMICRO's drop-test says dropping EUR_USD/GBP_USD kills it
=> these legs carry the edge)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

P=pd.DataFrame({n:twelvedata(n) for n in
    ['AUD_USD','EUR_GBP','EUR_USD','GBP_USD','NZD_USD','USD_CAD','USD_CHF','USD_JPY']}).dropna(how='any')
lp=np.log(P)
champ=load_champion()

books=[('GBP_USD','NZD_USD'),('AUD_USD','GBP_USD'),('AUD_USD','EUR_USD'),('EUR_USD','NZD_USD')]
# CFX4 = 4-book (21,63) dual-tf, cap2
def cfx4_ret(booklist, lbs=(21,63)):
    tot=0; cnt=0
    for a,b in booklist:
        sp=lp[a]-lp[b]
        pos=sum(zpos(sp,lb) for lb in lbs)/len(lbs)
        ra=P[a].pct_change(); rb=P[b].pct_change()
        r=net_of_book(pd.DataFrame({a:pos,b:-pos}),pd.DataFrame({a:ra,b:rb}))
        tot=tot+r.fillna(0); cnt+=1
    return (tot/cnt).dropna()

r4=cfx4_ret(books)
r8=r4[r4.index>='2008-01-01'] if False else r4
st=full_stats(r4)
print('CFX4 reproduction: SR %.3f ann %.2f%% MDD %.2f%% n=%d %s..%s'%(st['sr'],st['ann_geo']*100,st['mdd']*100,len(r4),st['first'],st['last']))
cfx_ref=pd.read_csv(f'{ROOT}/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
j=pd.concat([r4.rename('mine'),cfx_ref.rename('ref')],axis=1,join='inner').dropna()
print('corr to committed CFX4: %+.4f  max|diff| %.4f (vol scaling differs per CARRYFX finding)'%(j['mine'].corr(j['ref']), (j['mine']-j['ref']).abs().max()))

# single EUR_USD and GBP_USD legs vs USD, dual-tf z on log ccy
rows=[]
for c in ['EUR_USD','GBP_USD','AUD_USD','NZD_USD','USD_JPY','USD_CAD','USD_CHF','EUR_GBP']:
    sp=lp[c]
    for lb in [21,42,63,(21,63)]:
        lbs=lb if isinstance(lb,tuple) else (lb,)
        pos=sum(zpos(sp,l) for l in lbs)/len(lbs)
        r=net_of_book(pd.DataFrame({c:pos}),pd.DataFrame({c:P[c].pct_change()}))
        r8=r[r.index>='2019-10-01'].dropna()
        stt=full_stats(r8); h1,h2=halves_sr(r8)
        corr,nc=corr_to(r8,champ)
        rows.append(dict(pair=c,lb=str(lb),sr=round(stt['sr'],3),h1=round(h1,2),h2=round(h2,2),
                         mdd=round(stt['mdd']*100,1),ann=round(stt['ann_geo']*100,2),
                         negy=stt['negy'],corr14=round(corr,3)))
df=pd.DataFrame(rows).sort_values('sr',ascending=False)
print(df.to_string(index=False))
