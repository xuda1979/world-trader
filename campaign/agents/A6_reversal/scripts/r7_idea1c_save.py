"""Idea 1c: formal plateau + scramble for 2y LF trend. Chosen: k378 cad42 VT12."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
import r7_lib as L

DUR2 = 1.9
def tr2y():
    y = L.fnew("DGS2") / 100.0
    return (-DUR2 * y.diff() + y / 252.0).dropna()

def build(k, cad):
    tr = tr2y()
    sig = (tr.rolling(k).mean() > 0).astype(float)
    W = L.freeze(pd.DataFrame({"d2": sig}), cad)
    return W, pd.DataFrame({"d2": tr})

if __name__ == "__main__":
    print("=== plateau grid k x cad (SR, net VT12) ===")
    SRs = {}
    for k in [252, 315, 378, 441]:
        for cad in [21, 42, 63]:
            W, rets = build(k, cad)
            r, _ = L.from_W(W, rets, vt=0.12)
            SRs[(k, cad)] = r
            print(f"k{k} cad{cad}: SR={r.mean()/r.std()*np.sqrt(252):.2f}")
    peak = max(SRs.values(), key=lambda r: r.mean()/r.std())
    pk = max(r.mean()/r.std()*np.sqrt(252) for r in SRs.values())
    ch = (378, 42)
    neigh = [(315,21),(315,42),(315,63),(378,21),(378,63),(441,21),(441,42),(441,63)]
    nmins = [SRs[p].mean()/SRs[p].std()*np.sqrt(252) for p in neigh]
    print(f"\nchosen {ch} SR={SRs[ch].mean()/SRs[ch].std()*np.sqrt(252):.2f} | peak={pk:.2f} | "
          f"neighbor-min={min(nmins):.2f} | 0.8*peak={0.8*pk:.2f} | "
          f"plateau_ok={min(nmins) >= 0.8*pk}")
    # scramble (200x, costs+VT repriced)
    W, rets = build(*ch)
    r = SRs[ch]
    p = L.scramble(r, W, rets, vt=0.12)
    print(f"scramble p={p:.3f}")
    # cap-10 disclosure variant (same config, higher leverage ceiling)
    r10, _ = L.from_W(W, rets, vt=0.12, cap=10.0)
    s = r10.mean()/r10.std()*np.sqrt(252)
    print(f"disclosure cap10: SR={s:.2f} ann={r10.mean()*252*100:.1f}% vol={r10.std()*np.sqrt(252)*100:.1f}%")
    # persistence: fraction of days long, avg holding of the flat/long states
    W0, _ = build(*ch)
    frac = W0["d2"].mean()
    switches = (W0["d2"].diff().abs() > 0).sum()
    print(f"days-long fraction={frac:.2f}, switches over {(W0.index[-1]-W0.index[0]).days/365:.1f}y = {switches} (~{switches/((W0.index[-1]-W0.index[0]).days/365):.1f}/yr)")
