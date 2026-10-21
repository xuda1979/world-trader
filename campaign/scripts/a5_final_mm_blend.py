"""A5 FINAL candidate: implied-vol-managed blend (charter fallback).
Sleeve = SharpeW_lib * (0.7 + 0.3 * m_{t-1}),  m = clip(0.10 / ivol_ann, 0.25, 2.0),
ivol_ann = VIX3M_t/100 (3M implied vol known at t close). T+1 on m.
Expanding-window vol-target to 10% ann (min 60d, trailing only), costs 6bps/side
on every multiplier turnover. Blend weights (w, 1-w) scanned for plateau.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
from a5_common import *
import data as D

V3 = '/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix3m.csv'
BASE = "Multi_Strategy_SharpeW"

def build(w=0.3, vt=0.10, cap=2.0, floor=0.25, volmode="expanding", minlen=60):
    base = load_lib(BASE)                      # net of its own costs
    v3 = pd.read_csv(V3, parse_dates=['DATE']).set_index('DATE')['vix3m']
    v3d = v3.reindex(base.index).ffill()
    m = (vt / (v3d/100.0)).clip(floor, cap)
    m = m.shift(1).fillna(floor)               # T+1
    raw = base * (1-w + w*m)
    to = (1-w + w*m).diff().abs().fillna(0.0)  # turnover of the multiplier overlay
    net = raw - to*D.COST/1e4
    # expanding trailing vol-target to 10% (only past data), cap leverage 2x
    sv = net.expanding(min_periods=minlen).std()
    sc = (vt/np.sqrt(252)/sv).clip(0,2.0).shift(1).fillna(0.0)
    net = net*sc - ((1-w+w*m)*sc).diff().abs().fillna(0.0)*D.COST/1e4
    return net.dropna(), (m*sc).dropna(), base

def full_gates(name, net, pos, base):
    s = stats(net); h1,h2 = halves(net)
    sp = scramble_pval_sig(pos, base*pos/pos.max() if pos.max()>0 else base, n=200)
    ok_a = s['sr']>=0.6; ok_c = h1>=0.3 and h2>=0.3
    ok_d = s['neg_yr']<=2 and s['worst']>-5.0; ok_e = sp<=0.05
    ok = ok_a and ok_c and ok_d and ok_e
    print(f"{name}: SR={s['sr']:.2f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% scram={sp:.3f} gates[a={ok_a},c={ok_c},d={ok_d},e={ok_e}] ALL={'PASS' if ok else 'FAIL'}")
    print("   negyrs:", {k:round(v,2) for k,v in s['yearly'].items() if v<0})
    return ok, s

if __name__ == "__main__":
    print("=== FINAL: MM-blend plateau scan over (w, cap, floor) ===")
    grid = {}
    for w in [0.2, 0.3, 0.4]:
        for cap in [1.5, 2.0, 2.5]:
            for floor in [0.25, 0.5]:
                net, pos, base = build(w=w, cap=cap, floor=floor)
                s = stats(net)
                grid[(w,cap,floor)] = (s['sr'], net, pos, base)
                print(f"w={w} cap={cap} floor={floor}: SR={s['sr']:.2f}")
    peak = max(v[0] for v in grid.values())
    print(f"\npeak SR in grid: {peak:.2f}; neighbors within 20% of peak:")
    for k,(v,_,_,_) in sorted(grid.items()):
        if v >= 0.8*peak: print("  ", k, round(v,2))
