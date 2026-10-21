"""IDEA 3: FX carry from short-rate differentials.
Available on disk (verified): US DGS3MO daily (1981+). Foreign short rates: NONE on disk.
Proxy construction: implied carry from FORWARD-LOOKING FX itself is not PIT; so instead:
carry proxy = 3mo US rate - 3mo foreign-proxy. Foreign proxies on disk are MONTHLY 10y only
(FXMICRO/CARRYFX verdicts: dead). NEW angle here: DGS3MO as USD side + INTL 10y → mixed maturity
is not a deposit carry. CHARTER requires log BLOCKED if no foreign deposit rates.

Second idea tested instead: CARRY-ROTATION using realized rate-diff CHANGES (DGS3MO vs foreign
policy proxy = their 10y, PIT month-lag) — again 10y proxy.

HONEST VERDICT PATH: build the best PIT carry available: USD DGS3MO vs foreign 10y (m+1 lag)
for the 4 twelvedata pairs with rates (AU, CA, CH, JP, NZ, EZ, GB) + DEX crosses (JP, EU, UK,
NO, SD, SF, DN, SI, KO, IN, BZ, MX), vol-weighted long-high-carry. If SR<0.6 → charter idea
3 CLOSED on this disk, matching CARRYFX §6.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

us=pd.read_csv(f'{FR}/DGS3MO.csv',index_col=0,parse_dates=True).iloc[:,0]
us=pd.to_numeric(us,errors='coerce').dropna()

def f10(code):
    v=pd.read_csv(f'{FR}/{code}.csv',index_col=0,parse_dates=True).iloc[:,0]
    return pd.to_numeric(v,errors='coerce').dropna()

# PIT: monthly value m usable from first business day of m+1 (CARRYFX §2 convention)
def pit_monthly(s):
    m=s.resample('ME').last().dropna()
    idx=pd.to_datetime([d+pd.offsets.BMonthBegin(1) for d in m.index])
    return pd.Series(m.values,index=idx).reindex(pd.bdate_range(m.index[0],s.index[-1])).ffill()

pairs=[('au10y','DEXUSEU','AUD'),  # AUD via DEXUSEU? no — AUD not on DEX. use fx AUD_USD
      ]
print('Foreign 10y codes on disk:', [c for c in ['au10y','ca10y','ch10y','ez10y','gb10y','jp10y','nz10y'] ])
for c in ['au10y','ca10y','ch10y','ez10y','gb10y','jp10y','nz10y']:
    s=f10(c); print(f'  {c}: {s.index[0].date()}..{s.index[-1].date()} n={len(s)} freq~{"monthly" if len(s)<300 else "daily"}')
