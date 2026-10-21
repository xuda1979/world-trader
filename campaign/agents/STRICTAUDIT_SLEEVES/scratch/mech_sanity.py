import pandas as pd, numpy as np, json, os

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
out = {}
for name, path in SLEEVES.items():
    df = pd.read_csv(path, parse_dates=['date'])
    r = pd.to_numeric(df['ret'], errors='coerce')
    n = len(df)
    ndates = df['date'].duplicated().sum()
    first, last = df['date'].iloc[0], df['date'].iloc[-1]
    valid = r.dropna()
    # SR daily (rf=0)
    sr = valid.mean()/valid.std()*np.sqrt(252) if valid.std()>0 else np.nan
    ann = (1+valid).prod()**(252/len(valid))-1
    # halves SR by time split
    mid = df['date'].iloc[n//2]
    h1 = valid[df['date'].loc[valid.index] < mid]; h2 = valid[df['date'].loc[valid.index] >= mid]
    sr1 = h1.mean()/h1.std()*np.sqrt(252) if len(h1)>2 and h1.std()>0 else np.nan
    sr2 = h2.mean()/h2.std()*np.sqrt(252) if len(h2)>2 and h2.std()>0 else np.nan
    # yearly
    yr = (1+valid).groupby(df['date'].loc[valid.index].dt.year).prod()-1
    negyrs = int((yr < 0).sum())
    # MaxDD on cumulative
    cum = (1+valid).cumprod()
    dd = (cum/cum.cummax()-1).min()
    # max single day |ret|
    mx = valid.abs().max()
    # lag1 autocorr
    ac1 = valid.autocorr(1)
    # interior zero-runs >=5 (interior = between first and last nonzero)
    z = (valid.abs() < 1e-12).values
    nz = np.where(~z)[0]
    interior = z[nz[0]:nz[-1]+1] if len(nz) else z
    runs = []
    cnt = 0
    for v in interior:
        if v: cnt += 1
        else:
            if cnt >= 5: runs.append(cnt)
            cnt = 0
    if cnt >= 5: runs.append(cnt)
    runs_sorted = sorted(runs, reverse=True)
    lead_zeros = int(nz[0]) if len(nz) else 0
    trailing_zeros = int(len(z)-1-nz[-1]) if len(nz) else 0
    out[name] = dict(n=n, nan_ret=int(r.isna().sum()), dup_dates=int(ndates),
        start=str(first.date()), end=str(last.date()),
        SR_daily=round(float(sr),3), ann_pct=round(float(ann)*100,1),
        SR_h1=None if np.isnan(sr1) else round(float(sr1),3),
        SR_h2=None if np.isnan(sr2) else round(float(sr2),3),
        neg_years=negyrs, n_years=int(len(yr)),
        worst_yr_pct=round(float(yr.min())*100,1), best_yr_pct=round(float(yr.max())*100,1),
        MaxDD_pct=round(float(dd)*100,1), maxabsret_pct=round(float(mx)*100,1),
        lag1_ac=round(float(ac1),3),
        n_zero_rows=int(z.sum()), lead_zeros=lead_zeros, trail_zeros=trailing_zeros,
        runs_ge5=runs_sorted[:12])
print(json.dumps(out, indent=1, default=str))
