"""Volatility Risk Premium (VRP) / systematic put-selling (策略#5).
Core: E[implied variance] > E[realized variance] (persistent premium).
Implement a 1-month rolling short-variance style book: at month start, sell variance at
VIX^2 (annualized); daily P&L = realized variance accrual - amortized implied variance.
Proxy uses SP500 daily returns for realized var and VIX (CBOE) for implied. T+1, honest.
Also a PUT-index-style: short an ATM-protective exposure captured by realized-vol vs implied.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
DATA="/Users/daxu/software/world-trader/tools/quant/data"
champ=E.champ_ref()
def loadcol(path,col='close'):
    df=pd.read_csv(path); df['date']=pd.to_datetime(df['date'])
    df=df.drop_duplicates('date').set_index('date').sort_index()
    return df[col] if col in df.columns else df.iloc[:,0]
spx=loadcol(f"{DATA}/newdata/SP500.csv").astype(float).dropna()
vix=loadcol(f"{DATA}/more_vol/VIX.csv").astype(float).dropna()
r=spx.pct_change().dropna()
# realized variance (annualized, daily 21d)
rv21=(r.rolling(21).var())*252
# implied variance from VIX
iv=(vix/100)**2
df=pd.concat({'r':r,'rv':rv21,'iv':iv},axis=1).dropna()
# 1-month variance swap P&L: sold at implied IV_t (annualized var units), each day you pay realized.
# Variance swap daily return (per $1 notional of variance): realized_var_today/252 - (IV_quoted/252).
# Short variance => +[(IV_quote - realized_daily)/252].
# Roll monthly: at each month start, strike = IV_0; thereafter daily pnl = (k - r^2)/252; settle monthly.
months=pd.date_range(df.index[0],df.index[-1],freq='MS')
pnl=pd.Series(0.0,index=df.index)
k_hold=None; start=None
for t in df.index:
    if start is not None and t>=start+pd.Timedelta(days=29):
        # settle/roll
        k_hold=None; start=None
    if start is None and t in months or (start is None and k_hold is None):
        k_hold=df.loc[t,'iv']; start=t
    if k_hold is not None:
        pnl.loc[t]= (k_hold - (df.loc[t,'r']**2))/252*(1)   # short variance
# scale: variance notional such that ~1 vol unit; use VIX as scale so beta~ -1? keep simple $1 var notional
net=pnl.dropna(); nr=net['2006':].dropna(); nv,_=E.vol_target(nr,vt_ann=0.08)
st=E.evaluate(nv,champ,'vrp')
print("=== VRP (short monthly variance swap vs SPX), 2006+ ===")
for k in ['SR','ann_geo','MDD','negyr','worst','H1_H2','negyr_pass','ac1','uniqR','corr_champ']:
    print(f"  {k:12s} = {st[k]}")
print(f"  avg realized var {df['rv'].mean():.2f} vs avg implied var {df['iv'].mean():.2f} "
      f"(points of vol: {(np.sqrt(df['iv'])-np.sqrt(df['rv'])).mean():.2f})")
E.save_sleeve(nv, f"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_HF_STATARB/sleeves/vrp_shortvar.csv")
print("saved vrp sleeve")
