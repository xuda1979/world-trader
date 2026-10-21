"""CAMP_COST R2 — diescrack_L40Z20 byte-reconstruction + costfix.

Step 1: rebuild the committed CSV with the ORIGINAL (half-turn, 6.0bps) convention and
        byte-compare. Only if that matches do we trust the reconstruction.
Step 2: flip ONLY the cost line to FULL |dpos| @ 6.4bps, report before/after.
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/scratch")
import lib as L  # HUNT_BASIS2 lib (zrev, vol_target)

C = pd.read_csv(f"{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
                index_col=0, parse_dates=True)["ret"].astype(float)


def build(spread_sign=+1, borrow=True, vt=True, cost_bps=6.0, half=True):
    dj = L.fred("DJFUELUSGULF", src=f"{ROOT}/tools/quant/data/newdata")
    wt = L.fred("wti_full")
    a, b = np.log(dj * 42.0), np.log(wt)
    sp = (a - b) * spread_sign
    net, gr, pos, tup = L.zrev(sp, lookback=40, gate=2.0, min_start="2008-01-01",
                               cost_bps=cost_bps)
    if not half:  # costfix: full |dpos| at standard bps, same P&L
        ret = sp.diff().shift(-1)
        gr = (pos * ret).dropna()
        tup_full = pos.diff().abs().reindex(gr.index).fillna(0.0)
        net = gr - tup_full * cost_bps / 1e4
    if borrow:
        net = net - 0.005 / 252 * pos.abs().reindex(net.index).fillna(0.0) * (pos.reindex(net.index).fillna(0.0) != 0)
    if vt:
        net, _ = L.vol_target(net, vt_ann=0.08, min_days=60, cap=3.0)
    return net.dropna()


def dev(a, b):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1, join="inner").dropna()
    return len(j), float((j.a - j.b).abs().max()) if len(j) else float("nan")


if __name__ == "__main__":
    print(f"committed: n={len(C)} first={C.index.min().date()} last={C.index.max().date()} "
          f"sum={C.sum():.8f}")
    for sign in (+1, -1):
        for borrow in (True, False):
            for vt in (True, False):
                try:
                    r = build(spread_sign=sign, borrow=borrow, vt=vt)
                    n, d = dev(r, C)
                    tag = "MATCH" if d < 1e-12 else ""
                    print(f"sign={sign:+d} borrow={borrow} vt={vt}: n_inner={n} maxdev={d:.3e} {tag}")
                except Exception as e:
                    print(f"sign={sign:+d} borrow={borrow} vt={vt}: ERR {type(e).__name__} {e}")
