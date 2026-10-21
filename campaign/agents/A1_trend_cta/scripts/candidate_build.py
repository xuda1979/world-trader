"""r7 candidate: A1_macro793 — new-FRED multi-engine book (jpy trend, bond trend, slope,
winter energy: wti+propane). Honest funding, T+1, 6bps, member vt10 cap1, book vt8 cap2."""
import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import numpy as np, pandas as pd
exec(open("r7_charter.py").read().split("# ================= IDEA 1")[0])
jpy = load(f"{NEW}/DEXJPUS.csv")
prop = load(f"{NEW}/DPROPANEMBTX.csv")
ex_jpy = (jpy.pct_change() - rf_on(jpy.index))
ex_tr10b = ex_tr10.reindex(tr10.index)
ex_slope = (r_tr10 - r_tr2*(7.5/1.75)).reindex(slope.index)

def leg(px_or_base, ex, L, tgt=0.10, cap=1.0, seasonal=False, months=(11,12,1,2)):
    base = px_or_base
    if seasonal:
        m = base.index.month
        sig = pd.Series(0.0, index=base.index); sig[np.isin(m, months)] = 1.0
    else:
        sig = pd.Series(np.sign(base.diff(L)).fillna(0.0), index=base.index)
    pos = sig.shift(1).fillna(0)
    v = ex.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    size = (pos*(tgt/v)).clip(-cap, cap).fillna(0)
    return size*ex - size.diff().abs().fillna(0)*COST, size

def assemble(members, tgt=0.08, cap=2.0, win=W08):
    tot = None; sizes = {}
    for nm, args in members.items():
        c, sz = leg(*args[:2], *args[2:])
        tot = c if tot is None else tot + c.reindex(tot.index).fillna(0)
        sizes[nm] = sz
    net = rf_on(tot.index) + tot
    v = net.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    net = net*(tgt/v).clip(0, cap)
    net = net.dropna(); net = net[net.index >= win]
    return net, sizes

MEM = {
 "jpy252":  (jpy, ex_jpy, 252),
 "tr10_315":(tr10, ex_tr10b, 315),
 "slope252":(slope, ex_slope, 252),
 "wti_win": (wti, ex_wti, None, 0.10, 1.0, True),
 "prop_win":(prop, prop.pct_change().clip(-0.25,0.25)-rf_on(prop.index), None, 0.10, 1.0, True),
}
net, sizes = assemble(MEM)
show("A1_macro793 v1", stats(net, W08))
for drop in ["slope252","wti_win","prop_win","tr10_315","jpy252"]:
    m2 = {k:v for k,v in MEM.items() if k!=drop}
    n2,_ = assemble(m2); show(f"  drop {drop}", stats(n2, W08))
# weight variants (jpy heavier - strongest member)
for wj in [2.0]:
    MEM2 = dict(MEM); MEM2["jpy252"] = (jpy, ex_jpy*0+wj*0+ex_jpy, 252)
# book target variants
for tgt in [0.07, 0.09, 0.10]:
    n2,_ = assemble(MEM, tgt=tgt); show(f"  btgt={tgt}", stats(n2, W08))
