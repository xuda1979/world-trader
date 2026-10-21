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
# variant: sleeves used RAW (not vt10'd) with EW then vt at blend: scale = vt12/rolling60*cap8?
raw = pd.DataFrame({k:v for k,v in P.items()})
core_raw = raw.mean(axis=1)
def try_scale(core, tgt, cap, win=60, minp=60):
    vol = core.rolling(win,min_periods=minp).std().shift(1)*np.sqrt(252)
    sc=(tgt/vol.replace(0,np.nan)).clip(upper=cap).fillna(0.0)
    return core*sc
ch = pd.read_csv('../../../results/GOAL100_STRICTTRADE_BALANCED_daily.csv',parse_dates=['date']).set_index('date')
rc = pd.to_numeric(ch['ret'],errors='coerce').dropna()
best=None
for tgt in [0.08,0.10,0.12,0.15]:
    for cap in [4,6,8]:
        f = try_scale(core_raw, tgt, cap)
        j = pd.concat([f.rename('m'), rc.rename('c')],axis=1,sort=True).dropna()
        corr = j['m'].corr(j['c'])
        if best is None or corr>best[0]: best=(corr,tgt,cap)
        if corr>0.99: print(f"raw-core tgt={tgt} cap={cap}: corr={corr:.5f}")
print("best raw-core:", best)
# variant: per-sleeve vt10 cap8 (as before) but NO throttle; global vt target 0.12?
V = pd.DataFrame({k: vt10(v) for k,v in P.items()}) if False else None
def vt10(r, target=0.10, minobs=60, cap=8.0):
    vol = r.rolling(minobs,min_periods=minobs).std().shift(1)*np.sqrt(252)
    sc=(target/vol.replace(0,np.nan)).clip(upper=cap).fillna(0.0)
    return r*sc
V = pd.DataFrame({k: vt10(v) for k,v in P.items()})
core_v = V[list(SLEEVES)].mean(axis=1)
best=None
for tgt in [0.08,0.10,0.12,0.15,0.20]:
    for cap in [4,6,8,12]:
        f = try_scale(core_v, tgt, cap)
        j = pd.concat([f.rename('m'), rc.rename('c')],axis=1,sort=True).dropna()
        corr = j['m'].corr(j['c'])
        if best is None or corr>best[0]: best=(corr,tgt,cap)
        if corr>0.99: print(f"vt-core tgt={tgt} cap={cap}: corr={corr:.5f}")
print("best vt-core:", best)
