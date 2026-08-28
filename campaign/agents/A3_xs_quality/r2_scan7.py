"""r2 final: plateau-cell yearly robustness; EXT vol sanity; chosen-case detail."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
from r2lib import *
from engine import load_rets
import pandas as pd, numpy as np

ff = D.ff_factors()
mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
px, rets = load_rets()
MES = [d for d in month_ends(rets) if d in px.index]
sig121 = px.shift(21)/px.shift(252) - 1.0

def band_gate(win, band):
    ma = mkt.rolling(win, min_periods=win).mean()
    g = pd.Series(np.where(mkt > ma*(1+band), 1.0, np.where(mkt < ma*(1-band), 0.0, np.nan)), index=mkt.index)
    return g.reindex(px.index).ffill().fillna(0.0)

def gated_lo(gser, frac=1/3):
    idx = rets.index; W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    for t in [d for d in MES]:
        row = sig121.loc[t].dropna()
        if len(row) < 10: continue
        if gser.loc[t] > 0:
            row = row.sort_values(); nl = max(int(np.floor(len(row)*frac)),1)
            for s in row.index[-nl:]: W.loc[t, s] = 1.0/nl
    return W

print("yearly-gate check across plateau cells (win, band): negYr / worst% / SR")
npass = 0; ntot = 0
for win in [150, 175, 200, 225, 250]:
    line = []
    for band in [0.01, 0.02, 0.03, 0.04, 0.05]:
        net, w, _ = wbacktest(gated_lo(band_gate(win, band)), rets)
        nz = w.abs().sum(axis=1); start = nz[nz>0].index[0]
        r = strategy_ret(net, start)
        yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
        ny = int((yr<0).sum()); wy = yr.min()*100
        sr = r.mean()/r.std()*np.sqrt(252)
        okd = (ny <= 2) and (yr[yr<0].max() if ny else 0) > -0.05
        npass += okd; ntot += 1
        line.append(f"{ny}n/{wy:+.1f}/{'Y' if okd else 'N'}")
    print(f"{win}: " + "  ".join(line))
print(f"cells passing yearly gate: {npass}/{ntot}")

# chosen (200, 0.03): invested %, conditional beta, yearly
G = band_gate(200, 0.03)
net, w, turn = wbacktest(gated_lo(G), rets)
nz = w.abs().sum(axis=1); start = nz[nz>0].index[0]
r = strategy_ret(net, start)
gross_expo = nz.reindex(r.index)
inv = (gross_expo > 0).mean()
mkt_d = mkt.reindex(r.index).pct_change()
both = r.notna() & mkt_d.notna() & (gross_expo > 0)
cond_beta = np.cov(r[both], mkt_d[both])[0,1] / np.var(mkt_d[both])
cond_corr = np.corrcoef(r[both], mkt_d[both])[0,1]
print(f"chosen: invested_days={inv*100:.0f}%  cond_beta={cond_beta:.2f}  cond_corr={cond_corr:.2f}  ann_turnover={turn.mean()*252*100:.0f}%")
print("yearly:", {int(k): round(v*100,1) for k, v in r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1).items()})

# EXT realized vol sanity
pxe = D.closes(extended=True); rete = pxe.pct_change()
ma = mkt.rolling(200, min_periods=200).mean()
g = pd.Series(np.where(mkt > ma*1.03, 1.0, np.where(mkt < ma*0.97, 0.0, np.nan)), index=mkt.index)
GE = g.reindex(pxe.index).ffill().fillna(0.0)
MESe = [d for d in month_ends(rete) if d in pxe.index]
sige = pxe.shift(21)/pxe.shift(252) - 1.0
idx = rete.index; W = pd.DataFrame(0.0, index=idx, columns=rete.columns)
for t in [d for d in MESe if d >= pd.Timestamp("2020-01-01")]:
    row = sige.loc[t].dropna()
    if len(row) < 10: continue
    if GE.loc[t] > 0:
        row = row.sort_values(); nl = max(int(np.floor(len(row)/3)),1)
        for s in row.index[-nl:]: W.loc[t, s] = 1.0/nl
netE, wE, _ = wbacktest(W, rete)
rE = strategy_ret(netE, pd.Timestamp("2020-01-01"))
print(f"EXT: realized ann vol={rE.std()*np.sqrt(252)*100:.0f}%  ann={rE.mean()*252*100:.0f}%  max single-day={rE.max()*100:.1f}%  => data polluted: {rE.std()*np.sqrt(252) > 0.5}")
d1 = rete.diff().abs().max().sort_values(ascending=False)[:3]
print("EXT worst single-day |ret| names:", {k: round(v*100,0) for k, v in d1.items()})
