"""A5 r6 idea2 (charter): VIX-level term premium — vix vs its own 252d mean as slow
gate on SPX, 2000+ (spliced FRED spy_early + twelve_big SPY). Decorrelation vs the
saved vix3m-contango champion is the key question. T+1, 6bps, vt10, gates r6."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import data as D
from a5_r6_lib import build_net, gates_r6, corr_table, spy_returns_2000

vix = D.fred("vix")
R, seam = spy_returns_2000()
idx = vix.index.intersection(R.dropna().index)
V = vix.reindex(idx).ffill()
Rr = R.reindex(idx)
r2000 = Rr[Rr.index >= "2000-01-01"]
V2000 = V[V.index >= "2000-01-01"]

rows = []
for ma in (126, 252, 504):
    for mode in ("below", "above"):      # below-mean = calm regime long; above = event-driven
        g = (V2000 < V2000.rolling(ma).mean()) if mode == "below" else (V2000 > V2000.rolling(ma).mean())
        sig = g.astype(float)
        net, posf = build_net(sig, r2000, vt=0.10)
        ok, line = gates_r6(f"vixlvl ma{ma} {mode}", net, posf, r2000)
        print(line)
        rows.append((sig, net, posf, ok, line, f"ma{ma}_{mode}"))

# best-by-SR cell: decorrelation check vs saved champion (vt10 twin)
best = max(rows, key=lambda x: x[3] and x[1].std() > 0 and (x[1].mean()/x[1].std()) or -9)
sig, net, posf, ok, line, tag = max(rows, key=lambda x: x[1].mean()/max(x[1].std(),1e-9))
print("\nDECORRELATION for best cell", tag)
champ = pd.read_csv("campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
                    index_col=0, parse_dates=True).iloc[:,0]
j = pd.concat([net, champ], axis=1, join="inner").dropna()
print("corr(vix-level gate, saved champion) =", round(j.corr().iloc[0,1], 3), " n_overlap =", len(j))
ct = corr_table(net)
print("lib corr:", ct)
