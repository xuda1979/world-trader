"""FINAL AUDIT of FXD1_KRWTRI_raw (the only candidate): 
1. Re-verify saved CSV loads & matches in-memory series (byte check).
2. neg-yr floor check exact (each neg yr > -5%).
3. 3-seed scramble + seed-robustness.
4. Turnover/cost decomposition + gross exposure (no hidden leverage).
5. T+1 honesty probe: corr(pos_t, ret_t+1) vs corr(pos_t, ret_t) — no same-day leak.
6. corr vs CFX4 (dedup requirement).
7. max|day|.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

f=f'{ROOT}/campaign/agents/loop_team/HUNT_FXDEPO/sleeves/FXD1_KRWTRI_raw_daily.csv'
sv=pd.read_csv(f,index_col=0,parse_dates=True).iloc[:,0]
print('saved file: n=%d %s..%s sha? sum=%.6f'%(len(sv),sv.index[0].date(),sv.index[-1].date(),sv.sum()))

px=pd.DataFrame({n:dex(n) for n in ['DEXKOUS','DEXSDUS','DEXSFUS','DEXNOUS']})
lp=np.log(px); rets=px.pct_change()
books=[('DEXKOUS','DEXSDUS'),('DEXKOUS','DEXSFUS'),('DEXKOUS','DEXNOUS')]
rs=[]; POSs=[]
for a,b in books:
    sp=lp[a]-lp[b]
    pos=sum(zpos(sp,lb,2.0) for lb in (21,63))/2
    POSs.append(pos)
    rs.append(net_of_book(pd.DataFrame({a:pos,b:-pos}),pd.DataFrame({a:rets[a],b:rets[b]})).fillna(0))
r=pd.concat(rs,axis=1).sum(axis=1)/3
r8=r[r.index>='2008-01-01']
j=pd.concat([r8.rename('mem'),sv.rename('file')],axis=1,join='inner').dropna()
print('file vs in-memory max|diff| = %.2e'%(j['mem']-j['file']).abs().max())

# neg years exact
st=full_stats(sv)
neg={k:v for k,v in st['yearly'].items() if v<0}
print('neg years (file):',neg,' all > -5%?', all(v>-5 for v in neg.values()), 'count',len(neg))

# scramble 3 seeds
POSa=pd.concat([p.rename(f'B{i}') for i,p in enumerate(POSs)],axis=1)
POSa=pd.concat([POSa.rename(columns={f'B{i}':f'B{i}_L' for i in range(3)}),
                (-POSa).rename(columns={f'B{i}':f'B{i}_S' for i in range(3)})],axis=1).shift(1).reindex(sv.index).fillna(0)
RETa=pd.concat([rets[a].rename(f'B{i}_L') for i,(a,b) in enumerate(books)]
              +[rets[b].rename(f'B{i}_S') for i,(a,b) in enumerate(books)],axis=1).reindex(sv.index).fillna(0)[POSa.columns]
for seed in [0,1,2]:
    p,real=position_lag_block_p(POSa,RETa,n=200,seed=seed)
    print(f'poslag-block scramble seed{seed}: p={p:.4f} (real SR {real:.3f})')

# turnover & gross
turn=(POSa.diff().abs()/2.0).fillna(0).sum(axis=1)
gross=(POSa*RETa).sum(axis=1)
print('turnover one-side/day: mean %.3f max %.3f | cost drag %.2f%%/yr | borrow %.3f%%/yr'%(
    turn.mean(),turn.max(),turn.mean()*COST*252*100,BORROW*np.clip(POSa,0,None).sum(axis=1).mean()*252*100))
print('gross exposure: mean %.3f max %.3f'%(POSa.abs().sum(axis=1).mean()/3,POSa.abs().sum(axis=1).max()/3))

# T+1 probe: effective pos (shifted) vs same-day return alignment — should NOT be pos_t*ret_t
eff=POSa  # already shifted
same_day=pd.concat([pos.rename(f'B{i}') for i,pos in enumerate(POSs)],axis=1)
same_day=pd.concat([same_day.rename(columns={f'B{i}':f'B{i}_L' for i in range(3)}),
                (-same_day).rename(columns={f'B{i}':f'B{i}_S' for i in range(3)})],axis=1)
sd=(same_day.reindex(sv.index).fillna(0)*RETa).sum(axis=1)
print('T+1 probe: corr(same-day-align PnL, delivered) = %+.4f — same-day would inflate; delivered is shift(1)'%sd.corr(sv))

# corr vs CFX4 on full common
cfx=pd.read_csv(f'{ROOT}/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
cc=pd.concat([sv.rename('s'),cfx.rename('c')],axis=1,join='inner').dropna()
print('corr(FXD1, CFX4) full common: %+.4f n=%d'%(cc['s'].corr(cc['c']),len(cc)))
print('max|day|: %.3f%% on %s'%(sv.abs().max()*100, sv.abs().idxmax().date()))
# H1/H2 recheck on file
h1,h2=halves_sr(sv); print('halves on file: H1 %.3f H2 %.3f'%(h1,h2))
