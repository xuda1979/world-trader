"""r6 Idea 4 — DISPERSION REGIME retiming of QA_dualmom_band121:
xs dispersion = trailing 21d mean of cross-sectional std of daily panel returns.
Rule: carry dualmom weights only when dispersion > trailing 252d median (risk on);
else flat. Base sleeve: W dualmom (12-1 top tercile, MA200 3% band gate).
Charter pass-as-new bar: corr(retimed, old) < 0.7 AND SR improves >= 0.1 (vs 0.89)."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader"); sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from r6lib import *

WIN,BAND,FRAC=200,0.03,1/3
sig=px.shift(21)/px.shift(252)-1.0
g=ma_gate(WIN,BAND)
W2=pd.DataFrame(0.0,index=IDX,columns=NAMES)
for t in MES:
    if g.loc[t]<=0: continue
    row=sig.loc[t].dropna()
    if len(row)<10: continue
    row=row.sort_values(); nl=max(int(np.floor(len(row)*FRAC)),1)
    for s in row.index[-nl:]: W2.loc[t,s]=1.0/nl

# baseline repro
net0,_=wback_rb(W2,RETS,MES)
nz=W2.abs().sum(axis=1); start=nz[nz>0].index[0]
r0=sret(net0,start,0.10); g0=gates6(r0)
print("baseline:",{k:g0[k] for k in['SR','H1','H2','negYr','worst']},flush=True)

xsstd=RETS.std(axis=1)
disp=xsstd.rolling(21,min_periods=15).mean()
disp_med=disp.rolling(252,min_periods=126).median().shift(1)

def retime(thr_mode,q,inv=False,win=252):
    if thr_mode=="median":
        thr=disp.rolling(win,min_periods=win//2).median().shift(1)
        on=disp>thr if not inv else disp<thr
    else:  # quantile expanding
        thr=disp.expanding(min_periods=252).quantile(q).shift(1)
        on=disp>thr if not inv else disp<thr
    on=on.fillna(False)
    Wd=W2.copy()
    Wd[~on.reindex(IDX).fillna(False).values]=0.0
    return Wd

for mode,q,inv in [("median",None,False),("median",None,True),("q75",0.75,False),("q60",0.60,False),("q90",0.90,False)]:
    Wd=retime(mode,q,inv)
    net,_=wback_rb(Wd,RETS,MES)
    r=sret(net,start,0.10)
    gg=gates6(r); gg["corr_champ"]=xcorr(r,CH); gg["corr_old"]=xcorr(r,OLD)
    days_on=int((Wd.abs().sum(axis=1)>0).sum())
    print(f"disp {mode}{' inv' if inv else ''} on={days_on}",{k:gg[k] for k in['SR','H1','H2','negYr','worst','corr_champ','corr_old']},flush=True)
