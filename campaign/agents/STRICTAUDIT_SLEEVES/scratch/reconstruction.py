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
P = {}
for name, path in SLEEVES.items():
    df = pd.read_csv(path, parse_dates=['date']).set_index('date')
    P[name] = pd.to_numeric(df['ret'], errors='coerce')

def vt10(r, target=0.10, minobs=60, cap=8.0):
    vol = r.rolling(minobs, min_periods=minobs).std().shift(1) * np.sqrt(252)
    sc = (target / vol.replace(0, np.nan)).clip(upper=cap).fillna(0.0)
    return r * sc

V = pd.DataFrame({k: vt10(v) for k, v in P.items()})
# NYSE calendar approximation: union -> forward-fill missing? Champion only tradeable days.
# First: union calendar, then check difference vs champion index.
V['mean'] = V[list(SLEEVES)].mean(axis=1, skipna=True)  # NaN-tolerant? try both
# strict: require all non-NaN
vm = V[list(SLEEVES)]
core = vm.mean(axis=1)
# global vt
vol_g = core.rolling(60, min_periods=60).std().shift(1) * np.sqrt(252)
sc_g = (0.10 / vol_g.replace(0, np.nan)).clip(upper=8.0).fillna(0.0)
g = core * sc_g
# throttle 126d
eq = (1 + g.fillna(0)).cumprod()
peak = eq.rolling(126, min_periods=1).max().shift(1)
tdd = eq / peak - 1
throttle = pd.Series(np.where(tdd > -0.05, 1.0, 0.5), index=g.index)
f = g * throttle
ch = pd.read_csv('../../../results/GOAL100_STRICTTRADE_BALANCED_daily.csv', parse_dates=['date']).set_index('date')
rc = pd.to_numeric(ch['ret'], errors='coerce').dropna()
j = pd.concat([f.rename('mine'), rc.rename('comm')], axis=1, sort=True).dropna()
print(f"n={len(j)} corr={j['mine'].corr(j['comm']):.4f} maxdiff={abs(j['mine']-j['comm']).max():.5f} meandiff={abs(j['mine']-j['comm']).mean():.5f}")
sr = j['mine'].mean()/j['mine'].std()*np.sqrt(252)
print(f"my SR={sr:.2f} vs comm SR={j['comm'].mean()/j['comm'].std()*np.sqrt(252):.2f}")
# Scale check: daily linear regression comm ~ a*mine
a = (j['mine']*j['comm']).sum()/ (j['mine']**2).sum()
print(f"scale comm/mine = {a:.4f}")
# residual
res = j['comm'] - a*j['mine']
print(f"resid std={res.std():.5f} vs comm std={j['comm'].std():.5f}")
