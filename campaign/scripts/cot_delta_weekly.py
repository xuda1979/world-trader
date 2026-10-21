#!/usr/bin/env python3
"""COT DELTA — CLEAN WEEKLY backtest (matches the positive correlation finding exactly).

Timing: COT report as-of Tuesday t is released Friday t. Delta_t = pos_t - pos_{t-1}
known by Friday t. We position for week t+1 (Mon-Fri), rebalanced weekly.

wret_{t+1} = product of daily ETF returns over week t+1. position = sign(delta_t).
Weekly portfolio ret (EW across markets) net of 6.4bps one-side on sign flips.
Compounded to get a proper daily-equivalent for SR/annualization/gates.
"""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign')
import numpy as np, pandas as pd

ROOT='/Users/daxu/software/world-trader'
CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:,0]

PRICES = {
 'gold':   ('tools/quant/data/twelvedata/GLD.csv','close'),
 'silver': ('tools/quant/data/more_etf/SLV.csv',None),
 'copper': ('tools/quant/hedge_fund_strats/data_fred/copx.csv',None),
 'corn':   ('tools/quant/data/more_etf/CORN.csv',None),
 'soybeans':('tools/quant/data/more_etf/SOYB.csv',None),
 'natgas': ('tools/quant/data/more_etf/UNG.csv',None),
 'wti':    ('tools/quant/data/more_etf/USO.csv',None),
 'sugar':  ('tools/quant/data/more_etf/CANE.csv',None),
 'wheat':  ('tools/quant/data/more_etf/WEAT.csv',None),
}
COT = { 'gold':'gold_cot.csv','silver':'silver_cot.csv','copper':'copper_cot.csv',
 'corn':'corn_cot.csv','soybeans':'soybeans_cot.csv','natgas':'nat_gas_nymex_cot.csv',
 'wti':'crude_wti_nymex_cot.csv','sugar':'sugar_no11_cot.csv','wheat':'wheat_srw_cot.csv'}

def load_price(name):
    p,col=PRICES[name]
    df=pd.read_csv(f"{ROOT}/{p}",index_col=0,parse_dates=True)
    c=df[col] if col in df.columns else df.iloc[:,0]
    return c.astype(float).dropna()

def load_cot(name):
    return pd.read_csv(f"{ROOT}/tools/quant/data/more_cot/{COT[name]}", parse_dates=['date'])

def market_weekly(name, lookback=1, z_thr=0.0):
    """Return weekly series: date=Friday of week t+1, ret = sign(delta_t)*wret_{t+1}, and
    a turnover flag (sign change)."""
    cot=load_cot(name); px=load_price(name)
    ret=px.pct_change().reindex(px.index)
    # weekly Fri-Fri price returns
    wret=(ret+1).resample('W-FRI').prod()-1
    pos=cot.set_index('date')['net_noncomm_pct_oi']
    # align COT position to Friday weeks (as-of Tuesday -> that week's Friday)
    posw=pos.resample('W-FRI').apply(lambda x: x.iloc[-1] if len(x) else np.nan).ffill()
    delta=posw.diff(lookback)
    # z-score delta over trailing 52w
    mz=delta.rolling(52,min_periods=26).mean(); sz=delta.rolling(52,min_periods=26).std(ddof=1)
    z=((delta-mz)/sz.replace(0,np.nan))
    sig=np.sign(z).fillna(0.0)
    sig[sig.abs()<1e-9]=0.0
    if z_thr>0:
        # keep sig a pandas Series: np.where returned a raw ndarray whose
        # .shift(1) raised AttributeError, silently swallowed by build_weekly's
        # bare except -> 3 of 4 __main__ configs unrunnable (R4 audit,
        # HUNT_CMDT2/tests_tdd_r4_audit.py)
        sig=pd.Series(np.where(z>z_thr,1.0,np.where(z<-z_thr,-1.0,0.0)),
                      index=z.index)
        sig[sig.abs()<1e-9]=0.0
    # position taken for week AFTER the signal week (shift 1 week)
    pos_week=sig.shift(1)
    # weekly realized portfolio ret
    wk=pos_week*wret
    # costs on sign change between consecutive weeks
    to=pos_week.diff().abs()
    net=wk-to*(6.4/1e4)
    return net.dropna(), to.dropna()

def build_weekly(lookback, z_thr, start='2012-01-06'):
    nets={}
    for m in PRICES:
        # fail loud, not silent: a swallowed market-level exception previously
        # turned into pd.DataFrame(all-None) -> ValueError, hiding 3/4 broken
        # configs from the row's saved repro path (R4 audit)
        n,_=market_weekly(m,lookback,z_thr)
        nets[m]=n
    df=pd.DataFrame(nets)
    df=df[df.index>=start]
    return df

def to_daily(weekly):
    """Convert weekly portfolio returns to daily-compounded series aligned to champion calendar."""
    wk=weekly.fillna(0.0)
    idx=pd.date_range(wk.index.min(), CHAMP.index.max(), freq='B')
    # assign each business day to its Friday week
    fridays=wk.index
    d=pd.Series(0.0,index=idx)
    # for each week, spread? No: use weekly compounding -> daily = 0 except on week boundaries
    # Instead: map last business day of each week to the weekly return, others 0
    wdf=wk.to_frame('r'); wdf['f']=wdf.index
    daily=pd.Series(0.0,index=idx)
    for f,val in wk.items():
        # set the Friday (last B day of that week) to carry the weekly log ret as a single hit
        daily.loc[f]=np.log1p(val) if val>-1 else 0.0
    daily=np.exp(daily.cumsum())-1
    dr=daily.diff().fillna(daily.iloc[0])
    dr.iloc[0]=daily.iloc[0]
    return dr

if __name__=='__main__':
    for lb,zt in [(1,0.0),(1,0.5),(2,0.0),(1,1.0)]:
        df=build_weekly(lb,zt)
        wk=df.mean(axis=1).dropna()
        wk=wk[wk.abs()<0.5]
        dr=to_daily(wk)
        ann=(1+dr).prod()**(252/len(dr))-1
        sr=dr.mean()/dr.std()*np.sqrt(252)
        yrs=(1+wk).resample('YE').prod()-1
        corr=dr.reindex(CHAMP.index).dropna(); ch=CHAMP.reindex(corr.index).dropna()
        c=np.corrcoef(corr,ch)[0,1] if len(corr)>200 else float('nan')
        print(f'lb={lb} zthr={zt} n_wk={len(wk)} ann={ann:.1%} SR={sr:.2f} negyr={(yrs<0).sum()}/{len(yrs)} corrChamp={c:.2f} MDD={(dr.cumsum()-dr.cumsum().cummax()).min():.1%}')
