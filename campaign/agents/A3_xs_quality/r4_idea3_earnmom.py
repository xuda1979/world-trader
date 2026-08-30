"""r4 idea3: earnings-momentum proxy — 6-1 price momentum computed ONLY among names with
fresh PIT fundamentals (FY y usable Jul-1 y+1, freshness <= 24m => 'recently reported').
Long top quintile, MA-gated, vt15. Grid: frac, gate win, freshness."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from r4lib import *
from r2lib import wbacktest

f=pd.read_parquet("/Users/daxu/software/world-trader/alphaportfolio_replication/data/fundamentals_annual.parquet")
f=f[f.symbol.isin(px.columns)].copy()
f["avail"]=pd.to_datetime((f.fy+1).astype(str)+"-07-01")

def fresh_mask(max_age_m):
    """Wide bool: name has fundamentals filed within max_age_m months as of date t."""
    out=pd.DataFrame(False,index=IDX,columns=px.columns)
    sym=set(f.symbol.astype(str))
    ev=f[["symbol","avail"]].dropna()
    ev=ev[ev.avail<=IDX[-1]]
    for s,gp in ev.groupby("symbol"):
        if s not in out.columns: continue
        dates=gp.avail.sort_values().tolist()
        pos=np.searchsorted(np.array(dates,dtype="datetime64[ns]"),IDX.values.astype("datetime64[ns]"),side="right")-1
        ok=pos>=0
        idxs=np.where(ok)[0]
        for i in idxs:
            last=dates[pos[i]]
            if (IDX[i]-last).days<=max_age_m*30.44: out.iloc[i,out.columns.get_loc(s)]=True
    return out

sig=px.shift(21)/px.shift(126)-1.0
rows=[]
for fresh_m in (24,14):
    FM=fresh_mask(fresh_m)
    sig_c=sig.where(FM)
    for frac in (0.15,0.30):
        for gw in (150,200):
            G=ma_gate(gw,0.03)
            W=long_top(sig_c,frac,G)
            e=evaluate(f"fresh{fresh_m} f{frac} ma{gw}",W,0.15,verbose=False)
            if e:
                g=e["g"]; rows.append((fresh_m,frac,gw,g["SR"],g["H1"],g["H2"],g["negYr"],g["worst"],g["ann"],g["corr_champ"]))
                print(rows[-1],flush=True)
df=pd.DataFrame(rows,columns=["fresh_m","frac","gw","SR","H1","H2","negYr","worst","ann","corrC"])
print(df.to_string(index=False))
print("PASS count (std+halves.4+corr<=0.3):",((df.SR>=0.6)&(df.H1>=0.4)&(df.H2>=0.4)&(df.negYr<=2)&(df.worst>-5)&(df.corrC<=0.3)).sum())
