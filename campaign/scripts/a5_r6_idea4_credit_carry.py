"""A5 r6 idea4 (charter): credit carry on BAA-AAA spread. DV01-neutral synth:
credit excess ret = -dur*ds + s/252 (rate risk hedged by construction).
Signals: long when spread wide vs trailing stats, entry bands + hysteresis.
A1 found SR 0.53 (z250). Gates r6 + corr<0.35 (library has Credit_z250_1986
= near-duplicate risk). T+1, 6bps, vt10. Windows: 1986+ and 2000+."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import data as D
from a5_r6_lib import build_net, gates_r6, corr_table

baa, aaa = D.fred("baa"), D.fred("aaa")
S = (baa - aaa).dropna()                       # spread in pct
ds = S.diff() / 100.0
DUR = 7.5
RX = DUR * (-ds) + S / 100.0 / 252.0           # credit excess return, DV01-neutral

def run(tag, sig, win):
    R = RX[RX.index >= win]
    sig = sig.reindex(R.index)
    net, posf = build_net(sig, R, vt=0.10)
    return sig, net, posf

def z_of(s, lb): return (s - s.rolling(lb).mean()) / s.rolling(lb).std()

rows = []
for win in ("1986-01-01", "2000-01-01"):
    for lb in (126, 252, 504):
        z = z_of(S, lb)
        variants = {
            "always_long":  pd.Series(1.0, index=S.index),
            "z01_band":     pd.Series(np.where(z > 0.1, 1.0, np.where(z < -0.1, -1.0, np.nan)), index=S.index).ffill().fillna(0.0),
            "z03_band":     pd.Series(np.where(z > 0.3, 1.0, np.where(z < -0.3, -1.0, np.nan)), index=S.index).ffill().fillna(0.0),
            "z03_longflat": pd.Series(np.where(z > 0.3, 1.0, 0.0), index=S.index),
            "wide_long":    (S > S.rolling(lb).mean()).astype(float),
            "wide2_long":   (S > S.rolling(lb).mean() + 0.5*S.rolling(lb).std()).astype(float),
            "cont_clip":    pd.Series(np.clip(z/1.0, -1, 1), index=S.index),
        }
        for name, sig in variants.items():
            sg, net, posf = run(f"{win}_{lb}_{name}", sig, win)
            ok, line = gates_r6(f"credit {win[:4]} lb{lb} {name}", net, posf, RX.reindex(net.index))
            rows.append((win, lb, name, net, posf, ok, line))
            print(line)

# best per window by SR; decorrelation check
for win in ("1986-01-01", "2000-01-01"):
    sub = [r for r in rows if r[0] == win]
    best = max(sub, key=lambda r: r[3].mean()/max(r[3].std(),1e-9))
    print(f"\n== {win} best: {best[2]} lb{best[1]} ==")
    ct = corr_table(best[3])
    print("lib corr:", ct)
    cr = pd.read_csv(f"{D.SLEEVE_LIB}/Credit_z250_1986.csv", index_col=0, parse_dates=True).iloc[:,0]
    j = pd.concat([best[3], cr], axis=1, join="inner").dropna()
    print("corr to Credit_z250_1986:", round(j.corr().iloc[0,1],3), "n=", len(j))
