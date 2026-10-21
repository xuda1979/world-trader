"""FX Carry (外汇套息) — G10 short-rate differential top/bottom monthly L/S vs USD.
FREE data: FRED OECD 3M rates (monthly) + fx_hist USD crosses (daily). Monthly rebalance:
long highest-carry, short lowest-carry currencies; carry = foreign 3M - US 3M. Honest gates.
"""
import sys, urllib.request, json, time, numpy as np, pandas as pd, os
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
ROOT="/Users/daxu/software/world-trader"
DATA=f"{ROOT}/tools/quant/data"
champ=E.champ_ref()
KEY=open(f"{ROOT}/.env.local").read().split("FRED_KEY=")[1].splitlines()[0]
SID={'US':'IR3TIB01USM156N','JP':'IR3TIB01JPM156N','GB':'IR3TIB01GBM156N','CA':'IR3TIB01CAM156N',
     'AU':'IR3TIB01AUM156N','CH':'IR3TIB01CHM156N','NZ':'IR3TIB01NZM156N','SE':'IR3TIB01SEM156N',
     'NO':'IR3TIB01NOM156N','DE':'IR3TIB01DEM156N'}
def fetch_series(sid):
    url=f'https://api.stlouisfed.org/fred/series/observations?series_id={sid}&api_key={KEY}&file_type=json'
    d=json.loads(urllib.request.urlopen(url,timeout=25).read().decode())
    return pd.DataFrame([(o['date'],o['value']) for o in d['observations'] if o['value']!='.'],columns=['date','rate'])

rates=None
for c in ['US','JP','GB','CA','AU','CH','NZ','SE','NO','DE']:
    s=fetch_series(SID[c]); s['date']=pd.to_datetime(s['date']); s['rate']=s['rate'].astype(float)
    s=s.rename(columns={'rate':c}).set_index('date')[[c]]
    rates = s if rates is None else rates.join(s,how='outer')
rates=rates.ffill().sort_index().dropna(subset=['DE'])
# USD relative carry differentials (currency minus US)
carry=rates.drop(columns=['US']).sub(rates['US'],axis=0)

# FX crosses: USD_DEP (USD per foreign). Return = -d(log USD_DEP) approximated by pct_change of USD base
CUR={'JP':'USD_JPY','GB':'USD_GBP','CA':'USD_CAD','AU':'USD_AUD','CH':'USD_CHF','NZ':'USD_NZD','SE':'USD_SEK','NO':'USD_NOK','DE':'USD_EUR'}
def load_fx(pair):
    df=pd.read_csv(f"{DATA}/fx_hist/{pair}.csv"); df['date']=pd.to_datetime(df['date'])
    return df.set_index('date')['close'].astype(float).sort_index()
fx=pd.DataFrame({c:load_fx(pair) for c,pair in CUR.items() if os.path.exists(f"{DATA}/fx_hist/{pair}.csv")}).ffill()
ret=-(fx.pct_change())   # long foreign => earn FX appreciation (USD per FC down => FC up)

# monthly rebalance: long top-2 carry, short bottom-2 (user: TopK on carry)
rebal=carry.resample('MS').last()
pos=pd.DataFrame(0.0,index=ret.index,columns=ret.columns)
rbd=pd.DatetimeIndex(rebal.index)
for i,dt in enumerate(rbd[:]):
    if dt < ret.index[0]: continue
    row=rebal.loc[dt].dropna()
    if len(row)<4: continue
    rk=row.rank()
    K=2
    longs=rk[rk>=len(row)-K+1].index
    shorts=rk[rk<=K].index
    w=pd.Series(0.0,index=ret.columns)
    if len(longs): w[longs]+=1/len(longs)
    if len(shorts): w[shorts]-=1/len(shorts)
    end=rbd[i+1]-pd.Timedelta(days=1) if i+1<len(rbd)-1 else ret.index[-1]
    pos.loc[dt:end]=w.values

book=(pos.shift()*ret).sum(axis=1,min_count=1)
turn=pos.diff().abs().sum(axis=1)
net=book-turn*6.4/1e4
nr=net['2001':].dropna(); nv,_=E.vol_target(nr)
st=E.evaluate(nv,champ,'fx_carry')
print("=== FX CARRY (G10, top2/bottom2 vs USD, monthly) ===")
for k in ['SR','ann_geo','MDD','negyr','worst','H1_H2','negyr_pass','ac1','uniqR','corr_champ']:
    print(f"  {k:12s} = {st[k]}")
st['scramble_p']=E.scramble_p_lag(nv)[0]
print(f"  scramble_p = {st['scramble_p']:.3f}")
