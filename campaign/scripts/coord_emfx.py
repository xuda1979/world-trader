"""Coordinator: broad-dollar & EM-FX engines (DTWEXBGS + DEX series).
1. Broad dollar TS momentum (lb 21-252) — trade the index directly (ETF proxy cost OK).
2. EM-FX basket momentum: long strongest vs USD / short weakest (INR BRL MXN KRW SGD in USD terms).
3. EM vs DM divergence: EM basket vs EUR+JPY+GBP basket spread momentum.
T+1, 6bps, trailing vt10, honest gates.
"""
import sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.agents.B2_highfreq.gates import vol_target, full_stats

FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
def s(name):
    df=pd.read_csv(f'{FRED}/{name}.csv',index_col=0,parse_dates=True)
    v=df['value'] if 'value' in df.columns else df.iloc[:,0]
    v=v[v>0]
    return v[~v.index.duplicated(keep='last')].sort_index()

def ts_mom(px, lb, rebal=1, long_only=False, vt=True):
    sig=np.sign(px.pct_change(lb))
    if rebal>1:
        sig=sig.iloc[::rebal].reindex(px.index).ffill()
    ret=px.pct_change().shift(-1)
    gr=sig*ret; to=sig.diff().abs()/2
    net=gr-to*6e-4
    net=net.dropna()
    if vt:
        scaled,_=vol_target(net); return scaled
    return net

def report(tag, r):
    r=r.dropna(); r=r[r.index>='2008-01-01']
    if len(r)<1500: print(f"{tag}: too short ({len(r)})"); return
    st=full_stats(r)
    h=len(r)//2; h1=full_stats(r.iloc[:h]); h2=full_stats(r.iloc[h:])
    ok=st['sr']>=1.0 and h1['sr']>=0.5 and h2['sr']>=0.5 and st['negy']<=2
    print(f"{tag:34s} SR={st['sr']:5.2f} ann={st['ann']:6.1f}% mdd={st['mdd']:6.1f}% H1={h1['sr']:5.2f} H2={h2['sr']:5.2f} negy={st['negy']} {'*** PASS' if ok else ''}")

dxy=s('DTWEXBGS')
for lb in [21,63,126,252]:
    report(f"DTWEXBGS mom lb{lb}", ts_mom(dxy,lb))

# EM basket (USD per local ccy; higher = weaker EM ccy). Trade each with momentum sign.
ems={n:s(n) for n in ['DEXINUS','DEXBZUS','DEXMXUS','DEXKOUS','DEXSIUS']}
dms={n:s(n) for n in ['DEXJPUS','DEXUSEU','DEXUSUK','DEXCAUS']}

# basket-level: average of per-ccy momentum books
for lb in [21,63,126]:
    books=[]
    for n,px in ems.items():
        books.append(ts_mom(px,lb))
    j=pd.DataFrame(books).dropna(how='all').fillna(0).mean(axis=1)
    report(f"EM5 basket mom lb{lb}", j)

# EM vs DM spread
em=ems['DEXBZUS'].rename('em'); 
for lb in [21,63]:
    emret=pd.concat([px.pct_change() for px in ems.values()],axis=1).mean(axis=1)
    dmret=pd.concat([px.pct_change() for px in dms.values()],axis=1).mean(axis=1)
    sp=(emret-dmret).cumsum()
    report(f"EM-DM spread mom lb{lb}", ts_mom((1+emret).cumprod()/(1+dmret).cumprod(), lb))
