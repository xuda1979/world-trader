"""Build the model-ready monthly panel from DuckDB daily prices + SEC fundamentals.

Monthly cross-section of S&P 500 with:
  - returns from daily prices (adjusted close)
  - price/volume characteristics (momentum, volatility, amihud, turnover, ln price)
  - fundamental characteristics from SEC XBRL (book-to-market, ROOA, ROE,
    accruals, capex/assets, ...) aligned by fiscal year

Approximate mapping of the paper's characteristic categories onto the free tags:
  value:      book-to-market = equity / market cap
  profitability: ROE = net_income/equity; ROOA = op_income/(total_assets-cash)
  investment: capex/total_assets; inventory-change
  accruals:   (net_income - (operating cash flow)) approx from NI & dep
Assemble as long monthly panel columns; the model consumes 12-month lagged
sequences of these features cross-sectionally.
"""
import os, duckdb, pandas as pd, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DB_P = os.path.join(HERE, 'data/wh_prices.duckdb')
DB_F = os.path.join(HERE, 'data/fundamentals_annual.parquet')

def monthly_from_daily(con):
    """Monthly returns + avg dollar volume / turnover from daily prices (DuckDB)."""
    q = """
    WITH d AS (
      SELECT symbol, date,
             adj AS px,
             volume,
             close*volume AS dollar_vol
      FROM daily_prices
      WHERE adj IS NOT NULL AND adj > 0
    ),
    m AS (
      SELECT symbol,
             date_trunc('month', date)::DATE AS ymd,
             last(px ORDER BY date) AS px_end,
             first(px ORDER BY date) AS px_start,
             sum(dollar_vol) AS dolvol,
             max(volume) AS maxvol
      FROM d
      GROUP BY symbol, date_trunc('month', date)::DATE
    )
    SELECT symbol,
           strftime(ymd, '%Y-%m') AS ym,
           px_end, px_start, dolvol
    FROM m
    """
    return con.execute(q).fetchdf()

def build(monthly):
    df = monthly.sort_values(['symbol', 'ym']).copy()
    # monthly return in percent
    df['ret1'] = (df['px_end'] / df['px_start'] - 1.0) * 100.0
    df = df.replace([np.inf, -np.inf], np.nan)
    # momentum
    df['mom_3_1'] = df.groupby('symbol')['px_end'].pct_change(4) * 100.0   # 4-mo
    df['mom_6_1'] = df.groupby('symbol')['px_end'].pct_change(7) * 100.0
    df['mom_12_1'] = df.groupby('symbol')['px_end'].pct_change(13) * 100.0
    # vol (12m) 
    df['vol_mo'] = df.groupby('symbol')['ret1'].transform(lambda x: x.rolling(12).std())
    # ln price, ln dollar volume
    df['ln_price'] = np.log(df['px_end'].clip(lower=0.01))
    df['ln_dvol'] = np.log(df['dolvol'].clip(lower=1))
    # amihud approx: |ret| / dollar volume
    df['amihud'] = (df['ret1'].abs() / df['dolvol'].clip(lower=1)) * 1e9
    # turnover proxy: not directly available -> use 1/dolvol scaled (placeholder)
    df['turnover'] = df['dolvol'] / df['dolvol'].groupby(df['symbol']).transform('max')
    df['vol_6m'] = df.groupby('symbol')['ret1'].transform(lambda x: x.rolling(6).std())
    return df

def merge_fundamentals(df):
    """Merge SEC annual fundamentals aligned to fiscal year end -> following months."""
    fu = pd.read_parquet(DB_F)
    cols = ['equity','total_assets','net_income','op_income','cash','inventory',
            'payables','receivables','cogs','dep_amort','capex','revenue','d_and_a']
    cols = [c for c in cols if c in fu.columns]
    fu = fu[['symbol','fy'] + cols].copy()
    # market cap at fy -> book-to-market; approximate equity per share using shares
    # (shares may be missing; fall back to total-assets-based ratios)
    # Align: use FY t fundamentals for months in fiscal year t (approx via year)
    fu['year'] = fu['fy']
    def alias_fund(grp):
        return grp.ffill()
    df = df.merge(fu[['symbol','year']+cols], left_on=['symbol','year'], right_on=['symbol','year'], how='left')
    # characteristics
    df['b2m'] = df['equity'] / df['px_end'].clip(lower=0.01)
    df['roe'] = df['net_income'].div(df['equity'].replace(0,np.nan))
    df['rooa'] = df['op_income'].div((df['total_assets']-df['cash']).replace(0,np.nan))
    df['capex_to_assets'] = df['capex'].div(df['total_assets'].replace(0,np.nan))
    df['accruals_approx'] = df['net_income'].div(df['total_assets'].replace(0,np.nan))
    df['inv_to_assets'] = df['inventory'].div(df['total_assets'].replace(0,np.nan))
    return df

if __name__ == '__main__':
    con = duckdb.connect(DB_P, read_only=True)
    monthly = monthly_from_daily(con)
    df = build(monthly)
    df['year'] = df['ym'].str[:4].astype(int)
    df = merge_fundamentals(df)
    out = os.path.join(HERE, 'data/monthly_panel_full.csv')
    df.to_csv(out, index=False)
    print('panel shape:', df.shape)
    print('period:', df['ym'].min(), '->', df['ym'].max())
    print('symbols:', df['symbol'].nunique(), 'rows:', len(df))
    print('cols:', list(df.columns))
