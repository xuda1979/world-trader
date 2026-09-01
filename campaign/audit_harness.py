#!/usr/bin/env python3
# GOAL100 PERMANENT AUDIT HARNESS - mechanical checks on any sleeve CSV.
# Checks (all from the CSV alone, objective):
#   1. SR on 2008+ (report)
#   2. Interior exact-zero runs >= 20 days (report) - must be explained by design
#   3. Autocorrelation lag-1 (statistical sanity)
#   4. Daily |return| max (flag > 25% single-day = possible data/stitch error)
# Usage: python3 campaign/audit_harness.py
import sys, os
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
SLEEVES = {
 "A5r7":"campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",
 "A5r2":"campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7E":"campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxastsE":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "carryv2E":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "XGB1y":"campaign/results/sleeve_library/XGB1y_deploy.csv",
 "A1credit":"campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
 "C5ngE":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsumE":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "brwt15E":"campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10":"campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7":"campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5":"campaign/agents/COORD/sleeves/brwt5.csv",
}
def readv(p):
    try:
        df=pd.read_csv(f"{ROOT}/{p}",index_col=0,parse_dates=True)
        c="ret" if "ret" in df.columns else df.columns[0]
        return df[c].astype(float)
    except Exception:
        return None
rows=[]
for name,path in SLEEVES.items():
    r=readv(path)
    if r is None:
        rows.append((name,"CSV_ERR","","","","","")); continue
    r08=r[r.index>='2008-09-01'].dropna()
    sr=r08.mean()/r08.std()*np.sqrt(252) if len(r08)>10 and r08.std()>0 else 0
    mid=r.iloc[1:-1]; z=(mid==0); zruns=[]
    if z.any():
        groups=(z & ~z.shift(1).fillna(False)).cumsum()
        cnt=z.groupby(groups).sum()
        for k,v in cnt.items():
            if v>=20:
                di=mid.index.iloc[int(k)-1] if int(k)-1<len(mid.index) else None
                zruns.append((str(di.date()) if di is not None else "?",int(v)))
    ac1=r08.autocorr(1)
    mx=r08.abs().max()*100
    flag="OK" if (sr>=0.6 and mx<25) else "FLAG"
    rows.append((name,round(sr,2),round(float(ac1),3) if ac1==ac1 else 0,round(float(mx),1),len(zruns),str(zruns[:2]),flag))
pd.set_option("display.width",220); pd.set_option("display.max_colwidth",50)
for r in rows: print(f"{r[0]:11s} SR={r[1]:>5} ac1={r[2]:>6} max|d|%={r[3]:>6} zRuns={r[4]:>2d} {r[5][:46]:46s} {r[6]}")
