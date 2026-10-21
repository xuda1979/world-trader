import pandas as pd, numpy as np
# IBKR-layer sanity: the committed champion embeds "broker-real costs"?
# Quantify implied total cost drag: compare sleeve-only EW (no extra costs) recon (my recon ann 61.8%) vs committed 49.4%
# => implied extra layer ~ -12.4pp/yr arithmetic. Consistent with instrument costs+borrow claimed? 
# Rough estimate of expected: mean turnover per sleeve... quick estimate using pos proxy |ret| changes:
SLEEVES = {
 'brwt15': '../../../agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv',
 'brwt10': '../../../agents/COORD/sleeves/brwt10_2000.csv',
 'brwt7':  '../../../agents/COORD/sleeves/brwt7.csv',
 'brwt5':  '../../../agents/COORD/sleeves/brwt5.csv',
 'C5ng':   '../../../agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv',
 'C5ngsum':'../../../agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv',
 'A5r2':   '../../../agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv',
 'a6r7':   '../../../agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv',
 'QAxasts':'../../../agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv',
 'carryv2':'../../../agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv',
 'dualmom':'../../../agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv',
 'XGB1y':  '../../../results/sleeve_library/XGB1y_deploy.csv',
}
COSTS = {'brwt15':1.5,'brwt10':1.5,'brwt7':1.5,'brwt5':1.5,'C5ng':5,'C5ngsum':5,'A5r2':6,
 'a6r7':5,'QAxasts':8,'carryv2':8,'dualmom':15,'XGB1y':15}
P = {k: pd.to_numeric(pd.read_csv(p,parse_dates=['date']).set_index('date')['ret'],errors='coerce') for k,p in SLEEVES.items()}
def vt10(r, target=0.10, minobs=60, cap=8.0):
    vol=r.rolling(minobs,min_periods=minobs).std().shift(1)*np.sqrt(252)
    sc=(target/vol.replace(0,np.nan)).clip(upper=cap).fillna(0.0)
    return r*sc
V = pd.DataFrame({k: vt10(P[k]) for k in SLEEVES})
# turnover proxy: |r_t| / typical daily vol * ~2 sides... For a vt10 book at 10% vol, daily |trade| ~ turnover.
# Use documented numbers instead: report implied drag only.
ch = pd.read_csv('../../../results/GOAL100_STRICTTRADE_BALANCED_daily.csv',parse_dates=['date']).set_index('date')
rc = pd.to_numeric(ch['ret'],errors='coerce').dropna()
print(f"my no-extra-cost recon ann (arith) = {0.618*100:.1f}%  committed = {rc.mean()*252*100:.1f}%")
print(f"implied extra execution+borrow drag = {(0.618-rc.mean()*252)*100:.1f}pp/yr")
