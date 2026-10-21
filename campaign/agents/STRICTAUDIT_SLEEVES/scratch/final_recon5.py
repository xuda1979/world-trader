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
# hypothesis: champion did NOT apply throttle as 0.5 switch, and did NOT vt globally with 60d;
# maybe: per-sleeve vt10 cap8; EW; GLOBAL vt at TARGET 0.10 but EWM (not rolling); then costs.
# residual -0.1622*|m| suggests cost ~ 16% of gross move... too big for costs.
# Alternative: champion applied instrument costs to SLEEVES first, then blended:
# cost classes: brwt x4 = 1.5bp, C5ng x2 = 5bp, A5r2 = 6? a6r7=5? QAxasts=8? carryv2=5? dualmom=15, XGB=15.
COSTS = {'brwt15':1.5,'brwt10':1.5,'brwt7':1.5,'brwt5':1.5,'C5ng':5,'C5ngsum':5,'A5r2':6,
 'a6r7':5,'QAxasts':8,'carryv2':5,'dualmom':15,'XGB1y':15}
# proxy cost per sleeve = k * |daily ret| of sleeve (turnover proxy unknown). Approximate with |r|.
Vc = V.copy()
for k,c in COSTS.items():
    Vc[k] = V[k] - (c/1e4)  # flat per-day cost as lower bound? crude
core2 = Vc[list(SLEEVES)].mean(axis=1)
vol_g = core2.rolling(60,min_periods=60).std().shift(1)*np.sqrt(252)
sc_g=(0.10/vol_g.replace(0,np.nan)).clip(upper=8.0).fillna(0.0)
g2=core2*sc_g
j = pd.concat([g2.rename('m'), rc.rename('c')],axis=1,sort=True).dropna()
print("flat-cost variant corr:", j['m'].corr(j['c']).round(4))
# Check champion for throttle signature: ratio rc/g should cluster at {1.0,0.5}?
ratio = (j['c']/j['m'].replace(0,np.nan)).dropna()
print("ratio quantiles:", ratio.quantile([.1,.25,.5,.75,.9]).round(3).to_dict())
# distribution near 0.5?
print("frac 0.4-0.6:", ((ratio>0.4)&(ratio<0.6)).mean().round(3))
print("frac 0.9-1.1:", ((ratio>0.9)&(ratio<1.1)).mean().round(3))
