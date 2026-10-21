"""Extend the full panel (price + SEC fundamentals) into the model-ready feature
panel with cross-sectional ranks for ALL characteristics (price/volume AND
fundamental), matching the paper's construction of ranked cross-sectional inputs.
"""
import os, pandas as pd, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL = os.path.join(HERE, 'data/monthly_panel_full.csv')
OUT = os.path.join(HERE, 'data/model_panel_full.csv')

PRICE_FEATURES = ['ret1','mom_3_1','mom_6_1','mom_12_1','vol_mo','vol_6m',
                  'amihud','ln_dvol','ln_price','turnover']
FUND_FEATURES = ['b2m','roe','rooa','capex_to_assets','accruals_approx','inv_to_assets']
# Additional daily-OHLCV-derived characteristics (free, from wh_prices.duckdb).
# Overridable via DAILY_FEATS="a,b,c" to select a curated subset (reduces overfit).
_ALL_DAILY = ['idio_vol','skew_6m','kurt_6m','downside_6m','beta_12m',
              'corr_6m','vol_1m']
DAILY_FEATURES = [f.strip() for f in
                  os.environ.get("DAILY_FEATS", ",".join(_ALL_DAILY)).split(",")
                  if f.strip() and f.strip() in _ALL_DAILY]

def build():
    d = pd.read_csv(PANEL)
    d = d.sort_values(['symbol','ym']).copy()
    # merge additional daily-OHLCV-derived characteristics (free); toggle with
    # DAILY=0 to reproduce the baseline 35-feature panel.
    active_features = PRICE_FEATURES + FUND_FEATURES
    if os.environ.get("DAILY", "0").lower() not in ("0", "false", "off"):
        daily = pd.read_parquet(os.path.join(HERE, 'data/daily_features.parquet'))
        d = d.merge(daily[['symbol','ym'] + DAILY_FEATURES],
                    on=['symbol','ym'], how='left')
        active_features = active_features + DAILY_FEATURES
    # winsorize fundamentals at 1/99's before ranking (handle extreme ratios)
    for c in ['b2m','roe','rooa','capex_to_assets','accruals_approx','inv_to_assets']:
        v = d[c].to_numpy(dtype=float)
        lo, hi = np.nanpercentile(v,1), np.nanpercentile(v,99)
        d[c] = np.clip(v, lo, hi)
    # cross-sectional ranks for every characteristic (0..1)
    for c in active_features:
        d['r_' + c] = d.groupby('ym')[c].rank(pct=True)
    # interactions
    d['mom_12_x_size'] = d['r_mom_12_1'] * d['r_ln_dvol']
    d['mom_12_x_val']  = d['r_mom_12_1'] * d['r_b2m']
    d['mom_12_x_prof'] = d['r_mom_12_1'] * d['r_roe']
    # model feature list (raw + rank, no lookahead; ranks are per-month)
    FEATURES = [
        'ret1','mom_3_1','mom_6_1','mom_12_1','vol_mo','vol_6m','amihud',
        'ln_dvol','ln_price','turnover','b2m','roe','rooa','capex_to_assets',
        'accruals_approx','inv_to_assets',
        'r_ret1','r_mom_3_1','r_mom_6_1','r_mom_12_1','r_vol_mo','r_vol_6m',
        'r_amihud','r_ln_dvol','r_ln_price','r_turnover','r_b2m','r_roe','r_rooa',
        'r_capex_to_assets','r_accruals_approx','r_inv_to_assets',
        'mom_12_x_size','mom_12_x_val','mom_12_x_prof',
    ]
    # append daily-OHLCV-derived characteristics (raw + rank) when enabled
    if os.environ.get("DAILY", "0").lower() not in ("0", "false", "off"):
        DAILY_RANKS = ['r_' + c for c in DAILY_FEATURES]
        FEATURES = DAILY_FEATURES + DAILY_RANKS + FEATURES
    d.to_csv(OUT, index=False)
    # save FEATURES for the model
    with open(os.path.join(HERE, 'data/full_features.txt'), 'w') as f:
        f.write('\n'.join(FEATURES))
    print('model panel:', d.shape)
    print('period:', d['ym'].min(), '->', d['ym'].max())
    print('symbols:', d['symbol'].nunique())
    print('FEATURES:', len(FEATURES))
    return d, FEATURES

if __name__ == '__main__':
    build()
