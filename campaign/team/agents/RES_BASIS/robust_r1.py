#!/usr/bin/env python3
"""RES_BASIS R1 robustness: plateau grid (v1 3b), energy-sleeve corr (re-dress check),
T+2 decay, net flatten stats, blend-frontier battery (§8) for the two net-passers."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")

import numpy as np
import pandas as pd
from bt.gates import plateau_ok, lag1_autocorr, uniq_ratio, zero_runs_long, corr_to
from bt.metrics import sharpe_d, neg_years, ann_geo, max_dd, half_split
from hunt_r1 import pair_book, load_series, ROOT
from run_hunt import spreads, CHAMP

SLEEVE_LIB = f"{ROOT}/campaign/results/sleeve_library"
DIES = f"{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv"
BRWT15 = f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv"


def book(pair, win, zi, zo=1.0):
    d = spreads()[pair]
    return pair_book(d['r_a'], d['r_b'], d['spread'], win=win, z_in=zi, z_out=zo,
                     side='meanrev', return_rpu=True)


def net_of_live(t):
    net, We, g, rpu = t
    live = (We.fillna(0) != 0).any(axis=1)
    return net[net.index >= live.idxmax()], We


def main():
    champ = load_series(CHAMP, 'ret')
    print("=== PLATEAU (meanrev, ho_br, SR of NET book) ===")
    wins = [21, 40, 63, 90, 126, 189]
    srs_w = {}
    for w in wins:
        n, _ = net_of_live(book('ho_br', w, 1.5))
        srs_w[w] = sharpe_d(n)
    ok_w, info_w = plateau_ok(srs_w, 63)
    print(f"window grid SR: { {k: round(v,3) for k,v in srs_w.items()} } plateau@63 ok={ok_w} {info_w['neighbors']} thr={info_w['threshold']:.3f}")
    zis = [1.0, 1.5, 2.0, 2.5]
    srs_z = {}
    for z in zis:
        n, _ = net_of_live(book('ho_br', 63, z))
        srs_z[z] = sharpe_d(n)
    ok_z, info_z = plateau_ok(srs_z, 1.5)
    print(f"z_in grid SR: { {k: round(v,3) for k,v in srs_z.items()} } plateau@1.5 ok={ok_z} {info_z['neighbors']} thr={info_z['threshold']:.3f}")

    print("\n=== WINNER DEEP-DIVE (w63 z15 and w126 z15) ===")
    for w in (63, 126):
        net, We = net_of_live(book('ho_br', w, 1.5))
        print(f"w{w}: net SR={sharpe_d(net):.3f} ann={ann_geo(net)*100:.2f}% MDD={max_dd(net)*100:.2f}% "
              f"ac1={lag1_autocorr(net):+.3f} uniqR={uniq_ratio(net):.4f} "
              f"zruns>=20d={zero_runs_long(net, 20)} neg={neg_years(net)}")

    print("\n=== T+2 DECAY (positions lagged extra day, net SR) ===")
    d = spreads()['ho_br']
    from hunt_r1 import zscore_trailing, hysteresis_state, net_of
    z = zscore_trailing(d['spread'], win=63)
    st = hysteresis_state(z, z_in=1.5, z_out=1.0)
    import bt.engine as eng
    for extra in (0, 1, 2):
        W = pd.DataFrame({'a': -st, 'b': st}).shift(extra).fillna(0.0)
        net, We, g = net_of(W, pd.concat({'a': d['r_a'], 'b': d['r_b']}, axis=1))
        live = (We.fillna(0) != 0).any(axis=1)
        net = net[net.index >= live.idxmax()]
        print(f"  extra_lag={extra}: net SR={sharpe_d(net):.3f}")

    print("\n=== CORR to champion + champion ENERGY sleeves (re-dress check) ===")
    net63, _ = net_of_live(book('ho_br', 63, 1.5))
    net126, _ = net_of_live(book('ho_br', 126, 1.5))
    refs = {'champion': champ,
            'diescrack_L40Z20': load_series(DIES, 'ret'),
            'brwt15_2000': load_series(BRWT15, 'ret')}
    for nm, s in refs.items():
        print(f"  corr(w63, {nm})   = {corr_to(s, net63):+.4f}")
        print(f"  corr(w126, {nm}) = {corr_to(s, net126):+.4f}")
    print(f"  corr(w63, w126)  = {corr_to(net63, net126):+.4f}")

    print("\n=== BLEND FRONTIER (champion + w*sleeve, w on gross NAV, §8 battery) ===")
    for w in (0.025, 0.05, 0.10, 0.15):
        for tag, net in (('w63', net63), ('w126', net126)):
            s = net.reindex(champ.index).fillna(0.0) * (1.6 / 0.08) * w  # sleeve relevered to w of 1.6x NAV
            b = champ + s
            sr0, sr1 = sharpe_d(champ), sharpe_d(b)
            d_ann = (ann_geo(b) - ann_geo(champ)) * 100
            d_mdd = (max_dd(b) - max_dd(champ)) * 100
            neg, worst = neg_years(b)
            dh1 = sharpe_d(b.iloc[:len(b)//2]) - sharpe_d(champ.iloc[:len(champ)//2])
            dh2 = sharpe_d(b.iloc[len(b)//2:]) - sharpe_d(champ.iloc[len(champ)//2:])
            print(f"  {tag} w={w:.3f}: dSR={sr1-sr0:+.3f} dAnn={d_ann:+.3f}pp dMDD={d_mdd:+.3f}pp "
                  f"neg={neg} worst={worst*100:.2f}% dH1={dh1:+.3f} dH2={dh2:+.3f}")


if __name__ == '__main__':
    main()
