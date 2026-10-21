import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
Sn08=pd.DataFrame({n:vt(sn(p),0.08)[1] for n,p in POOL.items()}).dropna(how='all')
capW8=Sn08/N
# per-sleeve scale turnover (rebalancing of the vol-target overlay): |d(S_n)|/N summed
dS=Sn08.diff().abs()
sleeve_rebal_one_side = dS.sum(axis=1)/N   # fraction of NAV traded per day (one-side), sleeve level
# global scale turnover: |d(global scalar)| applied to blend notional
V={}
for n in POOL:
    r=sn(POOL[n]); v,s=vt(r,0.08)
    V[n]=v-capW8[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
Vn=pd.DataFrame(V)
blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
_,sb=vt(blend,0.07); _,sb2=vt(blend,0.091)
gs=0.5*(sb+sb2)
glob_rebal = gs.diff().abs().fillna(0)  # one-side turnover from global overlay (approx: blend notional=1 pre-throttle? scalar applies to normalized notional)
tot_missing = (sleeve_rebal_one_side + glob_rebal).reindex(blend.index)
tot_missing = tot_missing[tot_missing.index>='2008-03-31']
cost_miss = (tot_missing*6e-4)
print(f"missing rebalance turnover: sleeve-overlay {sleeve_rebal_one_side[sleeve_rebal_one_side.index>='2008-03-31'].mean()*100:.3f}%/day, global {glob_rebal[glob_rebal.index>='2008-03-31'].mean()*100:.3f}%/day")
print(f"missing cost drag: {cost_miss.mean()*252*100:.2f}%/yr (mean), p95 {cost_miss.quantile(.95)*252*100:.2f}%/yr")
# charged costs for comparison
W=Sn08.div(Sn08.sum(axis=1),axis=0).fillna(0)
tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
print(f"charged sleeve-turnover cost: {tw[tw.index>='2008-03-31'].mean()*6e-4*252*100:.2f}%/yr")
# apply missing costs to committed BAL
B=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
B2=B - cost_miss.reindex(B.index).fillna(0)
eq=(1+B2).cumprod(); m=(1+B2).resample('ME').prod()-1
y=B2.groupby(B2.index.year).apply(lambda x:(1+x).prod()-1)
print(f"BAL + missing rebalance costs: ann {(eq.iloc[-1]**(252/len(B2))-1)*100:.1f}% SR_d {B2.mean()/B2.std()*np.sqrt(252):.2f} MDD {(eq/eq.cummax()-1).min()*100:.2f}% neg {(y<0).sum()} worst {y.min()*100:.1f}%")
