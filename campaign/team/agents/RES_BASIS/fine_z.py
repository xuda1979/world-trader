import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import pandas as pd
from bt.gates import plateau_ok
from bt.metrics import sharpe_d, half_split, neg_years, ann_geo, max_dd
from hunt_r1 import pair_book, load_series
from run_hunt import spreads, CHAMP

champ = load_series(CHAMP, 'ret')
d = spreads()['ho_br']

def net_for(win, zi, zo):
    net, We, g, rpu = pair_book(d['r_a'], d['r_b'], d['spread'], win=win, z_in=zi,
                                z_out=zo, side='meanrev', return_rpu=True)
    live = (We.fillna(0) != 0).any(axis=1)
    return net[net.index >= live.idxmax()], We

print("=== fine z_in grid at w63 (zo=1.0) ===")
srs = {}
for zi in (0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0):
    n, _ = net_for(63, zi, 1.0)
    srs[zi] = sharpe_d(n)
print({k: round(v, 3) for k, v in srs.items()})
for pick in (0.75, 1.0, 1.25):
    ok, info = plateau_ok(srs, pick)
    print(f"plateau@{pick}: ok={ok} nb={ {k: round(v,3) for k,v in info['neighbors'].items()} } peak={info['peak']:.3f} thr={info['threshold']:.3f}")

print("\n=== z_in=1.0 zo variants (w63) ===")
for zo in (0.0, 0.5, 1.0):
    n, We = net_for(63, 1.0, zo)
    h1, h2 = half_split(n)
    neg, worst = neg_years(n)
    print(f"zo={zo}: SR={sharpe_d(n):.3f} H1={h1:.2f} H2={h2:.2f} neg={neg} worst={worst*100:.1f}% ann={ann_geo(n)*100:.1f}% MDD={max_dd(n)*100:.1f}%")

print("\n=== w grid at z1.0 zo0.0 ===")
srs2 = {}
for w in (21, 40, 63, 90, 126, 189):
    n, _ = net_for(w, 1.0, 0.0)
    srs2[w] = sharpe_d(n)
print({k: round(v, 3) for k, v in srs2.items()})
ok, info = plateau_ok(srs2, 63)
print(f"plateau@63: ok={ok} nb={ {k: round(v,3) for k,v in info['neighbors'].items()} } peak={info['peak']:.3f}")
