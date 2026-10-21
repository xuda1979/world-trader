import pandas as pd, numpy as np
# Does champion use each sleeve file as committed? Compare: champion ~ vt-combination.
# Key provenance Q: does committed champion contain a 2020-09-01 +14.7% day matching sleeves?
# Already: sleeve sum on that day ~ 3.27+2.64+2.59+2.61+0+0+0.74+0.1-0.06+0.04+1.26+0.26 = 13.45 -> /12=1.12% *vt scale...
# The +14.72% day must come from vt leverage: global vt scale on calm days can be ~8x cap.
# Reconstruct champion from the sleeve files with ONLY per-sleeve vt10 cap8 + EW + global vt + throttle (my recon):
X=0;SLEEVES = {
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
vol_g = core.rolling(60,min_periods=60).std().shift(1)*np.sqrt(252)
sc_g=(0.10/vol_g.replace(0,np.nan)).clip(upper=8.0).fillna(0.0)
g = core*sc_g
eq=(1+g.fillna(0)).cumprod(); peak=eq.rolling(126,min_periods=1).max().shift(1)
tdd=eq/peak-1
thr=pd.Series(np.where(tdd>-0.05,1.0,0.5),index=g.index)
f=g*thr
print("my 2020-09-01:", f.loc['2020-09-01'], "committed 0.147166")
# what global scale would produce 14.72%? committed/core_t before throttle:
d = P['2020-09-01'] if False else None
day = pd.Timestamp('2020-09-01')
core_day = V.loc[day].mean()
print("core(vt'd, EW) that day:", core_day, "=> committed/core =", 0.147166/core_day)
