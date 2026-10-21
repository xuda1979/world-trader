"""r2: validation of dualmom_band — scramble, plateau grid, library corr, EXT check."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
from r2lib import *
from engine import load_rets
import pandas as pd, numpy as np, glob, os

px, rets = load_rets()
MES = [d for d in month_ends(rets) if d in px.index]
ff = D.ff_factors()
mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()

def band_gate(win, band):
    ma = mkt.rolling(win, min_periods=win).mean()
    g = pd.Series(np.where(mkt > ma*(1+band), 1.0, np.where(mkt < ma*(1-band), 0.0, np.nan)), index=mkt.index)
    return g.reindex(px.index).ffill().fillna(0.0)

sig121 = px.shift(21)/px.shift(252) - 1.0

def gated_lo(scores, gser, frac=1/3):
    idx = rets.index; W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    for t in [d for d in MES if d in scores.index]:
        row = scores.loc[t].dropna()
        if len(row) < 10: continue
        if gser.loc[t] > 0:
            row = row.sort_values(); nl = max(int(np.floor(len(row)*frac)),1)
            for s in row.index[-nl:]: W.loc[t, s] = 1.0/nl
    return W

def sr_of(W, start=None):
    net, w, turn = wbacktest(W, rets)
    if start is None:
        nz = w.abs().sum(axis=1); start = nz[nz>0].index[0]
    r = strategy_ret(net, start)
    return r.mean()/r.std()*np.sqrt(252), r, net

# ---- plateau grid: MA win x band ----
grid = {}
for win in [150, 175, 200, 225, 250]:
    for band in [0.01, 0.02, 0.03, 0.04, 0.05]:
        s, _, _ = sr_of(gated_lo(sig121, band_gate(win, band)))
        grid[(win, band)] = round(s, 3)
print("PLATEAU GRID (rows=MA win, cols=band):")
bands = [0.01,0.02,0.03,0.04,0.05]
print("      " + "  ".join(f"b={b}" for b in bands))
for win in [150,175,200,225,250]:
    print(f"{win}  " + "  ".join(f"{grid[(win,b)]:+.2f}" for b in bands))
peak = max(grid.values())
near = {k: v for k, v in grid.items() if v >= 0.8*peak}
print(f"peak={peak:.2f}; cells within 20% of peak: {sorted(near.keys())} ({len(near)}/25)")

# ---- chosen: (200, 0.03) ----
G = band_gate(200, 0.03)
W = gated_lo(sig121, G)
sr, r, net = sr_of(W)
print(f"chosen SR={sr:.3f}, n_days={len(r)}")

# ---- scramble: permute xs signal, keep gate, 200 reps ----
rng = np.random.default_rng(42)
vals = sig121.values.copy(); mask = ~np.isnan(vals)
v = vals[mask]
srs = []
for i in range(200):
    pv = v.copy(); rng.shuffle(pv)
    p2 = np.full_like(vals, np.nan); p2[mask] = pv
    sp = pd.DataFrame(p2, index=sig121.index, columns=sig121.columns)
    s, _, _ = sr_of(gated_lo(sp, G))
    srs.append(s)
srs = np.array(srs)
pval = (srs < sr).mean()
print(f"scramble: real={sr:.3f} 95th pct={np.percentile(srs,95):.3f} mean={srs.mean():.3f} p={pval:.3f}")

# ---- library correlation ----
libdir = "/Users/daxu/software/world-trader/campaign/results/sleeve_library"
rows = []
for f in sorted(glob.glob(libdir + "/*.csv")):
    try:
        s2 = pd.read_csv(f, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
        df = pd.concat([r.rename("a"), s2.rename("b")], axis=1).dropna()
        if len(df) > 250:
            rows.append((os.path.basename(f)[:-4], round(df["a"].corr(df["b"]), 3)))
    except Exception: pass
rows.sort(key=lambda x: abs(x[1]), reverse=True)
print("TOP |corr| to library:", rows[:8])
print(f"mean |corr| over {len(rows)} library sleeves: {np.mean([abs(c) for _, c in rows]):.3f}")
import pickle
pickle.dump(dict(grid=grid, pval=float(pval), srs95=float(np.percentile(srs,95)), sr=float(sr),
                 corr=rows), open("/tmp/r2_final.pkl","wb"))
