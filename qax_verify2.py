import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality')
from r7_idea5_breadth import panel, RET_PAN
from r6lib import wback_rb
from r7lib import wed_rbd
from campaign.agents.B2_highfreq.gates import vol_target
MAW=189
R5=RET_PAN.drop(columns=["CASH"])
s=np.sign(panel-panel.rolling(MAW,min_periods=MAW//2).mean()).fillna(0)*0.2
Wt,rbd=s, wed_rbd(panel.index)
net,_=wback_rb(Wt,R5,rbd)
rfull,_=vol_target(net.dropna(),0.10)
rfull=rfull.dropna()
f = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv',parse_dates=['date']).set_index('date')['ret']
j = pd.concat([rfull.rename('r'), f.rename('f')],axis=1,sort=True).dropna()
d=(j['r']-j['f']).abs()
print(f"QAxasts (E1 path): n={len(j)} corr={j['r'].corr(j['f']):.8f} max|d|={d.max():.3e} exact={(d<1e-12).sum()}")
