"""C3_positioning shared loaders: COT/TFF positioning + price series."""
import sys, os
sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.agents.B2_highfreq.gates import full_stats, halves_sr, scramble_pval, vol_target
ROOT='/Users/daxu/software/world-trader'
COT=f'{ROOT}/tools/quant/hedge_fund_strats/data_cot'
FRED=f'{ROOT}/tools/quant/hedge_fund_strats/data_fred'
COST=6e-4

def load_cot():
    df=pd.read_csv(f'{COT}/cot_tidy.csv',parse_dates=['date','report_date'])
    return df
def load_tff():
    df=pd.read_csv(f'{COT}/tff_tidy.csv',parse_dates=['date','report_date'])
    return df
def px(name):
    s=pd.read_csv(f'{FRED}/{name}.csv',index_col=0,parse_dates=True).iloc[:,0]
    s=s[s>0]
    return s[~s.index.duplicated(keep='last')].sort_index()

def weekly_signal(sig_s, prices):
    """sig_s: series indexed by report_date (positioning known then).
    Forward-fill onto trading days, shift 1 (usable next session), reindex to price days."""
    s=sig_s.sort_index().dropna()
    daily=s.reindex(prices.index.union(s.index)).ffill().reindex(prices.index).shift(1)
    return daily

def build_ret(sig_daily, prices, vt=None, min_days=60):
    """sig_daily: position in [-1,1] (or z-scaled), prices: close series.
    Position held from t close to t+1 close based on signal at t (already shifted).
    Turnover = |pos change| per day, one-side cost 6bps."""
    p=prices.reindex(sig_daily.index).dropna()
    sd=sig_daily.reindex(p.index).fillna(0.0)
    ret=p.pct_change().fillna(0.0)
    pos=sd.clip(-1,1)
    gross=pos.shift(1)*ret  # pos set at close(t) earns t->t+1 return (NO lookahead)
    to=pos.diff().abs().fillna(0.0)
    net=gross-to*COST
    return net, to

def vol_scale(net, vt_ann=0.10, min_days=60, clip=3.0):
    rc=net.expanding(min_days).std()*np.sqrt(252)
    sc=(vt_ann/rc).clip(upper=clip)
    sc.iloc[:min_days]=np.nan
    return net*sc.shift(0)

def stats(r):
    s=full_stats(r.dropna())
    return s

def corr_to_blend(r):
    bl=pd.read_csv(f'{ROOT}/campaign/results/COORD_FINAL_daily.csv',index_col=0,parse_dates=True)['ret']
    df=pd.concat([r,bl],axis=1,join='inner').dropna()
    df.columns=['r','b']
    if len(df)<200: return np.nan, len(df)
    return df['r'].corr(df['b']), len(df)
