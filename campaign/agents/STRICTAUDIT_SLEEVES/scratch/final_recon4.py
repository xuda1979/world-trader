import pandas as pd, numpy as np
SLEEVES = {
 'brwt15': '../../../agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv',
 'brwt10': '../../../agents/COORD/sleeves/brwt10_2000.csv',
 'brwt7':  '../../../agents/COORD/sleeves/brwt7.csv',
 'brwt5':  '../../../agents/COORD/sleeves/brwt5.csv',
 'C5ng':   '../../../agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv',
 'C5ngsum':'../../../agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv',
 'A5r2':   '../../../agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv',
 'a6r7':   '../../../agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv',
 'QAxasts':'../../../agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv',
 'carryv2':'../../../agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv',
 'dualmom':'../../../agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv',
 'XGB1y':  '../../../results/sleeve_library/XGB1y_deploy.csv',
}
P = {k: pd.to_numeric(pd.read_csv(p,parse_dates=['date']).set_index('date')['ret'],errors='coerce') for k,p in SLEEVES.items()}
def vt10(r, target=0.10, minobs=60, cap=8.0):
    vol = r.rolling(minobs,min_periods=minobs).std().shift(1)*np.sqrt(252)
    sc=(target/vol.replace(0,np.nan)).clip(upper=cap).fillna(0.0)
    return r*sc
V = pd.DataFrame({k: vt10(v) for k,v in P.items()})
core = V[list(SLEEVES)].mean(axis=1)
ch = pd.read_csv('../../../results/GOAL100_STRICTTRADE_BALANCED_daily.csv',parse_dates=['date']).set_index('date')
rc = pd.to_numeric(ch['ret'],errors='coerce').dropna()
# NYSE calendar: champion index vs union of sleeves index
union = sorted(set.intersection(*[set(P[k].dropna().index) for k in SLEEVES]))
print("union all-12 index n:", len(union), "first", union[0].date(), "last", union[-1].date())
# try: reindex to champion calendar, ffill? And the key missing piece = instrument-real cost layer subtracted after vt+throttle.
# Estimate the cost layer: assume comm = (core*gsc*thr) - cost_daily. Since scale ~1.7 mean but my gsc*thr gave corr 0.9829 with residual mean 4.6bp.
# Try computing costs explicitly: turnover per sleeve at cap8 scale, cost per sleeve class.
# Simpler: does corr improve with trailing-peak throttle 126d on the champion eq? My throttle uses -5%/50%.
# Check champion throttle signature: find days where champion return abruptly halves.
# Instead: analyze residual: comm - core*gsc (my best 0.9829 recon f)
vol_g = core.rolling(60,min_periods=60).std().shift(1)*np.sqrt(252)
sc_g=(0.10/vol_g.replace(0,np.nan)).clip(upper=8.0).fillna(0.0)
g = core*sc_g
eq=(1+g.fillna(0)).cumprod(); peak=eq.rolling(126,min_periods=1).max().shift(1)
tdd=eq/peak-1
thr=pd.Series(np.where(tdd>-0.05,1.0,0.5),index=g.index)
f=g*thr
j = pd.concat([f.rename('m'), rc.rename('c')],axis=1,sort=True).dropna()
resid = j['c']-j['m']
# Is resid constant-sign around rebalances? distribution of resid on days when |m| big:
big = j['m'].abs()>0.01
print("resid on big-move days: mean bp", (resid[big].mean()*1e4).round(2), "n", big.sum())
print("resid on small days: mean bp", (resid[~big].mean()*1e4).round(2))
# regress resid on |m|
import numpy as np
A = np.vstack([j['m'].abs(), np.ones(len(j))]).T
coef, res_, *_ = np.linalg.lstsq(A, resid.values, rcond=None)
print("resid ~ a*|m|+b: a=", coef[0].round(4), "b=", (coef[1]*1e4).round(2),"bp")
