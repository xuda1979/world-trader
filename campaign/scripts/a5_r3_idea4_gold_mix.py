"""A5 r3 idea4: gold trend (126d) blended with A5 contango champion."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from a5_r3_lib import gates_a_c_d, vt_scale, sr, lib_corr, corr_summary
import data as D

X = D.fred("xau")
r = X.pct_change()
X = pd.DataFrame({"x": X, "r": r}).dropna()
for lb in (63, 126, 252):
    sig = (X["x"] > X["x"].shift(lb)).astype(float)
    pos1 = sig.shift(1).fillna(0.0)
    to = pos1.diff().abs().fillna(pos1.abs())
    net0 = pos1 * X["r"].reindex(sig.index).fillna(0.0) - to * D.COST / 1e4
    sc = vt_scale(net0)
    posf = pos1 * sc
    to2 = posf.diff().abs().fillna(posf.abs())
    gold = (posf * X["r"].reindex(sig.index).fillna(0.0) - to2 * D.COST / 1e4).dropna()
    gates_a_c_d(f"gold trend lb{lb}", gold)
    if lb == 126: gold126 = gold

# rebuild contango champion (same as idea3 script)
V1 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix_daily.csv',
                 parse_dates=['DATE']).set_index('DATE')['vix']
V3 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix3m.csv',
                 parse_dates=['DATE']).set_index('DATE')['vix3m']
TS = pd.concat([V1, V3], axis=1).dropna()
US = D.fred('us10y').reindex(TS.index).ffill()
R1 = D.closes()["SPY"].pct_change(); R1.index = R1.index.tz_localize(None)
R1 = R1.reindex(TS.index).fillna(0.0)
ratio = TS["vix"] / TS["vix3m"]
st = 0.0; base = []
for v in ratio.values:
    if v < 1.02: st = 1.0
    elif v > 1.07: st = 0.0
    base.append(st)
C = pd.Series(base, index=ratio.index)
shock = (US > 2.75) & ((US - US.shift(150)) > 0.25)
RS = (~shock.fillna(False)).astype(float)
P = C * RS
posc = P.shift(1).fillna(0.0)
toc = posc.diff().abs().fillna(posc.abs())
net0 = posc * R1 - toc * D.COST / 1e4
scc = vt_scale(net0, cap=2.0)
posf = posc * scc
to2 = posf.diff().abs().fillna(posf.abs())
contango = (posf * R1 - to2 * D.COST / 1e4).dropna()

both = pd.concat([gold126, contango], axis=1, keys=["g","t"]).dropna()
print("overlap:", both.index[0].date(), "->", both.index[-1].date(), "n=", len(both),
      "corr:", round(both.corr().iloc[0,1],3))

def shift_scramble(w, n=200, seed=2):
    rng = np.random.default_rng(seed)
    a = both["g"].values; b = both["t"].values
    mm0 = pd.Series(w*a + (1-w)*b, index=both.index); mm0 = mm0 * vt_scale(mm0)
    real = sr(mm0.dropna()); cnt = 0
    for _ in range(n):
        k = rng.integers(1, len(a))
        mm = pd.Series(w*np.roll(a,k) + (1-w)*b, index=both.index); mm = mm * vt_scale(mm)
        if sr(mm.dropna()) >= real: cnt += 1
    return real, cnt/n

for w in (0.3, 0.4, 0.5, 0.6):
    m = (w*both["g"] + (1-w)*both["t"]); m = (m * vt_scale(m)).dropna()
    g = gates_a_c_d(f"mix gold w={w}", m)
    if g["ok"]:
        real, p = shift_scramble(w)
        print(f"    shift-scramble real={real:.2f} p={p:.3f}")
        print(corr_summary(lib_corr(m)))
