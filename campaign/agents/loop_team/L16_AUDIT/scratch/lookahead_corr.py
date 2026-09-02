import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
B=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
# sleeve net contributions V[n] (post costs, per-sleeve vt 0.08)
Sn08=pd.DataFrame({n:vt(sn(p),0.08)[1] for n,p in POOL.items()}).dropna(how='all')
capW8=Sn08/N
V={}
for n in POOL:
    r=sn(POOL[n]); v,s=vt(r,0.08)
    V[n]=v-capW8[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
Vn=pd.DataFrame(V)
lead_lag={}
for lag in [-2,-1,0,1,2]:
    cs=[]
    for n in POOL:
        x=B.reindex(Vn.index)
        y=Vn[n].shift(lag)
        j=pd.concat([x.rename('x'),y.rename('y')],axis=1).dropna()
        j=j[j.index>='2008-03-31']
        cs.append(j.x.corr(j.y))
    lead_lag[lag]=np.mean(cs)
print("mean corr(BAL_t, sleevecontrib_{t+lag}) per sleeve:")
for lag,v in lead_lag.items(): print(f"  lag {lag:+d}: {v:.4f}")
# corr matrix of sleeve contributions (2008+)
C=Vn[Vn.index>='2008-03-31'].corr()
print("\nsleeve contrib corr (2008+), mean pairwise:",round(float(C.values[np.triu_indices(11,1)].mean()),3))
print(C.round(2).to_string())
# throttle sanity: how often tripped in A/B
