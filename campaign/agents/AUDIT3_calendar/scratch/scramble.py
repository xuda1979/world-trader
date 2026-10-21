"""Charter 4: calendar-scramble test — circular-shift the PRICE series by random offsets,
rebuild sleeve, p-value of real SR vs scrambled."""
import sys, pickle
import numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/AUDIT3_calendar/scratch')
from rebuild_ng import build

D='/Users/daxu/software/world-trader/tools/quant/data/newdata/DHHNGSP.csv'
s=pd.read_csv(D,index_col=0,parse_dates=True).iloc[:,0]
s=pd.to_numeric(s,errors='coerce'); s=s[s>0].dropna().sort_index()
rng=np.random.default_rng(20260901)

def build_shift(summer, offset):
    """circular shift of prices across the fixed calendar index (keeps weekday calendar,
    breaks calendar alignment of prices)."""
    v=s.values.copy()
    v=np.roll(v,offset)
    s2=pd.Series(v,index=s.index)
    lr=np.log(s2).diff(); idx=lr.index
    pos=pd.Series(0.0,index=idx)
    pos[idx.dayofweek==2]=-1.0; pos[idx.dayofweek==3]=-1.0; pos[idx.dayofweek==4]=1.0
    if summer: pos[~idx.month.isin(list(range(4,11)))]=0.0
    thr=lr.rolling(90).std().shift(1)*2.5
    pos=pos.mask(lr.abs()>thr,0.0)
    gr=pos*lr.shift(-1)
    turn=pos.diff().abs(); turn.iloc[0]=abs(pos.iloc[0])
    net=(gr-6e-4*turn).dropna()
    net=net[net.index>='1998-01-01']
    from campaign.agents.B2_highfreq.gates import vol_target
    sc,_=vol_target(net)
    return sc.dropna()

import pickle
R=pickle.load(open('/Users/daxu/software/world-trader/campaign/agents/AUDIT3_calendar/scratch/rebuilt.pkl','rb'))
for summer,realkey in [(False,'C5ng_full'),(True,'C5ngsum_full')]:
    real=R[realkey]; real=real[real.index>='1998-01-01']
    srr=real.mean()/real.std()*np.sqrt(252)
    n=50
    sims=np.empty(n)
    for i in range(n):
        off=rng.integers(200, len(s)-200)
        r2=build_shift(summer,int(off))
        sims[i]=r2.mean()/r2.std()*np.sqrt(252)
    p=(np.sum(sims>=srr)+1)/(n+1)
    print(f"summer={summer} real SR={srr:.2f} | scrambled SR: mean={sims.mean():.3f} sd={sims.std():.3f} "
          f"p95={np.percentile(sims,95):.2f} max={sims.max():.2f} | p={( (np.sum(sims>=srr)+1)/(n+1)):.4f}")
    np.save(f'/Users/daxu/software/world-trader/campaign/agents/AUDIT3_calendar/scratch/scramble_{summer}.npy',sims)
