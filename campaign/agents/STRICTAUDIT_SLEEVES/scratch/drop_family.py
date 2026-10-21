import pandas as pd, numpy as np
# Materiality: rebuild champion with each REDUNDANT family collapsed to ONE slot (dedup scenarios)
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
    vol=r.rolling(minobs,min_periods=minobs).std().shift(1)*np.sqrt(252)
    sc=(target/vol.replace(0,np.nan)).clip(upper=cap).fillna(0.0)
    return r*sc
def build(pool):
    V = pd.DataFrame({k: vt10(P[k]) for k in pool})
    core = V[pool].mean(axis=1)
    vol_g = core.rolling(60,min_periods=60).std().shift(1)*np.sqrt(252)
    sc_g=(0.10/vol_g.replace(0,np.nan)).clip(upper=8.0).fillna(0.0)
    g=core*sc_g
    eq=(1+g.fillna(0)).cumprod(); peak=eq.rolling(126,min_periods=1).max().shift(1)
    tdd=eq/peak-1
    thr=pd.Series(np.where(tdd>-0.05,1.0,0.5),index=g.index)
    f=g*thr
    f=f[f.index>='2008-09-01']
    sr=f.mean()/f.std()*np.sqrt(252)
    ann=f.mean()*252*100
    eqc=(1+f).cumprod(); dd=(eqc/eqc.cummax()-1).min()*100
    yr=(1+f).groupby(f.index.year).prod()-1
    return sr, ann, dd, (yr<0).sum(), len(yr)
scen = {
 'as-committed (my recon)': list(SLEEVES),
 'brwt->1 slot': ['brwt15','C5ng','C5ngsum','A5r2','a6r7','QAxasts','carryv2','dualmom','XGB1y'],
 'natgas->1 slot': ['brwt15','brwt10','brwt7','brwt5','C5ng','A5r2','a6r7','QAxasts','carryv2','dualmom','XGB1y'],
 'A5r2-dualmom keep both (no change)': list(SLEEVES),
 'fully-dedup econ pool (9)': ['brwt15','C5ng','A5r2','a6r7','QAxasts','carryv2','dualmom','XGB1y'],
}
for nm, pool in scen.items():
    sr, ann, dd, neg, ny = build(pool)
    print(f"{nm:38s} SR={sr:.2f} ann={ann:.1f}% DD={dd:.1f}% negyr={neg}/{ny}")
