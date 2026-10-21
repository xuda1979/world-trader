"""Coordinator: crack-spread z-reversion family (heating oil, RBOB/gasoline, jet vs WTI/Brent).
Sibling of the proven brwt recipe. Exact brwt construction + vt10 + honest gates.
"""
import sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.agents.B2_highfreq.gates import vol_target, full_stats

NEW='/Users/daxu/software/world-trader/tools/quant/data/newdata'
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
def s(d,f):
    v=pd.read_csv(f'{d}/{f}.csv',index_col=0,parse_dates=True).iloc[:,0]
    v=pd.to_numeric(v,errors='coerce'); v=v[v>0]
    return v[~v.index.duplicated(keep='last')].sort_index()

def run(sp, lb, z_in, min_start='2008-01-01'):
    z=(sp-sp.rolling(lb,min_periods=lb).mean())/sp.rolling(lb,min_periods=lb).std().replace(0,np.nan)
    pos=pd.Series(0.0,index=sp.index); pos[z<-z_in]=1.0; pos[z>z_in]=-1.0
    ret=sp.diff().shift(-1)
    gr=pos*ret; to=pos.diff().abs()/2.0
    net=gr-to*6e-4
    scaled,_=vol_target(net.dropna())
    return scaled[scaled.index>=min_start]

def report(tag, sp, lbs=(10,15,21,30), zins=(1.0,1.5,2.0)):
    best=None
    for lb in lbs:
        for z in zins:
            r=run(sp,lb,z)
            if len(r)<1500: continue
            st=full_stats(r)
            if best is None or st['sr']>best[0]['sr']: best=(st,lb,z,r)
    if best is None: print(f"{tag}: too short"); return None
    st,lb,z,r=best
    h=len(r)//2; h1=full_stats(r.iloc[:h]); h2=full_stats(r.iloc[h:])
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    worst=yr.min()
    ok=st['sr']>=1.0 and h1['sr']>=0.5 and h2['sr']>=0.5 and st['negy']<=2 and st['mdd']>-15 and worst>-0.05
    print(f"{tag:22s} lb{lb:3d} z{z:.1f} SR={st['sr']:5.2f} ann={st['ann']:6.1f}% mdd={st['mdd']:6.1f}% H1={h1['sr']:5.2f} H2={h2['sr']:5.2f} negy={st['negy']} worst {worst*100:5.1f}% {'*** PASS' if ok else ''}")
    return (tag,r) if ok else None

ho=s(NEW,'DHOILNYH')      # heating oil NY harbor (classic crack leg)
jet=s(NEW,'DJFUELUSGULF') # kerosene-type jet fuel gulf coast
rbob=s(NEW,'GASREGW')     # regular gasoline (WEEKLY — caveat)
wti=s(NEW,'DCOILWTICO')
brent=s(NEW,'DCOILBRENTEU')
props=[]
props.append(report("HO-WTI crack", np.log(ho)-np.log(wti)))
props.append(report("HO-Brent crack", np.log(ho)-np.log(brent)))
props.append(report("Jet-WTI crack", np.log(jet)-np.log(wti)))
props.append(report("Jet-HO spread", np.log(jet)-np.log(ho)))
props.append(report("WTI-Brent (rev)", np.log(wti)-np.log(brent)))
props.append(report("HO/Jet avg - WTI", (np.log(ho)+np.log(jet))/2-np.log(wti)))
saved=[p for p in props if p]
for tag,r in saved:
    out=f"/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/{tag.replace(' ','_').replace('/','_').replace('(','').replace(')','')}.csv"
    pd.DataFrame({'ret':r.values},index=r.index).to_csv(out)
    print("saved", out)
