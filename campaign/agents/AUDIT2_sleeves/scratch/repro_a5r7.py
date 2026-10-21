import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,"/Users/daxu/software/world-trader")
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from a5_r7_lib import fred_new, hysteresis_pos, build_net
ROOT="/Users/daxu/software/world-trader"
aaa=fred_new("DAAA"); baa=fred_new("DBAA"); y10=fred_new("DGS10")
for s in (aaa,baa,y10): s.index=s.index.tz_localize(None)
cr=pd.concat([aaa.rename("a"),baa.rename("b"),y10.rename("y")],axis=1,join="inner").ffill()
spr=(cr.b-cr.a)/100.0
ya=cr.a/100.0; yu=cr.y/100.0
TR_AA=(7.0*(-ya.diff())+ya/252.0).dropna()
TR_UST=(7.5*(-yu.diff())+yu/252.0).reindex(TR_AA.index).fillna(0.0)
TR_SPR=(7.0*(-spr.diff())+spr/252.0).reindex(TR_AA.index).fillna(0.0)
dy=yu.diff(21)
lb,th,c,lb_z,w=252,0.5,0.75,504,(0.1,0.6,0.3)
p=hysteresis_pos(((spr-spr.rolling(lb).mean())/spr.rolling(lb).std()).reindex(TR_AA.index).ffill(),th,0.25)
zy=((dy-dy.rolling(lb_z).mean())/dy.rolling(lb_z).std()).reindex(TR_AA.index).ffill()
hedge=(zy>c).astype(float).shift(1).fillna(0.0)
R=w[0]*TR_AA+w[1]*TR_SPR+w[2]*(TR_AA-hedge*TR_UST)
net,posf=build_net(p,R)
old=pd.read_csv(f"{ROOT}/campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",index_col=0,parse_dates=True).iloc[:,0].astype(float)
j=pd.concat([old.rename("old"),net.rename("new")],axis=1,join="inner").dropna()
md=float((j.old-j.new).abs().max())
print(f"A5r7: n={len(j)}/{len(old)} corr={j.old.corr(j.new):.6f} maxdiff={md:.3e} -> {'IDENTICAL' if md<1e-12 else 'DIFF'}")
sr=net.mean()/net.std()*np.sqrt(252)
print(f"  A5r7 SR={sr:.2f} ann={net.mean()*252*100:.1f}% (meta claims 1.51 / 4.8%)")
