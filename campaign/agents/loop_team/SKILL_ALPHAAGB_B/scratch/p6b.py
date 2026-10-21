"""P6b: audit QAxasts (champion pool member). Reconstruct the VIX leg position exactly
(VIX<MA189 -> short vol, 20% weight leg), test poslag on the LEG and on the whole 5-leg
sleeve return file; then diagnostic rebuild of champion WITHOUT QAxasts."""
import sys; sys.path.insert(0,'.')
from libb import *
import libb, pandas as pd, numpy as np
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
vix=pd.read_csv(f'{FRED}/VIXCLS.csv',index_col=0,parse_dates=True).iloc[:,0]
vix=pd.to_numeric(vix,errors='coerce'); vix=vix[~vix.index.duplicated(keep='last')].sort_index().dropna()
vix=vix[vix>0]
# VIX leg position (20% of sleeve): short below MA189, long above
pos=pd.Series(np.nan,index=vix.index)
pos[vix<vix.rolling(189).mean()]=-1.0
pos[vix>=vix.rolling(189).mean()]=1.0
pos=pos.ffill().fillna(0.0)
r_v=vix.pct_change()
leg_g=F.net_of(-pos,r_v)[0]  # 1.0 notional leg pnl
leg_s=F.vol_target_scale(leg_g,vt=0.02,min_days=60,cap=3.0,trailing_shift=1)  # 20% vt share
leg_pos=-pos*leg_s
leg_net=F.net_of(leg_pos,r_v)[0]
pl_leg,_=libb.book_position_lag_p(leg_pos.to_frame('p'),r_v.to_frame('r'),n=200,seed=1)
st_leg=F.full_stats(leg_net)
print(f"VIX leg (vt2 slot): SR {st_leg['sr']:.3f} ann {st_leg['ann_geo']*100:.1f}% poslag_p {pl_leg:.3f}")
# drift control: ALWAYS-short vol leg (no timing at all)
pos_always=pd.Series(-1.0,index=vix.index)
ga=F.net_of(-pos_always,r_v)[0]
sa=F.vol_target_scale(ga,vt=0.02,min_days=60,cap=3.0,trailing_shift=1)
posa=-pos_always*sa
neta=F.net_of(posa,r_v)[0]
st_a=F.full_stats(neta)
print(f"ALWAYS-short-vol control (vt2): SR {st_a['sr']:.3f} ann {st_a['ann_geo']*100:.1f}%  <- if ~= leg SR, edge is drift")
