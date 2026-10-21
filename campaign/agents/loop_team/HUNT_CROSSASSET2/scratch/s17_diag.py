"""SEC3 (P3 zs c1.5 lb15) diagnostics: T+2 lag, OOS, cost decomposition, marginal blend value."""
import sys; sys.path.insert(0,'.')
import pandas as pd, numpy as np
from s16_sweep import mkbook, etf, X, P3, COST
from lib import full_stats, load_blend, BORROW
res=[mkbook(X[a],X[b],15,1.5,'zs') for a,b in P3]
net=pd.concat([x[0] for x in res],axis=1).mean(axis=1)
r2=net[net.index>='2008-01-01']
st=full_stats(r2)
print('SEC3 SR %.3f ann %.2f%%'%(st['sr'],st['ann_geo']*100))
# cost decomposition
P=pd.concat([x[1] for x in res],axis=1)
tot=[]
for x in res:
    p=x[1]
    t=(p.shift(1).fillna(0).diff().abs()/2.0).fillna(0.0).sum(axis=1)
    tot.append(t)
turn=pd.concat(tot,axis=1).mean(axis=1).loc['2008':]
print('one-side turnover/day mean %.3f max %.2f -> cost drag %.2f%%/yr'%(turn.mean(),turn.max(),turn.mean()*6.0*1e-4*252*100))
print('borrow drag ~%.2f%%/yr'%(BORROW*pd.concat([x[1].shift(1).fillna(0).clip(upper=0).abs().sum(axis=1) for x in res],axis=1).mean(axis=1).loc['2008':].mean()*252*100))
print('gross exposure mean %.2f max %.2f'%(pd.concat([(x[1].shift(1).fillna(0).abs().sum(axis=1)) for x in res],axis=1).mean(axis=1).loc['2008':].mean(),
      pd.concat([(x[1].shift(1).fillna(0).abs().sum(axis=1)) for x in res],axis=1).max(axis=1).loc['2008':].max()))
# T+2: extra lag
for extra in [1,2]:
    tot=0
    for x in res:
        p=x[1].shift(extra).fillna(0)
        g=(p*x[2]).sum(axis=1)
        t=(p.diff().abs()/2.0).fillna(0).sum(axis=1)
        b=BORROW*p.clip(upper=0).abs().sum(axis=1)
        tot=tot+g-t*COST-b
    rr=(tot/3)[tot.index>='2008-01-01']
    print(f'T+{extra+1} SR {rr.mean()/rr.std()*np.sqrt(252):.3f}')
# OOS
for a,b in [('2017-01-01','OOS17+'),('2020-01-01','OOS20+'),('2023-01-01','OOS23+')]:
    rr=r2[r2.index>=a]
    print(f'{b} SR {rr.mean()/rr.std()*np.sqrt(252):.3f}')
# LOYO
loyo=r2.groupby(r2.index.year).apply(lambda x:x.mean()/x.std()*np.sqrt(252))
print('LOYO min %.3f (%d) max %.3f (%d)'%(loyo.min(),loyo.idxmin(),loyo.max(),loyo.idxmax()))
# scrub
top=r2.abs().sort_values(ascending=False)
for k in [5,10,20]:
    rr=r2.drop(top.index[:k])
    print(f'scrub{k} SR {rr.mean()/rr.std()*np.sqrt(252):.3f}')
# marginal blend value
b=load_blend()
for w in [0.05,0.10,0.15]:
    m=b*(1-w)+net.reindex(b.index).fillna(0)*w
    m2=m[m.index>='2008-01-01']
    b2=b[b.index>='2008-01-01']
    yr=m2.groupby(m2.index.year).apply(lambda x:(1+x).prod()-1)
    print(f'w={w}: champ SR {b2.mean()/b2.std()*np.sqrt(252):.3f} -> blend SR {m2.mean()/m2.std()*np.sqrt(252):.3f} ann {((m2+1).prod())**(252/len(m2))-1:.3f} negy {(yr<0).sum()}')
