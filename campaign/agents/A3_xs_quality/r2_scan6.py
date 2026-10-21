"""r2: frac sweep + EXT-panel cross-check (charter idea 6, robustness only)."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
from r2lib import *
from engine import load_rets
import pandas as pd, numpy as np

ff = D.ff_factors()
mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
px, rets = load_rets()
MES = [d for d in month_ends(rets) if d in px.index]
def band_gate(win, band, pxidx):
    ma = mkt.rolling(win, min_periods=win).mean()
    g = pd.Series(np.where(mkt > ma*(1+band), 1.0, np.where(mkt < ma*(1-band), 0.0, np.nan)), index=mkt.index)
    return g.reindex(pxidx).ffill().fillna(0.0)

sig121 = px.shift(21)/px.shift(252) - 1.0
G = band_gate(200, 0.03, px.index)

def gated_lo(scores, gser, frac):
    idx = rets.index; W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    for t in [d for d in MES if d in scores.index]:
        row = scores.loc[t].dropna()
        if len(row) < 10: continue
        if gser.loc[t] > 0:
            row = row.sort_values(); nl = max(int(np.floor(len(row)*frac)),1)
            for s in row.index[-nl:]: W.loc[t, s] = 1.0/nl
    return W

def sr_of(W):
    net, w, turn = wbacktest(W, rets)
    nz = w.abs().sum(axis=1); start = nz[nz>0].index[0]
    r = strategy_ret(net, start)
    return r.mean()/r.std()*np.sqrt(252), r

# frac sweep with mini-scramble (50 reps) to see xs-separation
rng = np.random.default_rng(7)
vals = sig121.values.copy(); mask = ~np.isnan(vals); v = vals[mask]
for frac in [0.1, 0.2, 1/3, 0.5]:
    s, _ = sr_of(gated_lo(sig121, G, frac))
    srs = []
    for i in range(50):
        pv = v.copy(); rng.shuffle(pv)
        p2 = np.full_like(vals, np.nan); p2[mask] = pv
        sp = pd.DataFrame(p2, index=sig121.index, columns=sig121.columns)
        s2, _ = sr_of(gated_lo(sp, G, frac))
        srs.append(s2)
    srs = np.array(srs)
    print(f"frac={frac:.2f}: real SR={s:.2f}  scramble mean={srs.mean():.2f} 95th={np.percentile(srs,95):.2f}  xs-edge={s-np.percentile(srs,95):+.2f}")

# ---- EXT panel cross-check (idea 6) ----
pxe = D.closes(extended=True)
rete = pxe.pct_change()
GE = band_gate(200, 0.03, pxe.index)
MESe = [d for d in month_ends(rete) if d in pxe.index]
sige = pxe.shift(21)/pxe.shift(252) - 1.0
# L/S and long-only on EXT, 2020+ window
def lo_ext(scores, gser, frac=1/3):
    idx = rete.index; W = pd.DataFrame(0.0, index=idx, columns=rete.columns)
    for t in [d for d in MESe if d in scores.index and d >= pd.Timestamp("2020-01-01")]:
        row = scores.loc[t].dropna()
        if len(row) < 10: continue
        if gser.loc[t] > 0:
            row = row.sort_values(); nl = max(int(np.floor(len(row)*frac)),1)
            for s in row.index[-nl:]: W.loc[t, s] = 1.0/nl
    return W
def ls_ext(scores, frac=1/3):
    idx = rete.index; W = pd.DataFrame(0.0, index=idx, columns=rete.columns)
    for t in [d for d in MESe if d in scores.index and d >= pd.Timestamp("2020-01-01")]:
        row = scores.loc[t].dropna()
        if len(row) < 10: continue
        row = row.sort_values(); n = len(row)
        nl = max(int(np.floor(n*frac)),1)
        for s in row.index[-nl:]: W.loc[t, s] = 1.0/nl
        for s in row.index[:nl]: W.loc[t, s] -= 1.0/nl
    return W
netE, _, _ = wbacktest(lo_ext(sige, GE), rete)
rE = strategy_ret(netE, pd.Timestamp("2020-01-01"))
srE = rE.mean()/rE.std()*np.sqrt(252)
yrE = rE.groupby(rE.index.year).apply(lambda x:(1+x).prod()-1)
netE2, _, _ = wbacktest(ls_ext(sige), rete)
rE2 = strategy_ret(netE2, pd.Timestamp("2020-01-01"))
srE2 = rE2.mean()/rE2.std()*np.sqrt(252)
print(f"EXT 440-name 2020+ : dualmom LO SR={srE:.2f} (yrly: { {int(k): round(v*100,1) for k,v in yrE.items()} })")
print(f"EXT 440-name 2020+ : 12-1 L/S  SR={srE2:.2f}")
