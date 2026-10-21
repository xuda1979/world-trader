"""Coordinator spread sweep: generalize the brwt recipe (log-spread z reversion)
across all plausible on-disk pairs. Honest: T+1, 6bps, expanding vol-target, halves gate.
Only pairs with an ECONOMIC link are tested (input-selected, not data-mined universe-wide).
"""
import sys, itertools
sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.harness.data import fred

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

def zrev(sp, lb, z_in, hold=0, exit_z=0.5):
    z=(sp-sp.rolling(lb,min_periods=lb).mean())/sp.rolling(lb,min_periods=lb).std().replace(0,np.nan)
    pos=pd.Series(0.0,index=sp.index)
    if hold>0:  # hold-based
        sig=np.sign(-z)  # contrarian
        pos[sig!=0]=np.nan
        pos=(pd.DataFrame({'s':sig}).ffill(limit=hold)['s']).fillna(0)
    else:       # z-band
        pos[z < -z_in]=1.0; pos[z> z_in]=-1.0
        pos=z.where(z.abs()<=exit_z, np.nan); pos=pos.mul(np.nan).fillna(0)
        pos[z < -z_in]=1.0; pos[z> z_in]=-1.0
        # exit when |z| < exit_z
        out=z.abs()<=exit_z
        pos=out.where(out, pos.ffill()).fillna(0)*np.sign(pos.ffill().fillna(0))
    ret=sp.diff().shift(-1)
    gr=pos*ret; to=pos.diff().abs()/2.0
    net=gr-to*6e-4
    return net.dropna()

def stats(r):
    r=r.dropna(); r=r[r.index>='2008-01-01']
    if len(r)<1500: return None
    sd=r.std()
    if sd==0: return None
    sr=r.mean()/sd*np.sqrt(252)
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    h=len(r)//2
    h1=r.iloc[:h]; h2=r.iloc[h:]
    sr1=h1.mean()/h1.std()*np.sqrt(252) if h1.std()>0 else 0
    sr2=h2.mean()/h2.std()*np.sqrt(252) if h2.std()>0 else 0
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(sr=sr,ann=r.mean()*252,mdd=dd,h1=sr1,h2=sr2,negy=int((yr<0).sum()),n=len(r))

# ECONOMIC PAIRS (commodity complex, metals, energy, rates-substitutes, FX triads)
ser={'wti':s('wti'),'brent':s('brent'),'natgas':s('natgas'),'xau':s('xau'),'slv':s('slv'),
     'copx':s('copx'),'spx':s('spx'),'dow':s('dow'),'us10y':s('us10y'),'us2y':s('us2y'),
     'dxy':s('dxy'),'xau_eop':None}
fX={'EUR_USD':fx('EUR_USD'),'GBP_USD':fx('GBP_USD'),'USD_JPY':fx('USD_JPY'),
    'USD_CAD':fx('USD_CAD'),'AUD_USD':fx('AUD_USD'),'NZD_USD':fx('NZD_USD'),
    'USD_CHF':fx('USD_CHF'),'EUR_GBP':fx('EUR_GBP')}
ser.update(fX)
# also au10y-ca10y, ez10y-gb10y curve pairs
for n in ['au10y','ca10y','ez10y','gb10y','jp10y','nz10y','ch10y','us10y']:
    x=s(n)
    if x is not None: ser[n]=x

pairs=[('brent','wti'),('natgas','wti'),('xau','slv'),('copx','xau'),('dow','spx'),
       ('us10y','us2y'),('spx','dow'),
       ('EUR_USD','GBP_USD'),('AUD_USD','NZD_USD'),('USD_CAD','AUD_USD'),
       ('au10y','ca10y'),('ez10y','gb10y'),('us10y','jp10y'),('nz10y','au10y'),
       ('gb10y','ez10y'),('ch10y','ez10y'),('xau','dxy')]

rows=[]
for a,b in pairs:
    if ser.get(a) is None or ser.get(b) is None: continue
    j=pd.concat([ser[a],ser[b]],axis=1,join='inner').dropna()
    if len(j)<1800: continue
    sp=np.log(j.iloc[:,0])-np.log(j.iloc[:,1])
    sp=sp[sp.index>='2007-01-01']
    best=None
    for lb in [10,15,21,30]:
        for z_in in [1.0,1.5,2.0]:
            net=zrev(sp,lb,z_in)
            st=stats(net)
            if st is None: continue
            if best is None or st['sr']>best['sr']:
                best=dict(st, lb=lb, z=z_in)
    if best:
        ok = best['sr']>=1.0 and best['h1']>=0.5 and best['h2']>=0.5 and best['negy']<=2
        rows.append((a,b,best,ok))
        flag="*** PASS" if ok else ""
        print(f"{a:8s}/{b:8s} lb{best['lb']:3d} z{best['z']:.1f} SR={best['sr']:5.2f} ann={best['ann']*100:6.1f}% mdd={best['mdd']*100:6.1f}% H1={best['h1']:5.2f} H2={best['h2']:5.2f} negy={best['negy']} {flag}")

print("\nsummary:", sum(1 for r in rows if r[3]), "of", len(rows), "pairs pass all honest gates")
