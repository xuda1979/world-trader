import sys, os
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/scripts")
import importlib.util
spec=importlib.util.spec_from_file_location("fx5b", f"{ROOT}/campaign/scripts/HUNT_FXCARRY2_round5.py")
fx5=importlib.util.module_from_spec(spec); spec.loader.exec_module(fx5)
from bt import metrics as M

px=fx5.load_frankfurter(); rates=fx5.load_rates()
R_spot=fx5.returns_from_px(px)
W=fx5.trend_book_weights(px, lb=63, mode="LS")
net,We,sig,r_pu=fx5.net_of(W,R_spot)
net_t=fx5.trim_warmup(net,sig)
idx=net_t.index
r_pu_i=r_pu.reindex(idx).fillna(0.0); sig_i=sig.reindex(idx).fillna(0.0)
r_eff=pd.Series(np.asarray(sig_i,float)*r_pu_i.values, index=idx)
print("n idx",len(idx),"n net_t",len(net_t))
both=pd.concat([r_eff,net_t],axis=1)
both.columns=["r_eff","net"]
d=(both.r_eff-both.net).abs()
print("max|r_eff-net| =",d.max(),"  n differing >1e-12:",int((d>1e-12).sum()))
worst=d.idxmax()
print("worst day",worst,"r_eff",both.loc[worst,'r_eff'],"net",both.loc[worst,'net'])
# is it NaN-related? count NaN in raw net within idx
print("NaN net in idx:",int(net_t.isna().sum())," NaN r_pu raw in idx:",int(r_pu.reindex(idx).isna().sum()))
print("sharpe r_eff:",M.sharpe_d(r_eff)," sharpe net_t:",M.sharpe_d(net_t))
print("sharpe net_t dropna:",M.sharpe_d(net_t.dropna()))
# halves/neg on r_eff vs net_t
h=M.half_split(r_eff); print("halves r_eff",h," json gates -0.3120/-1.1046")
neg=M.neg_years(r_eff); print("neg r_eff",neg)
negn=M.neg_years(net_t.dropna()); print("neg net dropna",negn)
