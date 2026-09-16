"""Financing stress-test the DECISION champion vs the champion of record (RAWEW15).
Uses the campaign's honest bt/financing_stress.py: call-rate rungs + borrow tiers.
Builds the daily net stream from the 18 weighted sleeves at the decision gross.
"""
import os, re, sys, json
import numpy as np, pandas as pd
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign")
from bt import financing_stress as fs

ROOT="/Users/daxu/software/world-trader/campaign"; OD=os.path.join(ROOT,"work_backtest_oos")
def load(rel):
    d=pd.read_csv(os.path.join(ROOT,rel),index_col=0); d.index=pd.to_datetime(d.index)
    c="ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
w=pd.read_csv(os.path.join(OD,"DECISION_CHAMPION_weights.csv"),index_col=0)['w']
# build daily weighted net
frame=pd.DataFrame({c:load(c) for c in w.index})
netd=frame.fillna(0).dot(w)                      # unlevered daily net (weights sum to 1)
# champion of record daily
champ=load('results/RAWEW15_REFRESH_CANDIDATE_daily.csv')
# common index within 2009+
common=netd.index.intersection(champ.index)
netd=netd.reindex(common); champ=champ.reindex(common)
# gross: decision is levered to match champion's ~1.6x. Champion runs gross 1.6.
GROSS=1.6
gross=pd.Series(np.full(len(netd),GROSS),index=netd.index)
gross_c=pd.Series(np.full(len(champ),GROSS),index=champ.index)

def to_monthly(r): return (1+r).resample("ME").prod()-1
def perf_m(r):
    r=to_monthly(r); r=r[r.abs()<0.4]
    eq=(1+r).cumprod()
    return dict(sr=r.mean()/r.std()*np.sqrt(12), ann=r.mean()*12*100,
                dd=(eq/eq.cummax()-1).min()*100, neg=int((r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)<0).sum()))

print("=== PRE-STRESS (full 2009+, monthly annualized, gross 1.6x vs champion ===")
print("NEW  :", perf_m(netd))
print("CHAMP:", perf_m(champ))
print("\n=== FINANCING STRESS: call-rate rung ladder @ gross 1.6 ===")
print("NEW champion:")
for rr in fs.DEFAULT_RUNGS:
    st=fs.stress_table(netd, gross, rr)
    # show stripped headline sr/ann/dd
    s=st.get('base',{}) if 'base' in st else st
    print(f"  rate {rr:.3f}: {json.dumps({k:round(float(v),3) if isinstance(v,(int,float)) else v for k,v in st.items() if k in ('sr','ann','mdd','neg_yrs','gross_ok')})}")
print("CHAMPION of record:")
for rr in fs.DEFAULT_RUNGS:
    st=fs.stress_table(champ, gross_c, rr)
    print(f"  rate {rr:.3f}: {json.dumps({k:round(float(v),3) if isinstance(v,(int,float)) else v for k,v in st.items() if k in ('sr','ann','mdd','neg_yrs','gross_ok')})}")
