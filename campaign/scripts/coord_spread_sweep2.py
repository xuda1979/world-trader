"""Spread sweep v2: EXACT brwt recipe (z-band, no explicit exit, expanding vol-target 10%).
"""
import sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.agents.B2_highfreq.gates import vol_target, full_stats

FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
def s(name):
    try:
        df=pd.read_csv(f'{FRED}/{name}.csv',index_col=0,parse_dates=True)
        v=df['value'] if 'value' in df.columns else df.iloc[:,0]
        return v[v>0].dropna()
    except Exception:
        return None
def fx(name):
    df=pd.read_csv(f'/Users/daxu/software/world-trader/tools/quant/data/fx/{name}.csv',index_col=0,parse_dates=True)
    return df['close'].dropna()

def run(sp, lb, z_in, min_start='2008-01-01'):
    z=(sp-sp.rolling(lb,min_periods=lb).mean())/sp.rolling(lb,min_periods=lb).std().replace(0,np.nan)
    pos=pd.Series(0.0,index=sp.index); pos[z<-z_in]=1.0; pos[z>z_in]=-1.0
    ret=sp.diff().shift(-1)
    gr=pos*ret; to=pos.diff().abs()/2.0
    net=gr-to*6e-4
    scaled,_=vol_target(net.dropna())
    return scaled[scaled.index>=min_start]

ser={'wti':s('wti'),'brent':s('brent'),'natgas':s('natgas'),'xau':s('xau'),'slv':s('slv'),
     'copx':s('copx'),'spx':s('spx'),'dow':s('dow'),'us10y':s('us10y'),'us2y':s('us2y'),
     'dxy':s('dxy'),'eur':s('eur'),'gbp':s('gbp'),'jpy':s('jpy'),'cad':s('cad'),
     'au10y':s('au10y'),'ca10y':s('ca10y'),'ez10y':s('ez10y'),'gb10y':s('gb10y'),
     'jp10y':s('jp10y'),'nz10y':s('nz10y'),'ch10y':s('ch10y')}
ser.update({k:v for k,v in dict(
    EUR_USD=fx('EUR_USD'),GBP_USD=fx('GBP_USD'),USD_JPY=fx('USD_JPY'),USD_CAD=fx('USD_CAD'),
    AUD_USD=fx('AUD_USD'),NZD_USD=fx('NZD_USD'),USD_CHF=fx('USD_CHF'),EUR_GBP=fx('EUR_GBP')).items()})

pairs=[('brent','wti'),('natgas','wti'),('xau','slv'),('copx','xau'),('dow','spx'),
       ('us10y','us2y'),('spx','dow'),('xau','dxy'),
       ('EUR_USD','GBP_USD'),('AUD_USD','NZD_USD'),('USD_CAD','AUD_USD'),
       ('au10y','ca10y'),('ez10y','gb10y'),('us10y','jp10y'),('nz10y','au10y'),
       ('gb10y','ez10y'),('ch10y','ez10y'),('eur','gbp'),('cad','aud')]

results=[]
for a,b in pairs:
    if ser.get(a) is None or ser.get(b) is None: 
        print(f"{a}/{b}: MISSING DATA"); continue
    j=pd.concat([ser[a],ser[b]],axis=1,join='inner').dropna()
    if len(j)<1800: 
        print(f"{a}/{b}: overlap {len(j)} too short"); continue
    sp=(np.log(j.iloc[:,0])-np.log(j.iloc[:,1])).dropna()
    best=None
    for lb in [10,15,21,30]:
        for z_in in [1.0,1.5,2.0]:
            r=run(sp,lb,z_in)
            if len(r)<1500: continue
            st=full_stats(r)
            if best is None or st['sr']>best[0]['sr']:
                best=(st,lb,z_in,r)
    if best is None: continue
    st,lb,z_in,r=best
    h=len(r)//2
    h1=full_stats(r.iloc[:h]); h2=full_stats(r.iloc[h:])
    ok = st['sr']>=1.0 and h1['sr']>=0.5 and h2['sr']>=0.5 and st['negy']<=2 and st['mdd']>-15
    flag="*** PASS" if ok else ""
    print(f"{a:8s}/{b:8s} lb{lb:3d} z{z_in:.1f} SR={st['sr']:5.2f} ann={st['ann']:6.1f}% mdd={st['mdd']:6.1f}% H1={h1['sr']:5.2f} H2={h2['sr']:5.2f} negy={st['negy']} {flag}")
    if ok: results.append((a,b,r))
    elif st['sr']>=0.7: results.append((f"{a}_{b}_WEAK",None,r))

import os
for a,b,r in results:
    if b is not None:
        out=f"/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/{a}_{b}_spread.csv"
        pd.DataFrame({'ret':r.values},index=r.index).to_csv(out)
        print("saved", out)
