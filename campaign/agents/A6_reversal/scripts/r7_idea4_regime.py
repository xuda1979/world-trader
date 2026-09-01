"""Idea 4 (charter): gated resid-mom + FRED VIX/DXY regime filter, @vt15/18.
Regimes tested (trailing only): VIX level bands (contango VIX>VIX63MA = risk-off veto),
DXY 63d trend veto, VIX percentile. rm leg from r4 cache (gated resid-mom, T+1, 6bps)."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
import r7_lib as L, r4_lib as R4, r3_lib as R3

raw, Wg = R4.rm_leg()
vix = L.fold("vix"); dxy = L.fold("dxy")

def regime_filter(extra_veto, name):
    W = Wg.copy()
    W = W.where(extra_veto.reindex(W.index).ffill() > 0, 0.0)  # veto -> flat
    rets, _ = R3.rets_px()
    gross = (W.shift(1) * rets).sum(axis=1)[L.START:]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)[L.START:].fillna(0.0)
    net = (gross - turn * 6 / 1e4).dropna()
    for vt in [0.15, 0.18]:
        sd = net.expanding(60).std().shift(1)
        lev = (vt / np.sqrt(252) / sd).clip(0, 5).fillna(0.0)
        rep = L.report(net * lev, f"{name} vt{int(vt*100)}")
    return net, W

print("=== IDEA 4: resid-mom + macro regime vetoes ===")
L.report(raw, "BASE rm leg (no veto) vt raw->15")
cal = raw.index
vx = vix.reindex(cal).ffill()
dx = dxy.reindex(cal).ffill()
vetoes = {
    "veto VIX>28": (vx > 28).astype(float),
    "veto VIX>VIX63MA": (vx > vx.rolling(63).mean()).astype(float),
    "veto VIX 63d-pct>0.7": (vx.rolling(63).rank(pct=True) > 0.7).astype(float),
    "veto DXY<DXY63MA": (dx < dx.rolling(63).mean()).astype(float),
    "veto (VIX>MA)|(DXY<MA)": ((vx > vx.rolling(63).mean()) | (dx < dx.rolling(63).mean())).astype(float),
}
for nm, v in vetoes.items():
    net, W = regime_filter(v, nm)
