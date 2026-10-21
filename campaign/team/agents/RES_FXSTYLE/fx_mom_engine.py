#!/usr/bin/env python3
"""RES_FXSTYLE — cross-sectional FX momentum engine on the NEW 508-pair fx_hist.

Builds a cross-sectional FX momentum/carry basket on major crosses, T+1 causal.
Sleeve delivered as net daily return series aligned to the champion calendar.
"""
import os, sys
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)

FXDIR = f"{ROOT}/tools/quant/data/fx_hist"

MAJORS = ['USD_JPY','EUR_USD','GBP_USD','AUD_USD','NZD_USD','USD_CAD','USD_CHF',
          'USD_SEK','USD_NOK','USD_CNY','USD_HKD','USD_SGD','USD_KRW','USD_THB',
          'USD_INR','USD_ZAR','USD_BRL','USD_MXN','USD_DKK','EUR_JPY','EUR_GBP',
          'EUR_CHF','AUD_JPY','GBP_JPY','USD_HUF','USD_PLN','USD_CZK','USD_TRY']

def load_price(pair):
    df = pd.read_csv(f"{FXDIR}/{pair}.csv")
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    return df['close'].astype(float)

def price_panel():
    p = pd.DataFrame({x: load_price(x) for x in MAJORS})
    return p

def xsmom(lookback=252, skip=21, top=5, bottom=5, hold=21):
    px = price_panel()
    ret = px.pct_change()
    mom = (px.shift(skip) / px.shift(lookback) - 1.0)
    ranks = mom.rank(axis=1, method='first')
    n = len(ranks.columns)
    pos = pd.DataFrame(0.0, index=ranks.index, columns=ranks.columns)
    long_mask = ranks > n - top
    short_mask = ranks <= bottom
    pos[long_mask] = 1.0
    pos[short_mask] = -1.0
    pos = pos.shift(1)  # T+1 execution
    rebalance_dates = pos.index[::hold]
    held = pd.DataFrame(np.nan, index=pos.index, columns=pos.columns)
    for rdate in rebalance_dates:
        window = pos.index[(pos.index >= rdate) & (pos.index < rdate + pd.Timedelta(days=hold*1.4))]
        if len(window):
            held.loc[window] = pos.loc[rdate].values
    held = held.ffill().fillna(0.0)
    book = (held * ret.fillna(0.0)).sum(axis=1)
    return held, book, px, ret

if __name__ == '__main__':
    held, book, px, ret = xsmom()
    book = book.dropna()
    ann = (1+book).prod()**(252/len(book))-1
    sr = book.mean()/book.std()*np.sqrt(252)
    nav=(1+book).cumprod()
    dd=(nav/nav.cummax()-1).min()
    print(f"FX xsmom: n={len(book)} ann={ann*100:.2f}% SR={sr:.3f} MaxDD={dd*100:.2f}%")
    book.to_csv('/tmp/fx_mom_raw.csv', header=['ret'])
