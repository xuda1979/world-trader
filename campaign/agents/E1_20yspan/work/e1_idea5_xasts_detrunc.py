"""E1 idea5: de-truncate QAxasts (panel floor 2006-09; MA189 warmup -> eval from 2007-02). Frozen params."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader"); sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from r7_idea5_breadth import panel, RET_PAN
from r6lib import wback_rb
from r7lib import wed_rbd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import save_sleeve
from campaign.agents.B2_highfreq.gates import full_stats, halves_sr

MAW=189
R5=RET_PAN.drop(columns=["CASH"])
s=np.sign(panel-panel.rolling(MAW,min_periods=MAW//2).mean()).fillna(0)*0.2
Wt,rbd=s, wed_rbd(panel.index)
net,_=wback_rb(Wt,R5,rbd)
r=net.dropna()   # NO 2008 truncation; vt applied by champion_build anyway, keep raw? NO: keep same shape as saved sleeve.
# saved sleeve had sret(): truncation + vol_target + iloc[5]. Apply vol_target on FULL history then eval:
from campaign.agents.B2_highfreq.gates import vol_target
rfull,_=vol_target(net.dropna(),0.10)
rfull=rfull.dropna()
BLEND=pd.read_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_CHAMPION20Y_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
for es in ['2007-02-01','2007-06-01']:
    e=rfull[rfull.index>=es]
    st=full_stats(e); h1,h2=halves_sr(e)
    a,b=e.align(BLEND,join='inner'); c=a.corr(b)
    print(f"xasts eval {es}+: start={e.index.min().date()} SR={st['sr']:.2f} ann={st['ann']:.1f}% MDD={st['mdd']:.1f}% negy={st['negy']}/{st['years']} worst={st['worst']:.1f}% H1={h1:.2f} H2={h2:.2f} corr_blend={c:.3f}")
    pre=e[e.index<'2017-01-01']; post=e[e.index>='2017-01-01']
    print(f"   IS={pre.mean()/pre.std()*np.sqrt(252):.2f} OOS={post.mean()/post.std()*np.sqrt(252):.2f}  yearly={st['yearly']}")
ov=pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality/sleeves/QA_xasts_tsmom189.csv',index_col=0,parse_dates=True).iloc[:,0]
j=pd.concat([rfull.rename('new'),ov.rename('old')],axis=1,join='inner').dropna()
print("overlap corr vs orig:", round(j.corr().iloc[0,1],4), "n=",len(j))
save_sleeve(rfull,'/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv',
"E1 QAxasts de-truncated: identical frozen construction (5-leg cross-asset TSMOM MA189, EW 20%, Wed rebalance, T+1, 6bps, vt10) with NO 2008 truncation. Panel floor 2006-09 (twelve_big); MA189 warmup -> honest from 2007-02.")
