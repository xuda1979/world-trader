"""Compute additional daily-based cross-sectional characteristics from free
daily OHLCV (wh_prices.duckdb) and cache them as monthly features.

Adds (beyond the existing price/volume set):
  idio_vol   : idiosyncratic vol (std of residual vs EW market, trailing ~6m)
  skew_6m    : skewness of daily returns (trailing ~6m)
  kurt_6m    : excess kurtosis of daily returns
  downside_6m: downside deviation / semivariance (trailing ~6m)
  beta_12m   : CAPM beta vs EW market (trailing ~12m)
  corr_6m    : correlation of stock ret with EW market (trailing ~6m)
  vol_20d_1m : realized vol over past ~1 month (recent vol)

These get cross-sectionally ranked (r_*) downstream like all other
characteristics. All data free.
"""
import os, duckdb, pandas as pd, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, 'data/wh_prices.duckdb')
OUT = os.path.join(HERE, 'data/daily_features.parquet')

WIN = 126   # ~6 months of trading days


def main():
    con = duckdb.connect(DB, read_only=True)
    df = con.execute('''
      SELECT symbol, date, adj, close*volume AS dolvol
      FROM daily_prices
      WHERE adj IS NOT NULL AND adj > 0 AND volume IS NOT NULL
      ORDER BY symbol, date
    ''').fetchdf()

    df = df.sort_values(['symbol', 'date']).copy()
    df['ret'] = df.groupby('symbol')['adj'].pct_change() * 100.0
    df = df.replace([np.inf, -np.inf], np.nan)

    # Equal-weight market return per date
    mkt = df.groupby('date')['ret'].mean().rename('mkt')
    df = df.merge(mkt, left_on='date', right_index=True, how='left')
    df['resid'] = df['ret'] - df['mkt']

    g = df.groupby('symbol')['ret']
    idio = df.groupby('symbol')['resid'].transform(lambda x: x.rolling(WIN).std())
    sk = g.transform(lambda x: x.rolling(WIN).skew())
    ku = g.transform(lambda x: x.rolling(WIN).kurt())
    neg = df['ret'].clip(upper=0)
    dd = neg.groupby(df['symbol']).transform(lambda x: (x**2).rolling(WIN).mean().pow(0.5))
    # beta = cov(ret,mkt)/var(mkt)
    Ex = df.groupby('symbol')['ret'].transform(lambda x: x.rolling(WIN).mean())
    Ey = df['mkt'].rolling(WIN).mean()
    Exy = (df['ret']*df['mkt']).groupby(df['symbol']).transform(lambda x: x.rolling(WIN).mean())
    mkt_var = (df['mkt'] - Ey).pow(2).rolling(WIN).mean()
    beta = (Exy - Ex*Ey) / (mkt_var + 1e-9)
    mkt_sd = df['mkt'].rolling(WIN).std()
    ret_sd = g.transform(lambda x: x.rolling(WIN).std())
    corr = (Exy - Ex*Ey) / (mkt_sd * ret_sd + 1e-9)
    # recent 1-month vol (21 trading days)
    rvol_1m = g.transform(lambda x: x.rolling(21).std())

    df['idio_vol'] = idio
    df['skew_6m'] = sk
    df['kurt_6m'] = ku
    df['downside_6m'] = dd
    df['beta_12m'] = beta
    df['corr_6m'] = corr
    df['vol_1m'] = rvol_1m

    df['ym'] = df['date'].astype(str).str[:7]
    cols = ['symbol', 'ym', 'idio_vol', 'skew_6m', 'kurt_6m',
            'downside_6m', 'beta_12m', 'corr_6m', 'vol_1m']
    feats = (df[cols + ['date']].sort_values(['symbol', 'ym', 'date'])
             .groupby(['symbol', 'ym'], as_index=False).last())

    feats.to_parquet(OUT, index=False)
    print('saved', OUT, feats.shape)
    print('period', feats['ym'].min(), '->', feats['ym'].max())
    print(feats[cols[2:]].describe())


if __name__ == '__main__':
    main()
