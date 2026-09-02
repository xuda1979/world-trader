import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
for cfg in ['BALANCED','SAFE','AGGRESSIVE']:
    r=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11X804_{cfg}_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
    eq=(1+r).cumprod()
    ann=(eq.iloc[-1]**(252/len(r))-1)*100
    print(f"X804 {cfg}: n={len(r)} ann(geo) {ann:.1f}% SR_d {r.mean()/r.std()*np.sqrt(252):.2f}")
# pub-def gross for X804: per-sleeve scales at 0.10 (committed builder Sn convention) with global .11/.14 blend
Sn10=pd.DataFrame({n:vt(sn(p),0.10)[1] for n,p in POOL.items()}).dropna(how='all')
V={}
for n in POOL:
    r=sn(POOL[n]); v,s=vt(r,0.10)
    V[n]=v-capW[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
Vn=pd.DataFrame(V)
blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
bA,sbA=vt(blend,0.11); bB,sbB=vt(blend,0.14)
g=0.5*(Sn10.mean(axis=1)*sbA+Sn10.mean(axis=1)*sbB)
print(f"X804 pub-def gross (EW per-sleeve scale, pre-throttle): mean {g[g.index>='2008-03-31'].mean():.2f}x max {g[g.index>='2008-03-31'].max():.2f}x p95 {g[g.index>='2008-03-31'].quantile(.95):.2f}x")
gall=0.5*(Sn10.mean(axis=1)*sbA*sbA+Sn10.mean(axis=1)*sbB*sbB)
print(f"X804 all-in (x global scalar): mean {gall[gall.index>='2008-03-31'].mean():.2f}x max {gall[gall.index>='2008-03-31'].max():.2f}x")
