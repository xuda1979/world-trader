import sys
import pandas as pd, numpy as np
# Natgas publication-lag materiality: C5ng calm filter uses same-day |log ret| > 2.5x trailing 90d sigma.
# If DHHNGSP prints publish NEXT morning, the filter would use t-1 info... actually filter at t uses lr(t) (same print) to decide entry at t -> T+1 convention earns s_{t+1}/s_t.
# The signal pos is set on day t USING day-t print (|lr_t|). If print available only t+1, the gate breaks.
# Quantify: rebuild with pos.shift(1) on gate (i.e., filter uses previous day's magnitude) and compare SR.
D='/Users/daxu/software/world-trader/tools/quant/data/newdata/DHHNGSP.csv'
s=pd.read_csv(D,index_col=0,parse_dates=True).iloc[:,0]
s=pd.to_numeric(s,errors='coerce'); s=s[s>0].dropna().sort_index()
lr=np.log(s).diff(); idx=s.index
pos=pd.Series(0.0,index=idx)
pos[idx.dayofweek==2]=-1.0; pos[idx.dayofweek==3]=-1.0; pos[idx.dayofweek==4]=1.0
thr=lr.rolling(90).std().shift(1)*2.5
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/B2_highfreq')
from gates import vol_target
def sr_of(x):
    x=x.dropna(); return x.mean()/x.std()*np.sqrt(252)
def build(gate_shift):
    p=pos.mask(lr.abs()>thr,0.0)
    if gate_shift: p=p.shift(1).fillna(0.0)   # degraded: filter info available 1d late -> shift whole pos
    gr=p*lr.shift(-1); turn=p.diff().abs().fillna(p.abs())
    net=(gr-turn*6e-4).dropna()
    scaled,_=vol_target(net)
    return scaled.dropna()
r_asis = build(False); r_lag = build(True)
print(f"C5ng as-is SR={sr_of(r_asis):.3f}  with gate delayed 1d SR={sr_of(r_lag):.3f}")
# monthly since 2008 (champion window)
for nm, r in [('asis',r_asis),('lag',r_lag)]:
    r08 = r[r.index>='2008-09-01']
    print(f"  {nm} 2008-09+ SR={r08.mean()/r08.std()*np.sqrt(252):.3f}")
