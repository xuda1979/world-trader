"""Idea 4b: full workup of rm + VIX>thr veto. Plateau thr 22..36, scramble, corr daily, margins."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
import r7_lib as L, r4_lib as R4, r3_lib as R3

raw, Wg = R4.rm_leg()
vix = L.fold("vix")
cal = raw.index
vx = vix.reindex(cal).ffill()
rets, _ = R3.rets_px()

def eval_thr(thr, vt=0.15):
    W = Wg.where((vx > thr).astype(float).reindex(Wg.index).ffill() > 0, 0.0)
    gross = (W.shift(1) * rets).sum(axis=1)[L.START:]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)[L.START:].fillna(0.0)
    net = (gross - turn * 6 / 1e4).dropna()
    sd = net.expanding(60).std().shift(1)
    lev = (vt / np.sqrt(252) / sd).clip(0, 5).fillna(0.0)
    return net * lev, W

print("=== plateau: VIX threshold x VT ===")
SRs = {}
for thr in [22, 25, 28, 31, 34]:
    for vt in [0.12, 0.15, 0.18]:
        r, _ = eval_thr(thr, vt)
        SRs[(thr, vt)] = r
        s = r.mean()/r.std()*np.sqrt(252)
        print(f"thr{thr} vt{int(vt*100)}: SR={s:.2f}")
peak = max(r.mean()/r.std()*np.sqrt(252) for r in SRs.values())
chosen = SRs[(28, 0.15)]
chsr = chosen.mean()/chosen.std()*np.sqrt(252)
neigh = [(25,0.12),(25,0.15),(25,0.18),(31,0.12),(31,0.15),(31,0.18),(22,0.15),(34,0.15)]
nmin = min(SRs[p].mean()/SRs[p].std()*np.sqrt(252) for p in neigh)
print(f"chosen(28,15): {chsr:.2f} peak={peak:.2f} neigh-min={nmin:.2f} 0.8*peak={0.8*peak:.2f} plateau_ok={nmin>=0.8*peak}")
# scramble on chosen
r, W = eval_thr(28, 0.15)
Wr = W.reindex(rets.index).fillna(0.0)
p = R6p = __import__("r6_lib").scramble_p(chsr, Wr, rets, start=L.START, vt_lvl=0.15)
print(f"scramble p={p:.3f}")
# daily corr disclosure
c6m, c5m = L.report(r, "CHOSEN rm+VIX>28 vt15")["c6"], L.report(r, "dup")["c6"]
champ6 = L.R6.champion6()
cd = r.corr(champ6)
print(f"corrDAILY to champion6 = {cd:+.2f}")
# margins: how many days vetoed
print(f"vetoed-day fraction (VIX>28): {(vx>28).mean():.2f}")
