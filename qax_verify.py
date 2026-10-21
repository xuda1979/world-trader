import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality')
from r7lib import *
from r7_idea5_breadth import panel, RET_PAN
from r6lib import wback_rb
MAW=189
R5=RET_PAN.drop(columns=["CASH"])
def build(sigp):
    s=np.sign(sigp-sigp.rolling(MAW,min_periods=MAW//2).mean()).fillna(0)*0.2
    return s, wed_rbd(sigp.index)
Wt,rbd=build(panel)
net,_=wback_rb(Wt,R5,rbd)
def vol_target(r, target=0.10, min_obs=60, cap=5.0):
    vol = r.expanding(min_obs).std().shift(1) * np.sqrt(252)
    lev = (target / vol.replace(0,np.nan)).clip(0, cap)
    return (r*lev).iloc[5:].dropna()
r = vol_target(net, 0.10)
f = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv',parse_dates=['date']).set_index('date')['ret']
j = pd.concat([r.rename('r'), f.rename('f')],axis=1,sort=True).dropna()
d=(j['r']-j['f']).abs()
print(f"QAxasts: n={len(j)} corr={j['r'].corr(j['f']):.8f} max|d|={d.max():.3e} exact={(d<1e-12).sum()}")
print("panel source:", panel.index[0], "->", panel.index[-1])
