import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,"/Users/daxu/software/world-trader")
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
def cmp(name, r, path):
    old = pd.read_csv(f"{ROOT}/{path}", index_col=0, parse_dates=True).iloc[:,0].astype(float)
    old = old[~old.index.duplicated()]
    j = pd.concat([old.rename("old"), r.rename("new")], axis=1, join="inner").dropna()
    md = float((j.old-j.new).abs().max()); corr=float(j.old.corr(j.new))
    idt = "IDENTICAL" if md<1e-12 else ("FLOAT-NOISE" if md<1e-9 else "DIFF")
    print(f"{name}: n={len(j)}/{len(old)} corr={corr:.6f} maxdiff={md:.3e} -> {idt}")

# ============ QAxasts (replicated from QA_xasts_tsmom189.py, no save) ============
from r6lib import wback_rb, sret
from r7_idea5_breadth import panel, RET_PAN
MAW=189
R5=RET_PAN.drop(columns=["CASH"])
sgn=np.sign(panel-panel.rolling(MAW,min_periods=MAW//2).mean()).fillna(0)*0.2
Wt=sgn
rbd=[d for d in panel.index if d.weekday()==2]
net,_=wback_rb(Wt,R5,rbd)
from engine import vol_target as vt_eng
r=vt_eng(net[net.index>="2008-01-01"],target=0.10).iloc[5:].dropna()
cmp("QAxasts", r, "campaign/agents/A3_xs_quality/sleeves/QA_xasts_tsmom189.csv")

# ============ dualmom (replicated from QA_dualmom_band121.py, no save) ============
from campaign.harness import data as D
from engine import month_ends, strategy_ret, COST
px = D.closes()
rets = px.pct_change()
MES = [d for d in month_ends(rets) if d in px.index]
WIN, BAND, FRAC = 200, 0.03, 1/3
sig = px.shift(21) / px.shift(252) - 1.0
ff = D.ff_factors()
mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
ma = mkt.rolling(WIN, min_periods=WIN).mean()
g = pd.Series(np.where(mkt > ma*(1+BAND),1.0,np.where(mkt < ma*(1-BAND),0.0,np.nan)), index=mkt.index)
g = g.reindex(px.index).ffill().fillna(0.0)
W = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
for t in MES:
    if t not in sig.index or g.loc[t] <= 0: continue
    row = sig.loc[t].dropna()
    if len(row) < 10: continue
    row = row.sort_values()
    nl = max(int(np.floor(len(row)*FRAC)),1)
    for s in row.index[-nl:]: W.loc[t,s] = 1.0/nl
idx = rets.index
w = pd.DataFrame(0.0, index=idx, columns=rets.columns)
prev = pd.Series(0.0, index=rets.columns); turn = pd.Series(0.0, index=idx)
pos_of = {d: idx.get_loc(d) for d in mes} if (mes:=[d for d in MES]) else {}
for i, t in enumerate(mes):
    neww = W.loc[t]; p = pos_of[t]
    if p+1 < len(idx):
        turn.iloc[p+1] = 0.5*(neww-prev).abs().sum()
        nxt_p = pos_of[mes[i+1]]+1 if i+1 < len(mes) else len(idx)
        w.iloc[p+1:nxt_p] = neww.values
        prev = neww
net2 = (w*rets.fillna(0.0)).sum(axis=1) - turn*COST/1e4
nz = w.abs().sum(axis=1)
start = nz[nz>0].index[0]
r2 = strategy_ret(net2, start)
cmp("dualmom", r2, "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv")
print("DONE repro part2")
