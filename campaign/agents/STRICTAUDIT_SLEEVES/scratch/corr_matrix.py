import pandas as pd, numpy as np, itertools, json

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
R = {}
for name, path in SLEEVES.items():
    df = pd.read_csv(path, parse_dates=['date']).set_index('date')
    r = pd.to_numeric(df['ret'], errors='coerce')
    R[name] = r
# raw pairwise corr on inner join
print("=== RAW pairwise corr (inner join, min 500 rows) ===")
keys = list(SLEEVES)
M = pd.DataFrame(index=keys, columns=keys, dtype=float)
N = pd.DataFrame(index=keys, columns=keys, dtype=float)
for a, b in itertools.combinations_with_replacement(keys, 2):
    j = pd.concat([R[a].rename('a'), R[b].rename('b')], axis=1).dropna()
    if len(j) >= 500:
        M.loc[a, b] = M.loc[b, a] = round(j['a'].corr(j['b']), 3)
        N.loc[a, b] = N.loc[b, a] = len(j)
print(M.to_string())
print("=== VT-NORMALIZED pairwise corr (per-sleeve scale = 0.10/ewm60_trailing_vol shift1 cap8, as construction docs) ===")
def vt_scale(r):
    vol = r.rolling(60, min_periods=60).std().shift(1) * np.sqrt(252)
    sc = (0.10 / vol.replace(0, np.nan)).clip(upper=8.0)
    return r * sc
V = {k: vt_scale(v.dropna()) for k, v in R.items()}
MV = pd.DataFrame(index=keys, columns=keys, dtype=float)
for a, b in itertools.combinations(keys, 2):
    j = pd.concat([V[a].rename('a'), V[b].rename('b')], axis=1).dropna()
    if len(j) >= 500:
        MV.loc[a, b] = MV.loc[b, a] = round(j['a'].corr(j['b']), 3)
print(MV.to_string())
# brwt overlap: also corr on common window only
print("=== brwt family: pairwise corr restricted to 2008+ common window ===")
for a, b in [('brwt15','brwt10'),('brwt15','brwt7'),('brwt15','brwt5'),('brwt10','brwt7'),('brwt10','brwt5'),('brwt7','brwt5')]:
    j = pd.concat([R[a].rename('a'), R[b].rename('b')], axis=1).dropna()
    j = j[j.index >= '2008-09-01']
    print(f"{a}-{b}: n={len(j)} corr={j['a'].corr(j['b']):.4f}  vt-corr={pd.concat([V[a],V[b]],axis=1).dropna().corr().iloc[0,1]:.4f}")
print("=== C5ng vs C5ngsum overlap ===")
j = pd.concat([R['C5ng'].rename('a'), R['C5ngsum'].rename('b')], axis=1).dropna()
print(f"raw n={len(j)} corr={j['a'].corr(j['b']):.4f}")
print(f"vt-corr={pd.concat([V['C5ng'],V['C5ngsum']],axis=1).dropna().corr().iloc[0,1]:.4f}")
M.to_csv('raw_corr_matrix.csv'); MV.to_csv('vt_corr_matrix.csv')
