import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
import bt.gates as bgates
from bt.gates import plateau_ok, lag1_autocorr, uniq_ratio, zero_runs_long, corr_to
from bt.metrics import sharpe_d, neg_years, ann_geo, max_dd, half_split
from hunt_r1 import pair_book, load_series, zscore_trailing, hysteresis_state, net_of
from run_hunt import spreads, champ_rets, benchmark_series, v2_battery, CHAMP
DIES = "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv"
BRWT15 = "/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv"

champ = champ_rets(); spy, ief, cta = benchmark_series()
d = spreads()['ho_br']

def book(win, zi, zo):
    net, We, g, rpu = pair_book(d['r_a'], d['r_b'], d['spread'], win=win, z_in=zi,
                                z_out=zo, side='meanrev', return_rpu=True)
    live = (We.fillna(0) != 0).any(axis=1)
    return net[net.index >= live.idxmax()], We, rpu

print("=== window plateau AT the chosen corner (z1.0 zo1.0) ===")
srs_w = {}
for w in (21, 40, 63, 90, 126):
    n, _, _ = book(w, 1.0, 1.0)
    srs_w[w] = sharpe_d(n)
print({k: round(v, 3) for k, v in srs_w.items()})
ok, info = plateau_ok(srs_w, 63)
print(f"plateau@63 ok={ok} nb={ {k: round(v,3) for k,v in info['neighbors'].items()} } thr={info['threshold']:.3f}")

print("\n=== CANDIDATE w63 z1.0 zo1.0: full battery ===")
net, We, rpu = book(63, 1.0, 1.0)
print(f"net SR={sharpe_d(net):.4f} ann={ann_geo(net)*100:.2f}% MDD={max_dd(net)*100:.2f}% "
      f"H1={half_split(net)[0]:.3f} H2={half_split(net)[1]:.3f} neg={neg_years(net)} "
      f"ac1={lag1_autocorr(net):+.4f} uniqR={uniq_ratio(net):.4f} "
      f"corr_champ={corr_to(champ, net):+.4f}")
v2 = v2_battery(rpu.reindex(We.index).fillna(0.0), sig=We['a'].fillna(0.0),
                ref=champ, spy=spy, ief=ief, cta=cta)
print(f"V2: v2sr={v2['sr']:.4f} v2corr={v2['corr']:+.4f} leak_ok={v2['leak_ok']} "
      f"bp_ok={v2['beats_passive_ok']} scr_p={v2['scr_p']} best_passive={v2['beats_passive']['best_passive_name']}:{v2['beats_passive']['best_passive_sr']:.3f} "
      f"ac1={v2['ac1']:.4f} uniq={v2['uniq']:.4f} PASS={v2['pass']}")
print(f"leak detail: corr0={v2['leak']['same_period_corr']:+.4f} p={v2['leak']['same_period_p']:.2e} lag_scan={ {k: round(v,4) for k,v in v2['leak']['lag_scan'].items()} }")

print("\n=== T+2 decay ===")
z = zscore_trailing(d['spread'], win=63)
st = hysteresis_state(z, z_in=1.0, z_out=1.0)
for extra in (0, 1, 2):
    W = pd.DataFrame({'a': -st, 'b': st}).shift(extra).fillna(0.0)
    n2, We2, g2 = net_of(W, pd.concat({'a': d['r_a'], 'b': d['r_b']}, axis=1))
    live = (We2.fillna(0) != 0).any(axis=1)
    n2 = n2[n2.index >= live.idxmax()]
    print(f"  extra_lag={extra}: net SR={sharpe_d(n2):.3f}")

print("\n=== corr to champion energy sleeves ===")
for nm, p in (('diescrack_L40Z20', DIES), ('brwt15_2000', BRWT15)):
    s = load_series(p, 'ret')
    print(f"  corr to {nm}: {corr_to(s, net):+.4f}")

print("\n=== yearly ===")
yr = net.groupby(net.index.year).apply(lambda x: (1+x).prod()-1)
print(yr.round(4).to_string())
