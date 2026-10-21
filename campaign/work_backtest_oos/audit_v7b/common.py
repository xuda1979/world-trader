import pandas as pd, numpy as np, os, pickle, warnings
warnings.filterwarnings('ignore')
OD="/Users/daxu/software/world-trader/campaign/work_backtest_oos"
ROOT="/Users/daxu/software/world-trader/campaign"
with open(os.path.join(OD,"audit_v5","v7_shared.pkl"),"rb") as f: D=pickle.load(f)
AGG=pd.read_csv(os.path.join(OD,"OPT_20V7_LEDGER_AGGREGATES.csv"),index_col=0,parse_dates=[0])
LED=pd.read_csv(os.path.join(OD,"OPT_20V7_FULL_LEDGER.csv"),parse_dates=['date'])
def sr(r,f=252):
    r=r.dropna(); return r.mean()/r.std()*np.sqrt(f) if len(r)>1 and r.std()>0 else 0
def ddf_(r):
    eq=(1+r).cumprod(); return (eq/eq.cummax()-1).min()*100
def ann(r,f=252): return r.mean()*f*100
def negy(r):
    yr=(1+r).groupby(r.index.year).prod()-1
    return int((yr<0).sum()),len(yr),yr
def net_series(bps=6.4, rate=0.053, borrow=0.0, short_frac=0.5, oos=False, lev=1.6):
    a=AGG
    n=lev*a.gross_ret - (a.notional_1leg+a.notional_extra_leg)*bps*1e-4 \
      - (lev-1.0)*rate/252 - lev*short_frac*borrow/252
    return (n[a.index>=pd.Timestamp("2017-01-01")] if oos else n).dropna()
def monthly(series):
    return (1+series).resample("ME").prod()-1
