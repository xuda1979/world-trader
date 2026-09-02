import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
cal=USFederalHolidayCalendar()
Sn10=pd.DataFrame({n:vt(sn(p),0.10)[1] for n,p in POOL.items()}).dropna(how='all')
Sn08=pd.DataFrame({n:vt(sn(p),0.08)[1] for n,p in POOL.items()}).dropna(how='all')
m8=Sn08[Sn08.index>='2008-03-31'].mean(axis=1); m10=Sn10[Sn10.index>='2008-03-31'].mean(axis=1)
print(f"EW per-sleeve scale (pre-throttle), 2008+ mean: perslv0.08 {m8.mean():.3f}x | perslv0.10 {m10.mean():.3f}x")
print(f"  p95 0.08: {m8.quantile(.95):.3f}x max {m8.max():.3f}x | p95 0.10: {m10.quantile(.95):.3f}x max {m10.max():.3f}x")
# global scalars means
V8={};V10={}
capW8=Sn08/N; capW10=Sn10/N
for n in POOL:
    r=sn(POOL[n])
    v8,s8=vt(r,0.08); v10,s10=vt(r,0.10)
    V8[n]=v8-capW8[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
    V10[n]=v10-capW10[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
b8_07,_=vt(pd.DataFrame(V8).mean(axis=1)[lambda x:x.index>='2006-10-01'],0.07)
b8_091,_=vt(pd.DataFrame(V8).mean(axis=1)[lambda x:x.index>='2006-10-01'],0.091)
b10_11,_=vt(pd.DataFrame(V10).mean(axis=1)[lambda x:x.index>='2006-10-01'],0.11)
print(f"global vt scalar mean 2008+: L16-A(0.07) {b8_07[b8_07.index>='2008-03-31'].mean():.3f}x  L16-B(0.091) {b8_091[b8_091.index>='2008-03-31'].mean():.3f}x  X804-A(0.11) {b10_11[b10_11.index>='2008-03-31'].mean():.3f}x")
print(f"all-in L16 BAL mean = EW08 x scalar: {m8.mean():.3f} x 2.1-ish; exact from earlier: 3.429x")
