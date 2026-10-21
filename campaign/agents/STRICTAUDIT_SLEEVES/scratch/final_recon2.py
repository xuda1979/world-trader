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
ch = pd.read_csv('../../../results/GOAL100_STRICTTRADE_BALANCED_daily.csv',parse_dates=['date']).set_index('date')
rc = pd.to_numeric(ch['ret'],errors='coerce').dropna()
core = V[list(SLEEVES)].mean(axis=1)
j = pd.concat([core.rename('core'), rc.rename('comm')],axis=1,sort=True).dropna()
# implied total scale per day = comm / core (pre-throttle)
scale = (j['comm']/j['core'].replace(0,np.nan)).dropna()
print("implied scale quantiles:", scale.quantile([.05,.25,.5,.75,.95,.99]).round(3).to_dict())
print("scale max:", scale.max().round(2))
# hypothesis: instrument costs subtracted: comm = core*scale - costs. Try global-vt-with-8x-cap + throttle(no 0.5, only FT) * borrow fee daily rate?
# borrow fee ~ 50bp/252 * short_gross ~0.3x => ~0.6bp/day tiny. instrument cost on turnover.
# Check ratio pattern: scale vs time
print("scale mean by year:")
print(scale.groupby(scale.index.year).mean().round(3))
