import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
STRICT={
 "brwt15":"campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10":"campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7":"campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5":"campaign/agents/COORD/sleeves/brwt5.csv",
 "C5ng":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2":"campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7":"campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "XGB1y":"campaign/results/sleeve_library/XGB1y_deploy.csv",
}
cal=USFederalHolidayCalendar(); hol=set(cal.holidays(start='2006-01-01',end='2026-12-31').date)
def sn(p):
    r=load(p).dropna()
    keep=np.array([(d.dayofweek<5 and d.date() not in hol) for d in r.index])
    out=pd.Series(0.0,index=r.index[keep]); cu=0.0; ki=0; v=r.values
    for i in range(len(r)):
        cu+=v[i]
        if keep[i]: out.iloc[ki]=cu; cu=0.0; ki+=1
    return out.iloc[:ki]
S={}
for n,p in STRICT.items():
    r=sn(p); v,s=vt(r,0.10); S[n]=s
Sn=pd.DataFrame(S).dropna(how='all')
gross = Sn.abs().mean(axis=1)  # mean per-sleeve gross weight (each |scale| up to 8x vt10 => weight 8/12 max)
blend_rebuilt_gross = Sn.abs().sum(axis=1)/12
# global vt scale:
capW=Sn/12
import numpy as np
V={}; 
for n in STRICT:
    r=sn(p) if False else None
for n in STRICT:
    r=sn(STRICT[n]); v,_=vt(r,0.10); V[n]=v
Vn=pd.DataFrame(V)
blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
b,_=vt(blend,0.091)  # B target
eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
sc=pd.Series(np.where(tdd<-0.03,0.5,1.0),index=b.index)
total_gross = (blend_rebuilt_gross*sc).reindex(b.index).dropna()
print(f"implied portfolio gross (sum |scale|/12 x throttle): mean {total_gross.mean():.2f}x p95 {total_gross.quantile(0.95):.2f}x max {total_gross.max():.2f}x")
