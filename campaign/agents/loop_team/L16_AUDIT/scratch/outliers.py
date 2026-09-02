import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
B=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
top=B.abs().sort_values(ascending=False).head(12)
print("top |daily| moves:"); print((top*100).round(2))
vol=B.std()*np.sqrt(252)
print(f"ann vol {vol*100:.2f}% daily vol {B.std()*100:.3f}%  -> max day = {B.abs().max()/B.std():.1f} sigma")
# sleeve contributions on the biggest day
Sn08=pd.DataFrame({n:vt(sn(p),0.08)[1] for n,p in POOL.items()}).dropna(how='all')
capW8=Sn08/N
V={}
for n in POOL:
    r=sn(POOL[n]); v,s=vt(r,0.08)
    V[n]=v-capW8[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
Vn=pd.DataFrame(V)
d=top.index[0]
print(f"\ncontrib on {d.date()} (bp):")
print((Vn.loc[d]*1e4).round(1).sort_values())
print(f"blend mean that day: {Vn.loc[Vn.index==d].mean(axis=1).iloc[0]*1e4:.1f}bp")
# raw sleeve returns that day
print("\nraw sleeve ret that day (bp):")
print(pd.Series({n:sn(POOL[n]).get(d,np.nan)*1e4 for n in POOL}).round(1))
# turnover mean
W=Sn08.div(Sn08.sum(axis=1),axis=0).fillna(0)
tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
print(f"\nmean one-side turnover (weights) {tw[tw.index>='2008-03-31'].mean()*100:.2f}%/day -> cost {tw.mean()*6:.2f}bp/day ~ {tw.mean()*6*252:.0f}bp/yr... wait units")
print(f"cost drag/yr from sleeve turnover: {tw[tw.index>='2008-03-31'].mean()*6e-4*252*100:.2f}%/yr")
