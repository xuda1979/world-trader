"""r2 final honesty: full-signal scramble decomposition + 'gate-only EW' null."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
from r2lib import *
from engine import load_rets
import pandas as pd, numpy as np

ff = D.ff_factors()
mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
px, rets = load_rets()
MES = [d for d in month_ends(rets) if d in px.index]
sig = px.shift(21)/px.shift(252) - 1.0
ma = mkt.rolling(200, min_periods=200).mean()
g0 = pd.Series(np.where(mkt > ma*1.03, 1.0, np.where(mkt < ma*0.97, 0.0, np.nan)), index=mkt.index)
G = g0.reindex(px.index).ffill().fillna(0.0)
IDX = rets.index

def build_W(scores, gate, frac=1/3):
    W = pd.DataFrame(0.0, index=IDX, columns=rets.columns)
    for t in MES:
        if t not in scores.index or gate.loc[t] <= 0: continue
        row = scores.loc[t].dropna()
        if len(row) < 10: continue
        row = row.sort_values(); nl = max(int(np.floor(len(row)*frac)),1)
        for s in row.index[-nl:]: W.loc[t, s] = 1.0/nl
    return W

def sr_of_W(W):
    net, w, turn = wbacktest(W, rets)
    nz = w.abs().sum(axis=1); start = nz[nz>0].index[0]
    r = strategy_ret(net, start)
    return r.mean()/r.std()*np.sqrt(252), r

def shift_gate(gser, shift):
    return pd.Series(np.roll(gser.values, shift), index=gser.index)

SR_REAL, R_REAL = sr_of_W(build_W(sig, G))
print(f"REAL SR = {SR_REAL:.3f}")

# A: xs permuted, gate intact
# B: gate shifted (63..2520d), xs intact
# C: both destroyed
vals = sig.values.copy(); mask = ~np.isnan(vals); v = vals[mask]
def run_scramble(mode, n=200, seed=42):
    rng = np.random.default_rng(seed)
    srs = []
    for _ in range(n):
        gs = G
        sc = sig
        if mode in ("xs","both"):
            pv = v.copy(); rng.shuffle(pv)
            p2 = np.full_like(vals, np.nan); p2[mask] = pv
            sc = pd.DataFrame(p2, index=sig.index, columns=sig.columns)
        if mode in ("gate","both"):
            gs = shift_gate(G, int(rng.integers(63, 2520)))
        s, _ = sr_of_W(build_W(sc, gs))
        srs.append(s)
    return np.array(srs)

for mode in ["xs", "gate", "both"]:
    srs = run_scramble(mode)
    p = (srs < SR_REAL).mean()
    print(f"scramble {mode:5s}: mean={srs.mean():.3f} 95th={np.percentile(srs,95):.3f} p={p:.3f} -> {'PASS' if p>0.95 else 'FAIL'}")

# NULL: buy ENTIRE universe EW when gate on (no xs at all)
Wnull = pd.DataFrame(0.0, index=IDX, columns=rets.columns)
for t in MES:
    if G.loc[t] <= 0: continue
    row = sig.loc[t].dropna()          # just tradability universe
    for s in row.index: Wnull.loc[t, s] = 1.0/len(row)
sr_null, r_null = sr_of_W(Wnull)
yr = r_null.groupby(r_null.index.year).apply(lambda x:(1+x).prod()-1)
print(f"NULL gate-only EW-all: SR={sr_null:.2f} negYr={(yr<0).sum()} worst={yr.min()*100:.1f}%")
# NULL 2: SPX itself vol-targeted (beta benchmark)
spx_r = mkt.reindex(R_REAL.index).pct_change()
vt = vol_target(spx_r[R_REAL.index[0]:])
print(f"beta SPX vt10%: SR={vt.mean()/vt.std()*np.sqrt(252):.2f}")
