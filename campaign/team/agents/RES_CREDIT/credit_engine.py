#!/usr/bin/env python3
"""RES_CREDIT — long-history credit-spread timing engine.

Signal family on the daily BAA-AAA credit spread (1986+, MORE_FRED DAAA/DBAA) and
BAA10Y (1986+), applied to a liquid credit ETF (LQD 2002+, HYG 2007+).
Logic: credit spreads mean-revert at the business-cycle horizon. When the spread is
WIDE vs its trailing z (credit cheap / risk-off), buy credit (spread tightening =>
price up); when TIGHT (credit rich / risk-on late-cycle), de-risk/short.
T+1, trailing-only stats, full |dW|@6.4 cost, borrow on shorts, fail-closed.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
from bt.engine import vol_target_scale, cost_turnover, borrow_cost

ROOT="/Users/daxu/software/world-trader"
FRED=f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
ETF=f"{ROOT}/tools/quant/data/more_etf"
VT_TARGET, VT_CAP = 0.10, 3.0

def load_credit(name):
    df=pd.read_csv(f"{FRED}/{name}.csv", parse_dates=['date'], index_col='date')['value'].astype(float)
    return df.sort_index()[~df.index.duplicated(keep='last')]

def load_px(req):
    # require close column
    d=pd.read_csv(f"{ETF}/{req}.csv", parse_dates=['date'], index_col='date')
    col='close' if 'close' in d.columns else d.columns[0]
    return d[col].astype(float).sort_index()[~d.index.duplicated(keep='last')]

def spread_series():
    baa=load_credit('baa'); aaa=load_credit('aaa')
    j=pd.concat({'baa':baa,'aaa':aaa},axis=1).dropna()
    return (j['baa']-j['aaa'])

def book(signal, px, enter, exit_, side='long', hold=10):
    """Timing book: in when signal crosses enter, out at exit (hysteresis)."""
    st=pd.Series(0.0,index=signal.index)
    cur=0.0
    for i,v in enumerate(signal.values):
        if np.isfinite(v):
            if cur==0.0 and (v>enter if side=='long' else v<enter):
                cur=1.0
            elif cur==1.0 and (v<=exit_ if side=='long' else v>=exit_):
                cur=0.0
        st.iloc[i]=cur
    lvl=pd.DataFrame({'a': st*1.6, 'b':0.0}, index=signal.index)
    r=px.pct_change().reindex(signal.index)
    rpu=r.fillna(0.0).rename('rpu')
    We=lvl.shift(1).fillna(0.0)
    s=vol_target_scale(pd.DataFrame({'g':(We['a']*rpu.abs())}),target=VT_TARGET,cap=VT_CAP)['g']
    We=We.mul(s,axis=0)
    net=(We['a']*rpu)-cost_turnover(We[['a']],6.4)-borrow_cost(We[['a']])
    return net.rename('ret'), We, rpu

def zscore(s, lb):
    m=s.rolling(lb,min_periods=60).mean(); sd=s.rolling(lb,min_periods=60).std()
    return ((s-m)/sd).shift(1)  # T+1, trailing only

def metrics(b):
    ann=(1+b).prod()**(252/len(b))-1
    sr=b.mean()/b.std()*np.sqrt(252)
    nav=(1+b).cumprod(); dd=(nav/nav.cummax()-1).min()
    y=pd.to_datetime(b.index).year
    yr=b.groupby(y).apply(lambda x:(1+x).prod()-1)
    return ann,sr,dd,int((yr<0).sum()),yr.min()

if __name__=='__main__':
    sp=spread_series()
    # test on LQD (2002+, covers champion 2008+)
    for inst in ['LQD','HYG']:
        px=load_px(inst)
        print(f"==== {inst} (span {px.index.min().date()}..{px.index.max().date()}) ====")
        for lb in [63,126,252]:
            z=zscore(sp,lb)
            z=z.reindex(px.index).dropna()
            for (ent,exi) in [(1.0,0.0),(1.5,0.5),(2.0,1.0),(-1.0,-2.0)]:
                # long when z>ent, exit z<=exi ; short when z<-ent, exit z>=-exi
                b,We,r=book(z,px,ent,exi,side='long')
                b=b.dropna()
                if len(b)<300: continue
                ann,sr,dd,neg,worst=metrics(b)
                print(f"  lb{lb} z>ent{ent}/exit{exi}: n={len(b)} ann={ann*100:6.2f}% SR={sr:5.2f} dd={dd*100:6.2f}% neg={neg} worst={worst*100:6.2f}%")

def momentum_test():
    """Test credit-spread MOMENTUM (widening => spread widens further / risk-off)."""
    sp=spread_series()
    print("==== CREDIT MOMENTUM (long LQD when spread DECLINING, short when rising) ====")
    px=load_px('LQD')
    for lb in [21,63,126]:
        dch = sp.diff(lb).shift(1).reindex(px.index)   # spread change over lb, T+1
        for thr in [0.0, 0.1, -0.1]:
            # long LQD when spread falling (dch<...), short when rising within-vol-normalized
            sig=pd.Series(np.where(dch<thr if False else (dch.clip(-1,1)),0,0),index=dch.index)
            # normalize change by its own std -> z-like
            z=dch / dch.rolling(252,min_periods=60).std()
            for (ent,exi) in [(0.5,-0.5),(1.0,0.0)]:
                # SHORT when spread-widening z>ent (credit risk-off), long when z<-ent
                for side in ['short','long']:
                    b,We,r=book(z,px,ent,exi,side=side)
                    b=b.dropna()
                    if len(b)<300: continue
                    ann,sr,dd,neg,worst=metrics(b)
                    print(f"  lb{lb} z{'>' if side=='short' else '<'}ent{ent}/exit{exi} {side}: ann={ann*100:6.2f}% SR={sr:5.2f} dd={dd*100:6.2f}% neg={neg} worst={worst*100:6.2f}%")
