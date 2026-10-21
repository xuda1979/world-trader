import pandas as pd, numpy as np
# Pooled-redundancy verdict inputs: average pairwise vt-corr within families vs across
# Also compute what fraction of champion variance each family contributes (via vt'd sleeves regressed on champion)
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
V = {k: pd.to_numeric(pd.read_csv(p,parse_dates=['date']).set_index('date')['ret'],errors='coerce') for k,p in SLEEVES.items()}
Vt = pd.DataFrame(V)
fams = {
 'brwt-family(4)': ['brwt15','brwt10','brwt7','brwt5'],
 'natgas(2)': ['C5ng','C5ngsum'],
 'A5r2-dualmom(A5r2 corr 0.54)': ['A5r2','dualmom'],
 'rest': ['a6r7','QAxasts','carryv2','XGB1y'],
}
for f, ks in fams.items():
    sub = Vt[ks].dropna()
    if len(ks)>1:
        cm = sub.corr().values
        n = len(ks)
        iu = np.triu_indices(n,1)
        print(f"{f}: mean pairwise corr={cm[iu].mean():.3f} (min {cm[iu].min():.3f} max {cm[iu].max():.3f})")
# cross-family: brwt vs natgas, brwt vs rest etc
cross = [('brwt15','C5ng'),('brwt15','a6r7'),('brwt15','QAxasts'),('C5ng','a6r7'),('A5r2','XGB1y'),('a6r7','XGB1y'),('dualmom','XGB1y'),('carryv2','a6r7')]
print("cross-family corr:", {f"{a}-{b}": round(Vt[a].corr(Vt[b]),3) for a,b in cross})
