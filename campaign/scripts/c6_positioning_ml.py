"""C6 Idea 3: Positioning-ML. COT/TFF MM z-scores (weekly, ffill->daily) + price momentum/vol
-> walk-forward GBM (monthly refit) per market -> 5d sign -> position capped +-1.
Books: long-only-convention adjusted prices (futures sign fix). T+1, 6bps/side, vol-target 10%.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr, scramble_pval
from sklearn.ensemble import GradientBoostingRegressor
import re, os
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
NEWD='/Users/daxu/software/world-trader/tools/quant/data/newdata'
FX='/Users/daxu/software/world-trader/tools/quant/data/fx'
def load_fred(n, col=None):
    df=pd.read_csv(f'{FRED}/{n}.csv',index_col=0,parse_dates=True)
    v=df.iloc[:,0].astype(float); v.index.name='date'
    return v[~v.index.duplicated(keep='last')].dropna()
def load_new(n):
    df=pd.read_csv(f'{NEWD}/{n}.csv',index_col=0,parse_dates=True)
    v=df.iloc[:,0].astype(float); v.index.name='date'
    return v[~v.index.duplicated(keep='last')].dropna()
def load_fx(n):
    df=pd.read_csv(f'{FX}/{n}.csv',index_col=0,parse_dates=True)
    v=df['close'].astype(float); v.index.name='date'
    return v[~v.index.duplicated(keep='last')].dropna()

# --- prices (long-only-convention adjusted) ---
px = {}
px['wti']    = -1*load_new('DCOILWTICO') if False else load_new('DCOILWTICO')  # placeholder, wti long-only below
px['wti']    = -load_new('DCOILWTICO')
px['brent']  = -load_new('DCOILBRENTEU')
px['natgas'] = -load_new('DHHNGSP')
px['gold']   = -load_fred('xau')
px['silver'] = -load_fred('slv')
px['spx']    = -load_fred('spx')
px['us10y']  = load_fred('us10y')          # yield down = bond futures up -> price = -yield; NOT sign-flip
px['us10y']  = -load_fred('us10y')
px['eur']    =  load_fred('eur')           # EUR futures quoted USD per EUR = EURUSD up
px['jpy']    =  load_fred('jpy')
px['gbp']    =  load_fred('gbp')
px['chf']    = 1/load_new('DEXSFUS')       # DEXSFUS = USD per CHF -> CHF futures price
px['aud']    = 1/load_new('DEXUSAL')       # DEXUSAL = USD per AUD
px['cad']    = 1/load_fred('cad')          # CAD futures = USD per CAD
# no NZD on disk
# copper via copx ETF (long-only already)
px['copper'] = load_fred('copx') if os.path.exists(f'{FRED}/copx.csv') else None
for k,v in list(px.items()):
    if v is None: print('drop',k); px.pop(k)
for k,v in px.items():
    print(k, v.index.min().date(), v.index.max().date(), len(v))
pd.to_pickle(px, '/tmp/c6_px.pkl')
