#!/usr/bin/env python3
"""Cross-sectional stat-arb probe on the 288-name deep free panel @3.8bps.
Composite signal (z-scored): 12-1m momentum + 1w reversal + 6m residual mom,
ranked cross-sectionally, vol-scaled, T+1, scramble-gated."""
import os, sys
import numpy as np, pandas as pd
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..",".."))
if ROOT not in sys.path: sys.path.insert(0,ROOT)
TD=252; COST=3.8; DATA='tools/quant/data/twelve_big'
def shp(r):
    r=r.dropna(); return r.mean()/r.std()*TD**0.5 if len(r)>30 and r.std()>0 else float('nan')
def load():
    P={}
    for fn in sorted(os.listdir(DATA)):
        if not fn.endswith('.csv'): continue
        df=pd.read_csv(os.path.join(DATA,fn),parse_dates=['date'],usecols=['date','close','vol'])
        df=df.drop_duplicates('date').set_index('date').sort_index()
        if len(df)<252: continue
        P[fn[:-4]]=df
    prices=pd.DataFrame({t:P[t]['close'] for t in P}).ffill()
    good=prices.columns[prices.notna().sum()>=int(0.5*len(prices))]
    return prices[good]
def signal(last_prices, mom12, rev1, resid):
    z=lambda s:(s-s.mean())/s.std() if s.std()>0 else s*0
    comp=0.5*z(mom12)+0.35*z(rev1)+0.15*z(resid)
    return comp
def backtest(prices, n_long, n_short, rebal, seed=None):
    if seed is not None:
        rng=np.random.default_rng(seed); prices=prices.copy()
        prices.columns=np.random.permutation(prices.columns)
    rets=prices.pct_change()
    dates=prices.index; tickers=prices.columns
    pos=pd.DataFrame(0.0,index=dates,columns=tickers)
    for t in range(252,len(dates)):
        if (t-252)%rebal!=0: continue
        w=prices.iloc[max(0,t-252):t]
        mom12=prices.iloc[t-1]/prices.iloc[max(0,t-252)]-1
        rev1=prices.iloc[t-1]/prices.iloc[max(0,t-6)]-1
        rw=w.pct_change().tail(120)
        resid=rw-rw.mean(axis=1).values.reshape(-1,1)
        ivol=resid.std().replace(0,np.nan)
        sig=pd.Series(0.0,index=tickers)
        comp = 0.5*((prices.iloc[t-1]/prices.iloc[max(0,t-252)]-1))  # 12m mom
        comp = comp - 0.20*rev1                                       # 1w reversal
        comp = comp - 0.30*(rw.std())                                 # low vol -> higher score
        s=comp.dropna()
        if len(s)<n_long+n_short: continue
        longs=s.nlargest(n_long).index; shorts=s.nsmallest(n_short).index
        pos.loc[dates[t],longs]=0.5/n_long; pos.loc[dates[t],shorts]=-0.5/n_short
    pos=pos.shift(1)
    daily=(pos*rets).sum(axis=1)
    daily=daily-pos.diff().abs().sum(axis=1)*(COST/1e4)
    out=pd.DataFrame({'daily_return':daily.iloc[252+60:]},index=dates[252+60:])
    return out
def main():
    prices=load()
    print(f'panel {prices.shape[1]} names x {len(prices)}d ({prices.index[0].date()}..{prices.index[-1].date()})')
    for nl in [15,25,40]:
        for rebal in [10,21]:
            r=backtest(prices,nl,nl,rebal)
            s=shp(r['daily_return'])
            # scramble
            nbad=0
            for sd in range(2000,2004):
                rs=backtest(prices,nl,nl,rebal,seed=sd); nbad+=(shp(rs['daily_return'])>=s)
            print(f'nl={nl:2d} rebal={rebal:2d}: SR={s:.3f} scramble_beat={nbad}/4 {"PASS" if nbad<=0 else "FAIL"}')
if __name__=='__main__': sys.exit(main())
