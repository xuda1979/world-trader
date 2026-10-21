import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
import bt.engine as eng
from bt.metrics import sharpe_d, neg_years, ann_geo, max_dd, half_split
from bt.gates import corr_to
from hunt_r1 import pair_book, load_series, zscore_trailing, hysteresis_state, net_of
from run_hunt import spreads, champ_rets

champ = champ_rets()
d = spreads()['ho_br']

def build(win=63, zi=1.0, zo=1.0):
    net, We, g, rpu = pair_book(d['r_a'], d['r_b'], d['spread'], win=win, z_in=zi,
                                z_out=zo, side='meanrev', return_rpu=True)
    live = (We.fillna(0) != 0).any(axis=1)
    return net[net.index >= live.idxmax()], We, rpu

net, We, rpu = build()
print(f"candidate n={len(net)} {net.index[0].date()}->{net.index[-1].date()}")

print("=== IS/OOS split at 2017-01-01 (champion fitting boundary) ===")
isr = net[net.index < '2017-01-01']; oos = net[net.index >= '2017-01-01']
print(f"IS SR={sharpe_d(isr):.3f} (n={len(isr)}) OOS SR={sharpe_d(oos):.3f} (n={len(oos)})")

print("\n=== cost sensitivity (net SR at higher bps, full |dW|) ===")
W = We[['a', 'b']] if hasattr(We, 'columns') else We
R = pd.concat({'a': d['r_a'], 'b': d['r_b']}, axis=1).reindex(We.index).fillna(0.0)
for bps in (6.4, 10.0, 20.0):
    port = (We * R).sum(axis=1)
    n2 = port - eng.cost_turnover(We, cost_bps=bps) - eng.borrow_cost(We)
    n2 = n2[n2.index >= net.index[0]]
    print(f"  {bps}bps: SR={sharpe_d(n2):.3f}")

print("\n=== MDD windows (champion vs candidate, overlap check) ===")
def dd_window(r):
    eq = (1 + r).cumprod(); dd = eq / eq.cummax() - 1
    t = dd.idxmin(); peak = eq[:t].idxmax()
    return peak, t, dd.min()
for nm, r in (('champion', champ), ('candidate', net)):
    p, t, m = dd_window(r)
    print(f"  {nm}: peak {p.date()} -> trough {t.date()} MDD {m*100:.2f}%")

print("\n=== blend at NATIVE sleeve vol (s = w * net, no relever), w grid ===")
for w in (0.5, 1.0, 1.5):
    s = net.reindex(champ.index).fillna(0.0) * w
    b = champ + s
    dSR = sharpe_d(b) - sharpe_d(champ)
    dAnn = (ann_geo(b) - ann_geo(champ)) * 100
    dMDD = (max_dd(b) - max_dd(champ)) * 100
    neg, worst = neg_years(b)
    h1b, h2b = half_split(b); h1c, h2c = half_split(champ)
    print(f"  w={w}: blendSR={sharpe_d(b):.3f} dSR={dSR:+.3f} dAnn={dAnn:+.2f}pp "
          f"blendMDD={max_dd(b)*100:.2f}% dMDD={dMDD:+.2f}pp neg={neg} dH1={h1b-h1c:+.3f} dH2={h2b-h2c:+.3f}")

print("\n=== span honesty: pre-2008 probe (1987-2008, informational) ===")
import run_hunt
sp_full = run_hunt.spreads(bound='1990-01-01')['ho_br']
net8, We8, _, _ = pair_book(sp_full['r_a'], sp_full['r_b'], sp_full['spread'], win=63,
                         z_in=1.0, z_out=1.0, side='meanrev', return_rpu=True)
live = (We8.fillna(0) != 0).any(axis=1)
net8 = net8[net8.index >= live.idxmax()]
pre = net8[net8.index < '2008-01-01']
print(f"pre-2008 span n={len(pre)} {pre.index[0].date()}->{pre.index[-1].date()} SR={sharpe_d(pre):.3f}")
