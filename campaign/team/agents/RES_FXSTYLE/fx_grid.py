#!/usr/bin/env python3
"""FX cross-sectional factor grid search (momentum / carry) on fx_hist. T+1 causal."""
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
import sys; sys.path.insert(0, ROOT)
FXDIR=f"{ROOT}/tools/quant/data/fx_hist"

# Bloc of well-diversified USD crosses (economies: US, JP, EU, UK, AU, NZ, CA, CH, SE, NO,
# HK, SG, KR, ZA, BR, MX, DK, CZ, PL, HU, TR, IN, TH, CNY)
USDX=['USD_JPY','EUR_USD','GBP_USD','AUD_USD','NZD_USD','USD_CAD','USD_CHF','USD_SEK','USD_NOK',
      'USD_HKD','USD_SGD','USD_KRW','USD_ZAR','USD_BRL','USD_MXN','USD_DKK','USD_CZK','USD_PLN',
      'USD_HUF','USD_TRY','USD_INR','USD_THB','USD_CNY']

def load_pair(p):
    df=pd.read_csv(f"{FXDIR}/{p}.csv"); df['date']=pd.to_datetime(df['date'])
    return df.set_index('date').sort_index()['close'].astype(float)

def panel():
    return pd.DataFrame({p:load_pair(p) for p in USDX})

def run(prices, lb, skip, nlong, nshort, hold, ret_window):
    """Cross-sectional factor. factor = mom(lb,skip) or carry proxy (ret_window recent).
    Positions: dollar-neutral, weight each long/short = 1/(nlong or nshort), T+1, hold."""
    ret = prices.pct_change()
    f = (prices.shift(skip)/prices.shift(lb) - 1.0)
    ranks = f.rank(axis=1, method='first')
    n=len(ranks.columns)
    pos=pd.DataFrame(0.0,index=ranks.index,columns=ranks.columns)
    pos[ranks > n-nlong] = 1.0/nlong
    pos[ranks <= nshort] = -1.0/nshort
    pos=pos.shift(1)
    # hold
    rdates=pos.index[::hold]
    held=pd.DataFrame(np.nan,index=pos.index,columns=pos.columns)
    for rd in rdates:
        w=pos.index[(pos.index>=rd)&(pos.index<rd+pd.Timedelta(days=hold*1.5))]
        if len(w): held.loc[w]=pos.loc[rd].values
    held=held.ffill().fillna(0.0)
    book=(held*ret.fillna(0.0)).sum(axis=1).dropna()
    return book, held

def metrics(b):
    ann=(1+b).prod()**(252/len(b))-1
    sr=b.mean()/b.std()*np.sqrt(252)
    nav=(1+b).cumprod(); dd=(nav/nav.cummax()-1).min()
    # neg years
    y=pd.to_datetime(b.index).year
    yr=b.groupby(y).apply(lambda x:(1+x).prod()-1)
    return ann,sr,dd,int((yr<0).sum())

if __name__=='__main__':
    prices=panel()
    results=[]
    for lb in [126, 189, 252]:
        for nlong,nshort in [(3,3),(4,4),(5,5),(3,5)]:
            for hold in [10,21]:
                b,h=run(prices,lb,21,nlong,nshort,hold,None)
                if len(b)<500: 
                    results.append((lb,21,nlong,nshort,hold,len(b),0,0,0)); continue
                ann,sr,dd,neg=metrics(b)
                results.append((lb,21,nlong,nshort,hold,len(b),ann,sr,dd,neg))
    print("lb,skip,nl,ns,hold,n,ann,SR,dd,negYr")
    for r in results:
        print(f"{r[0]:4d} {r[1]:3d} {r[2]:2d} {r[3]:2d} {r[4]:3d} n={r[5]:5d} ann={r[6]*100:7.2f}% SR={r[7]:6.3f} dd={r[8]*100:7.2f}% neg={r[9]}")
